## Working experiment plan: sweep → detect drop → drill down

This is a **working** plan for running experiments iteratively:
- start with a coarse sweep over difficulty axes
- identify where performance drops
- zoom in to bracket the boundary
- repeat across prompt/config variants

The goal is to gather enough data to answer: **where does the model stop being reliable, and why?**

---

### Quick context (for a fresh agent)
This repository contains multiple experiment frameworks. **All work in this plan is for `_refactor/`**.

Key paths under `_refactor/`:
- **Suites** (what to run): `configs/suites/*.yaml`
- **Targets** (which provider/model): `configs/targets/*.yaml`
- **Datasets**: `datasets/validation/*.jsonl`
- **Runner CLI**: `scripts/run.py` (calls `src/llmlog/runner.py`)
- **Artifacts (gitignored)**: `runs/<suite>/<run>/<provider>/<model>/<thinking_mode>/...`
- **Reports (gitignored)**: `reports/` (dashboards, exports)

Per target run folder you should expect:
- `results.jsonl`: minimal rows (`parsed_answer`, `correct`, `error`)
- `results.provenance.jsonl`: prompt + full completion + usage + raw response (when enabled)
- `results.summary.json`: per-target stats (accuracy, counts, token totals)
- `run.manifest.json`: reproducibility snapshot (suite, dataset selection, target)

Note: `_refactor/.gitignore` intentionally ignores `runs/` and `reports/`.
For third-party validation, export provenance into a standalone folder (see below) or archive the run folder.

### What counts as “done” (for a run id)
For a given `--suite` + `--run` + dataset selection:
- Every selected problem id has a row in `results.jsonl`
- Most rows are parseable (`parsed_answer` is 0/1, not 2)
- Transient API failures were rerun until acceptable coverage is reached
- Aggregation/dashboard exists, and provenance can be exported for spot checks

### Goals + hypothesis
- **Hypothesis**: performance is strong for small instances, then drops after some threshold in:
  - **variable count** (`maxvarnr`)
  - **clause length** (`maxlen`)
  - **prompting policy** (examples-only vs algorithmic; compact vs NL; hornonly vs nonhornonly)
- **Goal**: find the boundary region (e.g., “drop begins around vars ≈ 37 for maxlen=5”) and collect trace/provenance for failures.

---

### Why start with `hornonly` + examples-only
- **Horn-only is “structured”**: Horn CNF has a linear-time forward-chaining algorithm, so it’s a good sanity baseline.
- **Examples-only is the simplest prompt**: gives a clean baseline without forcing a method. If the model fails even here, that’s important.
- This first run also validates the plumbing: outputs, resume behavior, provenance, parsing, analysis dashboard.

---

### Fixed choices (for now)
- **Runner**: `_refactor/scripts/run.py`
- **Dataset**: `_refactor/datasets/validation/full_vars3-50_len3-5_hornmixed_per50_seed12345.jsonl`
- **Target**: `openai/gpt-5.2-pro` with `thinking.enabled=true`, `effort=high`
- **Suite (hornonly + examples-only)**:
  - `configs/suites/sat__repr-cnf_compact__subset-hornonly__prompt-examples_only__openai_gpt-5.2-pro__think-high.yaml`

---

### Execution checklist (agent-friendly)
- [ ] **Environment**: from repo root, `cd _refactor`; ensure API keys are set (`OPENAI_API_KEY` etc).
- [ ] **Preflight**: run `--preflight --estimate-cost` for the intended sweep filters.
- [ ] **Coarse sweep**: run vars 10/20/30/40/50 for each maxlen (3,4,5), with `--case-limit 10 --resume`.
- [ ] **Sanity**: ensure results exist under `runs/<suite>/<run>/...` and are parseable (few/no `parsed_answer==2`).
- [ ] **Rerun failures**:
  - `--rerun-errors` to retry rows with an error
  - `--rerun-unclear` to retry rows that parsed as unclear
- [ ] **Aggregate + dashboard**: create `reports/<run>.aggregated.json` + `<run>.dashboard.html` for review.
- [ ] **Drill down**: bracket the drop region with narrower `--maxvars` ranges (and/or fixed vars with varying `--maxlen`).
- [ ] **Export provenance**: export representative successes + failures to human-readable files for validation.
- [ ] **Repeat**: run the same sweep/drill loop across the other suite variants (see “Planned suite matrix”).

### Important concept: what is a “case”?
In the full dataset, rows are naturally grouped into “cases” by:
- **case key** = (`maxvarnr`, `maxlen`, `mustbehorn`)

For this dataset, each case has `percase=50` rows, balanced SAT/UNSAT.
- For a fixed `(maxvarnr, maxlen, mustbehorn)` you typically have **50 rows** ≈ **25 SAT + 25 UNSAT**.

We use `--case-limit N` to sample only the first N rows from each case.
- Use an **even** N (e.g. 10) to preserve SAT/UNSAT balance as much as possible.

---

### First pass (coarse sweep)

#### Strategy
- Sweep `maxvarnr` at: **10, 20, 30, 40, 50**
- Keep `maxlen` fixed per run: **3**, then **4**, then **5**
- Sample cheaply: `--case-limit 10`
- Use `--resume` so the run can be extended later without repeating completed ids.

#### Commands (copy/paste)

From repo root:
```
cd _refactor
SUITE="configs/suites/sat__repr-cnf_compact__subset-hornonly__prompt-examples_only__openai_gpt-5.2-pro__think-high.yaml"
```

Optional preflight cost estimate:
```
python3 scripts/run.py --suite "$SUITE" --preflight --estimate-cost \
  --maxvars 10,20,30,40,50 --maxlen 3 --case-limit 10
```

Run (repeat for maxlen=3,4,5 by changing `--maxlen` and `--run`):
```
python3 scripts/run.py --suite "$SUITE" --run horn_ex_only_len3_vars10_50_case10 \
  --maxvars 10,20,30,40,50 --maxlen 3 --case-limit 10 \
  --resume --lockstep
```

```
python3 scripts/run.py --suite "$SUITE" --run horn_ex_only_len4_vars10_50_case10 \
  --maxvars 10,20,30,40,50 --maxlen 4 --case-limit 10 \
  --resume --lockstep
```

```
python3 scripts/run.py --suite "$SUITE" --run horn_ex_only_len5_vars10_50_case10 \
  --maxvars 10,20,30,40,50 --maxlen 5 --case-limit 10 \
  --resume --lockstep
```

---

### Extending a run later (run the “extra 15”)
To go from 10 rows per case → 25 rows per case **without rerunning** the first 10:
- keep the **same** `--run` id
- keep `--resume`
- increase `--case-limit`

Example (extend the len=3 sweep from 10 → 25 rows/case):
```
python3 scripts/run.py --suite "$SUITE" --run horn_ex_only_len3_vars10_50_case10 \
  --maxvars 10,20,30,40,50 --maxlen 3 --case-limit 25 \
  --resume --lockstep
```

---

### Handling errors, reruns, and “completing” a run
The runner writes a row per problem id to `results.jsonl` with:
- `parsed_answer`: `0|1|2` (`2` means unclear)
- `error`: string or `null` (API/network/config errors show up here)

The run is intended to be **append-only** and **resumable**:
- Re-running the exact same command with `--resume` will skip ids that already have a “good enough” latest row.
- If you increase `--case-limit`, `--resume` will keep prior ids and only run the additional ids.

#### TODO (required): post-run “gap fill” for failed/unclear ids
In practice, API/network flakiness means many runs need **one or more extra passes** after the first sweep.
Treat this as part of “done”:
- [ ] **Run gap-fill passes** until there are **no remaining errors/unclear** in the *latest-per-id* view:
  - `--rerun-errors` (fills transient API failures)
  - `--rerun-unclear` (fills parse failures / ambiguous answers)
- [ ] **If only a few ids are failing**, rerun *just those ids* with `--ids ...` (keeps costs down and makes progress visible).
- [ ] **Only after gap-fill**, aggregate + dashboard (otherwise the dashboard reflects partial coverage).

Important note: `results.jsonl` is **append-only** — old error rows remain in the file even after an id later succeeds.
When deciding what to rerun (and when deciding if a run is “complete”), always reason about the **latest row per id**.

Helper: list remaining ids to rerun (latest-per-id) from a leaf `results.jsonl`:
```
python3 - <<'PY'
import json
from pathlib import Path

path = Path("runs/<suite>/<run>/<provider>/<model>/<thinking_mode>/results.jsonl")
latest = {}
for line in path.read_text().splitlines():
    if not line.strip():
        continue
    row = json.loads(line)
    latest[str(row.get("id"))] = row

error_ids = sorted(int(k) for k,v in latest.items() if v.get("error"))
unclear_ids = sorted(int(k) for k,v in latest.items() if (v.get("parsed_answer") == 2 and not v.get("error")))

print("error_ids:", error_ids)
print("unclear_ids:", unclear_ids)
PY
```

#### Rerun transient failures
If some rows have `error!=null` (rate limits, timeouts, 5xx), rerun just those:
```
python3 scripts/run.py --suite "$SUITE" --run horn_ex_only_len5_vars10_50_case10 \
  --maxvars 10,20,30,40,50 --maxlen 5 --case-limit 10 \
  --resume --lockstep --rerun-errors
```

#### Rerun unclear parses
If some rows have `parsed_answer==2`, rerun them (same selection filters):
```
python3 scripts/run.py --suite "$SUITE" --run horn_ex_only_len5_vars10_50_case10 \
  --maxvars 10,20,30,40,50 --maxlen 5 --case-limit 10 \
  --resume --lockstep --rerun-unclear
```

#### Rerun a specific set of ids
When drilling into particular interesting failures, rerun by id:
```
python3 scripts/run.py --suite "$SUITE" --run horn_ex_only_len5_vars10_50_case10 \
  --ids 123,456,789 --resume --lockstep --rerun-errors --rerun-unclear
```

#### Common error causes (and fixes)
- **HTTP 429 / rate limit**: rerun with `--rerun-errors`; if it persists, reduce `--case-limit` or run fewer suites in parallel.
- **Missing API key**: set `OPENAI_API_KEY` (or add `_refactor/secrets.json`, which is gitignored).
- **Token limits**: ensure targets have enough `max_tokens` (gpt-5.2-pro target uses 30000 by default).
- **Model id mismatch**: update the target model id in `configs/targets/*.yaml`.

### Drilldown plan (zooming in on the drop)

#### Vars drilldown
Suppose the first pass suggests the drop happens between vars=30 and vars=40 (for maxlen=5).
We “bracket” it:
- Run midpoints like 35, then 37/38, then 36/39, etc.

Example:
```
python3 scripts/run.py --suite "$SUITE" --run horn_ex_only_len5_drill_vars35_45_case10 \
  --maxvars 35-45 --maxlen 5 --case-limit 10 \
  --resume --lockstep
```

If you want to isolate one value (e.g., 37):
```
python3 scripts/run.py --suite "$SUITE" --run horn_ex_only_len5_vars37_case25 \
  --maxvars 37 --maxlen 5 --case-limit 25 \
  --resume --lockstep
```

#### Clause-length drilldown
Once you know the rough vars boundary, keep vars fixed and sweep maxlen (or vice versa).
Example (fix vars=40 and compare lengths 3/4/5 cheaply):
```
python3 scripts/run.py --suite "$SUITE" --run horn_ex_only_vars40_len3_5_case10 \
  --maxvars 40 --maxlen 3,4,5 --case-limit 10 \
  --resume --lockstep
```

---

### Analysis loop (after each pass)

Before aggregating, it’s usually worth ensuring you don’t have many `error` / `unclear` rows:
- rerun errors: `--rerun-errors`
- rerun unclear parses: `--rerun-unclear`

Aggregate + dashboard (overview):
```
python3 scripts/aggregate_results.py --run-id horn_ex_only_len5_vars10_50_case10 \
  --output reports/horn_ex_only_len5_vars10_50_case10.aggregated.json
python3 scripts/generate_dashboard.py \
  --input reports/horn_ex_only_len5_vars10_50_case10.aggregated.json \
  --output reports/horn_ex_only_len5_vars10_50_case10.dashboard.html
```

---

### Run management utilities (optional but recommended)
If you’re juggling many parallel runs, these helpers can keep everything consistent and easy to browse:

- `scripts/manage_runs.py active`: list active `scripts/run.py` processes
- `scripts/manage_runs.py stop --yes`: stop active runs (SIGINT → SIGTERM → SIGKILL)
- `scripts/manage_runs.py index`: create a **non-destructive** by-run view under `runs_by_run_view/<run_id>/<suite_name>` (symlinks)
- `scripts/manage_runs.py migrate --yes`: **move** `runs/<suite>/<run_id>` into `runs_by_run/<run_id>/<suite>` and leave a symlink behind so legacy paths keep working
- `scripts/manage_runs.py queue ... --max-parallel 3`: run a list of suite×len jobs with a global concurrency cap until each is complete

Where the reasoning trace is stored:
- For each leaf run:
  - `runs/<suite>/<run>/<provider>/<model>/<thinking_mode>/results.provenance.jsonl`
  - the full text is in `completion_text` (plus `raw_response` and best-effort `thinking_text` if present)

Export a handful of provenance rows to readable files (good for third-party validation):
```
python3 scripts/export_provenance.py \
  --provenance runs/<suite>/<run>/<provider>/<model>/<thinking_mode>/results.provenance.jsonl \
  --out reports/exports/<run_name> --limit 50 --no-raw
```

Export specific ids (repeat `--id`):
```
python3 scripts/export_provenance.py \
  --provenance runs/<suite>/<run>/<provider>/<model>/<thinking_mode>/results.provenance.jsonl \
  --out reports/exports/<run_name> --id 123 --id 456 --no-raw
```

Archive an export folder for sharing:
```
tar -czf reports/exports_<run_name>.tar.gz -C reports "exports/<run_name>"
```

---

### Run-id naming conventions (recommended)
Use run ids that encode:
- suite family (horn/nonhorn + prompt type)
- len vs vars sweep (or drill)
- sample size (case-limit)

Examples:
- `horn_ex_only_len3_vars10_50_case10`
- `horn_ex_only_len5_drill_vars35_45_case10`
- `horn_ex_only_len5_vars37_case25`

Rule of thumb:
- **Use the same `--run` id only when you intend to extend the same dataset selection** (e.g., increasing `--case-limit`).
- Use a **new `--run` id** when the filter region is different (e.g., switching maxlen or changing the var range for drilldown).

---

### After the horn-only baseline
Once the horn-only examples-only baseline is understood, repeat the same sweep/drill loop across the **full suite matrix**:
- **subset**: `hornonly` vs `nonhornonly`
- **representation**: `cnf_compact` vs `cnf_nl`
- **prompt policy**:
  - `examples_only` (baseline)
  - `horn_alg_linear` / `horn_alg_from` (hornonly; “from” is trace-rich)
  - `dpll_alg_linear` / `dpll_alg_from` (nonhornonly; “from” is trace-rich)

#### Suite paths (copy/paste)
```
HORN_COMPACT_EX="configs/suites/sat__repr-cnf_compact__subset-hornonly__prompt-examples_only__openai_gpt-5.2-pro__think-high.yaml"
HORN_COMPACT_HORN_LINEAR="configs/suites/sat__repr-cnf_compact__subset-hornonly__prompt-horn_alg_linear__openai_gpt-5.2-pro__think-high.yaml"
HORN_COMPACT_HORN_FROM="configs/suites/sat__repr-cnf_compact__subset-hornonly__prompt-horn_alg_from__openai_gpt-5.2-pro__think-high.yaml"

HORN_NL_EX="configs/suites/sat__repr-cnf_nl__subset-hornonly__prompt-examples_only__openai_gpt-5.2-pro__think-high.yaml"
HORN_NL_HORN_LINEAR="configs/suites/sat__repr-cnf_nl__subset-hornonly__prompt-horn_alg_linear__openai_gpt-5.2-pro__think-high.yaml"
HORN_NL_HORN_FROM="configs/suites/sat__repr-cnf_nl__subset-hornonly__prompt-horn_alg_from__openai_gpt-5.2-pro__think-high.yaml"

NONHORN_COMPACT_EX="configs/suites/sat__repr-cnf_compact__subset-nonhornonly__prompt-examples_only__openai_gpt-5.2-pro__think-high.yaml"
NONHORN_COMPACT_DPLL_LINEAR="configs/suites/sat__repr-cnf_compact__subset-nonhornonly__prompt-dpll_alg_linear__openai_gpt-5.2-pro__think-high.yaml"
NONHORN_COMPACT_DPLL_FROM="configs/suites/sat__repr-cnf_compact__subset-nonhornonly__prompt-dpll_alg_from__openai_gpt-5.2-pro__think-high.yaml"

NONHORN_NL_EX="configs/suites/sat__repr-cnf_nl__subset-nonhornonly__prompt-examples_only__openai_gpt-5.2-pro__think-high.yaml"
NONHORN_NL_DPLL_LINEAR="configs/suites/sat__repr-cnf_nl__subset-nonhornonly__prompt-dpll_alg_linear__openai_gpt-5.2-pro__think-high.yaml"
NONHORN_NL_DPLL_FROM="configs/suites/sat__repr-cnf_nl__subset-nonhornonly__prompt-dpll_alg_from__openai_gpt-5.2-pro__think-high.yaml"
```

#### Coarse sweep command template
All suites support the same drilldown flags:
- `--maxvars ...` (e.g. `10,20,30,40,50`)
- `--maxlen ...` (e.g. `3`, then `4`, then `5`)
- `--case-limit ...`
- `--resume`
- `--rerun-errors` / `--rerun-unclear` (when filling gaps)

#### Parallel execution (recommended for faster iteration)
The full matrix is large and long-running. To get useful signal quickly:
- Run **2 suites in parallel** (or 3 if you have plenty of quota and low error rate).
- Keep `--lockstep` enabled (fair comparisons across targets) but avoid running *too many* jobs concurrently (rate limits and transient API failures get worse).
- For `*_from_*` suites (trace-rich), use a **smaller `--case-limit`** (e.g. 4 or 6) on the first pass.

Two practical patterns:

**A) Multiple terminals (simplest):**
- Start one suite+len sweep per terminal.
- Re-run with `--resume --rerun-errors` until coverage is good.

**B) Single terminal, run 2 suites concurrently (copy/paste):**
```
cd _refactor

VAR_STEPS="10,20,30,40,50"
CASE_LIMIT_LINEAR=10
CASE_LIMIT_FROM=4

run_suite() {
  local SUITE="$1"
  local PREFIX="$2"
  local CASE_LIMIT="$3"
  for LEN in 3 4 5; do
    RUN="${PREFIX}_len${LEN}_vars10_50_case${CASE_LIMIT}"
    python3 scripts/run.py --suite "$SUITE" --run "$RUN" \
      --maxvars "$VAR_STEPS" --maxlen "$LEN" --case-limit "$CASE_LIMIT" \
      --resume --lockstep
  done
}

# Example starter set (fast signal): horn_alg_linear + dpll_alg_linear, compact + nl
run_suite "$HORN_COMPACT_HORN_LINEAR" horn_alg_linear_cnf_compact "$CASE_LIMIT_LINEAR" &
run_suite "$NONHORN_COMPACT_DPLL_LINEAR" nonhorn_dpll_linear_cnf_compact "$CASE_LIMIT_LINEAR" &
wait

run_suite "$HORN_NL_HORN_LINEAR" horn_alg_linear_cnf_nl "$CASE_LIMIT_LINEAR" &
run_suite "$NONHORN_NL_DPLL_LINEAR" nonhorn_dpll_linear_cnf_nl "$CASE_LIMIT_LINEAR" &
wait

# Optional trace-rich runs (start smaller; these can be slow/expensive)
run_suite "$HORN_COMPACT_HORN_FROM" horn_alg_from_cnf_compact "$CASE_LIMIT_FROM" &
run_suite "$NONHORN_COMPACT_DPLL_FROM" nonhorn_dpll_from_cnf_compact "$CASE_LIMIT_FROM" &
wait
```

Run the full matrix (edit the list to only include what you want):
```
cd _refactor

VAR_STEPS="10,20,30,40,50"
CASE_LIMIT=10

declare -A SUITES=(
  [horn_ex_only_cnf_compact]="$HORN_COMPACT_EX"
  [horn_alg_linear_cnf_compact]="$HORN_COMPACT_HORN_LINEAR"
  [horn_alg_from_cnf_compact]="$HORN_COMPACT_HORN_FROM"
  [horn_ex_only_cnf_nl]="$HORN_NL_EX"
  [horn_alg_linear_cnf_nl]="$HORN_NL_HORN_LINEAR"
  [horn_alg_from_cnf_nl]="$HORN_NL_HORN_FROM"
  [nonhorn_ex_only_cnf_compact]="$NONHORN_COMPACT_EX"
  [nonhorn_dpll_linear_cnf_compact]="$NONHORN_COMPACT_DPLL_LINEAR"
  [nonhorn_dpll_from_cnf_compact]="$NONHORN_COMPACT_DPLL_FROM"
  [nonhorn_ex_only_cnf_nl]="$NONHORN_NL_EX"
  [nonhorn_dpll_linear_cnf_nl]="$NONHORN_NL_DPLL_LINEAR"
  [nonhorn_dpll_from_cnf_nl]="$NONHORN_NL_DPLL_FROM"
)

for PREFIX in "${!SUITES[@]}"; do
  SUITE="${SUITES[$PREFIX]}"
  for LEN in 3 4 5; do
    RUN="${PREFIX}_len${LEN}_vars10_50_case${CASE_LIMIT}"
    python3 scripts/run.py --suite "$SUITE" --run "$RUN" \
      --maxvars "$VAR_STEPS" --maxlen "$LEN" --case-limit "$CASE_LIMIT" \
      --resume --lockstep
  done
done
```

Practical note: the `*_from_*` suites encourage much longer traces. Consider using a smaller `--case-limit`
for the first pass (e.g. 4 or 6), then increase later where needed.


