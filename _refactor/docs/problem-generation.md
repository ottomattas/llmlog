## Problem generation (`makeproblems`)

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
    - if UNSAT: a legacy-style resolution proof (list of derived clauses)
  - `units_derived_by_horn_clauses`: list of derived units (Horn-only forward chaining)

Important: to stay JSON-compatible for downstream tooling, proofs/models must remain **numbers + lists** (avoid raw solver text lines).

### Solver choices (what we choose and why)
- **SAT models**: PySAT with solver **`g3`** (fast, widely available in `python-sat` builds).
- **UNSAT proofs**:
  - We validated external proof logging via **Kissat**.
  - However, for **legacy parity**, UNSAT proofs are represented in the legacy internal proof format (resolution trace), not DRAT/LRAT text.
  - Post-parity, we can optionally add DRAT/LRAT as an additional artifact/output format.

### Determinism and seeds
- The legacy script `_legacy/makeproblems.py` is not inherently deterministic when run directly (it does not read a seed).
- For deterministic runs we standardize on **`PROBLEM_SEED`** (default `12345`) and run generators through a seeded entrypoint so parity can be verified mechanically (hash comparisons).

### Parity check (recommended)
Keep a “golden parity mode” and verify it:
- Generate legacy baseline
- Generate new output
- Compare checksums (`shasum`) or `diff`

### Next steps (planned)
- Copy `_legacy/makeproblems.py` into `scripts/makeproblems.py` unchanged as baseline.
- Introduce a minimal CLI (e.g., `--seed`, `--vars`, `--clens`, `--percase`, `--horn`) while preserving defaults.
- Remove dead options only after parity is protected by a stable test/harness.
