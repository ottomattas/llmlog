from __future__ import annotations

import http.client
import json
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
) -> Tuple[str, Dict[str, Any], Optional[str]]:
    secrets = load_secrets()
    key = get_provider_key(secrets, "openai")
    if not key:
        raise RuntimeError("Missing OpenAI API key in secrets.json or OPENAI_API_KEY")

    host = "api.openai.com"
    # Avoid indefinite hangs on connect/read. This is intentionally generous to allow
    # long-running reasoning responses while still guaranteeing eventual progress.
    timeout_s = 300

    def _request(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        conn = http.client.HTTPSConnection(host, timeout=timeout_s)
        conn.request(
            "POST",
            path,
            json.dumps(payload),
            headers={
                "Host": host,
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
                # Keep for backwards compatibility with earlier Responses API rollouts.
                "OpenAI-Beta": "responses=v1",
            },
        )
        response = conn.getresponse()
        raw = response.read()
        if response.status != 200:
            try:
                data = json.loads(raw)
                message = data.get("error", {}).get("message", "")
            except Exception:
                message = raw.decode("utf-8", errors="ignore")
            raise RuntimeError(f"OpenAI error {response.status} {response.reason}: {message}")
        try:
            data = json.loads(raw)
        except Exception:
            raise RuntimeError(f"OpenAI response is not JSON: {raw}")
        finally:
            conn.close()
        return data

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
        data = _request("/v1/responses", payload_in)
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


