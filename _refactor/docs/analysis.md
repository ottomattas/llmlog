## Analysis

### Aggregate results
Given a run id (the `${run}` segment in `runs/<suite>/<run>/...`):
```
python scripts/aggregate_results.py --run-id <run_id> --output reports/<run_id>.aggregated.json
```

### Cost normalization (pricing tables)
The runner can optionally compute **USD cost totals** per target using a versioned pricing YAML:
- Pricing tables live in `configs/pricing/` (example: `configs/pricing/openai_2025-12-18.yaml` from `https://platform.openai.com/pricing`).
- Suites can enable pricing by setting `pricing_table: <path>` (relative to `_refactor/` or absolute).

When enabled, `results.summary.json` will include:
- `stats.cost_input_usd`, `stats.cost_output_usd`, `stats.cost_total_usd`
- `pricing_table` and `pricing_rate` (the matched rate row snapshot used for the run)

### Generate a dashboard
```
python scripts/generate_dashboard.py --input reports/<run_id>.aggregated.json --output reports/<run_id>.dashboard.html
```

### Inspect prompts + reasoning
If you enabled provenance output, you can export individual prompts and responses:
```
python scripts/export_provenance.py --provenance runs/<suite>/<run>/<provider>/<model>/<thinking_mode>/results.provenance.jsonl --out reports/exports --limit 50 --no-raw
```

