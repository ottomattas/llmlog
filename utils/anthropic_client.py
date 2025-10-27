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
    thinking_buf: list[str] = []
    last_stream_usage: Dict[str, Any] = {}
    meta: Dict[str, Any] = {"raw_response": None, "finish_reason": "stream_stop", "usage": {}}
    # Prefer the SDK streaming context manager to reliably access final message (with usage)
    try:
        with client.messages.stream(**kwargs) as stream:
            # Prefer low-level iteration so we can capture text, thinking, and message_delta usage
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
                    # signature_delta and others are ignored for accumulation
                elif et == "message_delta":
                    # Capture cumulative usage snapshot if present
                    usage_obj = getattr(event, "usage", None)
                    if usage_obj:
                        last_stream_usage = {
                            "input_tokens": getattr(usage_obj, "input_tokens", None),
                            "output_tokens": getattr(usage_obj, "output_tokens", None),
                        }
                    else:
                        # Try dict() fallback
                        try:
                            d = getattr(event, "dict", lambda: None)()
                            if isinstance(d, dict) and d.get("usage"):
                                u = d["usage"]
                                last_stream_usage = {
                                    "input_tokens": u.get("input_tokens"),
                                    "output_tokens": u.get("output_tokens"),
                                }
                        except Exception:
                            pass
                else:
                    # ignore other event types
                    pass
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
            # If final message lacked usage, fallback to the last streamed usage snapshot
            if (meta["usage"].get("input_tokens") is None and meta["usage"].get("output_tokens") is None) and last_stream_usage:
                meta["usage"].update(last_stream_usage)
            if not text:
                try:
                    text = _extract_message_text(final_msg)
                except Exception:
                    pass
        # Optionally compute visible token counts for thinking/text; expose billed reasoning via usage
        if thinking_buf:
            thinking_text = "".join(thinking_buf)
            try:
                # Count tokens for the thinking content; API returns an object with input_tokens
                # We pass the thinking block as assistant content of type "thinking"
                count_resp = client.messages.count_tokens(
                    model=kwargs["model"],
                    messages=[{"role": "assistant", "content": [{"type": "thinking", "thinking": thinking_text}]}],
                )
                t_thinking = getattr(count_resp, "input_tokens", None)
                if t_thinking is None and hasattr(count_resp, "dict"):
                    try:
                        t_thinking = count_resp.dict().get("input_tokens")
                    except Exception:
                        pass
                meta.setdefault("usage", {})["thinking_visible_tokens"] = t_thinking
            except Exception:
                # If count endpoint not available or thinking blocks not countable, leave as None
                meta.setdefault("usage", {})["thinking_visible_tokens"] = None
        # Count visible final text tokens as well
        try:
            if text:
                c_text = client.messages.count_tokens(
                    model=kwargs["model"],
                    messages=[{"role": "assistant", "content": [{"type": "text", "text": text}]}],
                )
                t_text = getattr(c_text, "input_tokens", None)
                if t_text is None and hasattr(c_text, "dict"):
                    try:
                        t_text = c_text.dict().get("input_tokens")
                    except Exception:
                        pass
                meta.setdefault("usage", {})["text_visible_tokens"] = t_text
        except Exception:
            meta.setdefault("usage", {})["text_visible_tokens"] = None
        # Expose billed reasoning tokens when thinking is enabled (as total output tokens billed)
        if thinking and thinking.get("enabled"):
            try:
                out_total = meta.get("usage", {}).get("output_tokens")
                u = meta.setdefault("usage", {})
                u["reasoning_tokens_billed"] = out_total
                # Back-compat: populate reasoning_tokens field used by runner/provenance
                u["reasoning_tokens"] = out_total
            except Exception:
                pass
        else:
            # Ensure reasoning_tokens exists for schema compatibility
            meta.setdefault("usage", {})["reasoning_tokens"] = None
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


