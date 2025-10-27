import json
import http.client
from typing import Optional, Dict, Any, List, Tuple

from .secrets import load_secrets, get_provider_key


def chat_completion(messages: List[Dict[str, str]], model: str, max_tokens: Optional[int] = None, temperature: float = 0.0, seed: Optional[int] = None, thinking: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
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
                # Enable Responses API features per official docs
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

    # Prefer Responses API for GPT-5 always; explicitly disable reasoning for "nothink" by setting effort=none
    use_responses = (model.lower().startswith("gpt-5") or model == "gpt-5")
    if use_responses:
        # Map chat messages -> Responses input format
        input_blocks: List[Dict[str, Any]] = []
        for m in messages:
            role = m.get("role", "user")
            text = m.get("content") or ""
            input_blocks.append({
                "role": role,
                "content": [{"type": "input_text", "text": text}],
            })

        payload: Dict[str, Any] = {
            "model": model,
            "input": input_blocks,
        }
        # NOTE: Responses API may not accept 'seed' at top-level; omit to avoid 400
        if max_tokens is not None:
            payload["max_output_tokens"] = int(max_tokens)
        # Reasoning control: if thinking enabled with effort, pass it; otherwise explicitly disable
        eff = None
        enabled = False
        if thinking:
            try:
                enabled = bool(thinking.get("enabled"))
                eff = thinking.get("effort") or thinking.get("reasoning_effort")
            except Exception:
                enabled = False
                eff = None
        if enabled and isinstance(eff, str) and eff.lower() in ("low", "medium", "high"):
            payload["reasoning"] = {"effort": eff.lower()}
        else:
            # Minimal effort for nothink per Responses API
            payload["reasoning"] = {"effort": "minimal"}

        data = _request("/v1/responses", payload)

        # Extract text and metadata per Responses API
        resp_obj = data.get("response") or data
        text_accum: List[str] = []
        # Preferred: output_text
        if isinstance(resp_obj, dict) and isinstance(resp_obj.get("output_text"), str):
            text_accum.append(resp_obj["output_text"])
        else:
            # Fallback: stitch from output/content blocks
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

        # Map meta: finish_reason and usage if present
        finish_reason = None
        # Try common fields found in Responses output items
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
    # Some chat models expose `reasoning` top-level; include effort if provided
    if thinking:
        eff = None
        try:
            eff = thinking.get("effort") or thinking.get("reasoning_effort")
        except Exception:
            eff = None
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


