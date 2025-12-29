from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Set, Tuple

from .config.loader import resolve_suite
from .config.schema import (
    AnswerFormat,
    PromptFixedConfig,
    PromptMatchFormulaConfig,
    Representation,
    SuiteConfig,
)
from .parsers import parse_contradiction, parse_yes_no
from .problems.reader import iter_problem_rows

from .problems.filters import (
    limit_per_case,
    only_ids as filter_only_ids,
    only_maxlen as filter_only_maxlen,
    only_maxvars as filter_only_maxvars,
)
from .providers.router import run_chat
from .prompts.render import render_prompt
from .pricing.loader import load_pricing_table
from .pricing.cost import compute_cost_usd, match_rate


def _find_refactor_root(suite_path: Path) -> Path:
    cur = suite_path.resolve()
    for p in [cur.parent, *cur.parents]:
        if p.name == "_refactor":
            return p
    # fallback: suite is expected under _refactor/configs/suites
    return suite_path.resolve().parents[2]


def _thinking_mode_label(target: Dict[str, Any]) -> str:
    thinking = target.get("thinking") or {}
    try:
        enabled = bool(thinking.get("enabled"))
    except Exception:
        enabled = False
    if not enabled:
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


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _jsonl_iter(path: Path) -> Iterator[Dict[str, Any]]:
    with path.open("r") as f:
        for line in f:
            txt = line.strip()
            if not txt:
                continue
            try:
                obj = json.loads(txt)
            except Exception:
                continue
            if isinstance(obj, dict):
                yield obj


def _load_latest_results(results_path: Path) -> Dict[str, Dict[str, Any]]:
    """Return the latest result row per id (append-only JSONL)."""
    if not results_path.exists():
        return {}
    latest: Dict[str, Dict[str, Any]] = {}
    for obj in _jsonl_iter(results_path):
        rid = obj.get("id")
        if rid is None:
            continue
        latest[str(rid)] = obj
    return latest


def _should_rerun_latest(latest_row: Dict[str, Any], *, rerun_errors: bool, rerun_unclear: bool) -> bool:
    if rerun_errors and latest_row.get("error"):
        return True
    if rerun_unclear:
        try:
            if int(latest_row.get("parsed_answer")) == 2:
                return True
        except Exception:
            pass
    return False


def _load_done_ids(results_path: Path, *, rerun_errors: bool, rerun_unclear: bool) -> Set[str]:
    """Return ids considered 'done' for resume, based on the latest row per id.

    If rerun flags are enabled, ids whose latest row matches the rerun criteria are excluded
    (so they will be reprocessed).
    """
    latest = _load_latest_results(results_path)
    done: Set[str] = set()
    for rid, row in latest.items():
        if _should_rerun_latest(row, rerun_errors=rerun_errors, rerun_unclear=rerun_unclear):
            continue
        done.add(rid)
    return done


def _safe_int(v: Any) -> int:
    try:
        return int(v) if v is not None else 0
    except Exception:
        return 0


def _compute_unique_stats_from_latest(latest_by_id: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Compute accuracy-related stats over unique problems (latest attempt per id)."""
    stats: Dict[str, Any] = {
        "total": len(latest_by_id),
        "answered": 0,
        "correct": 0,
        "unclear": 0,
        "pending": 0,
        "errors": 0,
        # Usage/cost fields are filled from provenance (attempt spend) when available.
        "input_tokens": 0,
        "output_tokens": 0,
        "reasoning_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "cost_total_usd": 0.0,
        "cost_input_usd": 0.0,
        "cost_output_usd": 0.0,
        # Extra: how many attempts were recorded in provenance (useful when rerunning)
        "attempts_total": 0,
    }
    for row in latest_by_id.values():
        # Async submit-only mode: treat rows with an OpenAI response id but no parsed answer
        # as pending (not unclear).
        if row.get("openai_response_id") and row.get("parsed_answer") is None and not row.get("error"):
            stats["pending"] += 1
            continue
        try:
            parsed = row.get("parsed_answer")
            parsed_i = int(parsed) if parsed is not None else None
        except Exception:
            parsed_i = None
        if parsed_i == 2 or parsed_i is None:
            stats["unclear"] += 1
        else:
            stats["answered"] += 1
        if row.get("correct") is True:
            stats["correct"] += 1
        if row.get("error"):
            stats["errors"] += 1
    return stats


def _sum_usage_from_provenance(prov_path: Path) -> Dict[str, Any]:
    """Sum usage across all attempts in results.provenance.jsonl (represents spend)."""
    totals: Dict[str, Any] = {
        "input_tokens": 0,
        "output_tokens": 0,
        "reasoning_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "attempts_total": 0,
    }
    if not prov_path.exists():
        return totals
    for obj in _jsonl_iter(prov_path):
        totals["attempts_total"] += 1
        usage = obj.get("usage") or {}
        totals["input_tokens"] += _safe_int(usage.get("input_tokens"))
        totals["output_tokens"] += _safe_int(usage.get("output_tokens"))
        totals["reasoning_tokens"] += _safe_int(usage.get("reasoning_tokens"))
        totals["cache_creation_input_tokens"] += _safe_int(usage.get("cache_creation_input_tokens"))
        totals["cache_read_input_tokens"] += _safe_int(usage.get("cache_read_input_tokens"))
    return totals


def _sum_cost_from_provenance(prov_path: Path, rate_obj: Optional[Dict[str, Any]]) -> Dict[str, float]:
    """Sum USD cost across all attempts in provenance (represents spend)."""
    totals: Dict[str, float] = {"cost_total_usd": 0.0, "cost_input_usd": 0.0, "cost_output_usd": 0.0}
    if not prov_path.exists() or not rate_obj:
        return totals
    try:
        from .pricing.schema import ModelRate

        rate = ModelRate(**rate_obj)
    except Exception:
        return totals

    for obj in _jsonl_iter(prov_path):
        usage = obj.get("usage") or {}
        try:
            c = compute_cost_usd(rate, usage)
            totals["cost_total_usd"] += float(c.get("total_usd") or 0.0)
            totals["cost_input_usd"] += float(c.get("input_usd") or 0.0)
            totals["cost_output_usd"] += float(c.get("output_usd") or 0.0)
        except Exception:
            continue
    return totals


def _subset_filter(cfg: SuiteConfig, rows: Iterable[Any]) -> Iterator[Any]:
    if cfg.subset.value == "mixed":
        return iter(rows)
    if cfg.subset.value == "hornonly":
        return (r for r in rows if getattr(r, "mustbehorn", None) == 1)
    if cfg.subset.value == "nonhornonly":
        return (r for r in rows if getattr(r, "mustbehorn", None) == 0)
    return iter(rows)


def _select_prompting(
    prompting: Any, row: Any
) -> Tuple[Representation, str, AnswerFormat, Dict[str, Any]]:
    if isinstance(prompting, PromptFixedConfig):
        return (
            prompting.representation,
            prompting.template,
            prompting.answer_format,
            dict(prompting.variables or {}),
        )
    if isinstance(prompting, PromptMatchFormulaConfig):
        is_horn = getattr(row, "mustbehorn", None) == 1
        branch = prompting.horn if is_horn else prompting.nonhorn
        return (branch.representation, branch.template, branch.answer_format, dict(branch.variables or {}))
    raise TypeError(f"Unsupported prompting config: {type(prompting)}")


def _parse_answer(answer_format: AnswerFormat, text: str, *, yes_tokens: Optional[List[str]], no_tokens: Optional[List[str]]) -> int:
    if answer_format == AnswerFormat.yes_no:
        return parse_yes_no(text, yes_tokens=yes_tokens, no_tokens=no_tokens)
    if answer_format == AnswerFormat.contradiction_satisfiable:
        return parse_contradiction(text)
    return 2


def _expected_answer(row: Any) -> Optional[int]:
    # 0 = unsat / contradiction / YES(p0 derivable)
    # 1 = sat / satisfiable / NO(p0 not derivable)
    flag = getattr(row, "issatisfiable", None)
    if flag is None:
        return None
    return 1 if int(flag) == 1 else 0


def _build_outpath(root: Path, cfg: SuiteConfig, target: Dict[str, Any], run_id: str) -> Path:
    out = cfg.output_pattern
    out = (
        out.replace("${name}", cfg.name)
        .replace("${run}", run_id)
        .replace("${provider}", str(target.get("provider")))
        .replace("${model}", str(target.get("model")))
        .replace("${thinking_mode}", _thinking_mode_label(target))
    )
    return (root / out).resolve()


def _derive_paths(results_path: Path) -> Tuple[Path, Path]:
    # results.jsonl -> results.provenance.jsonl / results.summary.json
    p = str(results_path)
    if p.endswith(".jsonl"):
        base = p[: -len(".jsonl")]
        return (Path(base + ".provenance.jsonl"), Path(base + ".summary.json"))
    return (Path(p + ".provenance.jsonl"), Path(p + ".summary.json"))


def run_suite(
    *,
    suite_path: str,
    run_id: Optional[str] = None,
    output_root: Optional[str] = None,
    limit: Optional[int] = None,
    dry_run: bool = False,
    submit_only: bool = False,
    only_providers: Optional[List[str]] = None,
    resume: Optional[bool] = None,
    lockstep: Optional[bool] = None,
    only_maxvars: Optional[Set[int]] = None,
    only_maxlen: Optional[Set[int]] = None,
    only_ids: Optional[Set[str]] = None,
    case_limit: Optional[int] = None,
    rerun_errors: bool = False,
    rerun_unclear: bool = False,
) -> None:
    suite_file = Path(suite_path).resolve()
    root = _find_refactor_root(suite_file)
    out_root = Path(output_root).resolve() if output_root else root
    cfg = resolve_suite(str(suite_file))

    if submit_only and dry_run:
        raise ValueError("--submit-only cannot be combined with --dry-run")

    effective_limit_rows: Optional[int] = int(limit) if limit is not None else cfg.dataset.limit_rows
    if resume is not None:
        cfg.resume = bool(resume)
    if lockstep is not None:
        cfg.concurrency.lockstep = bool(lockstep)

    rid = run_id or time.strftime("%Y%m%d-%H%M%S")

    targets: List[Dict[str, Any]] = [t.model_dump(mode="json", exclude_none=True) for t in (cfg.targets or [])]
    if only_providers:
        allowed = {p.lower() for p in only_providers}
        targets = [t for t in targets if str(t.get("provider", "")).lower() in allowed]
    if not targets:
        raise ValueError("No targets selected")

    pricing_table = None
    if cfg.pricing_table:
        p = Path(cfg.pricing_table)
        if not p.is_absolute():
            p = (root / cfg.pricing_table).resolve()
        if p.exists():
            pricing_table = load_pricing_table(str(p))

    dataset_path = cfg.dataset.path
    data_path = Path(dataset_path)
    if not data_path.is_absolute():
        data_path = (root / dataset_path).resolve()
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    # Pre-load problems (small enough for our current datasets; simplifies lockstep)
    rows_iter = iter_problem_rows(str(data_path), skip_rows=cfg.dataset.skip_rows)
    rows_iter = _subset_filter(cfg, rows_iter)
    if only_ids:
        rows_iter = filter_only_ids(rows_iter, only_ids)
    if only_maxvars:
        rows_iter = filter_only_maxvars(rows_iter, only_maxvars)
    if only_maxlen:
        rows_iter = filter_only_maxlen(rows_iter, only_maxlen)
    if case_limit is not None:
        rows_iter = limit_per_case(rows_iter, int(case_limit))
    # Note: we intentionally do NOT apply `effective_limit_rows` here.
    # `--limit` is defined as "max processed problems" and should be applied AFTER skipping done ids,
    # so repeated `--resume --limit N` invocations can progress through the dataset in batches.
    rows = list(rows_iter)
    if not rows:
        raise ValueError("No dataset rows selected after applying filters")

    dataset_selection = {
        "only_maxvars": sorted(list(only_maxvars)) if only_maxvars else None,
        "only_maxlen": sorted(list(only_maxlen)) if only_maxlen else None,
        "only_ids": sorted(list(only_ids)) if only_ids else None,
        "case_limit": int(case_limit) if case_limit is not None else None,
    }

    # Prepare per-target outputs + resume sets
    out_info: List[Dict[str, Any]] = []
    for t in targets:
        results_path = _build_outpath(out_root, cfg, t, rid)
        prov_path, summary_path = _derive_paths(results_path)
        _ensure_dir(results_path)
        _ensure_dir(prov_path)
        _ensure_dir(summary_path)
        done_ids = (
            _load_done_ids(results_path, rerun_errors=rerun_errors, rerun_unclear=rerun_unclear)
            if cfg.resume
            else set()
        )
        rate = None
        if pricing_table is not None:
            try:
                rate = match_rate(pricing_table, provider=str(t.get("provider")), model=str(t.get("model")))
            except Exception:
                rate = None
        out_info.append(
            {
                "target": t,
                "results_path": results_path,
                "provenance_path": prov_path,
                "summary_path": summary_path,
                "pricing_rate": rate.model_dump(mode="json", exclude_none=True) if rate is not None else None,
                "done_ids": done_ids,
                "stats": {
                    "total": 0,
                    "answered": 0,
                    "correct": 0,
                    "unclear": 0,
                    "errors": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "reasoning_tokens": 0,
                    "cache_creation_input_tokens": 0,
                    "cache_read_input_tokens": 0,
                    "cost_total_usd": 0.0,
                    "cost_input_usd": 0.0,
                    "cost_output_usd": 0.0,
                },
            }
        )

    yes_tokens = cfg.parse.yes_tokens
    no_tokens = cfg.parse.no_tokens

    def _extract_openai_response_id(raw: Any) -> Optional[str]:
        try:
            if isinstance(raw, dict):
                if isinstance(raw.get("response"), dict) and raw["response"].get("id"):
                    return str(raw["response"]["id"])
                if raw.get("id"):
                    return str(raw["id"])
        except Exception:
            pass
        return None

    def _extract_openai_status(raw: Any) -> Optional[str]:
        try:
            if isinstance(raw, dict):
                obj = raw.get("response") if isinstance(raw.get("response"), dict) else raw
                st = obj.get("status") if isinstance(obj, dict) else None
                return str(st) if st else None
        except Exception:
            pass
        return None

    def call_one(target: Dict[str, Any], prompt: str, sysprompt: Optional[str]) -> Dict[str, Any]:
        attempts = 0
        err_msg: Optional[str] = None
        text = ""
        thinking_text = None
        meta: Dict[str, Any] = {}
        dur_ms: Optional[int] = None
        while True:
            try:
                start = time.time()
                res = run_chat(
                    provider=target.get("provider"),
                    model=target.get("model"),
                    prompt=prompt,
                    sysprompt=sysprompt,
                    max_tokens=target.get("max_tokens"),
                    temperature=float(target.get("temperature") or 0.0),
                    seed=target.get("seed"),
                    thinking=target.get("thinking"),
                    poll=(not submit_only),
                )
                dur_ms = int((time.time() - start) * 1000)
                text = res.get("text") or ""
                thinking_text = res.get("thinking_text")
                meta = {k: v for k, v in res.items() if k not in ("text", "thinking_text")}
                err_msg = None
                break
            except Exception as e:
                attempts += 1
                err_msg = str(e)
                if attempts >= cfg.concurrency.retry.max_attempts:
                    break
                # backoff
                try:
                    backoffs = cfg.concurrency.retry.backoff_seconds
                    sleep_s = backoffs[min(attempts - 1, len(backoffs) - 1)]
                except Exception:
                    sleep_s = 1
                time.sleep(max(0, int(sleep_s)))
        return {
            "text": text,
            "thinking_text": thinking_text,
            "meta": meta,
            "error": err_msg,
            "timing_ms": dur_ms,
            "attempts": attempts,
        }

    # Execution
    processed_rows = 0
    for row in rows:
        rid_row = str(getattr(row, "id", ""))
        # Skip rows that are already done for all targets (common when resuming).
        if all(rid_row in oi["done_ids"] for oi in out_info):
            continue
        # Apply `--limit` as a cap on *processed problems* (after skipping done ids).
        if effective_limit_rows is not None and processed_rows >= int(effective_limit_rows):
            break
        processed_rows += 1
        exp = _expected_answer(row)

        # Render prompt once per row based on suite policy
        rep, tmpl_rel, ans_fmt, vars_ = _select_prompting(cfg.prompting, row)
        tmpl_path = Path(tmpl_rel)
        if not tmpl_path.is_absolute():
            tmpl_path = (root / tmpl_rel).resolve()
        prompt_text = render_prompt(
            problem=row,
            template_path=str(tmpl_path),
            representation=rep.value,
            variables=vars_,
        )
        sysprompt = None

        # Call providers (optionally lockstep/concurrent across targets)
        lockstep_responses: Dict[str, Dict[str, Any]] = {}
        if cfg.concurrency.lockstep and not dry_run:
            with ThreadPoolExecutor(max_workers=max(1, min(cfg.concurrency.workers, len(out_info)))) as ex:
                future_map = {}
                for oi in out_info:
                    if rid_row in oi["done_ids"]:
                        continue
                    t = oi["target"]
                    key = f"{t.get('provider')}:{t.get('model')}:{_thinking_mode_label(t)}"
                    future_map[ex.submit(call_one, t, prompt_text, sysprompt)] = key
                for fut in as_completed(future_map):
                    key = future_map[fut]
                    try:
                        lockstep_responses[key] = fut.result()
                    except Exception as e:
                        lockstep_responses[key] = {
                            "text": "",
                            "thinking_text": None,
                            "meta": {},
                            "error": str(e),
                            "timing_ms": None,
                            "attempts": 0,
                        }

        for oi in out_info:
            if rid_row in oi["done_ids"]:
                continue

            t = oi["target"]
            results_path: Path = oi["results_path"]
            prov_path: Path = oi["provenance_path"]
            stats = oi["stats"]

            if dry_run:
                text = ""
                thinking_text = None
                meta = {}
                err = None
                dur_ms = None
                attempts = 0
            else:
                if cfg.concurrency.lockstep:
                    key = f"{t.get('provider')}:{t.get('model')}:{_thinking_mode_label(t)}"
                    resp = lockstep_responses.get(key) or {
                        "text": "",
                        "thinking_text": None,
                        "meta": {},
                        "error": "missing lockstep response",
                        "timing_ms": None,
                        "attempts": 0,
                    }
                else:
                    resp = call_one(t, prompt_text, sysprompt)
                text = resp["text"]
                thinking_text = resp["thinking_text"]
                meta = resp["meta"]
                err = resp["error"]
                dur_ms = resp["timing_ms"]
                attempts = resp["attempts"]

            # In submit-only mode we only enqueue background work and store the provider response id.
            # Parsing happens later in a collector step.
            if submit_only and not err:
                parsed = None
            else:
                parsed = _parse_answer(ans_fmt, text, yes_tokens=yes_tokens, no_tokens=no_tokens)
            correct = None
            if exp is not None:
                try:
                    if parsed in (0, 1):
                        correct = parsed == exp
                except Exception:
                    pass

            # Provider-resolved model id (best-effort). Useful when using aliases.
            model_resolved = meta.get("model") if isinstance(meta, dict) else None
            raw_resp = meta.get("raw_response") if isinstance(meta, dict) else None
            openai_response_id = _extract_openai_response_id(raw_resp) if (t.get("provider") == "openai") else None
            openai_response_status = _extract_openai_status(raw_resp) if (t.get("provider") == "openai") else None

            # Minimal results row
            result_row: Dict[str, Any] = {
                "id": getattr(row, "id", None),
                "meta": {
                    "maxvars": getattr(row, "maxvarnr", None),
                    "maxlen": getattr(row, "maxlen", None),
                    "horn": getattr(row, "mustbehorn", None),
                    "satflag": getattr(row, "issatisfiable", None),
                },
                "provider": t.get("provider"),
                "model": t.get("model"),
                "model_resolved": model_resolved,
                "parsed_answer": parsed,
                "correct": correct,
                "error": err,
                "openai_response_id": openai_response_id,
                "openai_response_status": openai_response_status,
            }

            # Provenance row (optional)
            prov_row: Dict[str, Any] = {
                **result_row,
                "prompt_template": tmpl_rel,
                "representation": rep.value,
                "answer_format": ans_fmt.value,
                "prompt": prompt_text if cfg.outputs.provenance.include_prompt else None,
                "completion_text": (None if (submit_only and not err) else text),
                "thinking_text": thinking_text if cfg.outputs.provenance.include_thinking_text else None,
                "finish_reason": meta.get("finish_reason"),
                "usage": meta.get("usage") if cfg.outputs.provenance.include_usage else None,
                "raw_response": meta.get("raw_response") if cfg.outputs.provenance.include_raw_response else None,
                "timing_ms": dur_ms,
                "attempts": attempts,
            }

            with results_path.open("a") as f:
                f.write(json.dumps(result_row, ensure_ascii=False) + "\n")
            if cfg.outputs.provenance.enabled:
                with prov_path.open("a") as f:
                    f.write(json.dumps(prov_row, ensure_ascii=False) + "\n")

            # Update stats
            stats["total"] += 1
            if parsed == 2:
                stats["unclear"] += 1
            else:
                stats["answered"] += 1
            if correct is True:
                stats["correct"] += 1
            if err:
                stats["errors"] += 1
            try:
                usage = meta.get("usage") or {}
                stats["input_tokens"] += int(usage.get("input_tokens") or 0)
                stats["output_tokens"] += int(usage.get("output_tokens") or 0)
                stats["reasoning_tokens"] += int(usage.get("reasoning_tokens") or 0)
                stats["cache_creation_input_tokens"] += int(usage.get("cache_creation_input_tokens") or 0)
                stats["cache_read_input_tokens"] += int(usage.get("cache_read_input_tokens") or 0)
                if pricing_table is not None and oi.get("pricing_rate") is not None:
                    rate_obj = oi["pricing_rate"]
                    # compute_cost_usd expects the ModelRate object; reconstruct via dict
                    try:
                        from .pricing.schema import ModelRate

                        rate = ModelRate(**rate_obj)
                        c = compute_cost_usd(rate, usage)
                        stats["cost_total_usd"] += float(c.get("total_usd") or 0.0)
                        stats["cost_input_usd"] += float(c.get("input_usd") or 0.0)
                        stats["cost_output_usd"] += float(c.get("output_usd") or 0.0)
                    except Exception:
                        pass
            except Exception:
                pass

        # End per-row

    # Write summaries
    for oi in out_info:
        summary_path: Path = oi["summary_path"]
        results_path: Path = oi["results_path"]
        prov_path: Path = oi["provenance_path"]
        latest = _load_latest_results(results_path)
        stats = _compute_unique_stats_from_latest(latest)
        # Sum usage/cost from provenance across all attempts (spend); keeps numbers stable across resume.
        if cfg.outputs.provenance.enabled:
            stats.update(_sum_usage_from_provenance(prov_path))
            stats.update(_sum_cost_from_provenance(prov_path, oi.get("pricing_rate")))

        acc = (stats["correct"] / stats["total"]) if stats["total"] else 0.0
        manifest_path = summary_path.parent / "run.manifest.json"
        payload = {
            "suite": cfg.name,
            "run": rid,
            "provider": oi["target"].get("provider"),
            "model": oi["target"].get("model"),
            "thinking_mode": _thinking_mode_label(oi["target"]),
            "dataset_selection": dataset_selection,
            "pricing_table": cfg.pricing_table,
            "pricing_rate": oi.get("pricing_rate"),
            "stats": stats,
            "accuracy": acc,
        }
        summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

        # Reproducibility: record what we actually ran (suite config inputs + target + pricing rate).
        try:
            manifest = {
                "suite_path": str(suite_file),
                "suite": cfg.name,
                "run": rid,
                "dataset": cfg.dataset.model_dump(mode="json"),
                "dataset_selection": dataset_selection,
                "prompting": cfg.prompting.model_dump(mode="json"),
                "target": oi["target"],
                "thinking_mode": _thinking_mode_label(oi["target"]),
                "pricing_table": cfg.pricing_table,
                "pricing_rate": oi.get("pricing_rate"),
            }
            manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        except Exception:
            pass

        # Operational trace: append a per-invocation record (helps when terminal history is lost).
        try:
            inv_path = summary_path.parent / "run.invocations.jsonl"
            inv = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "suite_path": str(suite_file),
                "suite": cfg.name,
                "run": rid,
                "provider": oi["target"].get("provider"),
                "model": oi["target"].get("model"),
                "thinking_mode": _thinking_mode_label(oi["target"]),
                "submit_only": bool(submit_only),
                "poll": (not submit_only),
                "limit": (int(limit) if limit is not None else None),
                "effective_limit_rows": (int(effective_limit_rows) if effective_limit_rows is not None else None),
                "resume": bool(cfg.resume),
                "lockstep": bool(cfg.concurrency.lockstep),
                "rerun_errors": bool(rerun_errors),
                "rerun_unclear": bool(rerun_unclear),
                "dataset_selection": dataset_selection,
                "env": {
                    "LLMLOG_OPENAI_HTTP_TIMEOUT_S": os.environ.get("LLMLOG_OPENAI_HTTP_TIMEOUT_S"),
                    "LLMLOG_OPENAI_POLL_TIMEOUT_S": os.environ.get("LLMLOG_OPENAI_POLL_TIMEOUT_S"),
                },
            }
            with inv_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(inv, ensure_ascii=False) + "\n")
        except Exception:
            pass


