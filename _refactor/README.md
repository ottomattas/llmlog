## llmlog

Config-driven framework for running **logic-focused LLM experiments** reproducibly.

This README applies to the `_refactor/` directory; commands below assume your working directory is `_refactor/` (or that you adjust paths accordingly).

It supports an end-to-end workflow:
- **Generate datasets** of propositional-logic problems (with ground truth + optional proof metadata)
- **Render prompts** from Jinja templates
- **Run suites** across multiple providers/models using YAML configs
- **Parse outputs** into a unified schema
- **Analyze results** (aggregation, plots, dashboards)

### Design goals
- **Reproducible**: dataset/run generation is parameterized (seed, config snapshot, checksums).
- **Config-driven**: experiments are defined in YAML (not per-experiment forks).
- **Clear separation**: code vs configs vs datasets vs generated artifacts.

### Quickstart
1) Create a virtual environment and install dependencies:
```
python3 -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

2) Provide API keys (via env vars or `secrets.json`):
```
export ANTHROPIC_API_KEY=...
export OPENAI_API_KEY=...
export GOOGLE_API_KEY=...
```

3) Generate a problem dataset:
```
python scripts/generate_problems.py --seed 12345 --dataset validation --name problems_validation_seed12345
```

4) Run a small test suite (limit 10):
```
python scripts/run.py --config configs/suites/exp8_horn_yesno.yaml --run validation_001 --resume --limit 10
```

5) Analyze results:
```
python scripts/analyze.py runs/exp8_horn_yesno/validation_001/*/*/results.jsonl
```

### Documentation
- **Documentation index**: [`docs/README.md`](docs/README.md)
- **Problem generation**: [`docs/problem-generation.md`](docs/problem-generation.md)
- **Repository layout**: [`docs/repository-layout.md`](docs/repository-layout.md)
- **Datasets**: [`docs/datasets.md`](docs/datasets.md)
- **Runner + configs**: [`docs/runner-and-configs.md`](docs/runner-and-configs.md)
- **Providers + secrets**: [`docs/providers-and-secrets.md`](docs/providers-and-secrets.md)
- **Runs and results (artifacts policy)**: [`docs/runs-and-results.md`](docs/runs-and-results.md)
- **Analysis**: [`docs/analysis.md`](docs/analysis.md)
- **Migration plan**: [`docs/migration-plan.md`](docs/migration-plan.md)

### Directory layout
```
src/llmlog/           # importable package (runner, providers, analysis, datasets)
scripts/              # CLI entrypoints (thin wrappers around src/llmlog/)
configs/              # YAML experiment suites and shared target definitions
prompts/              # Jinja prompt templates
datasets/             # curated datasets (legacy/validation/production)
runs/                 # run artifacts (NOT committed by default)
reports/              # plots/tables/dashboards (usually NOT committed)
docs/                 # documentation
```

### License
Apache 2.0. See `LICENSE`.
