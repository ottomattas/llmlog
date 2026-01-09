#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Sequence, Tuple


def _bootstrap_import_path() -> Path:
    """Allow running from repo root without installing the package.

    Returns the `_refactor/` root directory.
    """
    import sys

    here = Path(__file__).resolve()
    refactor_root = here.parents[1]
    src = refactor_root / "src"
    sys.path.insert(0, str(src))
    return refactor_root


def _jsonl_iter(path: Path) -> Iterator[Dict[str, Any]]:
    if not path.exists():
        return
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


def _derive_paths(results_path: Path) -> Tuple[Path, Path, Path]:
    # results.jsonl -> results.provenance.jsonl / results.summary.json / run.manifest.json
    p = str(results_path)
    if p.endswith(".jsonl"):
        base = p[: -len(".jsonl")]
        prov = Path(base + ".provenance.jsonl")
        summary = Path(base + ".summary.json")
        manifest = summary.parent / "run.manifest.json"
        return (prov, summary, manifest)
    prov = Path(p + ".provenance.jsonl")
    summary = Path(p + ".summary.json")
    manifest = summary.parent / "run.manifest.json"
    return (prov, summary, manifest)


def _load_target_from_manifest(manifest_path: Path, *, fallback_row: Dict[str, Any]) -> Dict[str, Any]:
    # `run.manifest.json` is written by runner for every results file.
    if manifest_path.exists():
        try:
            obj = json.loads(manifest_path.read_text())
            if isinstance(obj, dict) and isinstance(obj.get("target"), dict):
                return obj["target"]
        except Exception:
            pass

    # Fallback: best-effort from row fields (missing max_tokens / thinking).
    return {
        "provider": fallback_row.get("provider"),
        "model": fallback_row.get("model"),
        "temperature": 0.0,
        "seed": None,
        "max_tokens": None,
        "thinking": None,
    }


def collect_for_results_file(
    *,
    results_path: Path,
    include_providers: Optional[Sequence[str]],
    dry_run: bool,
    limit: Optional[int],
    max_attempts: int,
    backoff_seconds: Sequence[int],
) -> Dict[str, Any]:
    from llmlog.parsers import parse_contradiction, parse_yes_no
    from llmlog.providers.router import run_chat
    import llmlog.runner as runner_mod

    prov_path, summary_path, manifest_path = _derive_paths(results_path)

    # Latest result row per id
    latest: Dict[str, Dict[str, Any]] = {}
    for obj in _jsonl_iter(results_path):
        rid = obj.get("id")
        if rid is None:
            continue
        latest[str(rid)] = obj

    # Latest provenance row per id + last non-null prompt per id (we need prompt to execute locally)
    latest_prov: Dict[str, Dict[str, Any]] = {}
    prompt_seed: Dict[str, str] = {}
    for obj in _jsonl_iter(prov_path):
        rid = obj.get("id")
        if rid is None:
            continue
        rid_s = str(rid)
        latest_prov[rid_s] = obj
        p = obj.get("prompt")
        if isinstance(p, str) and p.strip():
            prompt_seed[rid_s] = p

    allowed: Optional[set[str]] = None
    if include_providers:
        allowed = {str(p).strip().lower() for p in include_providers if str(p).strip()}

    pending: Dict[str, str] = {}
    for rid, row in latest.items():
        prov = str(row.get("provider") or "").lower()
        if prov == "openai":
            continue
        if allowed is not None and prov not in allowed:
            continue
        if row.get("error"):
            continue
        if row.get("parsed_answer") is not None:
            continue
        sub_id = row.get("submission_id")
        # Local collector only handles locally enqueued items (submission_id starts with "local_").
        # Provider-side async submissions (e.g. Anthropic batches, Gemini batches) are handled by
        # dedicated collector scripts.
        if isinstance(sub_id, str) and sub_id and sub_id.startswith("local_"):
            pending[rid] = sub_id

    if limit is not None:
        pending = dict(list(sorted(pending.items(), key=lambda kv: kv[0]))[: int(limit)])

    if not pending:
        return {"results_path": str(results_path), "pending": 0, "collected": 0}

    # Use the target config from run.manifest.json (contains max_tokens / thinking / temperature).
    # All rows in this results file share the same target.
    first_row = next(iter(latest.values()))
    target = _load_target_from_manifest(manifest_path, fallback_row=first_row)
    provider = str(target.get("provider") or first_row.get("provider") or "")
    model = str(target.get("model") or first_row.get("model") or "")
    temperature = float(target.get("temperature") or 0.0)
    seed = target.get("seed")
    max_tokens = target.get("max_tokens")
    thinking = target.get("thinking")

    collected = 0
    wrote_any = False
    for rid, sub_id in pending.items():
        row = latest[rid]

        prompt = prompt_seed.get(rid)
        if not isinstance(prompt, str) or not prompt.strip():
            # Cannot execute without a prompt.
            err = "Missing prompt text in provenance; cannot collect local submission"
            result_row = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "submit_ts": row.get("ts"),
                "invocation_id": row.get("invocation_id"),
                "id": row.get("id"),
                "meta": row.get("meta"),
                "provider": row.get("provider"),
                "model": row.get("model"),
                "model_resolved": row.get("model_resolved"),
                "parsed_answer": None,
                "correct": None,
                "error": err,
                "submission_id": sub_id,
                "submission_status": "failed",
                "openai_response_id": row.get("openai_response_id"),
                "openai_response_status": row.get("openai_response_status"),
            }
            prov_seed = latest_prov.get(rid) or {}
            prov_row = {
                **result_row,
                "prompt_template": prov_seed.get("prompt_template"),
                "representation": prov_seed.get("representation"),
                "answer_format": prov_seed.get("answer_format"),
                "prompt": None,
                "completion_text": "",
                "thinking_text": None,
                "finish_reason": None,
                "usage": None,
                "raw_response": None,
                "timing_ms": None,
                "attempts": 0,
            }
            if not dry_run:
                with results_path.open("a") as f:
                    f.write(json.dumps(result_row, ensure_ascii=False) + "\n")
                with prov_path.open("a") as f:
                    f.write(json.dumps(prov_row, ensure_ascii=False) + "\n")
                wrote_any = True
            collected += 1
            continue

        err: Optional[str] = None
        text = ""
        thinking_text = None
        meta: Dict[str, Any] = {}
        dur_ms: Optional[int] = None

        # Retry transient transport/server errors (important for Gemini, which can drop connections).
        attempts = 0
        while True:
            try:
                start = time.time()
                res = run_chat(
                    provider=provider,
                    model=model,
                    prompt=prompt,
                    sysprompt=None,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    seed=seed,
                    thinking=thinking,
                    poll=True,
                )
                dur_ms = int((time.time() - start) * 1000)
                text = res.get("text") or ""
                thinking_text = res.get("thinking_text")
                meta = {k: v for k, v in res.items() if k not in ("text", "thinking_text")}
                err = None
                break
            except Exception as e:
                attempts += 1
                err = str(e)
                if attempts >= max(1, int(max_attempts)):
                    break
                try:
                    b = list(backoff_seconds) or [2, 5, 10]
                    sleep_s = float(b[min(attempts - 1, len(b) - 1)])
                except Exception:
                    sleep_s = 1.0
                # jitter helps avoid thundering herd if multiple collectors are running
                time.sleep(max(0.0, sleep_s + random.random()))

        prov_seed = latest_prov.get(rid) or {}
        ans_fmt = (prov_seed.get("answer_format") or "contradiction_satisfiable").strip()
        if err:
            parsed = None
        else:
            if ans_fmt == "yes_no":
                parsed = parse_yes_no(text)
            else:
                parsed = parse_contradiction(text)

        correct = None
        try:
            satflag = (row.get("meta") or {}).get("satflag")
            if satflag is not None and parsed in (0, 1):
                exp = 1 if int(satflag) == 1 else 0
                correct = parsed == exp
        except Exception:
            correct = None

        model_resolved = meta.get("model") if isinstance(meta, dict) else None
        finish_reason = meta.get("finish_reason") if isinstance(meta, dict) else None
        usage = meta.get("usage") if isinstance(meta, dict) else None
        raw_response = meta.get("raw_response") if isinstance(meta, dict) else None

        result_row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "submit_ts": row.get("ts"),
            "invocation_id": row.get("invocation_id"),
            "id": row.get("id"),
            "meta": row.get("meta"),
            "provider": row.get("provider"),
            "model": row.get("model"),
            "model_resolved": model_resolved,
            "parsed_answer": parsed,
            "correct": correct,
            "error": err,
            "submission_id": sub_id,
            "submission_status": ("failed" if err else "completed"),
            "openai_response_id": row.get("openai_response_id"),
            "openai_response_status": row.get("openai_response_status"),
        }

        prov_row = {
            **result_row,
            "prompt_template": prov_seed.get("prompt_template"),
            "representation": prov_seed.get("representation"),
            "answer_format": prov_seed.get("answer_format"),
            # Avoid duplicating prompt again; it exists on the submit row provenance.
            "prompt": None,
            "completion_text": text,
            "thinking_text": thinking_text,
            "finish_reason": finish_reason,
            "usage": usage,
            "raw_response": raw_response,
            "timing_ms": dur_ms,
            "attempts": 0,
        }

        if not dry_run:
            with results_path.open("a") as f:
                f.write(json.dumps(result_row, ensure_ascii=False) + "\n")
            with prov_path.open("a") as f:
                f.write(json.dumps(prov_row, ensure_ascii=False) + "\n")
            wrote_any = True

        collected += 1

    # Update summary once per results file.
    if wrote_any and summary_path.exists() and not dry_run:
        try:
            payload = json.loads(summary_path.read_text())
        except Exception:
            payload = {}
        latest2 = runner_mod._load_latest_results(results_path)  # noqa: SLF001
        stats2 = runner_mod._compute_unique_stats_from_latest(latest2)  # noqa: SLF001
        if payload.get("stats"):
            stats2.update(runner_mod._sum_usage_from_provenance(prov_path))  # noqa: SLF001
            stats2.update(runner_mod._sum_cost_from_provenance(prov_path, payload.get("pricing_rate")))  # noqa: SLF001
        payload["stats"] = stats2
        payload["accuracy"] = (stats2["correct"] / stats2["total"]) if stats2.get("total") else 0.0
        summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    return {"results_path": str(results_path), "pending": len(pending), "collected": collected}


def main() -> int:
    refactor_root = _bootstrap_import_path()

    ap = argparse.ArgumentParser(description="Collect locally queued submit-only runs (Anthropic/Google).")
    ap.add_argument("--runs-dir", default=str(refactor_root / "runs"), help="Runs directory (default: _refactor/runs)")
    ap.add_argument(
        "--providers",
        default="anthropic,google",
        help="Comma-separated providers to collect (default: anthropic,google).",
    )
    ap.add_argument("--dry-run", action="store_true", help="Do not write files; only report what would be collected")
    ap.add_argument("--limit", type=int, default=None, help="Max pending items to collect per results.jsonl")
    ap.add_argument("--max-attempts", type=int, default=5, help="Max attempts per item when calling providers (default: 5)")
    ap.add_argument(
        "--backoff-seconds",
        type=str,
        default="2,5,10,20,30",
        help="Comma-separated retry backoffs in seconds (default: 2,5,10,20,30)",
    )
    ap.add_argument(
        "--watch-seconds",
        type=int,
        default=None,
        help="If set, repeat collection every N seconds until no pending items remain.",
    )
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir).resolve()
    providers = [p.strip() for p in str(args.providers or "").split(",") if p.strip()] or None
    try:
        backoffs = [int(x.strip()) for x in str(args.backoff_seconds or "").split(",") if x.strip()]
    except Exception:
        backoffs = [2, 5, 10, 20, 30]

    def one_pass() -> Tuple[int, int]:
        # Rescan every pass so newly created run dirs are picked up (OpenAI collector UX).
        results_files = sorted(runs_dir.glob("**/results.jsonl"))
        total_pending = 0
        total_collected = 0
        for rp in results_files:
            out = collect_for_results_file(
                results_path=rp,
                include_providers=providers,
                dry_run=bool(args.dry_run),
                limit=args.limit,
                max_attempts=int(args.max_attempts),
                backoff_seconds=backoffs,
            )
            total_pending += int(out.get("pending") or 0)
            total_collected += int(out.get("collected") or 0)
            if int(out.get("pending") or 0) > 0:
                print(f"{rp}: pending={out.get('pending')} collected={out.get('collected')}", flush=True)
        print(f"pass_done pending={total_pending} collected={total_collected}", flush=True)
        return total_pending, total_collected

    if args.watch_seconds is not None:
        while True:
            pending, collected = one_pass()
            if pending <= 0:
                break
            time.sleep(max(1, int(args.watch_seconds)))
        return 0

    pending, collected = one_pass()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

