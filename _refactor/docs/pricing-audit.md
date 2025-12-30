## Pricing audit (OpenAI usage + cost exports)

This doc explains how we **validate and maintain** the pricing YAML tables used by the runner to compute
`cost_*_usd` totals in `results.summary.json`.

### What the runner uses
- **Pricing tables** live under `configs/pricing/` (versioned YAML; see `configs/pricing/openai_2025-12-18.yaml`).
- **Suites** can enable pricing by setting `pricing_table: <path>` in the suite YAML.
- **Matching rule** (see `src/llmlog/pricing/cost.py`):
  - Prefer an **exact** `model:` match
  - Else use the **longest** matching `model_prefix:`

Important practical note:
- **OpenAI dashboard exports** often report a **pinned snapshot id** (example: `gpt-5.2-pro-2025-12-11`)
  even if you requested a stable alias (example: `gpt-5.2-pro`) in your run config.
- If your pricing table only contains `model: gpt-5.2-pro` and a generic `model_prefix: gpt-5.2`,
  then `gpt-5.2-pro-2025-12-11` would incorrectly fall back to `gpt-5.2` pricing.
- Fix: add a **`model_prefix: gpt-5.2-pro`** row (same rates) to cover pinned snapshot ids.

### How to export the CSVs (OpenAI)
We validate pricing by combining two exports from the OpenAI dashboard:
- **Completions usage** (token counts)
- **Costs** (USD cost line items)

Both exports should cover the **same date range** so we can compute effective pricing.

Reference:
- [OpenAI Pricing page](https://platform.openai.com/pricing)
- [OpenAI pricing docs (tiers: Batch/Flex/Standard/Priority)](https://platform.openai.com/docs/pricing)

### Service tiers (why the “official price” may look different)
OpenAI publishes **different token prices** depending on how requests are processed:
- **Standard**: the default tier for regular API calls.
- **Priority**: higher price for faster processing (only applies to models/tier combos that support it).
- **Flex**: lower price with higher latency (only applies to supported models).
- **Batch**: discounted pricing when using the **Batch API** (asynchronous, high latency; requires submitting a batch job).

How this relates to our exports + runs:
- The **usage export** includes a `service_tier` column (your export shows `service_tier=default`), which corresponds to **Standard** pricing.
- The usage export also includes a `batch` boolean (your export shows `batch=False`), so these calls were **not** Batch API calls.

So if you compare the export-implied rates to the **Batch** table on the docs page, they will look ~2× higher
(because Batch is ~50% of Standard for many models). The correct comparison here is the **Standard** table.

### How we compute effective pricing from exports
Given totals over a date range:
- \(r_{in} = \\frac{\\text{input_cost_usd}}{\\text{input_tokens}} \\cdot 10^6\)
- \(r_{out} = \\frac{\\text{output_cost_usd}}{\\text{output_tokens}} \\cdot 10^6\)

These rates are in **USD per 1M tokens** and should match what we store in `configs/pricing/*.yaml`.

### Example audit (from the provided exports)
Exports:
- `completions_usage_2025-12-25_2025-12-31.csv`
- `cost_2025-12-22_2025-12-31.csv`

Model in the exports:
- `gpt-5.2-pro-2025-12-11` (service tier: `default`)

Totals over the covered usage window:
| model | requests | input_tokens | output_tokens | input_cost_usd | output_cost_usd | implied_input_usd_per_1M | implied_output_usd_per_1M |
|---|---:|---:|---:|---:|---:|---:|---:|
| gpt-5.2-pro-2025-12-11 | 972 | 2,893,538 | 9,615,673 | 60.764298 | 1,615.433064 | 21.00 | 168.00 |

Sanity check (daily breakdown from the cost export; token counts shown are implied by the same rates):
| date | input_cost_usd | implied_input_tokens (@$21/M) | output_cost_usd | implied_output_tokens (@$168/M) |
|---|---:|---:|---:|---:|
| 2025-12-25 | 8.595258 | 409,298 | 199.726968 | 1,188,851 |
| 2025-12-26 | 15.114771 | 719,751 | 637.649544 | 3,795,533 |
| 2025-12-29 | 2.949576 | 140,456 | 169.639512 | 1,009,759 |
| 2025-12-30 | 34.104693 | 1,624,033 | 608.417040 | 3,621,530 |
| **total** | **60.764298** | **2,893,538** | **1,615.433064** | **9,615,673** |

### Comparison vs the official pricing table
As of the pricing table snapshot in `configs/pricing/openai_2025-12-18.yaml` (Standard tier; seeded from the
[OpenAI Pricing page](https://platform.openai.com/pricing), and consistent with the Standard table in the
[OpenAI pricing docs](https://platform.openai.com/docs/pricing)):
- **`gpt-5.2-pro` input**: $21 / 1M tokens
- **`gpt-5.2-pro` output**: $168 / 1M tokens

The export-implied rates above match **exactly**, so we can treat the pricing table values as validated.

For completeness, the docs page also lists **Batch** pricing for `gpt-5.2-pro` at **$10.50 / $84.00**
(input/output per 1M). That is expected to be ~50% of Standard, but it only applies if `batch=True`
and you are actually using the Batch API.

### Recommended repo policy
- **Keep pricing YAML versioned** (`openai_YYYY-MM-DD.yaml`) to preserve reproducibility.
- When you update rates:
  - add a new dated file (don’t rewrite history), or
  - update an existing file only if it’s explicitly a “living” table for ongoing work.
- Ensure any “Pro” variants have **their own explicit rows** and/or **their own prefix rows**
  so they do not accidentally match a cheaper family prefix (e.g., `gpt-5.2`).


