from __future__ import annotations

import http.client
import json
import random
import time
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
            if not isinstance(p, dict):
                continue
            # When thought summaries are enabled, Gemini can include `thought: true` parts.
            # Exclude those from the visible answer text so parsing remains stable.
            if bool(p.get("thought")):
                continue
            t = p.get("text")
            if t:
                texts.append(t)
        return "\n".join(texts).strip()
    except Exception:
        return ""


def _extract_thinking_text(data: Dict[str, Any]) -> Optional[str]:
    """Best-effort extraction of any returned thought/thinking blocks.

    Note: depending on model + API settings, Gemini thinking may be *not* returned as text at all.
    In that case this returns None and only usageMetadata.thoughtsTokenCount is available.
    """
    try:
        candidates = data.get("candidates") or []
        if not candidates:
            return None
        parts = (((candidates[0] or {}).get("content") or {}).get("parts")) or []
        out = []
        for p in parts:
            if not isinstance(p, dict):
                continue
            # Thought summaries (Gemini): part has `thought: true` with summary text.
            if bool(p.get("thought")):
                t = p.get("text")
                if isinstance(t, str) and t.strip():
                    out.append(t.strip())
                continue
            ptype = str(p.get("type") or "").lower()
            if ptype in ("thought", "thinking", "reasoning"):
                t = p.get("text") or p.get("content")
                if isinstance(t, str) and t.strip():
                    out.append(t.strip())
            for key in ("thought", "thinking", "reasoning", "thoughtText", "thinkingText"):
                v = p.get(key)
                if isinstance(v, str) and v.strip():
                    out.append(v.strip())
        txt = "\n".join(out).strip()
        return txt or None
    except Exception:
        return None


def _validate_gemini3_thinking_level(*, model: str, level: str) -> str:
    """Validate and normalize Gemini 3 thinking levels.

    Gemini 3 Pro supports {low, high}. Gemini 3 Flash supports {minimal, low, medium, high}.

    Reference: https://ai.google.dev/gemini-api/docs/thinking
    """
    model_l = str(model or "").lower()
    lvl = str(level or "").strip().lower()
    if not lvl:
        raise ValueError("Gemini thinking level must be a non-empty string")
    if model_l.startswith("gemini-2."):
        raise ValueError(
            f"Gemini 2.x model {model!r} is not supported in `_refactor/`; use a Gemini 3 model id."
        )
    if model_l.startswith("gemini-3-pro"):
        allowed = {"low", "high"}
    elif model_l.startswith("gemini-3-flash"):
        allowed = {"minimal", "low", "medium", "high"}
    else:
        # Conservative fallback for unknown Gemini 3 variants.
        allowed = {"minimal", "low", "medium", "high"}
    if lvl not in allowed:
        raise ValueError(f"Unsupported thinking level {lvl!r} for model {model!r} (allowed: {sorted(allowed)})")
    return lvl


def chat_completion(
    *,
    prompt: str,
    system: Optional[str] = None,
    model: str,
    max_tokens: Optional[int] = None,
    temperature: float = 0.0,
    thinking: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Dict[str, Any], Optional[str]]:
    secrets = load_secrets()
    key = get_provider_key(secrets, "google") or get_provider_key(secrets, "gemini")
    if not key:
        raise RuntimeError("Missing Google/Gemini API key in secrets.json or GOOGLE_API_KEY/GEMINI_API_KEY")

    host = "generativelanguage.googleapis.com"
    path = f"/v1beta/models/{model}:generateContent?key={key}"

    body: Dict[str, Any] = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": float(temperature or 0.0)},
    }
    if system:
        # Prefer structured system instruction when supported by the API.
        body["system_instruction"] = {"parts": [{"text": str(system)}]}
    gen_cfg = body.setdefault("generationConfig", {})
    if thinking:
        enabled = bool(thinking.get("enabled"))
        # In `_refactor/`, we standardize Gemini on thinking levels (Gemini 3).
        if thinking.get("budget_tokens") is not None:
            raise ValueError(
                "Google/Gemini thinking `budget_tokens` is not supported in `_refactor/`. "
                "Use thinking.effort (mapped to Gemini thinking levels)."
            )
        if enabled:
            eff = thinking.get("effort") or thinking.get("thinking_level") or thinking.get("thinkingLevel")
            if not isinstance(eff, str) or not eff.strip():
                raise ValueError("Gemini thinking is enabled but no thinking level provided (set thinking.effort)")
            lvl = _validate_gemini3_thinking_level(model=model, level=eff)
            gen_cfg["thinkingConfig"] = {"thinkingLevel": lvl}

    if max_tokens is not None:
        gen_cfg["maxOutputTokens"] = int(max_tokens)

    # Transport-level flakiness (e.g. RemoteDisconnected) can happen; keep a small retry loop here.
    retryable_status = {429, 500, 502, 503, 504}
    last_err: Optional[BaseException] = None
    for attempt in range(1, 5):
        conn = http.client.HTTPSConnection(host, timeout=60)
        try:
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
                if resp.status in retryable_status and attempt < 4:
                    time.sleep(min(30.0, (2.0 ** (attempt - 1)) + random.random()))
                    continue
                raise RuntimeError(f"Gemini error {resp.status} {resp.reason}: {message}")
            try:
                data = json.loads(raw)
            except Exception:
                raise RuntimeError(f"Gemini response is not JSON: {raw}")
            break
        except Exception as e:
            last_err = e
            if attempt >= 4:
                raise
            time.sleep(min(30.0, (2.0 ** (attempt - 1)) + random.random()))
        finally:
            try:
                conn.close()
            except Exception:
                pass
    else:
        if last_err:
            raise last_err
        raise RuntimeError("Gemini request failed without an exception")

    text = _extract_text(data)
    thinking_text = _extract_thinking_text(data)
    meta: Dict[str, Any] = {
        "raw_response": data,
        "finish_reason": None,
        "usage": (data.get("usageMetadata") or {}),
    }
    return text, meta, thinking_text


