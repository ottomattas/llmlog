from typing import List, Dict, Any, Optional

from .openai_client import chat_completion as openai_chat
from .anthropic_client import chat_completion as anthropic_chat
from .google_client import chat_completion as gemini_chat
from .response_meta import normalize_meta


def run_chat(provider: str, model: str, prompt: str, sysprompt: Optional[str] = None, max_tokens: Optional[int] = None, temperature: float = 0.0, seed: Optional[int] = None, thinking: Optional[Dict[str, Any]] = None) -> dict:
    provider = provider.lower()
    if provider == "anthropic":
        # System prompt gets merged into user prompt for Claude simple path
        full_prompt = f"{sysprompt}\n{prompt}" if sysprompt else prompt
        text, meta = anthropic_chat(prompt=full_prompt, model=model, max_tokens=max_tokens, temperature=temperature, thinking=thinking)
        norm = normalize_meta("anthropic", model, meta)
        return {"text": text, **norm}
    elif provider in ("google", "gemini"):
        full_prompt = f"{sysprompt}\n{prompt}" if sysprompt else prompt
        text, meta = gemini_chat(prompt=full_prompt, model=model, max_tokens=max_tokens, temperature=temperature, thinking=thinking)
        norm = normalize_meta("google", model, meta)
        return {"text": text, **norm}
    elif provider == "openai":
        messages: List[Dict[str, str]] = []
        if sysprompt:
            messages.append({"role": "system", "content": sysprompt})
        messages.append({"role": "user", "content": prompt})
        text, meta = openai_chat(messages=messages, model=model, max_tokens=max_tokens, temperature=temperature, seed=seed, thinking=thinking)
        norm = normalize_meta("openai", model, meta)
        return {"text": text, **norm}
    else:
        raise NotImplementedError(f"Provider not supported: {provider}")


