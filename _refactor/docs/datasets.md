## Datasets

This doc covers **dataset management**: where datasets live, naming conventions, provenance, and storage policy.

For generator implementation details (solvers, ratios, output schema, runtime flags), see [`docs/problem-generation.md`](problem-generation.md).

All commands below assume your working directory is the `_refactor/` project root. If you are running from the repo root, use `_refactor/scripts/generate_problems.py` instead.

### Where datasets live
Datasets are stored under `datasets/`, split by purpose:
- **`datasets/legacy/`**: legacy-parity fixtures / regression baselines (typically produced with `--mode legacy`).
- **`datasets/validation/`**: curated datasets used for development, evaluation, and day-to-day experimentation.
- **`datasets/production/`**: long-lived “release” datasets you want to keep stable over time (often referenced in papers/reports).

### Dataset parameters (naming inputs)
Most datasets are described by a small set of generation parameters:
- **`--seed`**: determinism (same seed + same generator version ⇒ same file).
- **`--vars`**: variable count(s) \(n\) (e.g. `3-50`, `10-10`, or mixed like `3-5,7`).
- **`--clens`**: clause length(s) \(k\) (e.g. `3-5` or `3,4,5`).
- **`--horn`**: `only` / `no` / `mixed`.
- **`--percase`**: number of problems per \((n,k,horn)\) case (must be even; output is balanced SAT/UNSAT).

### Naming convention
When you omit `--name`, the generator auto-names files using a parameterized format like:
- `problems_{mode}_seed{seed}_vars{...}_len{...}_horn{horn}_percase{percase}.jsonl`

If you provide `--name`, we recommend still encoding the core parameters, e.g.:
- `full_vars3-50_len3-5_hornmixed_per50_seed12345`
- `vars10_len3-5_hornmixed_per20_seed12345`

### Provenance (what to record)
To make datasets reproducible and auditable, record at least:
- **Generation command** (full CLI invocation).
- **Generator version**: the git commit SHA of the repo (or at minimum the commit SHA of `scripts/generate_problems.py`).
- **Checksum**: run with `--print-sha256` and store the printed SHA-256.
- **Solver versions**: `kissat --version` and your `python-sat` version (optional but recommended).
- **Expected size/shape**: expected row count and any special ratios/overrides used.

In practice, the simplest place to record this is the **commit message** that adds the dataset (or a release note).

### Storage policy (Git LFS)
Datasets can be large. In this repo, JSONL datasets under `_refactor/datasets/**/*.jsonl` are tracked with **Git LFS** (see `.gitattributes`).

Implications:
- The repo stores a small **pointer file** in Git; the dataset bytes are stored in LFS.
- After cloning, run `git lfs install` and `git lfs pull` to download dataset contents.
- GitHub LFS has storage/bandwidth quotas; very large datasets may require a paid plan.

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

This produces a single JSONL file under `datasets/validation/` with **14400** problem rows (plus a header line).

### Example: “step” datasets (n = 10, 20, 30, 40, 50)
Generate five separate datasets (each 120 rows + header: \(3\) clause lengths × \(2\) horn flags × `percase=20`):

```
for n in 10 20 30 40 50; do
  python scripts/generate_problems.py \
    --mode pysat_kissat \
    --seed 12345 \
    --vars "${n}-${n}" \
    --clens 3-5 \
    --horn mixed \
    --percase 20 \
    --dataset validation \
    --name "vars${n}_len3-5_hornmixed_per20_seed12345" \
    --max-attempts 200000 \
    --progress-every 2000 \
    --print-sha256
done
```

### Curated datasets in this repo
- **`datasets/validation/full_vars3-50_len3-5_hornmixed_per50_seed12345.jsonl`**
  - `--mode pysat_kissat --seed 12345 --vars 3-50 --clens 3-5 --horn mixed --percase 50`
  - Rows: **14400** (plus header)
  - SHA-256: `f9542cb74c344e048ca6e9dbdf619f31a49d0b9065502c7f642a1a29bf8fb945`
