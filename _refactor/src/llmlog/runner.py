from __future__ import annotations

import json
import os
import time
import uuid
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
        # Keep the directory label consistent across providers and with OpenAI's
        # "effort: none" baseline runs.
        return "think_none"
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


def _is_pending_local(latest_row: Dict[str, Any]) -> bool:
    """Return True if the latest row represents a locally queued (not yet executed) submit-only item."""
    if latest_row.get("error"):
        return False
    if latest_row.get("parsed_answer") is not None:
        return False
    sub = latest_row.get("submission_id")
    return isinstance(sub, str) and sub.startswith("local_")


def _should_rerun_latest(
    latest_row: Dict[str, Any], *, rerun_errors: bool, rerun_unclear: bool, rerun_pending: bool
) -> bool:
    if rerun_errors and latest_row.get("error"):
        return True
    if rerun_pending and _is_pending_local(latest_row):
        return True
    if rerun_unclear:
        try:
            if int(latest_row.get("parsed_answer")) == 2:
                return True
        except Exception:
            pass
    return False


def _load_done_ids(results_path: Path, *, rerun_errors: bool, rerun_unclear: bool, rerun_pending: bool) -> Set[str]:
    """Return ids considered 'done' for resume, based on the latest row per id.

    If rerun flags are enabled, ids whose latest row matches the rerun criteria are excluded
    (so they will be reprocessed).
    """
    latest = _load_latest_results(results_path)
    done: Set[str] = set()
    for rid, row in latest.items():
        if _should_rerun_latest(row, rerun_errors=rerun_errors, rerun_unclear=rerun_unclear, rerun_pending=rerun_pending):
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
        # Async submit-only mode:
        # - OpenAI: rows have openai_response_id but no parsed answer yet (collected later).
        # - Non-OpenAI: rows have a local submission_id but no parsed answer yet (collected later).
        if (row.get("openai_response_id") or row.get("submission_id")) and row.get("parsed_answer") is None and not row.get("error"):
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
    rerun_pending: bool = False,
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
    invocation_id = uuid.uuid4().hex
    invocation_ts_start = datetime.now(timezone.utc).isoformat()

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
            _load_done_ids(results_path, rerun_errors=rerun_errors, rerun_unclear=rerun_unclear, rerun_pending=rerun_pending)
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
                # Per-invocation trace fields populated during execution (useful for cost/timing audits).
                "written_ids": [],
                "openai_response_ids": {},
                # For submit-only modes that batch-submit (e.g. Anthropic/Gemini), we stage work here and
                # submit after prompts are rendered.
                "batch_pending": [],
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
                    prov_l = str(t.get("provider") or "").lower()
                    # OpenAI submit-only uses provider-side async jobs; for other providers we enqueue locally
                    # (collector step performs the actual calls).
                    if submit_only and prov_l != "openai":
                        lockstep_responses[key] = {
                            "text": "",
                            "thinking_text": None,
                            "meta": {},
                            "error": None,
                            "timing_ms": None,
                            "attempts": 0,
                        }
                        continue
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
            prov_l = str(t.get("provider") or "").lower()

            # Provider-side submit-only modes:
            # - Anthropic: Messages Batches API (server-side async)
            # - Google Gemini: BatchGenerateContent (server-side async)
            # We stage requests here and submit batches after prompts are rendered.
            if submit_only and (not dry_run) and prov_l in ("anthropic", "google", "gemini"):
                try:
                    oi["batch_pending"].append(
                        {
                            "rid_row": rid_row,
                            "row_id": getattr(row, "id", None),
                            "meta": {
                                "maxvars": getattr(row, "maxvarnr", None),
                                "maxlen": getattr(row, "maxlen", None),
                                "horn": getattr(row, "mustbehorn", None),
                                "satflag": getattr(row, "issatisfiable", None),
                            },
                            "provider": t.get("provider"),
                            "model": t.get("model"),
                            "prompt_text": prompt_text,
                            "prompt_template": tmpl_rel,
                            "representation": rep.value,
                            "answer_format": ans_fmt.value,
                            "prompt_for_prov": (prompt_text if cfg.outputs.provenance.include_prompt else None),
                        }
                    )
                except Exception:
                    pass
                continue

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
                    if submit_only and prov_l != "openai":
                        resp = {
                            "text": "",
                            "thinking_text": None,
                            "meta": {},
                            "error": None,
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

            # In submit-only mode:
            # - OpenAI: enqueue provider-side background work and store response id (collector polls later).
            # - Non-OpenAI: enqueue locally (collector performs the actual provider calls later).
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
            submission_id = None
            submission_status = None
            try:
                prov_l = str(t.get("provider") or "").lower()
            except Exception:
                prov_l = ""
            if prov_l == "openai":
                submission_id = openai_response_id
                submission_status = openai_response_status
            elif submit_only and not err:
                # Local queue identifier (collector will execute).
                submission_id = f"local_{uuid.uuid4().hex}"
                submission_status = "queued"

            # Minimal results row
            result_row: Dict[str, Any] = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "invocation_id": invocation_id,
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
                "submission_id": submission_id,
                "submission_status": submission_status,
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

            # Record per-invocation mappings for later audits (which ids / resp_ids were submitted).
            try:
                oi["written_ids"].append(rid_row)
                if submit_only and not err and t.get("provider") == "openai" and openai_response_id:
                    oi["openai_response_ids"][rid_row] = openai_response_id
            except Exception:
                pass

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

    # Submit provider-side async work for submit-only runs that staged batch requests.
    # This lets the experiment be fully server-side (like OpenAI submit-only), and collected later.
    if submit_only and (not dry_run):
        # Batch sizes: keep payload sizes reasonable and allow incremental completion.
        try:
            anthropic_batch_size = int(os.environ.get("LLMLOG_ANTHROPIC_BATCH_SIZE") or 50)
        except Exception:
            anthropic_batch_size = 50
        try:
            google_batch_size = int(os.environ.get("LLMLOG_GOOGLE_BATCH_SIZE") or 50)
        except Exception:
            google_batch_size = 50
        anthropic_batch_size = max(1, anthropic_batch_size)
        google_batch_size = max(1, google_batch_size)

        def _chunked(items: List[Dict[str, Any]], n: int) -> Iterator[List[Dict[str, Any]]]:
            for i in range(0, len(items), max(1, int(n))):
                yield items[i : i + max(1, int(n))]

        # Anthropic: Messages Batches API
        try:
            import anthropic  # type: ignore

            from .providers.secrets import get_provider_key, load_secrets
        except Exception:
            anthropic = None  # type: ignore
            load_secrets = None  # type: ignore
            get_provider_key = None  # type: ignore

        # Google: Gemini Batch API (batchGenerateContent -> long-running Operation under `batches/*`)
        try:
            import http.client as http_client
            import random

            from .providers.secrets import get_provider_key as _get_key  # type: ignore
            from .providers.secrets import load_secrets as _load_secrets  # type: ignore
        except Exception:
            http_client = None  # type: ignore
            random = None  # type: ignore
            _get_key = None  # type: ignore
            _load_secrets = None  # type: ignore

        def _google_request_json(*, host: str, method: str, path: str, key: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
            method_u = (method or "GET").upper()
            body = json.dumps(payload).encode("utf-8") if payload is not None else None
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": key,
            }
            retryable_status = {429, 500, 502, 503, 504}
            last_err: Optional[BaseException] = None
            for attempt in range(1, 5):
                conn = http_client.HTTPSConnection(host, timeout=60)  # type: ignore[union-attr]
                try:
                    conn.request(method_u, path, body=body if method_u != "GET" else None, headers=headers)
                    resp = conn.getresponse()
                    raw = resp.read()
                    if resp.status != 200:
                        msg = raw.decode("utf-8", errors="ignore")
                        try:
                            data = json.loads(raw)
                            if isinstance(data, dict) and isinstance(data.get("error"), dict):
                                msg = str(data["error"].get("message") or msg)
                        except Exception:
                            pass
                        if resp.status in retryable_status and attempt < 4:
                            time.sleep(min(30.0, (2.0 ** (attempt - 1)) + (random.random() if random else 0.0)))
                            continue
                        raise RuntimeError(f"Gemini error {resp.status} {resp.reason}: {msg}")
                    return json.loads(raw)
                except Exception as e:
                    last_err = e
                    if attempt >= 4:
                        raise
                    time.sleep(min(30.0, (2.0 ** (attempt - 1)) + (random.random() if random else 0.0)))
                finally:
                    try:
                        conn.close()
                    except Exception:
                        pass
            if last_err:
                raise last_err
            raise RuntimeError("Gemini request failed without an exception")

        def _google_generation_config(*, model_name: str, max_tokens: Optional[int], temperature: float, thinking: Optional[Dict[str, Any]]) -> Dict[str, Any]:
            gen: Dict[str, Any] = {"temperature": float(temperature or 0.0)}
            if max_tokens is not None:
                gen["maxOutputTokens"] = int(max_tokens)
            try:
                t = thinking or {}
                enabled = bool(t.get("enabled"))
                budget = t.get("budget_tokens")
                model_lower = str(model_name or "").lower()
                if enabled:
                    if budget is not None:
                        b = int(budget)
                        is_pro = model_lower.startswith("gemini-2.5-pro")
                        is_flash = model_lower.startswith("gemini-2.5-flash") and not model_lower.startswith("gemini-2.5-flash-lite")
                        is_flash_lite = model_lower.startswith("gemini-2.5-flash-lite")
                        if b == 0:
                            gen["thinkingConfig"] = {"thinkingBudget": -1} if is_pro else {"thinkingBudget": 0}
                        elif b == -1:
                            gen["thinkingConfig"] = {"thinkingBudget": -1}
                        else:
                            if is_pro:
                                b = max(128, min(32768, b))
                            elif is_flash:
                                b = max(0, min(24576, b))
                            elif is_flash_lite and b != 0:
                                b = max(512, min(24576, b))
                            gen["thinkingConfig"] = {"thinkingBudget": int(b)}
                    else:
                        gen["thinkingConfig"] = {"thinkingBudget": 1024}
                else:
                    # Best-effort: disable thinking for Flash when possible.
                    if model_lower.startswith("gemini-2.5-flash"):
                        gen["thinkingConfig"] = {"thinkingBudget": 0}
            except Exception:
                pass
            return gen

        for oi in out_info:
            pending_items: List[Dict[str, Any]] = oi.get("batch_pending") or []
            if not pending_items:
                continue

            t = oi["target"]
            prov_l = str(t.get("provider") or "").lower()
            results_path: Path = oi["results_path"]
            prov_path: Path = oi["provenance_path"]

            if prov_l == "anthropic":
                if anthropic is None:
                    raise RuntimeError("Anthropic batch submission requested but anthropic SDK is not available")
                secrets = load_secrets() if load_secrets else {}
                key = get_provider_key(secrets, "anthropic") if get_provider_key else None
                if not key:
                    raise RuntimeError("Missing Anthropic API key in secrets.json or ANTHROPIC_API_KEY")
                client = anthropic.Anthropic(api_key=key)  # type: ignore[union-attr]

                thinking_cfg = t.get("thinking") or {}
                thinking_enabled = bool(thinking_cfg.get("enabled"))
                for chunk in _chunked(pending_items, anthropic_batch_size):
                    batch_id: Optional[str] = None
                    batch_status: Optional[str] = None
                    submit_err: Optional[str] = None
                    reqs = []
                    for it in chunk:
                        params: Dict[str, Any] = {
                            "model": t.get("model"),
                            "max_tokens": int(t.get("max_tokens") or 1000),
                            "messages": [{"role": "user", "content": it.get("prompt_text") or ""}],
                        }
                        # System prompt is top-level in Anthropic Messages API.
                        if sysprompt:
                            params["system"] = str(sysprompt)
                        # Temperature must be omitted when extended thinking is enabled.
                        if not thinking_enabled:
                            params["temperature"] = float(t.get("temperature") or 0.0)
                        # Extended thinking.
                        if thinking_enabled:
                            budget = thinking_cfg.get("budget_tokens")
                            params["thinking"] = {"type": "enabled"}
                            if budget is not None:
                                params["thinking"]["budget_tokens"] = int(budget)
                        reqs.append({"custom_id": str(it.get("rid_row") or ""), "params": params})
                    try:
                        mb = client.messages.batches.create(requests=reqs)
                        batch_id = str(mb.id)
                        batch_status = str(mb.processing_status or "in_progress")
                    except Exception as e:
                        submit_err = str(e)

                    for it in chunk:
                        rid_it = str(it.get("rid_row") or "")
                        model_resolved = None
                        result_row: Dict[str, Any] = {
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "invocation_id": invocation_id,
                            "id": it.get("row_id"),
                            "meta": it.get("meta"),
                            "provider": t.get("provider"),
                            "model": t.get("model"),
                            "model_resolved": model_resolved,
                            "parsed_answer": None,
                            "correct": None,
                            "error": (f"Anthropic batch submission failed: {submit_err}" if submit_err else None),
                            "submission_id": batch_id,
                            "submission_status": ("failed" if submit_err else batch_status),
                            "submission_custom_id": rid_it,
                            "submission_index": None,
                            "openai_response_id": None,
                            "openai_response_status": None,
                        }
                        prov_row: Dict[str, Any] = {
                            **result_row,
                            "prompt_template": it.get("prompt_template"),
                            "representation": it.get("representation"),
                            "answer_format": it.get("answer_format"),
                            "prompt": it.get("prompt_for_prov"),
                            "completion_text": None,
                            "thinking_text": None,
                            "finish_reason": None,
                            "usage": None,
                            "raw_response": None,
                            "timing_ms": None,
                            "attempts": 0,
                        }
                        try:
                            oi["written_ids"].append(rid_it)
                        except Exception:
                            pass
                        with results_path.open("a", encoding="utf-8") as f:
                            f.write(json.dumps(result_row, ensure_ascii=False) + "\n")
                        if cfg.outputs.provenance.enabled:
                            with prov_path.open("a", encoding="utf-8") as f:
                                f.write(json.dumps(prov_row, ensure_ascii=False) + "\n")

            elif prov_l in ("google", "gemini"):
                if http_client is None or _load_secrets is None or _get_key is None:
                    raise RuntimeError("Google batch submission requested but HTTP/secrets helpers are not available")
                secrets = _load_secrets()
                key = _get_key(secrets, "google") or _get_key(secrets, "gemini")
                if not key:
                    raise RuntimeError("Missing Google/Gemini API key in secrets.json or GOOGLE_API_KEY/GEMINI_API_KEY")

                host = "generativelanguage.googleapis.com"
                model_name = str(t.get("model") or "")
                thinking_cfg = t.get("thinking") if isinstance(t.get("thinking"), dict) else None
                for chunk in _chunked(pending_items, google_batch_size):
                    op_name: Optional[str] = None
                    submit_err: Optional[str] = None
                    inlined = []
                    for it in chunk:
                        gen_req: Dict[str, Any] = {
                            "contents": [{"role": "user", "parts": [{"text": it.get("prompt_text") or ""}]}],
                            "generationConfig": _google_generation_config(
                                model_name=model_name,
                                max_tokens=(int(t.get("max_tokens")) if t.get("max_tokens") is not None else None),
                                temperature=float(t.get("temperature") or 0.0),
                                thinking=thinking_cfg,
                            ),
                        }
                        if sysprompt:
                            # Proto JSON name in discovery doc is systemInstruction; keep best-effort.
                            gen_req["systemInstruction"] = {"parts": [{"text": str(sysprompt)}]}
                        inlined.append({"request": gen_req, "metadata": {"custom_id": str(it.get("rid_row") or "")}})

                    payload = {
                        "batch": {
                            "displayName": f"{cfg.name}::{rid}",
                            "inputConfig": {"requests": {"requests": inlined}},
                        }
                    }
                    try:
                        resp = _google_request_json(
                            host=host,
                            method="POST",
                            path=f"/v1beta/models/{model_name}:batchGenerateContent?key={key}",
                            key=key,
                            payload=payload,
                        )
                        op_name = str(resp.get("name") or "")
                        if not op_name:
                            raise RuntimeError(f"Missing operation name in response: {resp}")
                    except Exception as e:
                        submit_err = str(e)

                    for idx, it in enumerate(chunk):
                        rid_it = str(it.get("rid_row") or "")
                        result_row: Dict[str, Any] = {
                            "ts": datetime.now(timezone.utc).isoformat(),
                            "invocation_id": invocation_id,
                            "id": it.get("row_id"),
                            "meta": it.get("meta"),
                            "provider": t.get("provider"),
                            "model": t.get("model"),
                            "model_resolved": None,
                            "parsed_answer": None,
                            "correct": None,
                            "error": (f"Gemini batch submission failed: {submit_err}" if submit_err else None),
                            "submission_id": (op_name if op_name else None),
                            "submission_status": ("failed" if submit_err else "queued"),
                            "submission_custom_id": rid_it,
                            "submission_index": int(idx),
                            "openai_response_id": None,
                            "openai_response_status": None,
                        }
                        prov_row: Dict[str, Any] = {
                            **result_row,
                            "prompt_template": it.get("prompt_template"),
                            "representation": it.get("representation"),
                            "answer_format": it.get("answer_format"),
                            "prompt": it.get("prompt_for_prov"),
                            "completion_text": None,
                            "thinking_text": None,
                            "finish_reason": None,
                            "usage": None,
                            "raw_response": None,
                            "timing_ms": None,
                            "attempts": 0,
                        }
                        try:
                            oi["written_ids"].append(rid_it)
                        except Exception:
                            pass
                        with results_path.open("a", encoding="utf-8") as f:
                            f.write(json.dumps(result_row, ensure_ascii=False) + "\n")
                        if cfg.outputs.provenance.enabled:
                            with prov_path.open("a", encoding="utf-8") as f:
                                f.write(json.dumps(prov_row, ensure_ascii=False) + "\n")

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
            ts_end = datetime.now(timezone.utc).isoformat()
            inv = {
                "ts": ts_end,
                "invocation_id": invocation_id,
                "ts_start": invocation_ts_start,
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
                "written_ids": oi.get("written_ids") or [],
                "openai_response_ids": oi.get("openai_response_ids") or {},
                "env": {
                    "LLMLOG_OPENAI_HTTP_TIMEOUT_S": os.environ.get("LLMLOG_OPENAI_HTTP_TIMEOUT_S"),
                    "LLMLOG_OPENAI_POLL_TIMEOUT_S": os.environ.get("LLMLOG_OPENAI_POLL_TIMEOUT_S"),
                },
            }
            with inv_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(inv, ensure_ascii=False) + "\n")
        except Exception:
            pass


