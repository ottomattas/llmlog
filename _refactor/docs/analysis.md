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

### Generate a combined interactive dashboard (all runs)
For an interactive, single-file dashboard that:
- scans `runs/**/results.jsonl` (latest-per-id semantics)
- uses `run.manifest.json` (when present) to label **representation** and **prompt mechanism**
- renders a vars→accuracy plot with client-side filters (maxlen, prompt mechanism, horn vs nonhorn, etc.)

Run:
```
python scripts/generate_combined_dashboard.py --output reports/combined.dashboard.html
```

#### Accuracy metric (important for ongoing runs)
The combined dashboard offers multiple accuracy denominators:
- **completed (default)**: `correct / (answered + unclear)` (excludes **pending** and **errors**)
- **answered**: `correct / answered` (also excludes **unclear**)
- **nonpending**: `correct / (total - pending)` (includes **errors**)

This lets you track model performance during async collection without pending items dragging accuracy down.

#### Keeping it up to date while runs are ongoing
Run the OpenAI collector in watch mode:
```
python scripts/collect_openai_submissions.py --runs-dir runs --watch-seconds 60
```

Then refresh the dashboard periodically (or run in watch mode too):
```
python scripts/generate_combined_dashboard.py --output reports/combined.dashboard.html --watch-seconds 60
```

### Inspect prompts + reasoning
If you enabled provenance output, you can export individual prompts and responses:
```
python scripts/export_provenance.py --provenance runs/<suite>/<run>/<provider>/<model>/<thinking_mode>/results.provenance.jsonl --out reports/exports --limit 50 --no-raw
```

