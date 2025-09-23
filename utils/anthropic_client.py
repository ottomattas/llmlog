from typing import Optional, Tuple, Dict, Any
import anthropic

from .secrets import load_secrets, get_provider_key


def chat_completion(prompt: str, model: str, max_tokens: Optional[int] = 1000, temperature: Optional[float] = None) -> Tuple[str, Dict[str, Any]]:
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
    resp = client.messages.create(**kwargs)
    try:
        text = resp.content[0].text
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


