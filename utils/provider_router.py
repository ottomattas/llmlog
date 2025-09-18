from typing import List, Dict, Any, Optional

from .openai_client import chat_completion as openai_chat
from .anthropic_client import chat_completion as anthropic_chat
from .gemini_client import chat_completion as gemini_chat


def run_chat(provider: str, model: str, prompt: str, sysprompt: Optional[str] = None, max_tokens: Optional[int] = None, temperature: float = 0.0, seed: Optional[int] = None) -> str:
    provider = provider.lower()
    if provider == "anthropic":
        # System prompt gets merged into user prompt for Claude simple path
        full_prompt = f"{sysprompt}\n{prompt}" if sysprompt else prompt
        return anthropic_chat(prompt=full_prompt, model=model, max_tokens=max_tokens)
    elif provider in ("google"):
        full_prompt = f"{sysprompt}\n{prompt}" if sysprompt else prompt
        return gemini_chat(prompt=full_prompt, model=model, max_tokens=max_tokens, temperature=temperature)
    elif provider == "openai":
        messages: List[Dict[str, str]] = []
        if sysprompt:
            messages.append({"role": "system", "content": sysprompt})
        messages.append({"role": "user", "content": prompt})
        return openai_chat(messages=messages, model=model, max_tokens=max_tokens, temperature=temperature, seed=seed)
    else:
        raise NotImplementedError(f"Provider not supported: {provider}")


