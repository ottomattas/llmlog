#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Sequence, Tuple


def _bootstrap_import_path() -> Path:
    """Allow running from repo root without installing the package.

    Returns the project root directory.
    """
    import sys

    here = Path(__file__).resolve()
    project_root = here.parents[1]
    src = project_root / "src"
    sys.path.insert(0, str(src))
    return project_root


def _jsonl_iter(path: Path) -> Iterator[Dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
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


def _derive_paths(results_path: Path) -> Tuple[Path, Path]:
    # results.jsonl -> results.provenance.jsonl / results.summary.json
    p = str(results_path)
    if p.endswith(".jsonl"):
        base = p[: -len(".jsonl")]
        return (Path(base + ".provenance.jsonl"), Path(base + ".summary.json"))
    return (Path(p + ".provenance.jsonl"), Path(p + ".summary.json"))


def _extract_message_text_and_thinking(raw_message: Any) -> Tuple[str, Optional[str]]:
    """Return (text, thinking_text) from an Anthropic Message (dict-ish)."""
    try:
        if isinstance(raw_message, dict) and isinstance(raw_message.get("content"), list):
            text_parts = []
            thinking_parts = []
            for blk in raw_message.get("content") or []:
                if not isinstance(blk, dict):
                    continue
                btype = str(blk.get("type") or "")
                if btype == "text":
                    t = blk.get("text")
                    if isinstance(t, str) and t:
                        text_parts.append(t)
                elif btype in ("thinking", "redacted_thinking"):
                    # "thinking" blocks may carry `thinking`; redacted blocks may omit it.
                    t = blk.get("thinking") or blk.get("text")
                    if isinstance(t, str) and t:
                        thinking_parts.append(t)
            text = ("\n".join(text_parts)).strip()
            thinking_text = ("\n".join(thinking_parts)).strip() if thinking_parts else None
            return text, (thinking_text or None)
    except Exception:
        pass
    return "", None


def _poll_until_ended(*, client: Any, batch_id: str, poll_timeout_s: int) -> Any:
    deadline = time.time() + float(poll_timeout_s)
    poll_s = 1.0
    while True:
        mb = client.messages.batches.retrieve(batch_id)
        st = str(getattr(mb, "processing_status", "") or "").lower()
        if st == "ended":
            return mb
        if time.time() >= deadline:
            raise TimeoutError(f"Anthropic message batch {batch_id} still not ended after {poll_timeout_s}s")
        time.sleep(poll_s)
        poll_s = min(10.0, poll_s * 1.5)


def collect_for_results_file(
    *,
    results_path: Path,
    poll: bool,
    poll_timeout_s: int,
    dry_run: bool,
    limit: Optional[int],
) -> Dict[str, Any]:
    import anthropic

    from llmlog.providers.secrets import get_provider_key, load_secrets
    from llmlog.response_meta import normalize_meta
    from llmlog.parsers import parse_contradiction, parse_yes_no
    from llmlog.provenance_v2 import build_provenance_v2_row, provenance_v2_path_for_results
    import llmlog.runner as runner_mod

    prov_path, summary_path = _derive_paths(results_path)
    prov2_path = provenance_v2_path_for_results(results_path)
    try:
        prov2_path.parent.mkdir(parents=True, exist_ok=True)
    except Exception:
        pass

    latest: Dict[str, Dict[str, Any]] = {}
    for obj in _jsonl_iter(results_path):
        rid = obj.get("id")
        if rid is None:
            continue
        latest[str(rid)] = obj

    latest_prov: Dict[str, Dict[str, Any]] = {}
    for obj in _jsonl_iter(prov_path):
        rid = obj.get("id")
        if rid is None:
            continue
        latest_prov[str(rid)] = obj

    # pending ids grouped by batch id
    by_batch: Dict[str, set[str]] = {}
    for rid, row in latest.items():
        if str(row.get("provider") or "").lower() != "anthropic":
            continue
        if row.get("error"):
            continue
        if row.get("parsed_answer") is not None:
            continue
        sub_id = row.get("submission_id")
        if not (isinstance(sub_id, str) and sub_id and not sub_id.startswith("local_")):
            continue
        # custom_id == rid_row by our submitter convention
        by_batch.setdefault(sub_id, set()).add(str(rid))

    # Apply a per-results-file limit on number of pending items we attempt to collect.
    # For batches, this means we may skip some batches if a single batch is huge.
    if limit is not None:
        # Convert to stable ordering
        want = int(limit)
        trimmed: Dict[str, set[str]] = {}
        used = 0
        for bid in sorted(by_batch.keys()):
            ids = sorted(by_batch[bid])
            if used >= want:
                break
            take = ids[: max(0, want - used)]
            if take:
                trimmed[bid] = set(take)
                used += len(take)
        by_batch = trimmed

    if not by_batch:
        return {"results_path": str(results_path), "pending": 0, "collected": 0}

    secrets = load_secrets()
    key = get_provider_key(secrets, "anthropic")
    if not key:
        raise RuntimeError("Missing Anthropic API key in secrets.json or ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=key)

    collected = 0
    wrote_any = False

    for batch_id, pending_ids in sorted(by_batch.items(), key=lambda kv: kv[0]):
        try:
            mb = _poll_until_ended(client=client, batch_id=batch_id, poll_timeout_s=poll_timeout_s) if poll else client.messages.batches.retrieve(batch_id)
        except Exception:
            # Can't retrieve; skip for now.
            continue

        st = str(getattr(mb, "processing_status", "") or "").lower()
        if st != "ended":
            continue

        # Job-level metadata (best-effort) for provenance v2 timing.
        job_meta: Optional[Dict[str, Any]] = None
        try:
            rc = getattr(mb, "request_counts", None)
            try:
                rc_obj = getattr(rc, "dict", lambda: rc)()
            except Exception:
                rc_obj = rc if isinstance(rc, dict) else None

            def _s(v: Any) -> Optional[str]:
                if v is None:
                    return None
                try:
                    if hasattr(v, "isoformat"):
                        return str(v.isoformat())
                except Exception:
                    pass
                return str(v)

            job_meta = {
                "batch_id": batch_id,
                "processing_status": str(getattr(mb, "processing_status", None) or ""),
                "created_at": _s(getattr(mb, "created_at", None)),
                "ended_at": _s(getattr(mb, "ended_at", None)),
                "expires_at": _s(getattr(mb, "expires_at", None)),
                "archived_at": _s(getattr(mb, "archived_at", None)),
                "cancel_initiated_at": _s(getattr(mb, "cancel_initiated_at", None)),
                "request_counts": rc_obj,
            }
        except Exception:
            job_meta = None

        # Results are a JSONL stream of MessageBatchIndividualResponse objects.
        try:
            stream = client.messages.batches.results(batch_id)
        except Exception:
            continue

        for item in stream:
            try:
                custom_id = str(getattr(item, "custom_id", "") or "")
            except Exception:
                continue
            if not custom_id:
                continue
            if custom_id not in pending_ids:
                continue

            row = latest.get(custom_id) or {}
            req_model = str(row.get("model") or "unknown")
            prov_seed = latest_prov.get(custom_id) or {}
            ans_fmt = (prov_seed.get("answer_format") or "contradiction_satisfiable").strip()

            result = getattr(item, "result", None)
            rtype = str(getattr(result, "type", "") or "").lower()

            err: Optional[str] = None
            completion_text = ""
            thinking_text = None
            finish_reason = None
            usage_obj = None
            raw_message = None
            model_resolved = None

            if rtype == "succeeded":
                msg = getattr(result, "message", None)
                try:
                    raw_message = getattr(msg, "dict", lambda: msg)()
                except Exception:
                    raw_message = None
                if isinstance(raw_message, dict):
                    model_resolved = raw_message.get("model")
                    finish_reason = raw_message.get("stop_reason")
                    usage_obj = raw_message.get("usage")
                    completion_text, thinking_text = _extract_message_text_and_thinking(raw_message)
                else:
                    completion_text = ""
                    thinking_text = None
            elif rtype == "errored":
                try:
                    raw_err = getattr(getattr(result, "error", None), "dict", lambda: result.error)()
                except Exception:
                    raw_err = None
                err = f"Anthropic batch {batch_id} custom_id={custom_id} type=errored error={raw_err}"
            else:
                err = f"Anthropic batch {batch_id} custom_id={custom_id} type={rtype or 'unknown'}"

            # Normalize meta/usage to our standard shape.
            norm = normalize_meta(
                "anthropic",
                req_model,
                {
                    "finish_reason": finish_reason,
                    "usage": usage_obj,
                    "raw_response": raw_message,
                },
            )

            if err:
                parsed = None
            else:
                if ans_fmt == "yes_no":
                    parsed = parse_yes_no(completion_text)
                else:
                    parsed = parse_contradiction(completion_text)

            correct = None
            try:
                satflag = (row.get("meta") or {}).get("satflag")
                if satflag is not None and parsed in (0, 1):
                    exp = 1 if int(satflag) == 1 else 0
                    correct = parsed == exp
            except Exception:
                correct = None

            result_row = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "submit_ts": row.get("ts"),
                "invocation_id": row.get("invocation_id"),
                "id": row.get("id"),
                "meta": row.get("meta"),
                "provider": row.get("provider"),
                "model": row.get("model"),
                "model_resolved": (model_resolved or norm.get("model")),
                "parsed_answer": parsed,
                "correct": correct,
                "error": err,
                "submission_id": batch_id,
                "submission_status": ("failed" if err else "completed"),
                "submission_custom_id": custom_id,
                "submission_index": None,
                "openai_response_id": row.get("openai_response_id"),
                "openai_response_status": row.get("openai_response_status"),
            }

            prov_row = {
                **result_row,
                "prompt_template": prov_seed.get("prompt_template"),
                "representation": prov_seed.get("representation"),
                "answer_format": prov_seed.get("answer_format"),
                "prompt": None,
                "completion_text": completion_text,
                "thinking_text": thinking_text,
                "finish_reason": norm.get("finish_reason"),
                "usage": norm.get("usage"),
                "raw_response": norm.get("raw_response"),
                "timing_ms": None,
                "attempts": 0,
            }

            if not dry_run:
                with results_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(result_row, ensure_ascii=False) + "\n")
                with prov_path.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(prov_row, ensure_ascii=False) + "\n")
                try:
                    prov2_row = build_provenance_v2_row(
                        base=prov_row,
                        results_path=results_path,
                        event="collect",
                        http=None,
                        job_meta=job_meta,
                        extra={"submit_only": True},
                    )
                    with prov2_path.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(prov2_row, ensure_ascii=False) + "\n")
                except Exception:
                    pass
                wrote_any = True

            collected += 1

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

    pending_total = sum(len(v) for v in by_batch.values())
    return {"results_path": str(results_path), "pending": int(pending_total), "collected": int(collected)}


def main() -> int:
    project_root = _bootstrap_import_path()

    ap = argparse.ArgumentParser(description="Collect Anthropic Message Batch results for submit-only runs.")
    ap.add_argument("--runs-dir", default=str(project_root / "runs"), help="Runs directory (default: runs)")
    ap.add_argument("--poll", action="store_true", help="Poll each batch id until ended (slower, but thorough)")
    ap.add_argument("--poll-timeout-s", type=int, default=86_400, help="How long to poll per batch id (when --poll)")
    ap.add_argument("--dry-run", action="store_true", help="Do not write files; only report what would be collected")
    ap.add_argument("--limit", type=int, default=None, help="Max pending items to collect per results.jsonl")
    ap.add_argument(
        "--watch-seconds",
        type=int,
        default=None,
        help="If set, repeat collection every N seconds until no pending items remain.",
    )
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir).resolve()

    def one_pass() -> Tuple[int, int]:
        results_files = sorted(runs_dir.glob("**/results.jsonl"))
        total_pending = 0
        total_collected = 0
        for rf in results_files:
            out = collect_for_results_file(
                results_path=rf,
                poll=bool(args.poll),
                poll_timeout_s=int(args.poll_timeout_s),
                dry_run=bool(args.dry_run),
                limit=args.limit,
            )
            if int(out.get("pending") or 0) > 0:
                print(f"{rf}: pending={out['pending']} collected={out['collected']}", flush=True)
            total_pending += int(out.get("pending") or 0)
            total_collected += int(out.get("collected") or 0)
        print(f"pass_done pending={total_pending} collected={total_collected}", flush=True)
        return total_pending, total_collected

    if args.watch_seconds is None:
        one_pass()
        return 0

    while True:
        pending, _ = one_pass()
        if pending <= 0:
            break
        time.sleep(float(args.watch_seconds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

