from __future__ import annotations


def test_match_rate_exact_and_prefix() -> None:
    from llmlog.pricing.schema import PricingTable
    from llmlog.pricing.cost import match_rate

    tbl = PricingTable(
        name="t",
        rates=[
            {"provider": "openai", "model_prefix": "gpt-5", "input_per_million_usd": 1.0, "output_per_million_usd": 2.0},
            {"provider": "openai", "model": "gpt-5.2", "input_per_million_usd": 1.75, "output_per_million_usd": 14.0},
        ],
    )
    r = match_rate(tbl, provider="openai", model="gpt-5.2")
    assert r is not None
    assert r.model == "gpt-5.2"

    r2 = match_rate(tbl, provider="openai", model="gpt-5.1")
    assert r2 is not None
    assert r2.model_prefix == "gpt-5"


def test_compute_cost_usd() -> None:
    from llmlog.pricing.schema import ModelRate
    from llmlog.pricing.cost import compute_cost_usd

    rate = ModelRate(provider="openai", model="gpt-5.2", input_per_million_usd=2.0, output_per_million_usd=10.0)
    usage = {"input_tokens": 500_000, "output_tokens": 100_000, "reasoning_tokens": 50_000}
    cost = compute_cost_usd(rate, usage)
    assert abs(cost["input_usd"] - 1.0) < 1e-9
    assert abs(cost["output_usd"] - 1.0) < 1e-9
    assert abs(cost["total_usd"] - 2.0) < 1e-9


