#!/usr/bin/env python3
from __future__ import annotations

import argparse
import http.client
import json
import random
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple


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
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")

    headers = {
        "Host": host,
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
        # Keep for backwards compatibility with earlier Responses API rollouts.
        "OpenAI-Beta": "responses=v1",
    }

    retryable_status = {429, 500, 502, 503, 504}
    # Polling can occasionally see transient 404s immediately after creation.
    if method_u == "GET":
        retryable_status.add(404)

    last_err: Optional[BaseException] = None
    for attempt in range(1, max_attempts + 1):
        conn = http.client.HTTPSConnection(host, timeout=timeout_s)
        try:
            conn.request(method_u, path, body=body if method_u == "POST" else None, headers=headers)
            resp = conn.getresponse()
            raw = resp.read()
            if resp.status != 200:
                try:
                    data = json.loads(raw)
                    msg = (data.get("error") or {}).get("message") if isinstance(data, dict) else None
                except Exception:
                    msg = raw.decode("utf-8", errors="ignore")
                if resp.status in retryable_status and attempt < max_attempts:
                    sleep_s = min(30.0, (2.0 ** (attempt - 1)) + random.random())
                    time.sleep(sleep_s)
                    continue
                raise RuntimeError(f"OpenAI error {resp.status} {resp.reason}: {msg}")
            return json.loads(raw)
        except Exception as e:
            last_err = e
            if attempt >= max_attempts:
                raise
            sleep_s = min(30.0, (2.0 ** (attempt - 1)) + random.random())
            time.sleep(sleep_s)
        finally:
            try:
                conn.close()
            except Exception:
                pass

    if last_err:
        raise last_err
    raise RuntimeError("OpenAI request failed without an exception")


def _unwrap_response(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict) and isinstance(obj.get("response"), dict):
        return obj["response"]
    return obj if isinstance(obj, dict) else {}


def _extract_output_text(resp_obj: Dict[str, Any]) -> str:
    # Prefer convenience field when present.
    out = resp_obj.get("output_text")
    if isinstance(out, str) and out.strip():
        return out.strip()

    text_accum = []
    output = resp_obj.get("output") or []
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content") or []
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                ptype = (part.get("type") or "").lower()
                if ptype in ("output_text", "text"):
                    t = part.get("text") or part.get("content")
                    if isinstance(t, str) and t:
                        text_accum.append(t)
    return "\n".join(text_accum).strip()


def _timing_ms_from_response(resp_obj: Dict[str, Any]) -> Optional[int]:
    try:
        a = resp_obj.get("created_at")
        b = resp_obj.get("completed_at")
        if a is None or b is None:
            return None
        return int((int(b) - int(a)) * 1000)
    except Exception:
        return None


def _poll_until_terminal(
    *,
    host: str,
    key: str,
    resp_id: str,
    poll_timeout_s: int,
    http_timeout_s: int,
) -> Dict[str, Any]:
    deadline = time.time() + float(poll_timeout_s)
    poll_s = 1.0
    while True:
        snap = _request_json(
            host=host,
            key=key,
            method="GET",
            path=f"/v1/responses/{resp_id}",
            timeout_s=http_timeout_s,
        )
        resp_obj = _unwrap_response(snap)
        st = str(resp_obj.get("status") or "").lower()
        if st in ("completed", "failed", "cancelled", "incomplete"):
            return snap
        if time.time() >= deadline:
            raise TimeoutError(f"Response {resp_id} still not terminal after {poll_timeout_s}s")
        time.sleep(poll_s)
        poll_s = min(5.0, poll_s * 1.5)


def collect_for_results_file(
    *,
    results_path: Path,
    poll: bool,
    poll_timeout_s: int,
    http_timeout_s: int,
    dry_run: bool,
    limit: Optional[int],
) -> Dict[str, Any]:
    from llmlog.providers.secrets import get_provider_key, load_secrets
    from llmlog.response_meta import normalize_meta
    from llmlog.parsers import parse_contradiction, parse_yes_no
    import llmlog.runner as runner_mod

    prov_path, summary_path = _derive_paths(results_path)

    # Latest result row per id
    latest: Dict[str, Dict[str, Any]] = {}
    for obj in _jsonl_iter(results_path):
        rid = obj.get("id")
        if rid is None:
            continue
        latest[str(rid)] = obj

    # Latest provenance row per id (for answer_format, prompt_template, etc.)
    latest_prov: Dict[str, Dict[str, Any]] = {}
    for obj in _jsonl_iter(prov_path):
        rid = obj.get("id")
        if rid is None:
            continue
        latest_prov[str(rid)] = obj

    pending: Dict[str, str] = {}
    for rid, row in latest.items():
        if str(row.get("provider") or "").lower() != "openai":
            continue
        if row.get("error"):
            continue
        # runner submit-only writes parsed_answer=null and openai_response_id
        if row.get("parsed_answer") is not None:
            continue
        resp_id = row.get("openai_response_id")
        if isinstance(resp_id, str) and resp_id:
            pending[rid] = resp_id

    if limit is not None:
        pending = dict(list(sorted(pending.items(), key=lambda kv: kv[0]))[: int(limit)])

    if not pending:
        return {"results_path": str(results_path), "pending": 0, "collected": 0}

    secrets = load_secrets()
    key = get_provider_key(secrets, "openai")
    if not key:
        raise RuntimeError("Missing OpenAI API key in secrets.json or OPENAI_API_KEY")
    host = "api.openai.com"

    collected = 0
    for rid, resp_id in pending.items():
        row = latest[rid]
        req_model = str(row.get("model") or "unknown")

        try:
            if poll:
                snap = _poll_until_terminal(
                    host=host,
                    key=key,
                    resp_id=resp_id,
                    poll_timeout_s=poll_timeout_s,
                    http_timeout_s=http_timeout_s,
                )
            else:
                snap = _request_json(
                    host=host,
                    key=key,
                    method="GET",
                    path=f"/v1/responses/{resp_id}",
                    timeout_s=http_timeout_s,
                )
        except Exception:
            continue

        resp_obj = _unwrap_response(snap)
        st = str(resp_obj.get("status") or "").lower()
        if st not in ("completed", "incomplete", "failed", "cancelled"):
            continue

        finish_reason = resp_obj.get("finish_reason") or resp_obj.get("status")
        norm = normalize_meta(
            "openai",
            req_model,
            {
                "finish_reason": finish_reason,
                "usage": resp_obj.get("usage"),
                "raw_response": resp_obj,
            },
        )

        completion_text = _extract_output_text(resp_obj)
        ans_fmt = (latest_prov.get(rid) or {}).get("answer_format") or "contradiction_satisfiable"

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

        err = None
        if st == "incomplete":
            inc = resp_obj.get("incomplete_details") or {}
            reason = inc.get("reason") if isinstance(inc, dict) else None
            err = f"OpenAI response {resp_id} status=incomplete reason={reason or 'unknown'}"
        if st in ("failed", "cancelled"):
            err_obj = resp_obj.get("error")
            err = f"OpenAI response {resp_id} status={st} error={err_obj}"

        model_resolved = norm.get("model")
        submit_ts = row.get("ts")
        invocation_id = row.get("invocation_id")
        openai_created_at = resp_obj.get("created_at")
        openai_completed_at = resp_obj.get("completed_at")
        result_row = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "submit_ts": submit_ts,
            "invocation_id": invocation_id,
            "openai_created_at": openai_created_at,
            "openai_completed_at": openai_completed_at,
            "id": row.get("id"),
            "meta": row.get("meta"),
            "provider": row.get("provider"),
            "model": row.get("model"),
            "model_resolved": model_resolved,
            "parsed_answer": parsed,
            "correct": correct,
            "error": err,
            "openai_response_id": resp_id,
            "openai_response_status": st,
        }

        prov_seed = latest_prov.get(rid) or {}
        prov_row = {
            **result_row,
            "prompt_template": prov_seed.get("prompt_template"),
            "representation": prov_seed.get("representation"),
            "answer_format": prov_seed.get("answer_format"),
            # Avoid duplicating prompt again; it exists on the submit row provenance.
            "prompt": None,
            "completion_text": completion_text,
            "thinking_text": None,
            "finish_reason": norm.get("finish_reason"),
            "usage": norm.get("usage"),
            "raw_response": norm.get("raw_response"),
            "timing_ms": _timing_ms_from_response(resp_obj),
            "attempts": 0,
        }

        if not dry_run:
            with results_path.open("a") as f:
                f.write(json.dumps(result_row, ensure_ascii=False) + "\n")
            with prov_path.open("a") as f:
                f.write(json.dumps(prov_row, ensure_ascii=False) + "\n")

            # Update summary if present.
            if summary_path.exists():
                payload = json.loads(summary_path.read_text())
                latest2 = runner_mod._load_latest_results(results_path)  # noqa: SLF001
                stats2 = runner_mod._compute_unique_stats_from_latest(latest2)  # noqa: SLF001
                if payload.get("stats"):
                    # keep stable spend totals when provenance enabled
                    stats2.update(runner_mod._sum_usage_from_provenance(prov_path))  # noqa: SLF001
                    stats2.update(runner_mod._sum_cost_from_provenance(prov_path, payload.get("pricing_rate")))  # noqa: SLF001
                payload["stats"] = stats2
                payload["accuracy"] = (stats2["correct"] / stats2["total"]) if stats2.get("total") else 0.0
                summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

        collected += 1

    return {"results_path": str(results_path), "pending": len(pending), "collected": collected}


def main() -> int:
    refactor_root = _bootstrap_import_path()

    ap = argparse.ArgumentParser(description="Collect OpenAI Responses for submit-only runs (by openai_response_id).")
    ap.add_argument("--runs-dir", default=str(refactor_root / "runs"), help="Runs directory (default: _refactor/runs)")
    ap.add_argument("--poll", action="store_true", help="Poll each response id until terminal (slower, but thorough)")
    ap.add_argument("--poll-timeout-s", type=int, default=7200, help="How long to poll per response id (when --poll)")
    ap.add_argument("--http-timeout-s", type=int, default=60, help="HTTP timeout per request")
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
    results_files = sorted(runs_dir.glob("**/results.jsonl"))

    def one_pass() -> Tuple[int, int]:
        total_pending = 0
        total_collected = 0
        for rf in results_files:
            out = collect_for_results_file(
                results_path=rf,
                poll=bool(args.poll),
                poll_timeout_s=int(args.poll_timeout_s),
                http_timeout_s=int(args.http_timeout_s),
                dry_run=bool(args.dry_run),
                limit=args.limit,
            )
            if out["pending"]:
                print(f"{rf}: pending={out['pending']} collected={out['collected']}")
            total_pending += int(out["pending"])
            total_collected += int(out["collected"])
        print(f"pass_done pending={total_pending} collected={total_collected}")
        return total_pending, total_collected

    if args.watch_seconds is None:
        one_pass()
        return 0

    # Watch loop
    while True:
        pending, _ = one_pass()
        if pending <= 0:
            break
        time.sleep(float(args.watch_seconds))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


