## Working experiment plan: sweep → detect drop → drill down

This is a **working** plan for running experiments iteratively:
- start with a coarse sweep over difficulty axes
- identify where performance drops
- zoom in to bracket the boundary
- repeat across prompt/config variants

The goal is to gather enough data to answer: **where does the model stop being reliable, and why?**

---

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

Aggregate + dashboard:
```
python3 scripts/aggregate_results.py --run-id horn_ex_only_len5_vars10_50_case10 \
  --output reports/horn_ex_only_len5_vars10_50_case10.aggregated.json
python3 scripts/generate_dashboard.py \
  --input reports/horn_ex_only_len5_vars10_50_case10.aggregated.json \
  --output reports/horn_ex_only_len5_vars10_50_case10.dashboard.html
```

Where the reasoning trace is stored:
- For each leaf run:
  - `runs/<suite>/<run>/<provider>/<model>/<thinking_mode>/results.provenance.jsonl`
  - the full text is in `completion_text` (plus `raw_response` and best-effort `thinking_text` if present)

Export a handful of provenance rows to readable files:
```
python3 scripts/export_provenance.py \
  --provenance runs/<suite>/<run>/<provider>/<model>/<thinking_mode>/results.provenance.jsonl \
  --out reports/exports --limit 50 --no-raw
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
Once the horn-only examples-only baseline is understood, repeat the same sweep/drill loop for:
- **hornonly + algorithmic prompts** (linear vs “from”)
- **nonhornonly** (examples-only, DPLL linear, DPLL “from”)
- **representation**: compact CNF vs natural-language CNF

The same drilldown CLI flags apply across all suites:
- `--maxvars ...`
- `--maxlen ...`
- `--case-limit ...`
- `--resume`


