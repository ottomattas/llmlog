from typing import Optional, Tuple, Dict, Any
import anthropic

from .secrets import load_secrets, get_provider_key


def chat_completion(prompt: str, model: str, max_tokens: Optional[int] = 1000, temperature: Optional[float] = None, thinking: Optional[Dict[str, Any]] = None) -> Tuple[str, Dict[str, Any]]:
    secrets = load_secrets()
    key = get_provider_key(secrets, "anthropic")
    if not key:
        raise RuntimeError("Missing Anthropic API key in secrets.json or ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=key)
    kwargs = {
        "model": model,
        "max_tokens": max_tokens or 1000,
        "messages": [{"role": "user", "content": prompt}],
    }
    if temperature is not None:
        kwargs["temperature"] = float(temperature)
    # Extended thinking per docs: https://docs.claude.com/en/docs/build-with-claude/extended-thinking
    # Accept generic thinking dict: {enabled: bool, budget_tokens: int}
    if thinking and thinking.get("enabled"):
        budget = thinking.get("budget_tokens")
        kwargs["thinking"] = {"type": "enabled"}
        if budget is not None:
            kwargs["thinking"]["budget_tokens"] = int(budget)
    resp = client.messages.create(**kwargs)
    # Extract final text blocks; ignore thinking/redacted_thinking blocks
    text_parts = []
    try:
        for block in getattr(resp, "content", []) or []:
            btype = getattr(block, "type", None)
            if btype == "text":
                t = getattr(block, "text", None)
                if t:
                    text_parts.append(t)
        text = "\n".join(text_parts).strip() if text_parts else getattr(getattr(resp, "content", [None])[0], "text", "")
    except Exception:
        text = str(resp)
    meta: Dict[str, Any] = {
        "raw_response": getattr(resp, "dict", lambda: resp)(),
        "finish_reason": getattr(resp, "stop_reason", None),
        "usage": {
            "input_tokens": getattr(getattr(resp, "usage", None), "input_tokens", None),
            "output_tokens": getattr(getattr(resp, "usage", None), "output_tokens", None),
        },
    }
    return text, meta


