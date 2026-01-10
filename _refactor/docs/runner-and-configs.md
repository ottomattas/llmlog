## Runner and configs

This document describes how to configure and run experiments inside `_refactor/`.

### Concepts
- **Suite config**: a YAML file in `configs/suites/` describing *what to measure* (task/subset/representation/prompting policy) and where the dataset is.
- **Target set**: a YAML file in `configs/targets/` listing provider/model combinations (plus thinking/max_tokens/etc).

Targets can also include:
- `pricing_tier`: `standard|batch|flex|priority` (used to pick the correct pricing row when computing `cost_*` totals).
  If omitted, the runner defaults to `standard`, except that submit-only batch APIs (Anthropic/Gemini) default to `batch`.

Target sets in this repo are intentionally **model-specific**: each suite references one or more
target files under `configs/targets/` via `targets_ref`.

We do **not** auto-sync targets from provider model listing APIs inside `_refactor/` in order to
keep research runs reproducible. When you adopt a new model id, add a new target YAML explicitly
and wire it into suites.

### Running a suite
From `_refactor/`:
```
python scripts/run.py --suite configs/suites/sat__repr-cnf_compact__subset-hornonly__prompt-examples_only__openai_gpt-5.2__think-none.yaml --run demo-001 --limit 10 --resume --lockstep
```

### Where results are stored (results vs provenance)
Each suite+run+target writes to:
`runs/<suite_name>/<run_id>/<provider>/<model>/<thinking_mode>/`

Files:
- `results.jsonl`: **minimal** per-item record used for completion accounting:
  - `parsed_answer`, `error`, `submission_id`, etc.
  - Append-only: the **latest row per `id`** is authoritative.
- `results.provenance.jsonl`: **full provenance (v1)** (enabled by default) with:
  - `prompt` (optional), `completion_text`, `thinking_text`, `usage`, `finish_reason`, `raw_response`
- `results.provenance.v2.jsonl`: **full provenance (v2)** (also written by default):
  - Same core fields as v1, plus unified `job` / `provider_output` / timing source fields.
  - Dashboard/analysis prefers v2 when present; v1 remains for backwards compatibility.
- `results.summary.json`: aggregate stats (counts + token/cost totals when available)
- `run.manifest.json`: manifest with suite/model metadata used by dashboards/analysis

Provider-specific notes (what is / is not “chain-of-thought”):
- **OpenAI**: `completion_text` is the visible answer; `thinking_text` is a best-effort **reasoning summary** when the API exposes one. Full raw chain-of-thought is not generally exposed.
- **Anthropic**: when extended thinking is enabled, `thinking_text` captures streamed thinking deltas (see Anthropic extended thinking docs: `https://platform.claude.com/docs/en/build-with-claude/extended-thinking`).
- **Google Gemini**:
  - `raw_response` stores the full Gemini response object. For Gemini 3, responses may include **`thoughtSignature`** fields.
  - **Thought signatures are encrypted** and are **not** readable chain-of-thought. They are used to preserve reasoning context for tool/function calling and must be preserved when required (Gemini thought signatures docs: `https://ai.google.dev/gemini-api/docs/thought-signatures`).
  - If thought summaries are enabled on requests, we store them into `thinking_text` and exclude them from `completion_text` so answer parsing remains stable (Gemini thinking docs: `https://ai.google.dev/gemini-api/docs/thinking`).

### Two execution modes (recommended naming)
In this repo it helps to think of two modes:

- **Live mode (blocking / poll-until-done)**: `scripts/run.py` waits for the model response and parses it immediately.
- **Async mode (submit now, collect later)**: `scripts/run.py --submit-only` submits work and records response ids, then a separate collector fetches results later.

Notes:
- This is **not** “streaming mode”: we currently do not stream tokens in the runner CLI. (Streaming is mainly useful for interactive chat UX.)
- For OpenAI `gpt-5*`, requests are submitted with server-side `background=true`; “live mode” simply means we poll until terminal.

#### Choosing live vs async (practical guidance)
- **Prefer live mode** when:
  - you want the answer immediately (interactive debugging)
  - you expect most calls to finish quickly
  - you want parsing/correctness computed in the same step
- **Prefer async mode** when:
  - calls can take minutes (hard problems / high reasoning)
  - you want “submit fast, come back later”
  - you want to reduce client-side timeouts / terminal babysitting

#### Budget-aware batching (recommended for expensive requests)
If a single request costs ~€1–€2, avoid submitting hundreds at once.
A simple pattern is to submit **small batches** and collect between batches.

Use `--limit N` to cap how many new problems are processed per invocation.
With `--resume`, already-submitted ids (pending or completed) will not be resubmitted.

Notes:
- `--limit` is an **execution cap** (batch size), not a dataset definition change. It should not change the canonical run metadata.
- With `--resume`, you can repeat the same `--limit N` command to continue processing the next batch (already-done ids are skipped).
- For traceability, each runner invocation is appended to `run.invocations.jsonl` inside the per-target run folder.

Example “batch of 10” submit-only pass:
```
python scripts/run.py --suite <suite.yaml> --run <run_id> \
  --maxvars 10,20,30,40,50 --maxlen 3 --case-limit 10 \
  --resume --lockstep --rerun-errors --submit-only --limit 10
```

Then run the collector in watch mode:
```
python scripts/collect_openai_submissions.py --runs-dir runs --watch-seconds 60
```

Repeat the submit-only command until you no longer have remaining errors (or until you hit your spend cap).

#### Collector polling strategy (how aggressively to fetch)
The collector supports two approaches:
- **Watch (recommended)**: `--watch-seconds 30/60/120` repeatedly checks and appends results when they become terminal.
  - This avoids long blocking on a single response id and keeps API traffic predictable.
- **Per-id poll (`--poll`)**: waits for each response id to become terminal (can block a long time per item).
  - Use only for small numbers of ids when you explicitly want to wait until completion.

### Async mode (submit now, collect later) for OpenAI Responses
For long-running reasoning calls where you don't need results immediately, you can submit work in background
and collect later (useful to avoid client-side timeouts and keep better accounting of `resp_id`s).

Submit without polling (writes `openai_response_id` and leaves `parsed_answer` empty/pending):
```
python scripts/run.py --suite <suite.yaml> --run <run_id> \
  --maxvars 10,20,30,40,50 --maxlen 3 --case-limit 10 \
  --resume --lockstep --submit-only
```

Collect completed Responses later (batch or watch):
```
python scripts/collect_openai_submissions.py --runs-dir runs
python scripts/collect_openai_submissions.py --runs-dir runs --watch-seconds 60
```

You can also do a preflight (targets + pricing + rough cost upper bound) without running:
```
python scripts/run.py --suite configs/suites/sat__repr-cnf_compact__subset-hornonly__prompt-examples_only__openai_gpt-5.2__think-none.yaml --preflight-only --estimate-cost
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
- `prompts/sat_decision__horn_if_then__examples_only.j2`
- `prompts/sat_decision__horn_if_then__horn_alg_from.j2`
- `prompts/sat_decision__horn_if_then__horn_alg_linear.j2`
- `prompts/sat_decision__cnf_compact__examples_only.j2`
- `prompts/sat_decision__cnf_compact__horn_alg_from.j2`
- `prompts/sat_decision__cnf_compact__horn_alg_linear.j2`
- `prompts/sat_decision__cnf_compact__dpll_alg_from.j2`
- `prompts/sat_decision__cnf_compact__dpll_alg_linear.j2`
- `prompts/sat_decision__cnf_nl__examples_only.j2`
- `prompts/sat_decision__cnf_nl__horn_alg_from.j2`
- `prompts/sat_decision__cnf_nl__horn_alg_linear.j2`
- `prompts/sat_decision__cnf_nl__dpll_alg_from.j2`
- `prompts/sat_decision__cnf_nl__dpll_alg_linear.j2`

### Parsing + correctness
The runner parses model output into `parsed_answer`:
- `0`: YES / CONTRADICTION / UNSAT
- `1`: NO / SATISFIABLE / SAT
- `2`: unclear

In `--submit-only` mode, `parsed_answer` is left empty/pending until collection.

Correctness is computed against the dataset `issatisfiable` flag (`0` unsat, `1` sat) when available.

### Concurrency, retries, resume
Configured under `concurrency`:
- `lockstep`: run each problem across all targets before moving on (helpful for fair comparisons).
- `workers`: max concurrent API calls per problem in lockstep mode.
- `retry.max_attempts` and `retry.backoff_seconds`: basic retry/backoff for transient errors.

