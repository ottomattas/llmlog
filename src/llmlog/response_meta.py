from __future__ import annotations

from typing import Any, Dict, Optional


def _safe_get(obj: Any, *keys: str) -> Optional[Any]:
    cur = obj
    for k in keys:
        if isinstance(cur, dict):
            cur = cur.get(k)
        else:
            return None
    return cur


def normalize_meta(provider: str, model: str, meta: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize provider metadata into a unified shape.

    Characterization target: utils/response_meta.py
    """
    provider_l = (provider or "").lower()
    normalized: Dict[str, Any] = {
        "provider": provider,
        "model": model,
        "finish_reason": meta.get("finish_reason"),
        "usage": {
            "input_tokens": None,
            "output_tokens": None,
            "reasoning_tokens": None,
            # Optional extras (best-effort)
            "cache_creation_input_tokens": None,
            "cache_read_input_tokens": None,
        },
        "raw_response": meta.get("raw_response"),
    }

    raw = meta.get("raw_response") or {}

    # Anthropic
    if provider_l == "anthropic":
        # Prefer the provider-returned model id when present (useful when calling aliases).
        try:
            m = raw.get("model")
            if isinstance(m, str) and m:
                normalized["model"] = m
        except Exception:
            pass
        usage = meta.get("usage") or _safe_get(raw, "usage") or {}
        normalized["usage"]["input_tokens"] = usage.get("input_tokens")
        normalized["usage"]["output_tokens"] = usage.get("output_tokens")
        normalized["usage"]["cache_creation_input_tokens"] = usage.get("cache_creation_input_tokens")
        normalized["usage"]["cache_read_input_tokens"] = usage.get("cache_read_input_tokens")
        # If extended thinking is present (thinking or redacted_thinking blocks),
        # Anthropic bills thinking tokens as output tokens. Surface them as reasoning_tokens.
        try:
            blocks = raw.get("content") or []
            has_thinking = False
            for blk in blocks:
                if isinstance(blk, dict) and blk.get("type") in ("thinking", "redacted_thinking"):
                    has_thinking = True
                    break
            if has_thinking and usage.get("output_tokens") is not None:
                normalized["usage"]["reasoning_tokens"] = usage.get("output_tokens")
        except Exception:
            pass
        return normalized

    # Google Gemini
    if provider_l in ("google", "gemini"):
        # Gemini responses do not consistently include the resolved model id; keep requested id.
        usage_md = meta.get("usage") or _safe_get(raw, "usageMetadata") or {}
        normalized["usage"]["input_tokens"] = usage_md.get("promptTokenCount") or usage_md.get("prompt_tokens")
        normalized["usage"]["output_tokens"] = usage_md.get("candidatesTokenCount") or usage_md.get("candidates_tokens")
        normalized["usage"]["reasoning_tokens"] = usage_md.get("thoughtsTokenCount") or usage_md.get("thinking_tokens")
        return normalized

    # OpenAI
    if provider_l == "openai":
        # Prefer provider-returned model id when present (useful when using aliases or routed endpoints).
        try:
            m = raw.get("model") or _safe_get(raw, "response", "model")
            if isinstance(m, str) and m:
                normalized["model"] = m
        except Exception:
            pass
        usage = meta.get("usage") or raw.get("usage") or {}
        if usage:
            normalized["usage"]["input_tokens"] = usage.get("prompt_tokens") or usage.get("input_tokens")
            normalized["usage"]["output_tokens"] = usage.get("completion_tokens") or usage.get("output_tokens")
            details = usage.get("output_tokens_details") or {}
            normalized["usage"]["reasoning_tokens"] = details.get("reasoning_tokens")
            # Responses-style cached tokens sometimes appear here too
            in_details = usage.get("input_tokens_details") or {}
            normalized["usage"]["cache_read_input_tokens"] = in_details.get("cached_tokens")
            return normalized
        resp_obj = raw.get("response") or raw
        u2 = resp_obj.get("usage") if isinstance(resp_obj, dict) else None
        if isinstance(u2, dict):
            normalized["usage"]["input_tokens"] = u2.get("input_tokens")
            normalized["usage"]["output_tokens"] = u2.get("output_tokens")
            out_details = u2.get("output_tokens_details") or {}
            normalized["usage"]["reasoning_tokens"] = out_details.get("reasoning_tokens")
            in_details = u2.get("input_tokens_details") or {}
            normalized["usage"]["cache_read_input_tokens"] = in_details.get("cached_tokens")
        return normalized

    return normalized


