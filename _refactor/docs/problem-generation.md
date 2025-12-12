## Problem generation (`generate_problems`)

This doc describes the dataset generator used to create propositional logic problem sets consumed by the runner.

### Legacy parity mode (compatibility target)
- **Source of truth**: `_legacy/makeproblems.py` (while it exists)
- **Requirement**: the generator can reproduce legacy outputs **byte-for-byte** (given the same seed and parameters), so we can change internals safely while keeping downstream code usable.

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
    - if UNSAT: a Kissat DRAT proof encoded as lists of ints (see below)
  - `units_derived_by_horn_clauses`: list of derived units (Horn-only forward chaining)

Important: to stay JSON-compatible for downstream tooling, proofs/models must remain **numbers + lists** (avoid raw solver text lines).

### Solver choices (what we choose and why)
- **SAT models**: PySAT with solver **`g3`** (fast, widely available in `python-sat` builds).
- **UNSAT proofs**:
  - We validated external proof logging via **Kissat**.
  - Proofs are emitted as DRAT, but encoded as **numbers + lists** (not raw text) so the dataset stays JSON-compatible.

### UNSAT proof encoding (Kissat DRAT)
Kissat writes DRAT lines like:
- add clause: `-3 0`
- delete clause: `d -3 -2 0`
- empty clause: `0`

We encode each line as a list of ints:
- additions: `[ 1, lit1, lit2, ... ]`
- deletions: `[ -1, lit1, lit2, ... ]`
- empty clause: `[ 1 ]`

### Determinism and seeds
- The legacy script `_legacy/makeproblems.py` is not inherently deterministic when run directly (it does not read a seed).
- For deterministic runs we standardize on **`PROBLEM_SEED`** (default `12345`) and run generators through a seeded entrypoint so parity can be verified mechanically (hash comparisons).

### Parity check (recommended)
Keep a “golden parity mode” and verify it:
- Generate legacy baseline
- Generate new output
- Compare checksums (`shasum`) or `diff`

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
