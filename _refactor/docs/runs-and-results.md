## Runs and results (artifacts policy)

Run artifacts are written under `_refactor/runs/` and are **not meant to be committed**.

### Git ignore policy
`_refactor/.gitignore` ignores:
- `runs/`
- `reports/`
- `secrets.json`

### Output directory structure
The runner writes one folder per target:
```
runs/<suite>/<run>/<provider>/<model>/<thinking_mode>/
  results.jsonl
  results.provenance.jsonl
  results.summary.json
```

### File semantics
- `results.jsonl`: minimal rows for fast aggregation.
- `results.provenance.jsonl`: optional full provenance (prompt, raw response, usage, timing, thinking text when available).
- `results.summary.json`: per-target aggregate stats (accuracy, token totals, etc).

### Export for inspection
To export a provenance file into prompt/response text files:
```
python scripts/export_provenance.py --provenance runs/<suite>/<run>/<provider>/<model>/<thinking_mode>/results.provenance.jsonl --out reports/exports --limit 50 --no-raw
```

