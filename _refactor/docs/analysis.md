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
- `pricing_table`, resolved `pricing_tier`, and `pricing_rate` (the matched rate row snapshot used for the run)

Notes:
- `pricing_tier` defaults to `standard` unless the target explicitly overrides it.
- For submit-only batch APIs (Anthropic Message Batches, Gemini BatchGenerateContent), `_refactor` auto-selects
  `pricing_tier=batch` unless overridden.
- Cost totals are computed from **per-attempt provenance usage** and the saved `pricing_rate` snapshot. See
  `docs/runs-and-results.md` for provider-specific nuances (Google thinking tokens, OpenAI cached input, etc.).

### Generate a dashboard
```
python scripts/generate_dashboard.py --input reports/<run_id>.aggregated.json --output reports/<run_id>.dashboard.html
```

### Generate a combined interactive dashboard (all runs)
For an interactive, single-file dashboard that:
- scans `runs/**/results.jsonl` (latest-per-id semantics)
- uses `run.manifest.json` (when present) to label **representation** and **prompt mechanism**
- renders line plots with client-side filters over:
  - **model/compute**: provider, model, thinking mode
  - **problem structure**: horn vs nonhorn, SAT vs UNSAT
  - **difficulty**: maxvars (x-axis) and maxlen
  - **prompting**: prompt mechanism + representation

Run:
```
python scripts/generate_combined_dashboard.py --output reports/combined.dashboard.html
```

Defaults (when opening the HTML):
- **Thinking mode** defaults to `think_none` (non-thinking baselines), when present
- **Chart view** defaults to **Split by target (provider/model/thinking)** for model comparisons

To include high-reasoning runs, set **Thinking mode** to **All** and use the legend to toggle targets.

#### Accuracy metric (important for ongoing runs)
The combined dashboard offers multiple accuracy denominators:
- **completed (default)**: `correct / (answered + unclear)` (excludes **pending** and **errors**)
- **answered**: `correct / answered` (also excludes **unclear**)
- **nonpending**: `correct / (total - pending)` (includes **errors**)

This lets you track model performance during async collection without pending items dragging accuracy down.

#### Comparing lines on the same graph (multi-series)
To draw multiple lines for easy comparisons, use **Chart view** in the dashboard:
- **Aggregate (single line)**: one line for your current filter selection.
- **Split by …**: draws one line per category (e.g. target model, thinking mode, prompt mechanism, horn/nonhorn, SAT/UNSAT, maxlen, run).

When a split view is selected, a legend appears with checkboxes to toggle which series are shown (plus **All/None**).
Enable **Show overall baseline** to add an “Overall” line for quick “category vs average” comparisons (e.g. SAT/UNSAT vs overall).

#### Cost + latency (paper-oriented)
Use **Y metric** to switch the plot from accuracy to:
- **Cost / correct (USD)** (from per-attempt token usage and pricing-rate snapshots in `run.manifest.json`)
- **Reasoning cost / correct (USD, est.)** (uses `reasoning_tokens` × output-token rate as a best-effort estimate)
- **Latency (seconds, mean)** (from `timing_ms` in provenance)

This supports paper tables/figures for RQ3 (test-time compute vs cost-efficiency) and RQ5 (cross-provider comparisons).

Timing nuance:
- Dashboards/analysis prefer `results.provenance.v2.jsonl` when present.
- In batch submit-only modes, providers typically do **not** expose per-item latency; provenance v2 records batch-level
  durations when available and includes `timing_ms_source` to explain what the latency represents.

#### Suggested “figure recipes” (quick)
- **Cross-provider baseline comparison (RQ5)**:
  - Thinking mode: `think_none`
  - Chart view: `Split by target`
  - Y metric: `Accuracy`
  - Then compare curves across providers at fixed `{representation,prompt,maxlen,horn,sat}`.

- **Compute ablation (RQ3)**:
  - Thinking mode: `All`
  - Provider: `openai`
  - Chart view: `Split by target` (to compare `gpt-5.2* think_none` vs `gpt-5.2-pro think_high`)
  - Y metric: `Cost / correct (USD)` (and optionally `Accuracy` for the same filter set)

- **SAT/UNSAT asymmetry (RQ2/RQ5)**:
  - Chart view: `Split by SAT / UNSAT`
  - Baseline: on
  - Y metric: `Accuracy`

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
python scripts/export_provenance.py --provenance runs/<suite>/<run>/<provider>/<model>/<thinking_mode>/results.provenance.v2.jsonl --out reports/exports --limit 50 --no-raw
```

### Export validation slices (single Markdown)
For quick manual validation across many targets, you can export slices from `runs/**/results.provenance*.jsonl`
into a **single, shareable Markdown file** with an index and collapsible sections:
```
python scripts/export_validation_slices_md.py --runs-dir runs --out reports/validation_slices_vars40_all.md --maxvars 40
```

Notes:
- Outputs under `reports/` are **gitignored by default** (see `docs/runs-and-results.md`).
- The exporter prefers `results.provenance.v2.jsonl` when present and falls back to v1.
- Useful flags:
  - `--include-thinking`: include `thinking_text` blocks when present
  - `--ids-mode intersection`: only include ids present for every target-run in a slice
  - `--run-regex ...` / `--suite-regex ...`: restrict which runs are included
  - `--max-ids-per-slice 1`: generate a small preview quickly

