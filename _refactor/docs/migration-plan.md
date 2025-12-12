## Migration plan

This plan keeps the current workflow usable while refactoring incrementally.

### AI handoff / session bootstrap (source of truth)
The goal is that a new work session (or a fresh AI chat) can “rehydrate” context quickly from a small, stable set of files and a short checklist.

**When starting a new session, use these files as the source of truth (read in this order):**
1) `_refactor/README.md` — project purpose + quickstart + directory layout + doc links
2) `_refactor/docs/README.md` — documentation index
3) `_refactor/docs/problem-generation.md` — dataset schema + solver/proof decisions + encoding
4) `_refactor/docs/repository-layout.md` — target structure and conventions
5) `_refactor/docs/migration-plan.md` — this plan + current status + next tasks

**Key decisions (keep consistent unless you explicitly decide to change them):**
- Dataset generator CLI: `scripts/generate_problems.py`
- Generation engine reused from: `_legacy/makeproblems.py` (do not edit legacy while still using it as the reference)
- SAT solving: PySAT (`g3`) for models
- UNSAT proving: Kissat DRAT, encoded as JSON-friendly lists of ints (add/delete markers)
- Dataset output: JSONL (header line + rows), schema documented in `docs/problem-generation.md`

**Minimal “parity sanity check” to run after changes:**
- Generate a small dataset with a fixed seed and confirm it parses as JSONL.
- If you are intentionally keeping a legacy-parity mode, compare checksums (`shasum`) against the baseline for the same seed/params.

**How to talk to the AI agent (recommended prompt skeleton):**
- Provide the next task plus links to the above files. Example:
  - “Please read `_refactor/docs/migration-plan.md` and `_refactor/docs/problem-generation.md` and then implement <task>.”

### Stage A — problem generation parity
- Keep `_legacy/makeproblems.py` unchanged.
- Ensure the new generator can reproduce legacy datasets byte-for-byte (given the same seed/params).
- Keep downstream tooling working on both “legacy” and “new” datasets.

### Stage B — move framework code into a package
- Move `experiments/runner.py`, `schema.py`, `filters.py`, `parsers.py`, and analysis tools into `src/llmlog/`.
- Keep thin wrappers under `scripts/` so CLI usage remains stable.

### Stage C — artifact strategy
- Move run outputs out of the code tree (e.g., from `experiments/runs/` to `runs/`).
- Add ignore rules so large run artifacts don’t bloat the repository.

### Stage D — cutover
- When the new layout is complete and validated, move the new tree to the repo root and retire the legacy layout (keeping a tag or branch for archival if needed).

### Note on `.gitkeep`
This refactor branch uses `.gitkeep` files to allow Git to track empty directories (e.g., `scripts/`, `datasets/validation/`, `runs/`) before they contain real content.

- Keep `.gitkeep` while a directory is empty.
- Remove the `.gitkeep` as soon as you add the first real file to that directory.
- `.gitkeep` has no runtime effect; it’s only version-control bookkeeping.

### Current status (update this as you go)
- Stage A (problem generation parity): TODO
- Stage B (package refactor): TODO
- Stage C (artifact strategy): TODO
- Stage D (cutover): TODO

### Next tasks (keep short; update each session)
- TODO
