import json
import http.client
from typing import Optional, Dict, Any

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


def chat_completion(prompt: str, model: str, max_tokens: Optional[int] = None, temperature: float = 0.0) -> str:
    secrets = load_secrets()
    # support both keys
    key = get_provider_key(secrets, "google") or get_provider_key(secrets, "gemini")
    if not key:
        raise RuntimeError("Missing Google/Gemini API key in secrets.json or GOOGLE_API_KEY/GEMINI_API_KEY")

    host = "generativelanguage.googleapis.com"
    path = f"/v1beta/models/{model}:generateContent?key={key}"

    body: Dict[str, Any] = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}],
            }
        ],
        "generationConfig": {
            "temperature": float(temperature or 0.0),
        },
    }
    if max_tokens is not None:
        body["generationConfig"]["maxOutputTokens"] = int(max_tokens)

    conn = http.client.HTTPSConnection(host)
    conn.request(
        "POST",
        path,
        json.dumps(body),
        headers={
            "Content-Type": "application/json",
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
    return text




