## Problem generation (`generate_problems`)

This doc describes the dataset generator used to create propositional logic problem sets consumed by the runner.

All commands below assume your working directory is the `_refactor/` project root (so the generator path is `scripts/generate_problems.py`). If you are running from the repo root, use `_refactor/scripts/generate_problems.py` instead.

For dataset naming, provenance, and storage policy (Git LFS), see [`docs/datasets.md`](datasets.md).

### Legacy parity mode (compatibility target)
- **Source of truth**: `_legacy/makeproblems.py` (while it exists)
- **Requirement**: the generator can reproduce legacy outputs **byte-for-byte** (given the same seed and parameters), so we can change internals safely while keeping downstream code usable.

### Modes (`scripts/generate_problems.py`)
- **`--mode legacy`**: legacy parity output (uses legacy SAT/UNSAT logic + legacy proof/model shape).
- **`--mode pysat_kissat`**: modern solving (SAT models via PySAT `g3`, UNSAT proofs via Kissat DRAT encoded as int lists).

### Parameter defaults (and why)
The generator is parameterized by:
- number of variables (`--vars`, i.e. \(n\))
- max clause length (`--clens`, i.e. \(k\))
- Horn vs non-Horn (`--horn`)
- problems per case (`--percase`)
- clause/variable ratio (`goodratios`, `--ratio-*`)

These defaults come from `_legacy/makeproblems.py` (unless overridden by CLI flags):

- **Variables (`--vars`)**:
  - Legacy default is `3–15`.
  - We start at **3** because `n=1–2` tends to produce **toy / repetitive / degenerate** CNFs (and the legacy generator also enforces structural constraints like “at least one fully-positive and one fully-negative clause”). `n>=3` is still “small”, but not trivial.
  - CLI parsing accepts **ranges**, **lists**, and **mixed** specs (e.g. `3-50`, `3,4,7`, `3-5,7`).

- **Clause lengths (`--clens`)**:
  - Legacy default is **`[3, 4]`**.
  - Practical rationale:
    - `k=2` (2-SAT) is polynomial-time solvable and often too “easy” for the intended use.
    - `k=3` and `k=4` are standard NP-complete families and are easier to tune for balanced SAT/UNSAT generation.
    - `k=5` is supported, but at larger `n` it can become much harder to keep SAT/UNSAT balanced and (especially) to generate UNSAT proofs quickly.
  - Current tooling assumes `k` in `{2,3,4,5}` because the `goodratios` table is defined for those values.
  - If you pass an unsupported clause length (e.g. `--clens 6`), the generator exits with a clear error.

- **Horn vs non-Horn (`--horn`)**:
  - `only` generates Horn-only problems (typically much faster to solve/prove).
  - `no` generates general non-Horn CNFs (harder; proof generation dominates runtime).
  - `mixed` generates both; if one case is slow (often non-Horn at large `n`), the whole run can appear to “hang” while balancing that case.

- **Problems per case (`--percase`)**:
  - Must be **even**.
  - The generator tries to output a roughly **balanced** set (≈ half SAT / half UNSAT) for each \((n,k,horn)\) case. If one side is rare under the chosen ratio, generation can take a long time.

### Output paths
You can either provide an explicit output path, or let the generator write into the repo’s `datasets/` tree.

- **Explicit path**: `--output <path>` writes exactly to that path.
- **Repo-relative output (recommended)**: omit `--output` and use:
  - `--dataset {legacy,validation,production}` (defaults to `legacy` for `--mode legacy`, else `validation`)
  - `--name <filename>` (optional; `.jsonl` is added if missing; otherwise a name is generated from params)

Example:
```
python scripts/generate_problems.py --mode pysat_kissat --seed 12345 --dataset validation --name smoke
```
This writes: `datasets/validation/smoke.jsonl`.

### Example: full validation dataset (vars 3–50, clause length 3–5)
```
python scripts/generate_problems.py \
  --mode pysat_kissat \
  --seed 12345 \
  --vars 3-50 \
  --clens 3-5 \
  --horn mixed \
  --percase 50 \
  --dataset validation \
  --name full_vars3-50_len3-5_hornmixed_per50_seed12345 \
  --max-attempts 200000 \
  --progress-every 2000 \
  --print-sha256
```

- **Output path**: `datasets/validation/full_vars3-50_len3-5_hornmixed_per50_seed12345.jsonl`
- **Expected rows**: \(48 \times 3 \times 2 \times 50 = 14400\) (not counting the header line)
- **Tip**: record the printed SHA-256 checksum to make runs reproducible and comparable.

### Runtime controls: monitoring + avoiding “hangs”
These flags do **not** change the dataset meaning; they affect generation UX and failure behavior.

- **`--progress-every N`**:
  - Prints periodic progress lines to **stderr**.
  - During full dataset generation (balancing), it prints every **N attempts** inside each \((n,k,horn)\) case, e.g.:
    - `# progress attempts=... sat_seen=... unsat_seen=... sat_kept=... unsat_kept=... elapsed_s=...`
  - During **probe mode** (`--probe-samples`), it prints every **N probe samples** per case:
    - `# probe_progress case_var=... case_len=... horn=... i=... sat=... unsat=... unk=... elapsed_s=...`
  - If `N` is large (or a case finishes quickly), you may see **no progress output** even though generation is working. You’ll still see the final checksum if you pass `--print-sha256`.

- **`--max-attempts N`**:
  - Safety valve for balancing: aborts if a single \((n,k,horn)\) case can’t reach the requested balanced count within **N attempts**.
  - Default is `0` (disabled / no limit).
  - Useful when the chosen clause/variable ratio makes one side (SAT or UNSAT) too rare, or when UNSAT proof generation frequently times out.

### Output format (contract)
The generator emits rows that are **JSON-compatible** (numbers + lists only), so they can be parsed as JSONL:
- **Line 1**: header row (JSON array of column names)
- **Line N (N>1)**: each row is a JSON array with the legacy schema:
  - `id`: integer
  - `maxvarnr`: integer
  - `maxlen`: integer
  - `mustbehorn`: 0/1
  - `issatisfiable`: 0/1
  - `problem`: list of clauses (each clause is a list of ints)
  - `proof_of_inconsistency_or_satisfying_valuation`:
    - if SAT: a satisfying valuation (list of ints)
    - if UNSAT:
      - in `--mode legacy`: legacy resolution proof (nested int lists)
      - in `--mode pysat_kissat`: Kissat DRAT proof encoded as lists of ints (see below)
  - `units_derived_by_horn_clauses`: list of derived units (Horn-only forward chaining)

Important: to stay JSON-compatible for downstream tooling, proofs/models must remain **numbers + lists** (avoid raw solver text lines).

### Solver choices (what we choose and why)
- **SAT models**: PySAT with solver **`g3`** (fast, widely available in `python-sat` builds).
- **UNSAT proofs**:
  - We validated external proof logging via **Kissat**.
  - Proofs are emitted as DRAT, but encoded as **numbers + lists** (not raw text) so the dataset stays JSON-compatible.

### Clause/variable ratio (`goodratios`)
The legacy generator chooses the number of clauses as \(m = \lfloor n \cdot r \rfloor\), where:
- \(n\) is the number of variables (`--vars`)
- \(r\) is a heuristic clause/variable ratio (from a small hand-tuned table in the legacy script)

This ratio strongly controls **how often instances are SAT vs UNSAT**. If \(r\) is too low for a given \(k\) (clause length), almost everything is SAT; if \(r\) is too high, almost everything is UNSAT. Since the generator tries to produce **both** SAT and UNSAT examples per case, a badly chosen ratio can make generation appear to “hang” while it keeps sampling.

For large `--vars` (e.g. 100) and `--clens 5-5` in **non-Horn** mode, the legacy fallback ratios are often too SAT-heavy. Use one of:
- explicitly set `--ratio-nonhorn` (and/or `--ratio-horn`) to tune the SAT/UNSAT balance

By default (when you do **not** pass `--ratio-nonhorn`), this generator uses the legacy `goodratios` table *where it is defined* (small `n`), but for **larger `n` beyond the legacy table** it ramps the non-Horn ratio upward (instead of staying flat). This avoids the “all SAT at large `n`” behavior and makes balanced generation feasible for ranges like `--vars 3-50 --clens 3-5`.

There is also one important Horn corner case: with the legacy Horn ratio for `k=5`, very small `n` (notably `n=3`) becomes “always UNSAT” in practice. To keep balanced generation feasible when you include `--clens 5`, the generator ramps the Horn `k=5` ratio from `~2.0` at small `n` up to the legacy `4.6` by `n≈50` (unless you override via `--ratio-horn`).

As a rough starting point for **non-Horn random k-SAT**, the phase transition ratios (m/n) are often quoted around:
- `k=3`: ~4.3
- `k=4`: ~9.9
- `k=5`: ~21.1

However, the “right” ratio depends on `n` and on the legacy generator’s additional constraints, so you should **probe first** and then set `--ratio-nonhorn`/`--ratio-horn` explicitly.

### Probing SAT/UNSAT balance (recommended for large `--vars`)
To validate whether a ratio is producing a reasonable SAT/UNSAT mix **before** generating proofs, use probe mode:

```
python scripts/generate_problems.py --probe-samples 30 --vars 100-100 --clens 5-5 --horn no --ratio-nonhorn 21.0
```

This prints `sat=... unsat=...` plus average generation/solve times, and exits.

You can also write the sampled CNFs + labels for analysis:

```
python scripts/generate_problems.py --probe-samples 30 --probe-output /tmp/probe_vars100_len5.jsonl --vars 100-100 --clens 5-5 --horn no --ratio-nonhorn 21.0
```

### UNSAT proof encoding (Kissat DRAT)
Kissat writes DRAT lines like:
- add clause: `-3 0`
- delete clause: `d -3 -2 0`
- empty clause: `0`

We encode each line as a list of ints:
- additions: `[ 1, lit1, lit2, ... ]`
- deletions: `[ -1, lit1, lit2, ... ]`
- empty clause: `[ 1 ]` (addition) or `[ -1 ]` (deletion; rare)

### Determinism and seeds
- The legacy script `_legacy/makeproblems.py` is not inherently deterministic when run directly (it does not expose a seed flag).
- For deterministic runs we standardize on the wrapper CLI flag **`--seed`** (default `12345`).

### Parity check (recommended)
Keep a “golden parity mode” and verify it:
- Generate a file in **`--mode legacy`**
- Compare checksums (or `diff`) against a known-good baseline

### Checksum harness (recommended)
Use `--print-sha256` / `--expect-sha256` to turn parity into a mechanical check.

Small fixture (fast, stable):
```
python scripts/generate_problems.py --mode legacy --seed 12345 --vars 3-3 --clens 3-3 --horn mixed --percase 4 \
  --output /tmp/llmlog_legacy_fixture.jsonl \
  --print-sha256 \
  --expect-sha256 9d64eabd9bc546599a47ba90cecf76dd85a49b5b0d2e2db2f37f9cc98af21a9c
```

### Next steps (planned)
- Keep `_legacy/makeproblems.py` as the generation engine while we stabilize the wrapper.
- Introduce a minimal CLI (e.g., `--seed`, `--vars`, `--clens`, `--percase`, `--horn`) while preserving defaults.
- Remove dead options only after parity is protected by a stable test/harness.

### External dependencies (solving/proofs)
- **PySAT (python-sat)**: we use PySAT’s `formula` + `solvers` APIs to solve CNFs and extract SAT models.
  - Docs: [PySAT API documentation](https://pysathq.github.io/docs/html/#api-documentation)
  - Source: [pysathq/pysat (GitHub)](https://github.com/pysathq/pysat)
- **Kissat**: external SAT solver used to emit UNSAT proofs (DRAT) when `issatisfiable=0`.
  - Source: [arminbiere/kissat (GitHub)](https://github.com/arminbiere/kissat)

### Background reading (resolution + proof search)
These are useful context for why the internal “legacy parity” proof format looks the way it does, and for future improvements (indexing/subsumption/selection strategies):
- **Subsumption and performance**: T. Tammet, *Towards Efficient Subsumption* ([PDF](https://www.cs.cmu.edu/~fp/courses/atp/cmuonly/T98.pdf))
- **Given-clause / ANL loop** (resolution prover control loop): *The ANL Loop* ([article](https://cs.miami.edu/home/geoff/Courses/CSC749-24F/Content/ANLLoop.shtml))
