# Experiments Configs: Representation vs Task

This folder holds experiment YAML configs for `experiments/runner.py` using the schema in `experiments/schema.py`.
The key mental model:

- Representation (a.k.a. encoding): how the logic problem is rendered in text for the model
  - `horn_if_then`: facts and single-head implications (Horn clauses)
  - `cnf_v1`: verbose CNF with natural-language “pN is true/false … or …”
  - `cnf_v2`: compact CNF with symbolic `pN` and `not(pN)` joined by `or`

- Task (a.k.a. label scheme): what we ask the model to answer and how we parse it
  - `yes_no`: does the knowledge entail the goal? (for Horn, “is p0 derivable?”)
    - parsed answers: `yes` → 0, `no` → 1, otherwise 2 (unclear)
  - `contradiction`: is the set contradictory (unsatisfiable) or not?
    - expected last token: `contradiction` → 0, `satisfiable`/`unknown` → 1, otherwise 2 (unclear)

Why keep multiple representations?
- Different encodings change how models reason (ablation). You can compare accuracy, calibration and robustness across:
  - Goal-directed Horn derivation (`horn_if_then` + `yes_no`)
  - CNF satisfiability framed verbosely (`cnf_v1`) or compactly (`cnf_v2`) with `contradiction` task
- Token efficiency vs readability: `cnf_v2` is compact; `cnf_v1` is more NL-like; Horn is goal-centric and often short-output.

Config fields (selected)
- `targets[]`: provider/model pairs (+ per-target `temperature`, `seed`, `max_tokens`, optional `thinking`)
  - Anthropic with thinking: `temperature=1` and `max_tokens > thinking.budget_tokens (>=1024)`
  - Google Gemini thinking: `thinking.budget_tokens` uses `-1` (dynamic), `0` (disable on Flash/Lite), or a positive range per family
  - OpenAI reasoning: `thinking.effort` in `{low, medium, high}`
- `input_file`: dataset path (JSONL-like JS arrays per line)
- `filters`: `horn_only`, `skip_rows`, `limit_rows`
- `outputs`: minimal `results.jsonl` and optional rich `*.provenance.jsonl`
- `prompt`: `template`, `representation` (in code: `style`), and optional `variables`
- `parse`: `task` (in code: `type`) with token lists for `yes_no`
- `concurrency`: `workers`, `lockstep`, `retry` policy
- `resume`: append and skip already processed ids

Recommended pairings
- `horn_if_then` + `yes_no` (derive p0?)
- `cnf_v1` or `cnf_v2` + `contradiction` (unsat vs satisfiable/unknown)

CLI tips
- Limit rows: `--limit 100`
- Dry run (no API calls): `--dry-run`
- Restrict providers: `--only anthropic,openai`
- Override models per provider: `--models google:gemini-2.5-pro,openai:gpt-5`
- Inject run id: `--run demo-123`

Files of interest
- `_template_unified.yaml`: comprehensive example with comments
- Other `exp*.yaml`: historical or specialized runs you can mirror.
