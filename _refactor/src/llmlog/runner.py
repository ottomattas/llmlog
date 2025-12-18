from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

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
from .providers.router import run_chat
from .prompts.render import render_prompt


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


def _load_done_ids(results_path: Path) -> set[str]:
    if not results_path.exists():
        return set()
    done: set[str] = set()
    for obj in _jsonl_iter(results_path):
        rid = obj.get("id")
        if rid is None:
            continue
        done.add(str(rid))
    return done


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
        return (
            Path(p[:-5] + ".provenance.jsonl"),
            Path(p[:-5] + ".summary.json"),
        )
    return (Path(p + ".provenance.jsonl"), Path(p + ".summary.json"))


def run_suite(
    *,
    suite_path: str,
    run_id: Optional[str] = None,
    output_root: Optional[str] = None,
    limit: Optional[int] = None,
    dry_run: bool = False,
    only_providers: Optional[List[str]] = None,
    resume: Optional[bool] = None,
    lockstep: Optional[bool] = None,
) -> None:
    suite_file = Path(suite_path).resolve()
    root = _find_refactor_root(suite_file)
    out_root = Path(output_root).resolve() if output_root else root
    cfg = resolve_suite(str(suite_file))

    if limit is not None:
        cfg.dataset.limit_rows = int(limit)
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

    dataset_path = cfg.dataset.path
    data_path = Path(dataset_path)
    if not data_path.is_absolute():
        data_path = (root / dataset_path).resolve()
    if not data_path.exists():
        raise FileNotFoundError(f"Dataset not found: {data_path}")

    # Pre-load problems (small enough for our current datasets; simplifies lockstep)
    rows_iter = iter_problem_rows(str(data_path), skip_rows=cfg.dataset.skip_rows)
    rows_iter = _subset_filter(cfg, rows_iter)
    if cfg.dataset.limit_rows is not None:
        n = int(cfg.dataset.limit_rows)
        rows: List[Any] = []
        for i, r in enumerate(rows_iter):
            if i >= n:
                break
            rows.append(r)
    else:
        rows = list(rows_iter)

    # Prepare per-target outputs + resume sets
    out_info: List[Dict[str, Any]] = []
    for t in targets:
        results_path = _build_outpath(out_root, cfg, t, rid)
        prov_path, summary_path = _derive_paths(results_path)
        _ensure_dir(results_path)
        _ensure_dir(prov_path)
        _ensure_dir(summary_path)
        done_ids = _load_done_ids(results_path) if cfg.resume else set()
        out_info.append(
            {
                "target": t,
                "results_path": results_path,
                "provenance_path": prov_path,
                "summary_path": summary_path,
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
                },
            }
        )

    yes_tokens = cfg.parse.yes_tokens
    no_tokens = cfg.parse.no_tokens

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
    for row in rows:
        rid_row = str(getattr(row, "id", ""))
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

            parsed = _parse_answer(ans_fmt, text, yes_tokens=yes_tokens, no_tokens=no_tokens)
            correct = None
            if exp is not None and parsed in (0, 1):
                correct = parsed == exp

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
                "parsed_answer": parsed,
                "correct": correct,
                "error": err,
            }

            # Provenance row (optional)
            prov_row: Dict[str, Any] = {
                **result_row,
                "prompt_template": tmpl_rel,
                "representation": rep.value,
                "answer_format": ans_fmt.value,
                "prompt": prompt_text if cfg.outputs.provenance.include_prompt else None,
                "completion_text": text,
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
            except Exception:
                pass

        # End per-row

    # Write summaries
    for oi in out_info:
        summary_path: Path = oi["summary_path"]
        stats = oi["stats"]
        acc = (stats["correct"] / stats["total"]) if stats["total"] else 0.0
        payload = {
            "suite": cfg.name,
            "run": rid,
            "provider": oi["target"].get("provider"),
            "model": oi["target"].get("model"),
            "thinking_mode": _thinking_mode_label(oi["target"]),
            "stats": stats,
            "accuracy": acc,
        }
        summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


