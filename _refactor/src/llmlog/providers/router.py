from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..response_meta import normalize_meta
from .anthropic_client import chat_completion as anthropic_chat
from .google_client import chat_completion as gemini_chat
from .openai_client import chat_completion as openai_chat


def run_chat(
    *,
    provider: str,
    model: str,
    prompt: str,
    sysprompt: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: float = 0.0,
    seed: Optional[int] = None,
    thinking: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run a single prompt against a provider/model and return normalized metadata.

    Returns a dict containing:
    - text: visible model output text
    - thinking_text: provider-returned thinking/reasoning text when available (best-effort)
    - provider/model/finish_reason/usage/raw_response: normalized via `llmlog.response_meta.normalize_meta`
    """
    provider_l = (provider or "").lower()

    if provider_l == "anthropic":
        text, meta, thinking_text = anthropic_chat(
            prompt=prompt,
            system=sysprompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            thinking=thinking,
        )
        norm = normalize_meta("anthropic", model, meta)
        return {"text": text, "thinking_text": thinking_text, **norm}

    if provider_l in ("google", "gemini"):
        text, meta = gemini_chat(
            prompt=prompt,
            system=sysprompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            thinking=thinking,
        )
        norm = normalize_meta("google", model, meta)
        # Gemini thinking text is not always returned; keep placeholder for symmetry
        return {"text": text, "thinking_text": None, **norm}

    if provider_l == "openai":
        messages: List[Dict[str, str]] = []
        if sysprompt:
            messages.append({"role": "system", "content": sysprompt})
        messages.append({"role": "user", "content": prompt})
        text, meta = openai_chat(
            messages=messages,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            seed=seed,
            thinking=thinking,
        )
        norm = normalize_meta("openai", model, meta)
        return {"text": text, "thinking_text": None, **norm}

    raise NotImplementedError(f"Provider not supported: {provider}")


