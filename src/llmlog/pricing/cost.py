from __future__ import annotations

from typing import Any, Dict, Optional

from .schema import ModelRate, PricingTable


def match_rate(
    table: PricingTable,
    *,
    provider: str,
    model: str,
    tier: str = "standard",
    allow_fallback_to_standard: bool = True,
) -> Optional[ModelRate]:
    """Find the best matching rate row for a given provider/model + pricing tier.

    Matching precedence:
    - Provider must match (case-insensitive)
    - Tier must match (default: standard). Rows with missing tier are treated as standard.
    - Prefer exact `model`
    - Else use `model_prefix` (longest prefix wins)

    If `tier` isn't found and `allow_fallback_to_standard` is True, we retry with tier=standard.
    """
    prov = (provider or "").lower()
    mod = (model or "")
    tier_l = (tier or "standard").lower()

    best: Optional[ModelRate] = None
    best_score = -1

    for r in table.rates:
        if (r.provider or "").lower() != prov:
            continue
        r_tier = (getattr(r, "tier", None) or "standard")
        if str(r_tier).lower() != tier_l:
            continue
        if r.model and r.model == mod:
            score = 10_000  # exact match always wins
        elif r.model_prefix and mod.startswith(r.model_prefix):
            score = len(r.model_prefix)
        else:
            continue

        if score > best_score:
            best = r
            best_score = score

    if best is None and allow_fallback_to_standard and tier_l != "standard":
        return match_rate(table, provider=provider, model=model, tier="standard", allow_fallback_to_standard=False)
    return best


def compute_cost_usd(rate: ModelRate, usage: Dict[str, Any]) -> Dict[str, Any]:
    """Compute a best-effort USD cost breakdown from normalized `usage` fields."""

    def _i(key: str) -> int:
        try:
            v = usage.get(key)
            return int(v) if v is not None else 0
        except Exception:
            return 0

    input_tokens = _i("input_tokens")
    output_tokens = _i("output_tokens")
    reasoning_tokens = _i("reasoning_tokens")
    cache_read_input_tokens = _i("cache_read_input_tokens")
    cache_creation_input_tokens = _i("cache_creation_input_tokens")

    provider_l = (rate.provider or "").lower()

    # Input pricing nuance:
    # - OpenAI: usage may include `input_tokens_details.cached_tokens` (we normalize to
    #   `cache_read_input_tokens`). Those cached tokens are a subset of input tokens and are billed at
    #   a separate cached-input rate. Avoid double-counting by charging:
    #     (input_tokens - cached_tokens) at input rate, plus cached_tokens at cached-input rate.
    # - Anthropic: cache read/write tokens are surfaced separately and should be charged in addition.
    non_cached_input_tokens = input_tokens
    if provider_l == "openai" and cache_read_input_tokens:
        non_cached_input_tokens = max(0, input_tokens - cache_read_input_tokens)

    input_usd = (non_cached_input_tokens / 1_000_000.0) * float(rate.input_per_million_usd)

    # Provider nuance:
    # - Google Gemini pricing is listed as "output tokens including thinking tokens".
    #   The API often reports thinking separately (thoughtsTokenCount). For Google runs, include
    #   `reasoning_tokens` in billed output.
    # - OpenAI and Anthropic output token counts already reflect billed output semantics.
    billed_output_tokens = output_tokens
    try:
        if provider_l == "google" and reasoning_tokens:
            billed_output_tokens = output_tokens + reasoning_tokens
    except Exception:
        pass
    output_usd = (billed_output_tokens / 1_000_000.0) * float(rate.output_per_million_usd)

    cache_read_usd = 0.0
    if rate.cache_read_input_per_million_usd is not None:
        cache_read_usd = (cache_read_input_tokens / 1_000_000.0) * float(rate.cache_read_input_per_million_usd)

    cache_creation_usd = 0.0
    if rate.cache_creation_input_per_million_usd is not None:
        cache_creation_usd = (cache_creation_input_tokens / 1_000_000.0) * float(rate.cache_creation_input_per_million_usd)

    reasoning_usd = (reasoning_tokens / 1_000_000.0) * float(rate.output_per_million_usd) if reasoning_tokens else 0.0
    total_usd = input_usd + output_usd + cache_read_usd + cache_creation_usd

    return {
        "currency": "USD",
        "input_usd": input_usd,
        "output_usd": output_usd,
        "cache_read_input_usd": cache_read_usd,
        "cache_creation_input_usd": cache_creation_usd,
        "reasoning_usd_estimate": reasoning_usd,
        "total_usd": total_usd,
    }


