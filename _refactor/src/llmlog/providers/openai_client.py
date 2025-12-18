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
) -> Tuple[str, Dict[str, Any]]:
    secrets = load_secrets()
    key = get_provider_key(secrets, "openai")
    if not key:
        raise RuntimeError("Missing OpenAI API key in secrets.json or OPENAI_API_KEY")

    host = "api.openai.com"

    def _request(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        conn = http.client.HTTPSConnection(host)
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

    # Prefer Responses API for GPT-5 models
    use_responses = str(model).lower().startswith("gpt-5")
    if use_responses:
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

        eff = None
        enabled = False
        if thinking:
            enabled = bool(thinking.get("enabled"))
            eff = thinking.get("effort") or thinking.get("reasoning_effort")
        if enabled and isinstance(eff, str) and eff.lower() in ("low", "medium", "high"):
            payload["reasoning"] = {"effort": eff.lower()}
        else:
            # Best-effort disable
            payload["reasoning"] = {"effort": "minimal"}

        data = _request("/v1/responses", payload)
        resp_obj = data.get("response") or data

        text_accum: List[str] = []
        if isinstance(resp_obj, dict) and isinstance(resp_obj.get("output_text"), str):
            text_accum.append(resp_obj["output_text"])
        else:
            output = resp_obj.get("output") or []
            if isinstance(output, list):
                for item in output:
                    content = (item or {}).get("content") or []
                    if isinstance(content, list):
                        for part in content:
                            t = part.get("text") or part.get("content")
                            if t:
                                text_accum.append(str(t))
        text_out = "\n".join([t for t in text_accum if t]).strip()

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
        return (text_out or str(data)), meta

    # Default: Chat Completions API
    call: Dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if seed is not None:
        call["seed"] = seed
    if max_tokens is not None:
        call["max_tokens"] = max_tokens
    if thinking:
        eff = thinking.get("effort") or thinking.get("reasoning_effort")
        if isinstance(eff, str) and eff.lower() in ("low", "medium", "high"):
            call["reasoning"] = {"effort": eff.lower()}

    data = _request("/v1/chat/completions", call)
    if "choices" not in data:
        raise RuntimeError("OpenAI response missing 'choices'")
    res = ""
    for ch in data["choices"]:
        if "message" in ch and "content" in ch["message"]:
            res += ch["message"]["content"]
        elif "text" in ch:
            if res:
                res += "\n"
            res += ch["text"].strip()
    meta: Dict[str, Any] = {
        "raw_response": data,
        "finish_reason": (data.get("choices", [{}])[0] or {}).get("finish_reason"),
        "usage": data.get("usage"),
    }
    return res, meta


