## Paper outputs pipeline

This folder contains scripts to generate **paper-ready figures, tables, captions, and coverage-gap reports** from all historical runs under `experiments/runs/`.

All outputs are written to `experiments/paper_outputs/` (safe to delete and regenerate).

### Quick start

From repo root:

```bash
venv/bin/python -m experiments.paper.run_all
```

Options:

```bash
# include unclear-rate figure pages (in addition to accuracy / sat / unsat)
venv/bin/python -m experiments.paper.run_all --include-unclear-fig

# include full_text in the normalized dataset (makes data file much larger)
venv/bin/python -m experiments.paper.run_all --include-full-text
```

### What gets generated

#### Normalized data (re-parsed)

Under `experiments/paper_outputs/data/`:
- `reparsed_rows.jsonl`: one row per (leaf-run × problem id), using **re-parsed outputs** from provenance where possible
- `leaf_runs.csv`: one row per leaf run, basic health and file paths
- `leaf_run_prompt_map.csv`: mapping from leaf run → `prompt_id`
- `prompt_index.json`: prompt metadata (instruction text, prompt_style, parse_family)
- `prompt_examples.json`: a few example statement blocks per prompt_id (low/mid/high)
- `metrics_by_bucket.csv`: aggregated metrics by (model, prompt_id, thinking_mode, horn, maxvars, maxlen)
- `metrics_by_leaf.csv`: aggregated metrics by (model, prompt_id, thinking_mode, horn)

#### Prompt catalog

Under `experiments/paper_outputs/prompts/`:
- `prompt_catalog.md`: exact instruction text per prompt_id + example statement blocks

#### Figures

Under `experiments/paper_outputs/figures/`:
- `model_reports/`: one **PDF** per model (provider+model)
- `png/<provider>__<model>/`: per-page **PNG** exports

Each prompt_id typically has these pages:
- `__accuracy.png`: overall accuracy
- `__sat_accuracy.png`: accuracy on satisfiable instances (satflag=1)
- `__unsat_accuracy.png`: accuracy on unsatisfiable/contradiction instances (satflag=0)

Figures are **faceted by thinking_mode** (columns) and **horn flag** (rows, when both appear).

#### Tables

Under `experiments/paper_outputs/tables/`:
- `model_summary.csv`: one row per (model × thinking_mode × prompt_id × horn)
- `per_model/*__summary.csv`: model-scoped slices
- `per_model/*__summary.tex`: minimal LaTeX tabular versions

#### Captions

Under `experiments/paper_outputs/captions/`:
- `captions.md`: neutral, copy/paste captions for each figure page

#### Gap reports + suggested reruns

Under `experiments/paper_outputs/gaps/`:
- `gaps_by_group.csv`: missingness vs group union (per leaf run)
- `gaps_by_model_prompt.csv`: missing maxvars within observed spans (classified as `internal_hole` vs `sparse_span`)
- `run_recommendations.md`: suggested `experiments.runner` commands to resume/rerun incomplete/errored leaf runs

### Key implementation note: re-parsing

This pipeline **re-parses** from `results.provenance.jsonl` `full_text` where possible, using a robust “last decisive token” scan. This reduces historical “unclear” due to older parsing limitations, while still preserving “unclear” when outputs genuinely can’t be interpreted.

### Condensed figures (cross-model)

In addition to the per-model heatmap reports, the pipeline also generates a **condensed, cross-model** view under:

- `experiments/paper_outputs/figures_condensed/condensed_reports/`
- `experiments/paper_outputs/figures_condensed/png/`

These figures are grouped by **prompt family** (e.g. `horn_if_then`, `cnf_v1`, `cnf_v2`, plus `horn_unified_answer` when present) and use **line charts**:

- **x-axis**: `maxvars`
- **y-axis**: accuracy (overall / satisfiable-only / unsatisfiable-only)
- Separate panels for `maxlen`
- Separate pages for horn vs non-horn
- Marker size ∝ \(\\sqrt{n}\\) for the metric denominator, so sparse evidence is visually obvious


