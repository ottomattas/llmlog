from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


PricingTier = Literal["standard", "batch", "flex", "priority"]


class ModelRate(BaseModel):
    """Per-million-token USD rates for a provider/model family.

    Matching:
    - Prefer exact `model`
    - Else use `model_prefix` (longest prefix wins)
    """

    provider: str
    model: Optional[str] = None
    model_prefix: Optional[str] = None

    # Pricing tier / service class (provider-specific but we standardize common ones)
    tier: PricingTier = "standard"

    input_per_million_usd: float
    output_per_million_usd: float

    # Optional cache token pricing (provider dependent)
    cache_read_input_per_million_usd: Optional[float] = None
    cache_creation_input_per_million_usd: Optional[float] = None
    # Some providers expose multiple cache-write TTLs (e.g., Anthropic 5m vs 1h).
    # When present, `cache_creation_input_per_million_usd` is treated as the default cache-write rate.
    cache_creation_input_1h_per_million_usd: Optional[float] = None

    # Optional context-cache storage cost (Google lists $/1M tokens/hour). Not currently used in cost calc.
    cache_storage_per_million_token_hours_usd: Optional[float] = None

    @model_validator(mode="after")
    def _validate_selector(self) -> "ModelRate":
        if not self.model and not self.model_prefix:
            raise ValueError("ModelRate must specify either model or model_prefix")
        return self


class PricingSource(BaseModel):
    source_url: str
    retrieved_at: str
    notes: Optional[str] = None


class PricingTable(BaseModel):
    name: str
    currency: Literal["USD"] = "USD"
    sources: List[PricingSource] = Field(default_factory=list)
    rates: List[ModelRate]


