from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import anthropic

from .secrets import get_provider_key, load_secrets


def chat_completion(
    *,
    prompt: str,
    system: Optional[str] = None,
    model: str,
    max_tokens: Optional[int] = 1000,
    temperature: Optional[float] = None,
    thinking: Optional[Dict[str, Any]] = None,
) -> Tuple[str, Dict[str, Any], Optional[str]]:
    """Return (text, meta, thinking_text)."""
    secrets = load_secrets()
    key = get_provider_key(secrets, "anthropic")
    if not key:
        raise RuntimeError("Missing Anthropic API key in secrets.json or ANTHROPIC_API_KEY")

    client = anthropic.Anthropic(api_key=key)
    kwargs: Dict[str, Any] = {
        "model": model,
        "max_tokens": max_tokens or 1000,
        "messages": [{"role": "user", "content": prompt}],
    }
    # Messages API has a top-level system parameter (no "system" role in messages).
    if system:
        kwargs["system"] = str(system)

    # When extended thinking is enabled, Anthropic requires temperature semantics of 1;
    # omit temperature to avoid invalid combinations.
    if thinking and thinking.get("enabled"):
        pass
    else:
        if temperature is not None:
            kwargs["temperature"] = float(temperature)

    # Extended thinking per docs: https://docs.claude.com/en/docs/build-with-claude/extended-thinking
    if thinking and thinking.get("enabled"):
        budget = thinking.get("budget_tokens")
        kwargs["thinking"] = {"type": "enabled"}
        if budget is not None:
            kwargs["thinking"]["budget_tokens"] = int(budget)
            try:
                cur_max = int(kwargs.get("max_tokens") or 0)
                b = int(budget)
                if cur_max <= b:
                    kwargs["max_tokens"] = b + 512
            except Exception:
                pass

    def _extract_message_text(message_obj: Any) -> str:
        parts = []
        try:
            for block in getattr(message_obj, "content", []) or []:
                if getattr(block, "type", None) == "text":
                    t = getattr(block, "text", None)
                    if t:
                        parts.append(t)
        except Exception:
            pass
        return ("\n".join(parts)).strip()

    text_buf: list[str] = []
    thinking_buf: list[str] = []
    last_stream_usage: Dict[str, Any] = {}
    meta: Dict[str, Any] = {"raw_response": None, "finish_reason": "stream_stop", "usage": {}}

    try:
        with client.messages.stream(**kwargs) as stream:
            for event in stream:
                et = getattr(event, "type", None)
                if et == "content_block_delta":
                    delta = getattr(event, "delta", None)
                    if not delta:
                        continue
                    dt = getattr(delta, "type", None)
                    if dt == "text_delta":
                        frag = getattr(delta, "text", None)
                        if frag:
                            text_buf.append(frag)
                    elif dt == "thinking_delta":
                        tfrag = getattr(delta, "thinking", None)
                        if tfrag:
                            thinking_buf.append(tfrag)
                elif et == "message_delta":
                    usage_obj = getattr(event, "usage", None)
                    if usage_obj:
                        last_stream_usage = {
                            "input_tokens": getattr(usage_obj, "input_tokens", None),
                            "output_tokens": getattr(usage_obj, "output_tokens", None),
                        }
            try:
                final_msg = stream.get_final_message()
            except Exception:
                final_msg = None

        text = ("".join(text_buf)).strip()
        if final_msg:
            try:
                meta["raw_response"] = getattr(final_msg, "dict", lambda: final_msg)()
            except Exception:
                meta["raw_response"] = None
            meta["finish_reason"] = getattr(final_msg, "stop_reason", None)
            usage_obj = getattr(final_msg, "usage", None)
            meta["usage"] = {
                "input_tokens": getattr(usage_obj, "input_tokens", None) if usage_obj else None,
                "output_tokens": getattr(usage_obj, "output_tokens", None) if usage_obj else None,
                "cache_creation_input_tokens": getattr(usage_obj, "cache_creation_input_tokens", None) if usage_obj else None,
                "cache_read_input_tokens": getattr(usage_obj, "cache_read_input_tokens", None) if usage_obj else None,
            }
            if (meta["usage"].get("input_tokens") is None and meta["usage"].get("output_tokens") is None) and last_stream_usage:
                meta["usage"].update(last_stream_usage)
            if not text:
                text = _extract_message_text(final_msg)

        thinking_text = ("".join(thinking_buf)).strip() if thinking_buf else None
        return text, meta, thinking_text
    except Exception:
        # Fallback to non-streaming
        resp = client.messages.create(**kwargs)
        text = _extract_message_text(resp) or str(resp)
        meta = {
            "raw_response": getattr(resp, "dict", lambda: resp)(),
            "finish_reason": getattr(resp, "stop_reason", None),
            "usage": {
                "input_tokens": getattr(getattr(resp, "usage", None), "input_tokens", None),
                "output_tokens": getattr(getattr(resp, "usage", None), "output_tokens", None),
                "cache_creation_input_tokens": getattr(getattr(resp, "usage", None), "cache_creation_input_tokens", None),
                "cache_read_input_tokens": getattr(getattr(resp, "usage", None), "cache_read_input_tokens", None),
            },
        }
        return text, meta, None


