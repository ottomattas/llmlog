import json
import http.client
from typing import Optional, Dict, Any, Tuple

from .secrets import load_secrets, get_provider_key


def _extract_text(data: Dict[str, Any]) -> str:
    try:
        candidates = data.get("candidates") or []
        if not candidates:
            return ""
        parts = (((candidates[0] or {}).get("content") or {}).get("parts")) or []
        texts = []
        for p in parts:
            t = p.get("text")
            if t:
                texts.append(t)
        return "\n".join(texts).strip()
    except Exception:
        return ""


def chat_completion(prompt: str, model: str, max_tokens: Optional[int] = None, temperature: float = 0.0) -> Tuple[str, Dict[str, Any]]:
    secrets = load_secrets()
    # support both keys
    key = get_provider_key(secrets, "google") or get_provider_key(secrets, "gemini")
    if not key:
        raise RuntimeError("Missing Google/Gemini API key in secrets.json or GOOGLE_API_KEY/GEMINI_API_KEY")

    host = "generativelanguage.googleapis.com"
    # Include key in query param (in addition to header) for broader compatibility
    path = f"/v1beta/models/{model}:generateContent?key={key}"

    body: Dict[str, Any] = {
        "contents": [
            {
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": float(temperature or 0.0),
        },
    }
    # For Gemini 2.5 Flash, disable thinking to ensure plain text output and reduce blanks
    try:
        if str(model).startswith("gemini-2.5-flash"):
            body.setdefault("generationConfig", {})["thinkingConfig"] = {"thinkingBudget": 0}
    except Exception:
        pass
    if max_tokens is not None:
        body["generationConfig"]["maxOutputTokens"] = int(max_tokens)

    conn = http.client.HTTPSConnection(host)
    conn.request(
        "POST",
        path,
        json.dumps(body),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": key,
        },
    )
    resp = conn.getresponse()
    raw = resp.read()
    if resp.status != 200:
        try:
            data = json.loads(raw)
            message = data.get("error", {}).get("message", "")
        except Exception:
            message = raw.decode("utf-8", errors="ignore")
        raise RuntimeError(f"Gemini error {resp.status} {resp.reason}: {message}")
    try:
        data = json.loads(raw)
    except Exception:
        raise RuntimeError(f"Gemini response is not JSON: {raw}")
    finally:
        conn.close()
    text = _extract_text(data)
    meta: Dict[str, Any] = {
        "raw_response": data,
        "finish_reason": None,
        "usage": (data.get("usageMetadata") or {}),
    }
    return text, meta




