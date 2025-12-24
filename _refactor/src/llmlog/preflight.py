from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .config.loader import resolve_suite
from .config.schema import PromptFixedConfig, PromptMatchFormulaConfig, Representation, SuiteConfig
from .pricing.cost import match_rate
from .pricing.loader import load_pricing_table
from .problems.reader import iter_problem_rows
from .problems.filters import (
    limit_per_case,
    only_ids as filter_only_ids,
    only_maxlen as filter_only_maxlen,
    only_maxvars as filter_only_maxvars,
)
from .prompts.render import render_prompt


def _find_refactor_root(suite_path: Path) -> Path:
    cur = suite_path.resolve()
    for p in [cur.parent, *cur.parents]:
        if p.name == "_refactor":
            return p
    return suite_path.resolve().parents[2]


def _thinking_mode_label(target: Dict[str, Any]) -> str:
    thinking = target.get("thinking") or {}
    if not bool(thinking.get("enabled")):
        return "nothink"
    eff = thinking.get("effort")
    if isinstance(eff, str) and eff:
        return f"think_{eff.lower()}"
    budget = thinking.get("budget_tokens")
    if budget is None:
        return "think"
    try:
        return f"think_{int(budget)}"
    except Exception:
        return "think"


def _subset_keep(cfg: SuiteConfig, row: Any) -> bool:
    if cfg.subset.value == "mixed":
        return True
    if cfg.subset.value == "hornonly":
        return getattr(row, "mustbehorn", None) == 1
    if cfg.subset.value == "nonhornonly":
        return getattr(row, "mustbehorn", None) == 0
    return True


def _select_prompting(prompting: Any, row: Any) -> Tuple[Representation, str, Dict[str, Any]]:
    if isinstance(prompting, PromptFixedConfig):
        return prompting.representation, prompting.template, dict(prompting.variables or {})
    if isinstance(prompting, PromptMatchFormulaConfig):
        is_horn = getattr(row, "mustbehorn", None) == 1
        branch = prompting.horn if is_horn else prompting.nonhorn
        return branch.representation, branch.template, dict(branch.variables or {})
    raise TypeError(f"Unsupported prompting config: {type(prompting)}")


def _estimate_tokens_from_text(text: str) -> int:
    # Provider tokenizers differ; for preflight we use a rough heuristic (~4 chars/token).
    # This is intended to provide order-of-magnitude cost awareness, not billing precision.
    t = text or ""
    if not t:
        return 0
    return max(1, int(len(t) / 4))


@dataclass(frozen=True)
class TargetPreflight:
    provider: str
    model: str
    thinking_mode: str
    max_tokens: Optional[int]
    pricing_rate: Optional[Dict[str, Any]]


@dataclass(frozen=True)
class SuitePreflight:
    suite_name: str
    run_rows: int
    avg_prompt_tokens_est: int
    targets: List[TargetPreflight]
    pricing_table: Optional[str]


def preflight_suite(
    *,
    suite_path: str,
    limit: Optional[int] = None,
    only_providers: Optional[List[str]] = None,
    only_maxvars: Optional[Set[int]] = None,
    only_maxlen: Optional[Set[int]] = None,
    only_ids: Optional[Set[str]] = None,
    case_limit: Optional[int] = None,
) -> SuitePreflight:
    suite_file = Path(suite_path).resolve()
    root = _find_refactor_root(suite_file)
    cfg = resolve_suite(str(suite_file))
    if limit is not None:
        cfg.dataset.limit_rows = int(limit)

    targets = [t.model_dump(mode="json", exclude_none=True) for t in (cfg.targets or [])]
    if only_providers:
        allowed = {p.lower() for p in only_providers}
        targets = [t for t in targets if str(t.get("provider", "")).lower() in allowed]

    # Pricing table (optional)
    pricing_table = None
    if cfg.pricing_table:
        p = Path(cfg.pricing_table)
        if not p.is_absolute():
            p = (root / cfg.pricing_table).resolve()
        if p.exists():
            pricing_table = load_pricing_table(str(p))

    # Count rows and estimate average prompt length from a small sample
    data_path = Path(cfg.dataset.path)
    if not data_path.is_absolute():
        data_path = (root / cfg.dataset.path).resolve()

    sample_prompts: List[str] = []
    run_rows = 0

    rows = iter_problem_rows(str(data_path), skip_rows=cfg.dataset.skip_rows)
    rows = (r for r in rows if _subset_keep(cfg, r))
    if only_ids:
        rows = filter_only_ids(rows, only_ids)
    if only_maxvars:
        rows = filter_only_maxvars(rows, only_maxvars)
    if only_maxlen:
        rows = filter_only_maxlen(rows, only_maxlen)
    if case_limit is not None:
        rows = limit_per_case(rows, int(case_limit))

    for row in rows:
        run_rows += 1
        if len(sample_prompts) < 5:
            rep, tmpl_rel, vars_ = _select_prompting(cfg.prompting, row)
            tmpl_path = Path(tmpl_rel)
            if not tmpl_path.is_absolute():
                tmpl_path = (root / tmpl_rel).resolve()
            sample_prompts.append(
                render_prompt(problem=row, template_path=str(tmpl_path), representation=rep.value, variables=vars_)
            )
        if cfg.dataset.limit_rows is not None and run_rows >= int(cfg.dataset.limit_rows):
            break

    avg_prompt_tokens_est = 0
    if sample_prompts:
        avg_prompt_tokens_est = int(sum(_estimate_tokens_from_text(p) for p in sample_prompts) / len(sample_prompts))

    out_targets: List[TargetPreflight] = []
    for t in targets:
        rate = None
        if pricing_table is not None:
            try:
                r = match_rate(pricing_table, provider=str(t.get("provider")), model=str(t.get("model")))
                rate = r.model_dump(mode="json", exclude_none=True) if r is not None else None
            except Exception:
                rate = None
        out_targets.append(
            TargetPreflight(
                provider=str(t.get("provider")),
                model=str(t.get("model")),
                thinking_mode=_thinking_mode_label(t),
                max_tokens=(int(t.get("max_tokens")) if t.get("max_tokens") is not None else None),
                pricing_rate=rate,
            )
        )

    return SuitePreflight(
        suite_name=cfg.name,
        run_rows=run_rows,
        avg_prompt_tokens_est=avg_prompt_tokens_est,
        targets=out_targets,
        pricing_table=cfg.pricing_table,
    )


def estimate_cost_upper_bound_usd(
    *,
    preflight: SuitePreflight,
) -> Dict[str, Any]:
    """Estimate a rough upper bound cost using:
    - avg_prompt_tokens_est (heuristic)
    - per-target max_tokens as worst-case output tokens
    - pricing_rate (must include per-million input/output USD rates)
    """
    total = 0.0
    per_target: List[Dict[str, Any]] = []
    for t in preflight.targets:
        rate = t.pricing_rate
        if not rate:
            per_target.append(
                {
                    "provider": t.provider,
                    "model": t.model,
                    "thinking_mode": t.thinking_mode,
                    "estimated_total_usd": None,
                    "note": "missing pricing rate",
                }
            )
            continue
        in_rate = float(rate.get("input_per_million_usd") or 0.0)
        out_rate = float(rate.get("output_per_million_usd") or 0.0)
        in_tokens = preflight.avg_prompt_tokens_est * preflight.run_rows
        out_tokens = (int(t.max_tokens) if t.max_tokens is not None else 0) * preflight.run_rows
        est = (in_tokens / 1_000_000.0) * in_rate + (out_tokens / 1_000_000.0) * out_rate
        total += est
        per_target.append(
            {
                "provider": t.provider,
                "model": t.model,
                "thinking_mode": t.thinking_mode,
                "estimated_input_tokens": in_tokens,
                "estimated_output_tokens": out_tokens,
                "estimated_total_usd": est,
            }
        )
    return {"estimated_total_usd": total, "per_target": per_target}


