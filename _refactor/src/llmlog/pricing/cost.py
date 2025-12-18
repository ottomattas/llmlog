from __future__ import annotations

from typing import Any, Dict, Optional

from .schema import ModelRate, PricingTable


def match_rate(table: PricingTable, *, provider: str, model: str) -> Optional[ModelRate]:
    """Find the best matching rate row for a given provider/model."""
    prov = (provider or "").lower()
    mod = (model or "")

    best: Optional[ModelRate] = None
    best_score = -1

    for r in table.rates:
        if (r.provider or "").lower() != prov:
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

    input_usd = (input_tokens / 1_000_000.0) * float(rate.input_per_million_usd)
    output_usd = (output_tokens / 1_000_000.0) * float(rate.output_per_million_usd)

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


