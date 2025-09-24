#!/usr/bin/env python3

import argparse
import json
import os
import sys
import time
from typing import Any, Dict, Iterable, Iterator, List, Optional

import yaml
from concurrent.futures import ThreadPoolExecutor, as_completed

# Support running both as a module (python -m experiments.runner)
# and as a script (python experiments/runner.py)
try:
    from .schema import RunConfig, SingleTarget, ResultRow, ProblemMeta
    from .filters import horn_only as filter_horn_only, skip as filter_skip, limit as filter_limit
    from .parsers import parse_yes_no, parse_contradiction
    from ..utils.provider_router import run_chat
except Exception:
    # Fallback for script execution
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from experiments.schema import RunConfig, SingleTarget, ResultRow, ProblemMeta
    from experiments.filters import horn_only as filter_horn_only, skip as filter_skip, limit as filter_limit
    from experiments.parsers import parse_yes_no, parse_contradiction
    from utils.provider_router import run_chat


def read_jsonl_rows(path: str) -> Iterator[List[Any]]:
    with open(path, "r") as f:
        header_skipped = False
        for line in f:
            txt = line.strip()
            if not txt:
                continue
            try:
                row = json.loads(txt)
            except Exception:
                # allow a header or malformed first line
                if not header_skipped:
                    header_skipped = True
                    continue
                else:
                    continue
            yield row


def apply_filters(rows: Iterable[List[Any]], cfg: RunConfig) -> Iterator[List[Any]]:
    r: Iterator[List[Any]] = iter(rows)
    if cfg.filters.skip_rows:
        r = filter_skip(r, cfg.filters.skip_rows)
    if cfg.filters.horn_only:
        r = filter_horn_only(r)
    if cfg.filters.limit_rows is not None:
        r = filter_limit(r, cfg.filters.limit_rows)
    return r


def render_prompt(problem: List[Any], template_text: str, style: Optional[str]) -> str:
    clauses = problem[5]
    if style in (None, "horn_if_then"):
        lines: List[str] = []
        for clause in clauses:
            pos: List[int] = []
            neg: List[int] = []
            for var in clause:
                if var > 0:
                    pos.append(var)
                else:
                    neg.append(var)
            if pos and not neg and len(pos) == 1:
                s = f"p{pos[0]}."
                lines.append(s)
            elif neg and not pos:
                prem = " and ".join([f"p{0 - el}" for el in neg])
                lines.append(f"if {prem} then p0.")
            elif neg and len(pos) == 1:
                prem = " and ".join([f"p{0 - el}" for el in neg])
                lines.append(f"if {prem} then p{pos[0]}.")
            else:
                raise RuntimeError(f"Cannot handle clause (maybe not horn?): {clause}")
        body = "\n".join(lines)
        return template_text.replace("{{ clauses }}", body)
    elif style == "cnf_v1":
        # v1: "pN is true/false" with ORs
        lines: List[str] = []
        for clause in clauses:
            parts: List[str] = []
            for var in clause:
                if var > 0:
                    parts.append(f"p{var} is true")
                else:
                    parts.append(f"p{0 - var} is false")
            lines.append(" or ".join(parts) + ".")
        body = "\n".join(lines)
        return template_text.replace("{{ clauses }}", body)
    elif style == "cnf_v2":
        # v2: compact "pN" and "not(pN)" with ORs
        lines: List[str] = []
        for clause in clauses:
            parts: List[str] = []
            for var in clause:
                parts.append(f"p{var}" if var > 0 else f"not(p{0 - var})")
            lines.append(" or ".join(parts) + ".")
        body = "\n".join(lines)
        return template_text.replace("{{ clauses }}", body)
    else:
        raise RuntimeError(f"Unknown prompt style: {style}")


def parse_output(text: str, parse_cfg) -> int:
    if parse_cfg.type == "yes_no":
        return parse_yes_no(text, parse_cfg.yes_tokens or ["yes"], parse_cfg.no_tokens or ["no"])
    elif parse_cfg.type == "contradiction":
        return parse_contradiction(text)
    else:
        return 2


def read_text(path: str) -> str:
    with open(path, "r") as f:
        return f.read()


def ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def _build_outpath(cfg: RunConfig, target: SingleTarget, model: str, run_id: Optional[str]) -> str:
    if cfg.output_pattern:
        outpath = cfg.output_pattern
        outpath = (
            outpath.replace("${name}", cfg.name)
            .replace("${provider}", target.provider)
            .replace("${model}", model)
        )
        if "${run}" in outpath:
            rid = run_id or time.strftime("%Y%m%d-%H%M%S")
            outpath = outpath.replace("${run}", rid)
    else:
        outpath = (cfg.output_file or f"experiments/runs/{cfg.name}/results.jsonl").replace("${name}", cfg.name)
        if "${run}" in outpath:
            rid = run_id or time.strftime("%Y%m%d-%H%M%S")
            outpath = outpath.replace("${run}", rid)
    ensure_dir(outpath)
    return outpath


def run_targets_lockstep(
    cfg: RunConfig,
    targets: List[SingleTarget],
    only_providers: Optional[List[str]] = None,
    model_overrides: Optional[Dict[str, List[str]]] = None,
    dry_run: bool = False,
    run_id: Optional[str] = None,
) -> None:
    # Read and filter problems once
    rows_iter = read_jsonl_rows(cfg.input_file)
    rows_iter = apply_filters(rows_iter, cfg)
    problems = list(rows_iter)

    tmpl = read_text(cfg.prompt.template)

    # Expand targets x models taking overrides into account and apply provider filter
    expanded: List[SingleTarget]
    expanded = []
    for t in targets:
        if only_providers and t.provider.lower() not in [p.lower() for p in only_providers]:
            continue
        models: List[str]
        if model_overrides and t.provider in model_overrides:
            models = model_overrides[t.provider]
        else:
            models = [t.model]
        for m in models:
            expanded.append(SingleTarget(provider=t.provider, model=m, temperature=t.temperature, seed=t.seed, max_tokens=t.max_tokens))

    if not expanded:
        return

    # Prepare per-(provider,model) outpaths, processed ids, and stats
    key_to_outpath: Dict[str, str] = {}
    key_to_processed: Dict[str, set] = {}
    stats: Dict[str, Dict[str, Any]] = {}

    def key_for(t: SingleTarget) -> str:
        return f"{t.provider}::{t.model}"

    for t in expanded:
        k = key_for(t)
        if k in key_to_outpath:
            continue
        outpath = _build_outpath(cfg, t, t.model, run_id)
        key_to_outpath[k] = outpath
        # Determine outputs settings (prefer unified outputs, fallback to legacy flags)
        write_results = cfg.outputs.results.enabled
        provenance_enabled = cfg.outputs.provenance.enabled
        provenance_include_prompt = cfg.outputs.provenance.include_prompt
        # Optionally prepare a parallel responses (provenance) file path
        if provenance_enabled:
            base, ext = os.path.splitext(outpath)
            key_to_outpath[k + "::responses"] = (base + ".provenance.jsonl" if ext else outpath + ".provenance.jsonl")
        processed_ids = set()
        if cfg.resume and os.path.exists(outpath):
            try:
                with open(outpath, "r") as rf:
                    for line in rf:
                        try:
                            obj = json.loads(line)
                            processed_ids.add(obj.get("id"))
                        except Exception:
                            continue
            except Exception:
                pass
        key_to_processed[k] = processed_ids
        stats[k] = {
            "total": 0,
            "correct": 0,
            "unclear": 0,
            "sat_total": 0,
            "sat_correct": 0,
            "unsat_total": 0,
            "unsat_correct": 0,
            "timing_sum": 0,
            "timing_count": 0,
            "provider": t.provider,
            "model": t.model,
        }

    sysprompt = None

    # Per-problem lockstep
    for idx, problem in enumerate(problems, start=1):
        pid = problem[0] if isinstance(problem, list) and len(problem) > 0 else idx
        prompt = render_prompt(problem, tmpl, cfg.prompt.style)

        # Build task list for keys that still need this pid
        tasks: List[Dict[str, Any]] = []
        for t in expanded:
            k = key_for(t)
            if pid in key_to_processed[k]:
                continue
            tasks.append({"target": t, "key": k})

        # If dry-run: write placeholder rows immediately (no API calls)
        if dry_run:
            for t in expanded:
                k = key_for(t)
                if pid in key_to_processed[k]:
                    continue
                parsed = 2
                gt = None
                try:
                    satflag = int(problem[4])
                    gt = (parsed == satflag)
                except Exception:
                    gt = None
                meta = ProblemMeta(
                    maxvars=problem[1] if len(problem) > 1 else None,
                    maxlen=problem[2] if len(problem) > 2 else None,
                    horn=problem[3] if len(problem) > 3 else None,
                    satflag=problem[4] if len(problem) > 4 else None,
                    proof=problem[6] if len(problem) > 6 else None,
                )
                row = ResultRow(
                    id=pid,
                    meta=meta,
                    provider=t.provider,
                    model=t.model,
                    prompt=prompt if cfg.save_prompt else None,
                    completion_text=None,
                    parsed_answer=parsed,
                    correct=gt,
                    timing_ms=0,
                    seed=t.seed if t.seed is not None else cfg.seed,
                    temperature=t.temperature if t.temperature is not None else cfg.temperature,
                    error=None,
                )
                with open(key_to_outpath[k], "a") as of:
                    of.write(row.model_dump_json() + "\n")
                # Update stats
                s = stats[k]
                s["total"] += 1
                if row.correct:
                    s["correct"] += 1
                if row.parsed_answer == 2:
                    s["unclear"] += 1
                try:
                    sf = int(problem[4])
                    if sf == 1:
                        s["sat_total"] += 1
                        if row.correct:
                            s["sat_correct"] += 1
                    elif sf == 0:
                        s["unsat_total"] += 1
                        if row.correct:
                            s["unsat_correct"] += 1
                except Exception:
                    pass
                s["timing_sum"] += 0
                # no timing_count increment for 0? Keep consistent with run_target using ints only
                s["timing_count"] += 1
            continue

        # Execute in parallel for this problem
        if tasks:
            max_workers = cfg.concurrency.workers if (cfg.concurrency and cfg.concurrency.workers) else len(tasks)
            max_workers = max(1, min(max_workers, len(tasks)))

            def call_one(t: SingleTarget) -> Dict[str, Any]:
                attempts = 0
                err_msg = None
                text = ""
                dur_ms: Optional[int] = None
                meta: Dict[str, Any] = {}
                while True:
                    try:
                        start = time.time()
                        res = run_chat(
                            provider=t.provider,
                            model=t.model,
                            prompt=prompt,
                            sysprompt=sysprompt,
                            max_tokens=t.max_tokens or cfg.max_tokens,
                            temperature=t.temperature if t.temperature is not None else (cfg.temperature or 0.0),
                            seed=t.seed if t.seed is not None else cfg.seed,
                        )
                        dur_ms = int((time.time() - start) * 1000)
                        err_msg = None
                        text = res.get("text") or ""
                        meta = {k: v for k, v in res.items() if k != "text"}
                        break
                    except Exception as e:
                        attempts += 1
                        err_msg = str(e)
                        max_attempts = (cfg.concurrency.retry.max_attempts if cfg.concurrency and cfg.concurrency.retry else 3)
                        backoff = (cfg.concurrency.retry.backoff_seconds if cfg.concurrency and cfg.concurrency.retry else [2, 5, 10])
                        # Fast-fail for non-retriable? Keep generic for now
                        if attempts >= max_attempts:
                            text = ""
                            break
                        wait_s = backoff[min(attempts - 1, len(backoff) - 1)]
                        time.sleep(wait_s)
                return {"text": text, "dur_ms": dur_ms, "err": err_msg, "meta": meta}

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_key = {}
                for item in tasks:
                    t = item["target"]
                    k = item["key"]
                    future = executor.submit(call_one, t)
                    future_to_key[future] = (t, k)

                for fut in as_completed(future_to_key):
                    t, k = future_to_key[fut]
                    result = fut.result()
                    text = result["text"]
                    dur_ms = result["dur_ms"]
                    err_msg = result["err"]
                    resp_meta = result.get("meta") or {}

                    # Parse and derive normalized token from parsed result
                    parsed = parse_output(text, cfg.parse) if (not err_msg) else 2
                    norm = ("yes" if parsed == 0 else ("no" if parsed == 1 else None))
                    gt = None
                    try:
                        satflag = int(problem[4])
                        gt = (parsed == satflag)
                    except Exception:
                        gt = None

                    problem_meta = ProblemMeta(
                        maxvars=problem[1] if len(problem) > 1 else None,
                        maxlen=problem[2] if len(problem) > 2 else None,
                        horn=problem[3] if len(problem) > 3 else None,
                        satflag=problem[4] if len(problem) > 4 else None,
                        proof=problem[6] if len(problem) > 6 else None,
                    )
                    # Map a compact error_class
                    def classify_error(msg: Optional[str]) -> Optional[str]:
                        if not msg:
                            return None
                        m = msg.lower()
                        if "429" in m or "too many requests" in m or "rate limit" in m:
                            return "rate_limit"
                        if "overloaded" in m or "529" in m:
                            return "overloaded"
                        if "usage limits" in m or "quota" in m:
                            return "quota"
                        if "timeout" in m:
                            return "timeout"
                        return "error"

                    row = ResultRow(
                        id=pid,
                        meta=problem_meta,
                        provider=t.provider,
                        model=t.model,
                        prompt=None,
                        prompt_template=None,
                        completion_text=(norm if (norm is not None) else (text if (cfg.save_response and not err_msg) else None)),
                        normalized_text=norm,
                        raw_response=resp_meta.get("raw_response"),
                        finish_reason=resp_meta.get("finish_reason"),
                        usage=resp_meta.get("usage"),
                        parsed_answer=parsed,
                        correct=gt,
                        timing_ms=dur_ms,
                        seed=t.seed if t.seed is not None else cfg.seed,
                        temperature=t.temperature if t.temperature is not None else cfg.temperature,
                        error=err_msg,
                        error_class=classify_error(err_msg),
                    )
                    # Write minimal results row for statistical analysis
                    if write_results:
                        minimal = {
                            "id": row.id,
                            "meta": row.meta.model_dump(),
                            "parsed_answer": row.parsed_answer,
                        }
                        with open(key_to_outpath[k], "a") as of:
                            of.write(json.dumps(minimal) + "\n")
                    # Write full responses if enabled
                    if provenance_enabled:
                        full_out = {
                            "id": pid,
                            "provider": t.provider,
                            "model": t.model,
                            "prompt": prompt if provenance_include_prompt else None,
                            "prompt_template": cfg.prompt.template,
                            "full_text": text,
                            "raw_response": (resp_meta.get("raw_response") if cfg.outputs.provenance.include_raw_response else None),
                            "finish_reason": resp_meta.get("finish_reason"),
                            "usage": resp_meta.get("usage"),
                            "timing_ms": dur_ms,
                            "error": err_msg,
                        }
                        with open(key_to_outpath[k + "::responses"], "a") as rf:
                            rf.write(json.dumps(full_out) + "\n")

                    # Update stats
                    s = stats[k]
                    s["total"] += 1
                    if row.correct:
                        s["correct"] += 1
                    if row.parsed_answer == 2:
                        s["unclear"] += 1
                    try:
                        sf = int(problem[4])
                        if sf == 1:
                            s["sat_total"] += 1
                            if row.correct:
                                s["sat_correct"] += 1
                        elif sf == 0:
                            s["unsat_total"] += 1
                            if row.correct:
                                s["unsat_correct"] += 1
                    except Exception:
                        pass
                    if isinstance(row.timing_ms, int):
                        s["timing_sum"] += row.timing_ms
                        s["timing_count"] += 1

    # Write per-target summaries
    for k, outpath in key_to_outpath.items():
        try:
            base, ext = os.path.splitext(outpath)
            summary_path = base + ".summary.json" if ext else outpath + ".summary.json"
            ensure_dir(summary_path)
            s = stats[k]
            avg_timing = (s["timing_sum"] / s["timing_count"]) if s["timing_count"] > 0 else None
            summary = {
                "name": cfg.name,
                "provider": s["provider"],
                "model": s["model"],
                "run": run_id,
                "total": s["total"],
                "correct": s["correct"],
                "accuracy": (s["correct"] / s["total"]) if s["total"] > 0 else None,
                "unclear": s["unclear"],
                "sat_total": s["sat_total"],
                "sat_correct": s["sat_correct"],
                "sat_accuracy": (s["sat_correct"] / s["sat_total"]) if s["sat_total"] > 0 else None,
                "unsat_total": s["unsat_total"],
                "unsat_correct": s["unsat_correct"],
                "unsat_accuracy": (s["unsat_correct"] / s["unsat_total"]) if s["unsat_total"] > 0 else None,
                "avg_timing_ms": avg_timing,
                "timestamp": int(time.time()),
            }
            with open(summary_path, "w") as sf:
                json.dump(summary, sf, indent=2)
        except Exception:
            pass

def run_target(
    cfg: RunConfig,
    target: SingleTarget,
    only_providers: Optional[List[str]] = None,
    model_overrides: Optional[Dict[str, List[str]]] = None,
    dry_run: bool = False,
    run_id: Optional[str] = None,
) -> None:
    if only_providers and target.provider.lower() not in [p.lower() for p in only_providers]:
        return
    models: List[str]
    if model_overrides and target.provider in model_overrides:
        models = model_overrides[target.provider]
    else:
        models = [target.model]

    rows_iter = read_jsonl_rows(cfg.input_file)
    rows_iter = apply_filters(rows_iter, cfg)
    problems = list(rows_iter)

    tmpl = read_text(cfg.prompt.template)

    for model in models:
        # decide output path
        if cfg.output_pattern:
            outpath = cfg.output_pattern
            outpath = (
                outpath.replace("${name}", cfg.name)
                .replace("${provider}", target.provider)
                .replace("${model}", model)
            )
            if "${run}" in outpath:
                rid = run_id or time.strftime("%Y%m%d-%H%M%S")
                outpath = outpath.replace("${run}", rid)
        else:
            outpath = (cfg.output_file or f"experiments/runs/{cfg.name}/results.jsonl").replace("${name}", cfg.name)
            if "${run}" in outpath:
                rid = run_id or time.strftime("%Y%m%d-%H%M%S")
                outpath = outpath.replace("${run}", rid)
        ensure_dir(outpath)
        # Determine outputs settings (prefer unified outputs, fallback to legacy flags)
        results_include_prompt = cfg.outputs.results.include_prompt
        provenance_enabled = cfg.outputs.provenance.enabled
        provenance_include_prompt = cfg.outputs.provenance.include_prompt

        responses_path = None
        if provenance_enabled:
            base, ext = os.path.splitext(outpath)
            responses_path = (base + ".provenance.jsonl" if ext else outpath + ".provenance.jsonl")
            ensure_dir(responses_path)

        # resume support: append mode, naive duplicate avoidance via counting lines
        processed_ids = set()
        if cfg.resume and os.path.exists(outpath):
            try:
                with open(outpath, "r") as rf:
                    for line in rf:
                        try:
                            obj = json.loads(line)
                            processed_ids.add(obj.get("id"))
                        except Exception:
                            continue
            except Exception:
                pass

        # basic stats for summary
        total_count = 0
        correct_count = 0
        unclear_count = 0
        sat_total = 0
        sat_correct = 0
        unsat_total = 0
        unsat_correct = 0
        timing_sum = 0
        timing_count = 0

        with open(outpath, "a") as of:
            idx = 0
            for problem in problems:
                idx += 1
                pid = problem[0] if isinstance(problem, list) and len(problem) > 0 else idx
                if pid in processed_ids:
                    continue

                prompt = render_prompt(problem, tmpl, cfg.prompt.style)
                sysprompt = None

                if dry_run:
                    text = ""
                    dur_ms = 0
                    err_msg = None
                    resp_meta: Dict[str, Any] = {}
                else:
                    attempts = 0
                    err_msg = None
                    text = ""
                    resp_meta: Dict[str, Any] = {}
                    while True:
                        try:
                            start = time.time()
                            res = run_chat(
                                provider=target.provider,
                                model=model,
                                prompt=prompt,
                                sysprompt=sysprompt,
                                max_tokens=target.max_tokens or cfg.max_tokens,
                                temperature=target.temperature if target.temperature is not None else (cfg.temperature or 0.0),
                                seed=target.seed if target.seed is not None else cfg.seed,
                            )
                            dur_ms = int((time.time() - start) * 1000)
                            err_msg = None
                            text = res.get("text") or ""
                            resp_meta = {k: v for k, v in res.items() if k != "text"}
                            break
                        except Exception as e:
                            attempts += 1
                            err_msg = str(e)
                            # determine backoff
                            max_attempts = (cfg.concurrency.retry.max_attempts if cfg.concurrency and cfg.concurrency.retry else 3)
                            backoff = (cfg.concurrency.retry.backoff_seconds if cfg.concurrency and cfg.concurrency.retry else [2, 5, 10])
                            if attempts >= max_attempts:
                                dur_ms = None
                                text = ""
                                break
                            wait_s = backoff[min(attempts - 1, len(backoff) - 1)]
                            time.sleep(wait_s)

                parsed = parse_output(text, cfg.parse) if (not dry_run and not err_msg) else 2
                norm = ("yes" if parsed == 0 else ("no" if parsed == 1 else None))
                gt = None
                try:
                    satflag = int(problem[4])
                    gt = (parsed == satflag)
                except Exception:
                    gt = None

                problem_meta = ProblemMeta(
                    maxvars=problem[1] if len(problem) > 1 else None,
                    maxlen=problem[2] if len(problem) > 2 else None,
                    horn=problem[3] if len(problem) > 3 else None,
                    satflag=problem[4] if len(problem) > 4 else None,
                    proof=problem[6] if len(problem) > 6 else None,
                )
                def classify_error(msg: Optional[str]) -> Optional[str]:
                    if not msg:
                        return None
                    m = msg.lower()
                    if "429" in m or "too many requests" in m or "rate limit" in m:
                        return "rate_limit"
                    if "overloaded" in m or "529" in m:
                        return "overloaded"
                    if "usage limits" in m or "quota" in m:
                        return "quota"
                    if "timeout" in m:
                        return "timeout"
                    return "error"

                row = ResultRow(
                    id=pid,
                    meta=problem_meta,
                    provider=target.provider,
                    model=model,
                    prompt=prompt if results_include_prompt else None,
                    prompt_template=cfg.prompt.template if results_include_prompt else None,
                    completion_text=(norm if (norm is not None) else (text if (cfg.save_response and not err_msg) else None)),
                    normalized_text=norm,
                    raw_response=resp_meta.get("raw_response"),
                    finish_reason=resp_meta.get("finish_reason"),
                    usage=resp_meta.get("usage"),
                    parsed_answer=parsed,
                    correct=gt,
                    timing_ms=dur_ms,
                    seed=target.seed if target.seed is not None else cfg.seed,
                    temperature=target.temperature if target.temperature is not None else cfg.temperature,
                    error=err_msg,
                    error_class=classify_error(err_msg),
                )
                # Write minimal results row for statistical analysis
                if write_results:
                    minimal = {
                        "id": row.id,
                        "meta": row.meta.model_dump(),
                        "parsed_answer": row.parsed_answer,
                    }
                    of.write(json.dumps(minimal) + "\n")
                if provenance_enabled and responses_path:
                    full_out = {
                        "id": pid,
                        "provider": target.provider,
                        "model": model,
                        "prompt": prompt if provenance_include_prompt else None,
                        "prompt_template": cfg.prompt.template,
                        "full_text": text,
                        "raw_response": (resp_meta.get("raw_response") if cfg.outputs.provenance.include_raw_response else None),
                        "finish_reason": resp_meta.get("finish_reason") if not dry_run else None,
                        "usage": resp_meta.get("usage") if not dry_run else None,
                        "timing_ms": dur_ms,
                        "error": err_msg,
                    }
                    with open(responses_path, "a") as rf:
                        rf.write(json.dumps(full_out) + "\n")

                # Update stats
                total_count += 1
                if row.correct:
                    correct_count += 1
                if row.parsed_answer == 2:
                    unclear_count += 1
                try:
                    sf = int(problem[4])
                    if sf == 1:
                        sat_total += 1
                        if row.correct:
                            sat_correct += 1
                    elif sf == 0:
                        unsat_total += 1
                        if row.correct:
                            unsat_correct += 1
                except Exception:
                    pass
                if isinstance(row.timing_ms, int):
                    timing_sum += row.timing_ms
                    timing_count += 1

        # write summary file next to results
        try:
            base, ext = os.path.splitext(outpath)
            summary_path = base + ".summary.json" if ext else outpath + ".summary.json"
            ensure_dir(summary_path)
            avg_timing = (timing_sum / timing_count) if timing_count > 0 else None
            summary = {
                "name": cfg.name,
                "provider": target.provider,
                "model": model,
                "run": run_id,
                "total": total_count,
                "correct": correct_count,
                "accuracy": (correct_count / total_count) if total_count > 0 else None,
                "unclear": unclear_count,
                "sat_total": sat_total,
                "sat_correct": sat_correct,
                "sat_accuracy": (sat_correct / sat_total) if sat_total > 0 else None,
                "unsat_total": unsat_total,
                "unsat_correct": unsat_correct,
                "unsat_accuracy": (unsat_correct / unsat_total) if unsat_total > 0 else None,
                "avg_timing_ms": avg_timing,
                "timestamp": int(time.time()),
            }
            with open(summary_path, "w") as sf:
                json.dump(summary, sf, indent=2)
        except Exception:
            pass


def main() -> None:
    ap = argparse.ArgumentParser(description="Run config-driven LLM experiments")
    ap.add_argument("--config", required=True, help="Path to YAML config")
    ap.add_argument("--limit", type=int, default=None, help="Limit processed items")
    ap.add_argument("--dry-run", action="store_true", help="Only render prompts without calling the API")
    ap.add_argument("--resume", action="store_true", help="Resume an interrupted run")
    ap.add_argument("--only", type=str, default=None, help="Comma-separated providers to include")
    ap.add_argument("--models", type=str, default=None, help="Comma-separated provider:model filters, e.g. openai:gpt-4o,anthropic:claude-3")
    ap.add_argument("--run", type=str, default=None, help="Run identifier to inject into ${run} in output paths (e.g., 20250923 or git-<sha>)")
    args = ap.parse_args()

    with open(args.config, "r") as f:
        raw = yaml.safe_load(f)
    cfg = RunConfig(**raw)

    # CLI overrides
    if args.limit is not None:
        cfg.filters.limit_rows = args.limit
    if args.resume:
        cfg.resume = True

    only_providers: Optional[List[str]] = None
    if args.only:
        only_providers = [p.strip() for p in args.only.split(",") if p.strip()]

    model_overrides: Optional[Dict[str, List[str]]] = None
    if args.models:
        model_overrides = {}
        for pair in args.models.split(","):
            pair = pair.strip()
            if not pair:
                continue
            if ":" not in pair:
                continue
            prov, mod = pair.split(":", 1)
            model_overrides.setdefault(prov, []).append(mod)

    # Build target list
    targets: List[SingleTarget] = []
    if cfg.targets and len(cfg.targets) > 0:
        targets = cfg.targets
    else:
        if not (cfg.provider and cfg.model):
            raise RuntimeError("Config must include either (provider, model) or targets[]")
        targets = [SingleTarget(provider=cfg.provider, model=cfg.model, temperature=cfg.temperature or 0.0, seed=cfg.seed, max_tokens=cfg.max_tokens)]

    # Lockstep vs original per-target mode
    if cfg.concurrency and getattr(cfg.concurrency, "lockstep", False):
        run_targets_lockstep(
            cfg,
            targets,
            only_providers=only_providers,
            model_overrides=model_overrides,
            dry_run=args.dry_run,
            run_id=args.run,
        )
    else:
        # Run targets concurrently using targets_workers
        max_workers = cfg.concurrency.targets_workers if cfg.concurrency and cfg.concurrency.targets_workers else 1
        if max_workers <= 1 or len(targets) <= 1:
            for t in targets:
                run_target(cfg, t, only_providers=only_providers, model_overrides=model_overrides, dry_run=args.dry_run, run_id=args.run)
        else:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(
                        run_target,
                        cfg,
                        t,
                        only_providers,
                        model_overrides,
                        args.dry_run,
                        args.run,
                    )
                    for t in targets
                ]
                for _ in as_completed(futures):
                    pass


if __name__ == "__main__":
    main()


