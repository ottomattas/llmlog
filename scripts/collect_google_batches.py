#!/usr/bin/env python3
from __future__ import annotations

import argparse
import http.client
import json
import random
import time
import urllib.request
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


def _request_json(
    *,
    host: str,
    key: str,
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    timeout_s: int = 60,
    max_attempts: int = 4,
) -> Dict[str, Any]:
    method_u = (method or "GET").upper()
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Host": host,
        "Content-Type": "application/json",
        "x-goog-api-key": key,
    }

    retryable_status = {429, 500, 502, 503, 504}
    last_err: Optional[BaseException] = None
    for attempt in range(1, max_attempts + 1):
        conn = http.client.HTTPSConnection(host, timeout=timeout_s)
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
                if resp.status in retryable_status and attempt < max_attempts:
                    time.sleep(min(30.0, (2.0 ** (attempt - 1)) + random.random()))
                    continue
                raise RuntimeError(f"Gemini error {resp.status} {resp.reason}: {msg}")
            return json.loads(raw)
        except Exception as e:
            last_err = e
            if attempt >= max_attempts:
                raise
            time.sleep(min(30.0, (2.0 ** (attempt - 1)) + random.random()))
        finally:
            try:
                conn.close()
            except Exception:
                pass

    if last_err:
        raise last_err
    raise RuntimeError("Gemini request failed without an exception")


def _download_text(url: str, *, timeout_s: int = 60) -> str:
    with urllib.request.urlopen(url, timeout=timeout_s) as resp:  # nosec - URL comes from provider API
        return resp.read().decode("utf-8", errors="replace")


def _extract_batch_state(op: Dict[str, Any]) -> Optional[str]:
    """Best-effort extraction of a batch/job state string.

    Gemini batch polling can return either:
    - an Operation-like object with `done` + `metadata.state`, or
    - a Batch-like object with top-level `state` (no `done` field).
    """
    md = op.get("metadata")
    if isinstance(md, dict):
        st = md.get("state")
        if isinstance(st, str) and st.strip():
            return st.strip()
    st2 = op.get("state")
    if isinstance(st2, str) and st2.strip():
        return st2.strip()
    return None


def _is_done_snapshot(op: Dict[str, Any]) -> bool:
    """Return True when a poll snapshot indicates completion."""
    if bool(op.get("done")):
        return True
    st = _extract_batch_state(op)
    if isinstance(st, str) and st:
        s = st.strip().upper()
        # Handle both enum-style and plain strings, e.g.:
        # - "SUCCEEDED" / "FAILED"
        # - "BATCH_STATE_SUCCEEDED" / "BATCH_STATE_FAILED"
        if any(tok in s for tok in ("SUCCEEDED", "FAILED", "CANCELLED", "CANCELED", "COMPLETED", "DONE")):
            return True
    # Some variants omit `done` but include output handles when complete.
    try:
        out = op.get("output")
        if isinstance(out, dict) and (out.get("inlinedResponses") is not None or out.get("responsesFile") is not None):
            return True
        resp = op.get("response")
        if isinstance(resp, dict):
            out2 = resp.get("output")
            if isinstance(out2, dict) and (out2.get("inlinedResponses") is not None or out2.get("responsesFile") is not None):
                return True
            batch = resp.get("batch")
            if isinstance(batch, dict):
                out3 = batch.get("output")
                if isinstance(out3, dict) and (out3.get("inlinedResponses") is not None or out3.get("responsesFile") is not None):
                    return True
    except Exception:
        pass
    return False


def _poll_until_done(*, host: str, key: str, op_name: str, poll_timeout_s: int) -> Dict[str, Any]:
    deadline = time.time() + float(poll_timeout_s)
    poll_s = 1.0
    while True:
        snap = _request_json(host=host, key=key, method="GET", path=f"/v1beta/{op_name}?key={key}", timeout_s=60)
        if _is_done_snapshot(snap):
            return snap
        if time.time() >= deadline:
            st = _extract_batch_state(snap)
            raise TimeoutError(f"Gemini batch {op_name} still not done after {poll_timeout_s}s (state={st!r})")
        time.sleep(poll_s)
        poll_s = min(10.0, poll_s * 1.5)


def _batch_from_operation(op: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    resp = op.get("response")
    if isinstance(resp, dict):
        if isinstance(resp.get("batch"), dict):
            return resp["batch"]
        # Sometimes the response is the batch object itself.
        if "output" in resp and "inputConfig" in resp:
            return resp
    return None


def collect_for_results_file(
    *,
    results_path: Path,
    poll: bool,
    poll_timeout_s: int,
    dry_run: bool,
    limit: Optional[int],
) -> Dict[str, Any]:
    from llmlog.providers.secrets import get_provider_key, load_secrets
    from llmlog.response_meta import normalize_meta
    from llmlog.parsers import parse_contradiction, parse_yes_no
    from llmlog.providers.google_client import _extract_text as _extract_text_google  # type: ignore
    from llmlog.providers.google_client import _extract_thinking_text as _extract_thinking_text_google  # type: ignore
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

    # pending ids grouped by operation name (submission_id)
    by_op: Dict[str, Dict[int, str]] = {}
    for rid, row in latest.items():
        if str(row.get("provider") or "").lower() not in ("google", "gemini"):
            continue
        if row.get("error"):
            continue
        if row.get("parsed_answer") is not None:
            continue
        sub_id = row.get("submission_id")
        if not (isinstance(sub_id, str) and sub_id and not sub_id.startswith("local_")):
            continue
        idx = row.get("submission_index")
        try:
            idx_i = int(idx)
        except Exception:
            continue
        by_op.setdefault(sub_id, {})[idx_i] = rid

    # Apply a per-results-file limit on number of pending items we attempt to collect.
    if limit is not None:
        want = int(limit)
        trimmed: Dict[str, Dict[int, str]] = {}
        used = 0
        for op_name in sorted(by_op.keys()):
            idxs = sorted(by_op[op_name].keys())
            if used >= want:
                break
            take_idxs = idxs[: max(0, want - used)]
            if take_idxs:
                trimmed[op_name] = {i: by_op[op_name][i] for i in take_idxs}
                used += len(take_idxs)
        by_op = trimmed

    if not by_op:
        return {"results_path": str(results_path), "pending": 0, "collected": 0}

    secrets = load_secrets()
    key = get_provider_key(secrets, "google") or get_provider_key(secrets, "gemini")
    if not key:
        raise RuntimeError("Missing Google/Gemini API key in secrets.json or GOOGLE_API_KEY/GEMINI_API_KEY")
    host = "generativelanguage.googleapis.com"

    collected = 0
    wrote_any = False

    for op_name, idx_to_rid in sorted(by_op.items(), key=lambda kv: kv[0]):
        try:
            op = _poll_until_done(host=host, key=key, op_name=op_name, poll_timeout_s=poll_timeout_s) if poll else _request_json(host=host, key=key, method="GET", path=f"/v1beta/{op_name}?key={key}")
        except Exception:
            continue

        if not _is_done_snapshot(op):
            continue

        if op.get("error"):
            # Whole-batch error.
            err_obj = op.get("error")
            opm = op.get("metadata") if isinstance(op, dict) else None
            job_meta = None
            if isinstance(opm, dict):
                job_meta = {
                    "name": opm.get("name") or op.get("name"),
                    "state": opm.get("state"),
                    "model": opm.get("model"),
                    "displayName": opm.get("displayName"),
                    "createTime": opm.get("createTime"),
                    "endTime": opm.get("endTime"),
                    "updateTime": opm.get("updateTime"),
                    "batchStats": opm.get("batchStats"),
                }
            elif isinstance(op, dict):
                if any(k in op for k in ("state", "model", "displayName", "createTime", "endTime", "updateTime", "batchStats")):
                    job_meta = {
                        "name": op.get("name"),
                        "state": op.get("state"),
                        "model": op.get("model"),
                        "displayName": op.get("displayName"),
                        "createTime": op.get("createTime"),
                        "endTime": op.get("endTime"),
                        "updateTime": op.get("updateTime"),
                        "batchStats": op.get("batchStats"),
                    }
            for idx, rid in idx_to_rid.items():
                row = latest.get(rid) or {}
                result_row = {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "submit_ts": row.get("ts"),
                    "invocation_id": row.get("invocation_id"),
                    "id": row.get("id"),
                    "meta": row.get("meta"),
                    "provider": row.get("provider"),
                    "model": row.get("model"),
                    "model_resolved": None,
                    "parsed_answer": None,
                    "correct": None,
                    "error": f"Gemini batch {op_name} failed error={err_obj}",
                    "submission_id": op_name,
                    "submission_status": "failed",
                    "submission_custom_id": row.get("submission_custom_id"),
                    "submission_index": int(idx),
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
            continue

        # The Gemini Batch API may return results in multiple shapes:
        # 1) Operation-like object with `response.inlinedResponses.inlinedResponses` (AI Studio keys).
        # 2) Legacy/alternate batch object with `response.batch.output.{inlinedResponses|responsesFile}`.
        responses: Optional[list[Dict[str, Any]]] = None

        resp = op.get("response")
        if isinstance(resp, dict):
            ir = resp.get("inlinedResponses")
            if isinstance(ir, dict) and isinstance(ir.get("inlinedResponses"), list):
                responses = [(item if isinstance(item, dict) else {}) for item in (ir.get("inlinedResponses") or [])]

        if responses is None:
            batch = _batch_from_operation(op)
            if batch is None and isinstance(op, dict) and isinstance(op.get("output"), dict) and isinstance(op.get("inputConfig"), dict):
                # Some Gemini batch endpoints return a Batch-like object directly (no operation wrapper).
                batch = op
            if not batch:
                continue
            output = batch.get("output") if isinstance(batch.get("output"), dict) else {}

            # Prefer inlined responses when available.
            inlined = None
            try:
                ir = output.get("inlinedResponses")
                if isinstance(ir, dict) and isinstance(ir.get("inlinedResponses"), list):
                    inlined = ir.get("inlinedResponses") or []
            except Exception:
                inlined = None

            if inlined is not None:
                # Convert to list of per-request objects with 'response' or 'error'
                responses = []
                for item in inlined:
                    if isinstance(item, dict):
                        responses.append(item)
                    else:
                        responses.append({})
            else:
                file_name = output.get("responsesFile")
                if isinstance(file_name, str) and file_name:
                    try:
                        file_obj = _request_json(host=host, key=key, method="GET", path=f"/v1beta/{file_name}?key={key}")
                        dl = file_obj.get("downloadUri")
                        if isinstance(dl, str) and dl:
                            txt = _download_text(dl, timeout_s=60)
                            responses = []
                            for line in txt.splitlines():
                                if not line.strip():
                                    continue
                                try:
                                    responses.append(json.loads(line))
                                except Exception:
                                    responses.append({})
                    except Exception:
                        responses = None

        if responses is None:
            continue

        opm = op.get("metadata") if isinstance(op, dict) else None
        job_meta = None
        if isinstance(opm, dict):
            job_meta = {
                "name": opm.get("name") or op.get("name"),
                "state": opm.get("state"),
                "model": opm.get("model"),
                "displayName": opm.get("displayName"),
                "createTime": opm.get("createTime"),
                "endTime": opm.get("endTime"),
                "updateTime": opm.get("updateTime"),
                "batchStats": opm.get("batchStats"),
            }
        elif isinstance(op, dict):
            if any(k in op for k in ("state", "model", "displayName", "createTime", "endTime", "updateTime", "batchStats")):
                job_meta = {
                    "name": op.get("name"),
                    "state": op.get("state"),
                    "model": op.get("model"),
                    "displayName": op.get("displayName"),
                    "createTime": op.get("createTime"),
                    "endTime": op.get("endTime"),
                    "updateTime": op.get("updateTime"),
                    "batchStats": op.get("batchStats"),
                }

        # Build collected rows for any pending indices present.
        for idx, rid in sorted(idx_to_rid.items(), key=lambda kv: kv[0]):
            if idx < 0 or idx >= len(responses):
                continue
            row = latest.get(rid) or {}
            req_model = str(row.get("model") or "unknown")
            prov_seed = latest_prov.get(rid) or {}
            ans_fmt = (prov_seed.get("answer_format") or "contradiction_satisfiable").strip()

            item = responses[idx]
            if isinstance(item, dict) and item.get("error") and item.get("response") is None:
                err = f"Gemini batch {op_name} idx={idx} error={item.get('error')}"
                completion_text = ""
                thinking_text = None
                norm = normalize_meta("google", req_model, {"finish_reason": None, "usage": None, "raw_response": None})
            else:
                # InlinedResponse has shape {response,error,metadata}; responsesFile has GenerateContentResponse directly.
                resp_obj = item.get("response") if isinstance(item, dict) and isinstance(item.get("response"), dict) else (item if isinstance(item, dict) else {})
                completion_text = _extract_text_google(resp_obj)
                thinking_text = _extract_thinking_text_google(resp_obj)
                finish_reason = None
                try:
                    if isinstance(resp_obj, dict):
                        cands = resp_obj.get("candidates") or []
                        if isinstance(cands, list) and cands and isinstance(cands[0], dict):
                            finish_reason = cands[0].get("finishReason")
                except Exception:
                    finish_reason = None
                norm = normalize_meta(
                    "google",
                    req_model,
                    {
                        "finish_reason": finish_reason,
                        "usage": resp_obj.get("usageMetadata"),
                        "raw_response": resp_obj,
                    },
                )
                err = None

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
                "model_resolved": norm.get("model"),
                "parsed_answer": parsed,
                "correct": correct,
                "error": err,
                "submission_id": op_name,
                "submission_status": ("failed" if err else "completed"),
                "submission_custom_id": row.get("submission_custom_id"),
                "submission_index": int(idx),
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

    pending_total = sum(len(v) for v in by_op.values())
    return {"results_path": str(results_path), "pending": int(pending_total), "collected": int(collected)}


def main() -> int:
    project_root = _bootstrap_import_path()

    ap = argparse.ArgumentParser(description="Collect Gemini BatchGenerateContent results for submit-only runs.")
    ap.add_argument("--runs-dir", default=str(project_root / "runs"), help="Runs directory (default: runs)")
    ap.add_argument("--poll", action="store_true", help="Poll each batch operation until done (slower, but thorough)")
    ap.add_argument("--poll-timeout-s", type=int, default=86_400, help="How long to poll per batch op (when --poll)")
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

