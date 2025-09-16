from typing import Optional
import anthropic

from .secrets import load_secrets, get_provider_key


def chat_completion(prompt: str, model: str, max_tokens: Optional[int] = 1000) -> str:
    secrets = load_secrets()
    key = get_provider_key(secrets, "anthropic")
    if not key:
        raise RuntimeError("Missing Anthropic API key in secrets.json or ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=key)
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens or 1000,
        messages=[{"role": "user", "content": prompt}],
    )
    try:
        return resp.content[0].text
    except Exception:
        return str(resp)


