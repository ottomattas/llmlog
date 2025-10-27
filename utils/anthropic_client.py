from typing import Optional, Tuple, Dict, Any
import anthropic

from .secrets import load_secrets, get_provider_key


def chat_completion(prompt: str, model: str, max_tokens: Optional[int] = 1000, temperature: Optional[float] = None, thinking: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
    secrets = load_secrets()
    key = get_provider_key(secrets, "anthropic")
    if not key:
        raise RuntimeError("Missing Anthropic API key in secrets.json or ANTHROPIC_API_KEY")
    # Use a reasonable client timeout; SDK default is 10 minutes for non-streaming
    client = anthropic.Anthropic(api_key=key)
    kwargs = {
        "model": model,
        "max_tokens": max_tokens or 1000,
        "messages": [{"role": "user", "content": prompt}],
    }
    # Temperature handling: when extended thinking is enabled, Anthropic requires temperature semantics of 1
    # (API errors if you set another value). We therefore ignore provided temperature when thinking is enabled.
    if thinking and thinking.get("enabled"):
        # omit temperature entirely or force to 1; prefer omitting to avoid conflicts
        pass
    else:
        if temperature is not None:
            kwargs["temperature"] = float(temperature)
    # Extended thinking per docs: https://docs.claude.com/en/docs/build-with-claude/extended-thinking
    # Accept generic thinking dict: {enabled: bool, budget_tokens: int}
    if thinking and thinking.get("enabled"):
        budget = thinking.get("budget_tokens")
        kwargs["thinking"] = {"type": "enabled"}
        if budget is not None:
            kwargs["thinking"]["budget_tokens"] = int(budget)
            # Ensure Anthropic constraint: max_tokens must be greater than thinking.budget_tokens
            try:
                cur_max = int(kwargs.get("max_tokens") or 0)
                b = int(budget)
                if cur_max <= b:
                    # bump max_tokens just above budget; choose a small buffer
                    kwargs["max_tokens"] = b + 512
            except Exception:
                pass
    # Prefer streaming for long/complex requests to avoid SDK 10-minute guard on non-streaming
    # See: Anthropic SDK docs (long requests, streaming responses)
    # https://github.com/anthropics/anthropic-sdk-python?tab=readme-ov-file#long-requests
    # https://github.com/anthropics/anthropic-sdk-python?tab=readme-ov-file#streaming-responses

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

    # Always stream to avoid non-stream 10-minute guard
    text_buf: list[str] = []
    meta: Dict[str, Any] = {"raw_response": None, "finish_reason": "stream_stop", "usage": {}}
    # Prefer the SDK streaming context manager to reliably access final message (with usage)
    try:
        with client.messages.stream(**kwargs) as stream:
            # Collect only text deltas via high-level iterator if available
            try:
                for delta in stream.text_stream:
                    if delta:
                        text_buf.append(delta)
            except Exception:
                # Fallback to low-level event iteration
                for event in stream:
                    et = getattr(event, "type", None)
                    if et == "content_block_delta":
                        delta = getattr(event, "delta", None)
                        if delta and getattr(delta, "type", None) == "text_delta":
                            frag = getattr(delta, "text", None)
                            if frag:
                                text_buf.append(frag)
            # Get final message containing usage
            try:
                final_msg = stream.get_final_message()
            except Exception:
                final_msg = None
        text = ("".join(text_buf)).strip()
        if final_msg:
            # Populate meta from final message
            try:
                meta["raw_response"] = getattr(final_msg, "dict", lambda: final_msg)()
            except Exception:
                meta["raw_response"] = None
            meta["finish_reason"] = getattr(final_msg, "stop_reason", None)
            usage_obj = getattr(final_msg, "usage", None)
            meta["usage"] = {
                "input_tokens": getattr(usage_obj, "input_tokens", None) if usage_obj else None,
                "output_tokens": getattr(usage_obj, "output_tokens", None) if usage_obj else None,
            }
            if not text:
                try:
                    text = _extract_message_text(final_msg)
                except Exception:
                    pass
        return text, meta
    except Exception:
        # As a last resort, try non-stream to ensure we at least get a response and usage
        try:
            resp = client.messages.create(**kwargs)
            text = _extract_message_text(resp)
            if not text:
                text = str(resp)
            meta = {
                "raw_response": getattr(resp, "dict", lambda: resp)(),
                "finish_reason": getattr(resp, "stop_reason", None),
                "usage": {
                    "input_tokens": getattr(getattr(resp, "usage", None), "input_tokens", None),
                    "output_tokens": getattr(getattr(resp, "usage", None), "output_tokens", None),
                },
            }
            return text, meta
        except Exception:
            # Give up; return empty usage
            return "", meta


