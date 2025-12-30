#!/usr/bin/env python3
from __future__ import annotations

import argparse
import http.client
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


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


def _request_json(
    *,
    host: str,
    key: str,
    method: str,
    path: str,
    payload: Optional[Dict[str, Any]] = None,
    timeout_s: int = 60,
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
            raise RuntimeError(f"OpenAI error {resp.status} {resp.reason}: {msg}")
        return json.loads(raw)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def _unwrap_response(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict) and isinstance(obj.get("response"), dict):
        return obj["response"]
    return obj if isinstance(obj, dict) else {}


def _extract_output_text(resp_obj: Dict[str, Any]) -> str:
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


def _fmt_age(created_at: Any) -> str:
    try:
        ts = int(created_at)
    except Exception:
        return ""
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    age = datetime.now(timezone.utc) - dt
    return f"{dt.isoformat()} age={age}"


def main() -> int:
    refactor_root = _bootstrap_import_path()

    from llmlog.providers.secrets import get_provider_key, load_secrets

    ap = argparse.ArgumentParser(description="Inspect/cancel OpenAI Responses by resp_id (admin/debug tool).")
    ap.add_argument("resp_ids", nargs="+", help="One or more OpenAI response ids (resp_...).")
    ap.add_argument("--cancel", action="store_true", help="Attempt to cancel each response id.")
    ap.add_argument("--poll", action="store_true", help="Poll until each response becomes terminal.")
    ap.add_argument("--poll-timeout-s", type=int, default=3600, help="Max seconds to poll per response id.")
    ap.add_argument("--http-timeout-s", type=int, default=60, help="HTTP timeout per request.")
    ap.add_argument("--show-text", action="store_true", help="Print up to 500 chars of output text when present.")
    args = ap.parse_args()

    secrets = load_secrets()
    key = get_provider_key(secrets, "openai")
    if not key:
        raise SystemExit("Missing OpenAI API key in secrets.json or OPENAI_API_KEY")

    host = "api.openai.com"

    def get_one(resp_id: str) -> Dict[str, Any]:
        snap = _request_json(
            host=host,
            key=key,
            method="GET",
            path=f"/v1/responses/{resp_id}",
            timeout_s=int(args.http_timeout_s),
        )
        return _unwrap_response(snap)

    def cancel_one(resp_id: str) -> Dict[str, Any]:
        snap = _request_json(
            host=host,
            key=key,
            method="POST",
            path=f"/v1/responses/{resp_id}/cancel",
            payload={},
            timeout_s=int(args.http_timeout_s),
        )
        return _unwrap_response(snap)

    for resp_id in args.resp_ids:
        if args.cancel:
            try:
                cancelled = cancel_one(resp_id)
                st = str(cancelled.get("status") or "")
                print(f"[cancel] {resp_id} status={st}")
            except Exception as e:
                print(f"[cancel] {resp_id} ERROR: {e}")

        try:
            snap = get_one(resp_id)
        except Exception as e:
            print(f"[get] {resp_id} ERROR: {e}")
            continue

        st = str(snap.get("status") or "").lower()
        print(f"[get] {resp_id} status={st} created_at={snap.get('created_at')} ({_fmt_age(snap.get('created_at'))})")
        if snap.get("completed_at") is not None:
            print(f"      completed_at={snap.get('completed_at')}")
        if snap.get("incomplete_details") is not None:
            print(f"      incomplete_details={snap.get('incomplete_details')}")
        if snap.get("error") is not None:
            print(f"      error={snap.get('error')}")
        if isinstance(snap.get("usage"), dict):
            u = snap["usage"]
            print(
                "      usage="
                + json.dumps(
                    {
                        "input_tokens": u.get("input_tokens"),
                        "output_tokens": u.get("output_tokens"),
                        "reasoning_tokens": u.get("reasoning_tokens"),
                        "cache_read_input_tokens": u.get("cache_read_input_tokens"),
                    },
                    ensure_ascii=False,
                )
            )

        if args.show_text:
            txt = _extract_output_text(snap)
            if txt:
                show = txt[:500].replace("\n", "\\n")
                print(f"      output_text_len={len(txt)} head={show}")

        if args.poll:
            deadline = time.time() + float(args.poll_timeout_s)
            while st not in ("completed", "failed", "cancelled", "incomplete"):
                if time.time() >= deadline:
                    print(f"[poll] {resp_id} still non-terminal after {args.poll_timeout_s}s")
                    break
                time.sleep(2.0)
                snap = get_one(resp_id)
                st = str(snap.get("status") or "").lower()
                print(f"[poll] {resp_id} status={st}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


