## Experiment matrix (done vs todo)

This repo has a large experiment design space (subset × representation × prompt style × target × thinking mode × dataset slice).
To keep work coordinated, we track progress with a **matrix** generated from:

- **Configured design space** (suite YAMLs + a small matrix spec YAML), and
- **Observed run artifacts** under `runs/**/results.jsonl` (latest-per-id semantics).

### Why not rely on `run.manifest.json` for selection?

`run.manifest.json` is written into each leaf run folder, but it can be overwritten by later invocations (e.g. `--ids` gap-fill reruns).
For progress tracking, we instead key off the `meta` fields embedded in `results.jsonl`:

- `meta.maxvars`
- `meta.maxlen`
- `meta.horn`
- `meta.satflag`

### Generator

Use:

```
cd _refactor
python scripts/experiment_matrix.py \
  --matrix configs/matrices/openai_gpt-5.2-pro__think-high__prompt-matrix.yaml \
  --output docs/experiment-status/openai_gpt-5.2-pro__think-high__prompt-matrix.md
```

Compute-baseline tracking (gpt-5.2-2025-12-11 think-none vs gpt-5.2-pro think-high):

```
cd _refactor
python scripts/experiment_matrix.py \
  --matrix configs/matrices/openai_gpt-5.2__matrix.yaml --view compute_baseline \
  --output docs/experiment-status/openai_gpt-5.2__compute_baseline.md
```

Full think-none prompt matrix (mirrors the pro think-high prompt matrix):

```
cd _refactor
python scripts/experiment_matrix.py \
  --matrix configs/matrices/openai_gpt-5.2__matrix.yaml --view think_none_prompt_matrix \
  --output docs/experiment-status/openai_gpt-5.2__think-none__prompt-matrix.md
```

This produces a Markdown table with one row per suite and one column per `maxlen` value, marking each cell as:

- `DONE`: enough rows exist for that slice and there are no remaining errors/unclear (latest-per-id)
- `PARTIAL`: some rows exist but coverage is below the expected count
- `ERRORS` / `UNCLEAR` / `PENDING`: the slice exists but needs gap-fill passes
- `MISSING`: no matching run found

### Matrix specs

Matrix specs live under `configs/matrices/`. They define:

- the suite list to track
- the coarse sweep selection (`maxvars`, `lens`, `case_limit`)
- which `runs_dir` to scan

Start with the OpenAI-focused one:
- `configs/matrices/openai_gpt-5.2-pro__think-high__prompt-matrix.yaml`
- `configs/matrices/openai_gpt-5.2__matrix.yaml` (use `--view compute_baseline` or `--view think_none_prompt_matrix`)


