from __future__ import annotations

import http.client
import json
from typing import Any, Dict, Optional, Tuple

from .secrets import get_provider_key, load_secrets


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


def chat_completion(
    *,
    prompt: str,
    model: str,
    max_tokens: Optional[int] = None,
    temperature: float = 0.0,
    thinking: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Dict[str, Any]]:
    secrets = load_secrets()
    key = get_provider_key(secrets, "google") or get_provider_key(secrets, "gemini")
    if not key:
        raise RuntimeError("Missing Google/Gemini API key in secrets.json or GOOGLE_API_KEY/GEMINI_API_KEY")

    host = "generativelanguage.googleapis.com"
    path = f"/v1beta/models/{model}:generateContent?key={key}"

    body: Dict[str, Any] = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": float(temperature or 0.0)},
    }
    gen_cfg = body.setdefault("generationConfig", {})
    try:
        if thinking and thinking.get("enabled"):
            budget = thinking.get("budget_tokens")
            if budget is not None:
                b = int(budget)
                model_lower = str(model or "").lower()
                is_pro = model_lower.startswith("gemini-2.5-pro")
                is_flash = model_lower.startswith("gemini-2.5-flash") and not model_lower.startswith("gemini-2.5-flash-lite")
                is_flash_lite = model_lower.startswith("gemini-2.5-flash-lite")

                if b == 0:
                    gen_cfg["thinkingConfig"] = {"thinkingBudget": -1} if is_pro else {"thinkingBudget": 0}
                elif b == -1:
                    gen_cfg["thinkingConfig"] = {"thinkingBudget": -1}
                else:
                    if is_pro:
                        b = max(128, min(32768, b))
                    elif is_flash:
                        b = max(0, min(24576, b))
                    elif is_flash_lite:
                        if b != 0:
                            b = max(512, min(24576, b))
                    gen_cfg["thinkingConfig"] = {"thinkingBudget": int(b)}
            else:
                gen_cfg["thinkingConfig"] = {"thinkingBudget": 1024}
        else:
            if str(model).startswith("gemini-2.5-flash"):
                gen_cfg["thinkingConfig"] = {"thinkingBudget": 0}
    except Exception:
        pass

    if max_tokens is not None:
        gen_cfg["maxOutputTokens"] = int(max_tokens)

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


