#!/usr/bin/env python3
from __future__ import annotations

import argparse
import http.client
import json
import random
import re
import time
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple


RESP_ID_RE = re.compile(r"(resp_[a-zA-Z0-9]+)")


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


def _extract_resp_id(err: str) -> Optional[str]:
    if not err:
        return None
    m = RESP_ID_RE.search(err)
    return m.group(1) if m else None


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


def _recover_one_response(
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
        if st in ("completed", "failed", "cancelled"):
            return snap
        if time.time() >= deadline:
            raise TimeoutError(f"Response {resp_id} still not terminal after {poll_timeout_s}s")
        time.sleep(poll_s)
        poll_s = min(5.0, poll_s * 1.5)


def recover_results_file(
    *,
    results_path: Path,
    poll_timeout_s: int,
    http_timeout_s: int,
    poll: bool,
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

    to_recover: Dict[str, str] = {}
    for rid, row in latest.items():
        err = row.get("error")
        if not isinstance(err, str) or not err:
            continue
        # Only recover runner-side polling timeouts (these include a resp_id).
        if "did not complete within" not in err:
            continue
        resp_id = _extract_resp_id(err)
        if not resp_id:
            continue
        to_recover[rid] = resp_id

    if limit is not None:
        # Keep deterministic order
        to_recover = dict(list(sorted(to_recover.items(), key=lambda kv: kv[0]))[: int(limit)])

    if not to_recover:
        return {"results_path": str(results_path), "candidates": 0, "recovered": 0}

    secrets = load_secrets()
    key = get_provider_key(secrets, "openai")
    if not key:
        raise RuntimeError("Missing OpenAI API key in secrets.json or OPENAI_API_KEY")
    host = "api.openai.com"

    recovered = 0
    pending = 0
    for rid, resp_id in to_recover.items():
        row = latest[rid]
        req_model = str(row.get("model") or "unknown")

        try:
            if poll:
                snap = _recover_one_response(
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
        except TimeoutError:
            # Still running; skip for now.
            pending += 1
            continue
        except Exception:
            # Best-effort: skip anything we can't retrieve right now (will be picked up on a later run).
            continue
        resp_obj = _unwrap_response(snap)
        st = str(resp_obj.get("status") or "").lower()
        if st not in ("completed", "incomplete"):
            if st and st not in ("failed", "cancelled", "incomplete"):
                pending += 1
            continue

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

        # Append a new "recovered" row so resume/aggregation picks it up as the latest attempt.
        model_resolved = norm.get("model")
        recovered_err = None
        if st == "incomplete":
            # Terminal but truncated (commonly max_output_tokens). Preserve as an error-like signal
            # while still capturing usage and the partial output.
            inc = resp_obj.get("incomplete_details") or {}
            reason = inc.get("reason") if isinstance(inc, dict) else None
            recovered_err = f"OpenAI response {resp_id} status=incomplete reason={reason or 'unknown'}"
        result_row = {
            "id": row.get("id"),
            "meta": row.get("meta"),
            "provider": row.get("provider"),
            "model": row.get("model"),
            "model_resolved": model_resolved,
            "parsed_answer": parsed,
            "correct": correct,
            "error": recovered_err,
        }

        prov_seed = latest_prov.get(rid) or {}
        prov_row = {
            **result_row,
            "prompt_template": prov_seed.get("prompt_template"),
            "representation": prov_seed.get("representation"),
            "answer_format": prov_seed.get("answer_format"),
            # Avoid duplicating the full prompt again; it's already present on earlier attempts.
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
        recovered += 1

    # Update summary if present.
    if not dry_run and summary_path.exists():
        payload = json.loads(summary_path.read_text())
        latest2 = runner_mod._load_latest_results(results_path)  # noqa: SLF001
        stats = runner_mod._compute_unique_stats_from_latest(latest2)  # noqa: SLF001
        stats.update(runner_mod._sum_usage_from_provenance(prov_path))  # noqa: SLF001
        stats.update(runner_mod._sum_cost_from_provenance(prov_path, payload.get("pricing_rate")))  # noqa: SLF001
        payload["stats"] = stats
        payload["accuracy"] = (stats["correct"] / stats["total"]) if stats.get("total") else 0.0
        summary_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")

    return {
        "results_path": str(results_path),
        "candidates": len(to_recover),
        "recovered": recovered,
        "pending": pending,
    }


def main() -> int:
    refactor_root = _bootstrap_import_path()

    ap = argparse.ArgumentParser(
        description="Recover OpenAI Responses after runner-side polling timeouts by retrieving resp_id results."
    )
    ap.add_argument("--runs-dir", default=str(refactor_root / "runs"), help="Runs directory (default: _refactor/runs)")
    ap.add_argument(
        "--poll",
        action="store_true",
        help="Poll each response id until terminal (may take a long time). Without this flag, we only fetch once.",
    )
    ap.add_argument("--poll-timeout-s", type=int, default=3600, help="How long to poll per response id (when --poll)")
    ap.add_argument("--http-timeout-s", type=int, default=60, help="HTTP timeout per request")
    ap.add_argument("--dry-run", action="store_true", help="Do not write files; only report what would be recovered")
    ap.add_argument("--limit", type=int, default=None, help="Max number of items to recover per results.jsonl")
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir).resolve()
    results_files = sorted(runs_dir.glob("**/results.jsonl"))

    total_candidates = 0
    total_recovered = 0
    total_pending = 0
    touched = 0
    for rf in results_files:
        out = recover_results_file(
            results_path=rf,
            poll_timeout_s=int(args.poll_timeout_s),
            http_timeout_s=int(args.http_timeout_s),
            poll=bool(args.poll),
            dry_run=bool(args.dry_run),
            limit=args.limit,
        )
        if out["candidates"]:
            touched += 1
            total_candidates += int(out["candidates"])
            total_recovered += int(out["recovered"])
            total_pending += int(out.get("pending") or 0)
            extra = f" pending={out.get('pending')}" if out.get("pending") is not None else ""
            print(f"{rf}: candidates={out['candidates']} recovered={out['recovered']}{extra}")

    print(
        f"Done. files_with_candidates={touched} candidates={total_candidates} "
        f"recovered={total_recovered} pending={total_pending}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


