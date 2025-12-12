## Migration plan

This plan keeps the current workflow usable while refactoring incrementally.

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
