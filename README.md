## llmlog — New Config-Driven Experiment Framework

This repository hosts a new, unified framework for running logic-focused LLM experiments efficiently and reproducibly. The legacy one-off scripts (exp1–exp8) have been moved under `_legacy/` and remain intact. The new setup replaces copy‑pasted per-experiment code with a single runner configured via YAML, prompt templates, and pluggable parsing/filters.

### Quickstart
1) Set up environment and install dependencies
```
python -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

2) Provide API keys (alphabetically ordered providers)
```
export ANTHROPIC_API_KEY=...
export OPENAI_API_KEY=...
# or use a secrets.json as documented below
```

3) Run a small test (limit=10) against Anthropic + OpenAI using a ready config
```
python -m experiments.runner --config experiments/configs/exp8_yesno_horn.yaml \
  --resume --limit 10 --only anthropic,openai
```

4) Analyze and plot results
```
python -m experiments.analyze_generic experiments/runs/exp8_yesno_horn/anthropic_claude-3-5-sonnet-latest.jsonl
python -m experiments.analyze_generic experiments/runs/exp8_yesno_horn/openai_gpt-4o-2024-11-20.jsonl
python -m experiments.plot_results
ls experiments/plots
```

That’s it. Edit YAML configs under `experiments/configs/` to switch experiments or add more targets.

### Naming Scheme for Config Files
- Pattern: `exp<N>_<domain>_<task>[_<variant>]`
  - `<domain>`: `cnf` | `horn`
  - `<task>`: `contradiction` | `yesno` | `cot`
  - `<variant>` (optional): `linear` | `parents` | `v1` | `v2`
- Examples:
  - `exp3_cnf_cot_linear`
  - `exp4_cnf_cot_parents`
  - `exp5_horn_cot_linear`
  - `exp6_horn_yesno`
  - `exp8_horn_yesno`

This keeps descriptors in a consistent order: domain first, then task, then variant.

### Goals
- **Single runner, many configs**: No per-experiment code forks
- **Prompt templating**: Jinja2 templates with per-run variables
- **Pluggable parsing**: Swap out how model outputs are parsed (e.g., yes/no, contradiction)
- **Flexible filtering**: Run subsets (e.g., horn-only) without editing code
- **Concurrency + retries**: Faster runs with rate-limit aware backoff
- **Resumability**: Safe to stop/resume without redoing completed items
- **Standard JSONL outputs**: One schema across all experiments
- **Reproducibility**: Save config, template hash, and git SHA per run

### Directory Layout (new)
- `.gitignore` - ignore files for git (e.g., secrets.json, experiments/runs/)
- `_legacy/` — previous experiments kept as-is
- `experiments/`
  - `runner.py` — generic executor (config-driven)
  - `analyze_generic.py` — analysis over the standard JSONL schema
  - `plot_results.py` — generates PNG plots from run outputs
  - `parsers.py` — output parsers (e.g., `yes_no`, `contradiction`)
  - `filters.py` — input filters (e.g., `horn_only`, `skip`, `limit`)
  - `schema.py` — Pydantic models for input/output rows
  - `configs/` — YAML configs, one per experiment variant
  - `runs/` — run artifacts (results, config snapshot, metadata)
  - `plots/` — generated charts (PNG)
- `prompts/` — Jinja2 prompt templates used by configs
- `data/` — input JSONL problem sets (e.g., `problems_dist20_v1.js`)
- `utils/` — shared helpers (providers, clients)

Note: Some of these paths will be created as part of upcoming commits; the README documents the intended structure to enable a clean migration.

### Installation
1) Python 3.10+ recommended (repo currently uses a recent Python; 3.13 works).
2) Install deps:
```
python -m venv venv
source venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### Provider Credentials (unified `secrets.json`)
Providers are documented and listed alphabetically to avoid implying preference.
All provider credentials live in a single root file: `secrets.json`.

Minimal example (Anthropic + Google + OpenAI):
```
{
  "anthropic": {
    "api_key": "sk-ant-..."
  },
  "google": {
    "api_key": "sk-..."
  },
  "openai": {
    "api_key": "sk-..."
  }
}
```

Optional/extended keys per provider (only if needed by your account/deployment):
```
{
  "anthropic": { "api_key": "..." },
  "azure_openai": { "api_key": "...", "endpoint": "https://...", "deployment": "gpt-4o" },
  "google": { "api_key": "..." },
  "openai": { "api_key": "..." }
}
```

Environment variables may override the file at runtime (if set):
- `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `OPENAI_API_KEY`, etc.

Provider wiring is centralized under `utils/`; additional providers can be added without changing experiment configs.

### Input Data
Inputs are JSONL (one JSON array/object per line). Existing datasets (e.g., `problems_dist20_v1.js`) can be reused. Header lines can be skipped via config.

Generate a dataset with the legacy generator:
```
python experiments/generate_dataset.py --output data/problems_dist20_v1.js
```
This wraps `_legacy/makeproblems.py` and writes the output to `data/`.

### Config-Driven Runs
Each experiment is defined by a YAML file under `experiments/configs/`.

Single-target example (exp8-equivalent yes/no on horn clauses):
```yaml
name: exp8_yesno_horn
provider: openai
model: gpt-4o-2024-11-20
temperature: 0
seed: 1234
max_tokens: 2000

input_file: data/problems_dist20_v1.js
output_file: experiments/runs/${name}/results.jsonl

filters:
  horn_only: true
  skip_rows: 1     # skip header if present
  limit_rows: null # or a number for quick tests

prompt:
  template: prompts/if_then_yesno.j2
  variables: {}

parse:
  type: yes_no
  yes_tokens: ["yes"]
  no_tokens: ["no"]

concurrency:
  workers: 4
  rate_limit_per_min: 120
  retry:
    max_attempts: 3
    backoff_seconds: [2, 5, 10]

resume: true
save_prompt: true
save_response: true
```

Multi-target example (run the same experiment for multiple providers/models):
```yaml
name: horn_yesno_suite

# When `targets` is present, the runner fans out and runs each target concurrently
targets:
  - provider: openai
    model: gpt-4o-2024-11-20
    temperature: 0
    seed: 1234
    max_tokens: 2000
  - provider: anthropic
    model: claude-3-5-sonnet-latest
    temperature: 0
    seed: 1234
    max_tokens: 2000

input_file: data/problems_dist20_v1.js

# Either write one merged results file, or shard by provider/model using a pattern
output_file: experiments/runs/${name}/merged.results.jsonl
# Alternatively:
# output_pattern: experiments/runs/${name}/${provider}/${model}/results.jsonl

filters:
  horn_only: true
  skip_rows: 1

prompt:
  template: prompts/if_then_yesno.j2

parse:
  type: yes_no

concurrency:
  workers: 4              # per-target concurrency over items
  targets_workers: 2      # number of targets processed in parallel
  rate_limit_per_min: 120 # applied per provider target
  retry:
    max_attempts: 3
    backoff_seconds: [2, 5, 10]

resume: true
save_prompt: false
save_response: true
```

Prompt template example `prompts/exp8_if_then_yesno.j2`:
```jinja2
Your task is to solve a problem in propositional logic containing both facts and if-then rules.
You will get a list of facts and if-then rules and have to determine whether a fact p0 can be derived from this list.
If a fact p0 can be derived, the last word of your answer should be 'yes', otherwise the last word should be 'no'.

Statements:
{% for clause in clauses %}
{{ clause }}
{% endfor %}

Please answer whether a fact p0 can be derived from the following facts and rules.
```

### Running Experiments
Run the new generic runner with a config:
```
python experiments/runner.py --config experiments/configs/exp8_yesno_horn.yaml
```
Useful options (to be supported by the CLI):
- `--limit 50` — process only the first 50 items
- `--dry-run` — print prompts without calling the API
- `--resume` — continue an interrupted run
- `--only anthropic,openai` — restrict to a subset of providers in a multi-target config
- `--models anthropic:claude-3-5-sonnet-latest,openai:gpt-4o-2024-11-20` — restrict models per provider

Artifacts are stored under `experiments/runs/<name>/` and include:
- `results.jsonl` or per-target files via `output_pattern` — standard output rows

### Standard Output Schema
Each line in `results.jsonl` is a JSON object with at least:
```
{
  "id": <int|str>,
  "meta": { "maxvars": int, "maxlen": int, "horn": 0|1, "satflag": 0|1, "proof": [...] },
  "provider": "anthropic|google|openai|...",
  "prompt": "...",               # optional if save_prompt=true
  "completion_text": "...",      # optional if save_response=true
  "parsed_answer": 0|1|2,         # 2 = unclear
  "correct": true|false|null,     # null if no ground truth
  "timing_ms": <int>,
  "model": "...",
  "seed": <int>,
  "temperature": <number>,
  "error": "..." | null
}
```

### Analysis
Use the generic analyzer on any run file:
```
python experiments/analyze_generic.py experiments/runs/exp8_yesno_horn/results.jsonl
```
It reports accuracy grouped by `maxvars`/`maxlen`/`horn` and, when present, per-depth stats using `proof` data.

### Plotting
Generate accuracy plots per experiment and an overall grouped chart. Requires matplotlib (already in `requirements.txt`).
```
python -m experiments.plot_results
```
Outputs PNG files under `experiments/plots/` (e.g., `overall.png`, `exp8_yesno_horn.png`).
Provider series in plots are ordered alphabetically.

### Porting a Legacy Experiment
1) Identify the prompt style and parsing logic from `legacy/expX/`.
2) Create a template in `prompts/` capturing that style.
3) Add a YAML config under `experiments/configs/` that:
   - points to the dataset
   - references the template
   - selects the appropriate parser type and tokens
   - defines any filters (e.g., horn-only, skip/limit)
4) Run and compare a small subset vs. the legacy output to validate parity.

### Roadmap
- Enhance runner concurrency (async), keep retry/backoff and resumability
- Extend parsers/filters/schema and analyzer as needed
- Wire providers via `utils/provider_router.py` (Anthropic, Google, OpenAI; optional others)
- Optional: caching-by-hash to avoid duplicate API calls

### License
Apache 2.0. See `LICENSE`.


