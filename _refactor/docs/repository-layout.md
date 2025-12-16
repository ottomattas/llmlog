## Repository layout

This document describes a target layout that cleanly separates:
- **Code** (importable Python package)
- **CLIs** (thin wrappers)
- **Configs** (YAML)
- **Prompts** (templates)
- **Datasets** (curated inputs)
- **Artifacts** (runs/plots/reports; usually not committed)

### Current layout (what exists today)
- `_legacy/`: original exp1–exp8 scripts and outputs (kept intact).
- `experiments/`: config-driven runner + analysis tools + dashboards.
- `prompts/`: Jinja templates and legacy prompt samples.
- `data/`: problem sets used as inputs.
- `utils/`: provider clients and router.
- `experiments/runs/`: large run artifact tree (results/config snapshots/metadata).

### Target layout (recommended)

```
src/
  llmlog/
    problems/        # dataset schema + generator + solver adapters
    prompts/         # template rendering helpers
    run/             # runner + concurrency/retry + provenance writing
    providers/       # anthropic/google/openai + unified router
    analysis/        # analyze/aggregate/compare/plot (pure functions)

scripts/
  makeproblems.py    # dataset generator CLI (writes dataset files)
  run.py             # run an experiment suite
  analyze.py         # analyze one or more result files

configs/
  README.md
  suites/            # experiment suite configs
  targets/           # shared provider/model target definitions

prompts/
  README.md
  *.j2

datasets/
  README.md
  legacy/
  validation/
  production/

runs/                # run artifacts (NOT committed by default)
reports/             # plots/tables/dashboards (usually NOT committed)
```

### Conventions
- **Code lives under `src/`**: avoids accidental imports from the repo root and makes packaging straightforward.
- **Artifacts are not code**: treat `runs/` and most of `reports/` as generated outputs. Keep the repo lean by default.
- **Datasets are curated**: keep validation/production sets separated; record seed + generation command + checksum. Large datasets are tracked via Git LFS (see `.gitattributes`).
