from __future__ import annotations

import http.client
import hashlib
import json
import os
import random
import time
from typing import Any, Dict, List, Optional, Tuple

from .secrets import get_provider_key, load_secrets


def chat_completion(
    *,
    messages: List[Dict[str, str]],
    model: str,
    max_tokens: Optional[int] = None,
    temperature: float = 0.0,
    seed: Optional[int] = None,
    thinking: Optional[Dict[str, Any]] = None,
    poll: bool = True,
) -> Tuple[str, Dict[str, Any], Optional[str]]:
    secrets = load_secrets()
    key = get_provider_key(secrets, "openai")
    if not key:
        raise RuntimeError("Missing OpenAI API key in secrets.json or OPENAI_API_KEY")

    host = "api.openai.com"
    # Avoid indefinite hangs on connect/read. This is intentionally generous to allow
    # long-running reasoning responses while still guaranteeing eventual progress.
    def _env_int(name: str, default: int) -> int:
        try:
            return int(os.getenv(name, str(default)))
        except Exception:
            return int(default)

    http_timeout_s = _env_int("LLMLOG_OPENAI_HTTP_TIMEOUT_S", 300)
    # Background responses are polled; some GPT-5 tasks can legitimately take >5 minutes,
    # so allow a separate (typically larger) polling deadline.
    # Default to 1 hour so we don't drop results on long-running reasoning calls.
    poll_timeout_s = _env_int("LLMLOG_OPENAI_POLL_TIMEOUT_S", 3600)

    def _request_json(method: str, path: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a JSON request to the OpenAI API with best-effort retries.

        Retries are intentionally conservative and focus on transient network failures and
        server-side errors (e.g. 5xx/429). The runner also retries at a higher level.
        """
        method_u = (method or "GET").upper()

        # Use a deterministic idempotency key for POST so that retries on connection drops
        # don't accidentally duplicate billable work.
        idem_key = None
        body = None
        if payload is not None:
            try:
                dumped = json.dumps(payload, sort_keys=True, separators=(",", ":"))
            except Exception:
                dumped = json.dumps(payload)
            body = dumped.encode("utf-8")
            if method_u == "POST":
                h = hashlib.sha256(body).hexdigest()[:32]
                idem_key = f"llmlog-{h}"

        headers: Dict[str, str] = {
            "Host": host,
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            # Keep for backwards compatibility with earlier Responses API rollouts.
            "OpenAI-Beta": "responses=v1",
        }
        if idem_key:
            headers["Idempotency-Key"] = idem_key

        retryable_status = {429, 500, 502, 503, 504}
        # Some Responses polling edge-cases can transiently return 404 right after creation.
        if method_u == "GET":
            retryable_status.add(404)
        max_attempts = 4

        last_exc: Optional[BaseException] = None
        for attempt in range(1, max_attempts + 1):
            conn = http.client.HTTPSConnection(host, timeout=http_timeout_s)
            try:
                conn.request(method_u, path, body=body if method_u == "POST" else None, headers=headers)
                response = conn.getresponse()
                raw = response.read()

                if response.status != 200:
                    # Extract message when possible
                    try:
                        data = json.loads(raw)
                        err_obj = data.get("error", {}) if isinstance(data, dict) else {}
                        message = err_obj.get("message", "") if isinstance(err_obj, dict) else ""
                        err_code = err_obj.get("code") if isinstance(err_obj, dict) else None
                    except Exception:
                        message = raw.decode("utf-8", errors="ignore")
                        err_code = None

                    # If quota is exhausted, retries are pointless and just waste time.
                    msg_l = (message or "").lower()
                    if response.status == 429 and (
                        (isinstance(err_code, str) and err_code == "insufficient_quota")
                        or ("exceeded your current quota" in msg_l)
                        or ("check your plan and billing details" in msg_l)
                    ):
                        code_s = f" [{err_code}]" if err_code else ""
                        raise RuntimeError(f"OpenAI error {response.status} {response.reason}{code_s}: {message}")

                    # Retry transient server-side failures and rate limits.
                    if response.status in retryable_status and attempt < max_attempts:
                        # Respect Retry-After when provided (seconds), otherwise exponential backoff with jitter.
                        retry_after = response.getheader("Retry-After")
                        if retry_after:
                            try:
                                sleep_s = max(0.0, float(retry_after))
                            except Exception:
                                sleep_s = 0.0
                        else:
                            sleep_s = min(30.0, (2.0 ** (attempt - 1)) + random.random())
                        time.sleep(sleep_s)
                        continue

                    code_s = f" [{err_code}]" if err_code else ""
                    raise RuntimeError(f"OpenAI error {response.status} {response.reason}{code_s}: {message}")

                try:
                    return json.loads(raw)
                except Exception:
                    raise RuntimeError(f"OpenAI response is not JSON: {raw}")
            except Exception as e:
                # Retry common transient connection failures. `RemoteDisconnected` message appears as:
                # "Remote end closed connection without response".
                last_exc = e
                if attempt >= max_attempts:
                    raise
                sleep_s = min(30.0, (2.0 ** (attempt - 1)) + random.random())
                time.sleep(sleep_s)
                continue
            finally:
                try:
                    conn.close()
                except Exception:
                    pass

        # Should never reach here
        if last_exc:
            raise last_exc
        raise RuntimeError("OpenAI request failed without an exception")

    # Responses API (unified generation endpoint).
    #
    # We intentionally do NOT support Chat Completions here. OpenAI is converging on Responses,
    # and many newer models (e.g. GPT-5 tiers) are not chat-completions compatible.
    input_blocks: List[Dict[str, Any]] = []
    for m in messages:
        role = m.get("role", "user")
        text = m.get("content") or ""
        input_blocks.append({"role": role, "content": [{"type": "input_text", "text": text}]})

    payload: Dict[str, Any] = {
        "model": model,
        "input": input_blocks,
    }
    # Ensure the response can be retrieved later by `resp_id` (useful for recovery after timeouts).
    # See: https://platform.openai.com/docs/api-reference/responses
    payload["store"] = True
    if max_tokens is not None:
        payload["max_output_tokens"] = int(max_tokens)

    model_lower = str(model).lower()

    # Some OpenAI models (notably GPT-5 tiers) reject `temperature` on the Responses API.
    # For non-GPT-5 models we keep passing temperature when provided (e.g. 0 for determinism).
    if not model_lower.startswith("gpt-5"):
        try:
            if temperature is not None:
                payload["temperature"] = float(temperature)
        except Exception:
            # If temperature is non-numeric, just omit it.
            pass

    enabled = False
    eff: Optional[str] = None
    if thinking:
        enabled = bool(thinking.get("enabled"))
        eff = thinking.get("effort") or thinking.get("reasoning_effort")
    if enabled and isinstance(eff, str) and eff.strip():
        eff_l = eff.strip().lower()
        # Keep this list permissive; unsupported values will be surfaced as a 4xx.
        if eff_l in ("none", "minimal", "low", "medium", "high", "xhigh"):
            payload["reasoning"] = {"effort": eff_l}

    def _extract_text_and_reasoning(resp_obj: Any) -> Tuple[str, Optional[str]]:
        text_accum: List[str] = []
        reasoning_accum: List[str] = []

        if isinstance(resp_obj, dict):
            # Direct convenience field
            if isinstance(resp_obj.get("output_text"), str):
                text_accum.append(resp_obj["output_text"])

            # Some rollouts attach reasoning summaries separately.
            r = resp_obj.get("reasoning")
            if isinstance(r, dict):
                rs = r.get("summary") or r.get("text")
                if isinstance(rs, str) and rs.strip():
                    reasoning_accum.append(rs.strip())

            output = resp_obj.get("output") or []
            if isinstance(output, list):
                for item in output:
                    content = (item or {}).get("content") or []
                    if not isinstance(content, list):
                        continue
                    for part in content:
                        if not isinstance(part, dict):
                            continue
                        ptype = (part.get("type") or "").lower()

                        # Visible response text
                        if ptype in ("output_text", "text"):
                            t = part.get("text") or part.get("content")
                            if isinstance(t, str) and t:
                                text_accum.append(t)

                        # Reasoning summary / thinking (when exposed)
                        if ptype in ("reasoning", "reasoning_summary", "output_reasoning", "thinking"):
                            rs = part.get("summary") or part.get("text") or part.get("thinking") or part.get("content")
                            if isinstance(rs, str) and rs.strip():
                                reasoning_accum.append(rs.strip())
                        else:
                            # Some schemas use a generic type but store a summary field.
                            rs = part.get("summary")
                            if isinstance(rs, str) and rs.strip():
                                reasoning_accum.append(rs.strip())

        text_out = "\n".join([t for t in text_accum if t]).strip()
        reasoning_out = "\n".join([t for t in reasoning_accum if t]).strip()
        return text_out, (reasoning_out or None)

    def _responses_call(payload_in: Dict[str, Any]) -> Tuple[str, Dict[str, Any], Optional[str]]:
        # For long-running reasoning responses, prefer background mode to avoid holding
        # a single HTTP connection open for the full duration.
        payload_local = dict(payload_in)
        use_background = bool(model_lower.startswith("gpt-5"))
        if use_background:
            payload_local["background"] = True

        data = _request_json("POST", "/v1/responses", payload_local)

        # If the response is running in background, poll until completion.
        resp_top = data.get("response") or data
        if use_background and isinstance(resp_top, dict) and poll:
            status = str(resp_top.get("status") or "").lower()
            resp_id = resp_top.get("id") or data.get("id")
            if status and status not in ("completed", "failed", "cancelled") and resp_id:
                deadline = time.time() + float(poll_timeout_s)
                poll_s = 1.0
                while True:
                    if time.time() >= deadline:
                        raise TimeoutError(
                            f"OpenAI response {resp_id} did not complete within {poll_timeout_s}s "
                            f"(set LLMLOG_OPENAI_POLL_TIMEOUT_S to increase)"
                        )
                    snap = _request_json("GET", f"/v1/responses/{resp_id}")
                    snap_obj = snap.get("response") or snap
                    st = str((snap_obj or {}).get("status") or "").lower()
                    if st == "completed":
                        data = snap
                        break
                    if st == "incomplete":
                        # Terminal but truncated (commonly max_output_tokens). Still return the response
                        # so callers can log partial output + usage instead of timing out.
                        data = snap
                        break
                    if st in ("failed", "cancelled"):
                        err_obj = (snap_obj or {}).get("error") or snap.get("error")
                        raise RuntimeError(f"OpenAI response {resp_id} status={st} error={err_obj}")
                    time.sleep(poll_s)
                    poll_s = min(5.0, poll_s * 1.5)

        resp_obj = data.get("response") or data

        text_out, thinking_text = _extract_text_and_reasoning(resp_obj)

        finish_reason = None
        if isinstance(resp_obj, dict):
            finish_reason = resp_obj.get("finish_reason") or resp_obj.get("status")

        usage = None
        if isinstance(resp_obj, dict) and isinstance(resp_obj.get("usage"), dict):
            usage = resp_obj.get("usage")
        elif isinstance(data.get("usage"), dict):
            usage = data.get("usage")

        meta: Dict[str, Any] = {
            "raw_response": data,
            "finish_reason": finish_reason,
            "usage": usage,
        }
        return (text_out or str(data)), meta, thinking_text

    # Some Responses API deployments reject seed; try it only for non-GPT-5 by default.
    if seed is not None and not model_lower.startswith("gpt-5"):
        payload["seed"] = int(seed)
    try:
        return _responses_call(payload)
    except Exception:
        if "seed" in payload:
            payload2 = dict(payload)
            payload2.pop("seed", None)
            return _responses_call(payload2)
        raise


