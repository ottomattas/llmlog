## Runner and configs

This document describes how to configure and run experiments inside `_refactor/`.

### Concepts
- **Suite config**: a YAML file in `configs/suites/` describing *what to measure* (task/subset/representation/prompting policy) and where the dataset is.
- **Target set**: a YAML file in `configs/targets/` listing provider/model combinations (plus thinking/max_tokens/etc).

We include two example target sets:
- `configs/targets/twelve_models.yaml`: stable 12-model matrix used in earlier experiments
- `configs/targets/latest_models.yaml`: curated pinned “latest models” set (see provider docs)
- `configs/targets/rolling_latest.yaml`: uses provider aliases where supported (fast adoption; less reproducible)

If you want to refresh targets automatically from provider APIs, use:
```
python scripts/sync_targets.py --out configs/targets/generated_latest_models.yaml --inventory-out reports/models_inventory.json
```

### Running a suite
From `_refactor/`:
```
python scripts/run.py --suite configs/suites/sat__repr-cnf_compact__subset-mixed.yaml --run demo-001 --limit 10 --resume --lockstep
```

You can also do a preflight (targets + pricing + rough cost upper bound) without running:
```
python scripts/run.py --suite configs/suites/sat__repr-cnf_compact__subset-mixed.yaml --preflight-only --estimate-cost
```

### Dataset drilldown (vars/len/id filters)
For iterative sweeps and “zoom in” experiments, `scripts/run.py` supports filtering rows from a larger dataset:
- `--maxvars 10,20,30,40,50` or `--maxvars 35-45`
- `--maxlen 3,4,5`
- `--ids 123,456,789` (exact row ids)
- `--case-limit N`: cap rows per case `(maxvarnr,maxlen,mustbehorn)` after filtering (useful for cheap sweeps)
- `--rerun-errors`: when resuming, re-run rows whose latest recorded result has `error != null`
- `--rerun-unclear`: when resuming, re-run rows whose latest recorded result has `parsed_answer == 2`

Examples:
```
# Sweep just var=10 and var=20 on the full dataset, 10 rows per (vars,len,horn) case
python scripts/run.py --suite <suite.yaml> --run sweep_vars10_20 --maxvars 10,20 --case-limit 10

# Drill into a suspected drop region
python scripts/run.py --suite <suite.yaml> --run drill_vars35_45 --maxvars 35-45 --case-limit 10

# Re-run specific problematic items by id
python scripts/run.py --suite <suite.yaml> --run ids_debug --ids 123,456,789
```

### Suite YAML fields (current)
See `src/llmlog/config/schema.py` for the full schema.

Key fields:
- `name`: suite id (used in output paths).
- `task`: currently `sat_decision`.
- `subset`: `hornonly | nonhornonly | mixed`.
- `dataset.path`: typically `datasets/validation/<file>.jsonl` (relative to `_refactor/`).
- `dataset.skip_rows`: usually `1` to skip the JSON header row.
- `prompting.render_policy`:
  - `fixed`: always use one `{representation, template, answer_format}` for all problems.
  - `match_formula`: choose one branch for Horn problems and another for non-Horn problems.
- `targets_ref`: one or more target-set YAML paths (relative to the suite file).
- `output_pattern`: output path template; supports `${name} ${run} ${provider} ${model} ${thinking_mode}`.
- `pricing_table` (optional): path to a pricing YAML under `configs/pricing/` used to compute `cost_*` totals in summaries.

### Prompt templates
Templates live under `prompts/` and are rendered with Jinja2. The runner injects:
- `clauses`: the rendered formula (depends on `representation`)

Current templates:
- `prompts/sat_decision__horn_rules__answer_only.j2`
- `prompts/sat_decision__cnf_compact__answer_only.j2`
- `prompts/sat_decision__cnf_nl__answer_only.j2`
- `prompts/sat_decision__mixed_interpretation__answer_only.j2`

### Parsing + correctness
The runner parses model output into `parsed_answer`:
- `0`: YES / CONTRADICTION / UNSAT
- `1`: NO / SATISFIABLE / SAT
- `2`: unclear

Correctness is computed against the dataset `issatisfiable` flag (`0` unsat, `1` sat) when available.

### Concurrency, retries, resume
Configured under `concurrency`:
- `lockstep`: run each problem across all targets before moving on (helpful for fair comparisons).
- `workers`: max concurrent API calls per problem in lockstep mode.
- `retry.max_attempts` and `retry.backoff_seconds`: basic retry/backoff for transient errors.

