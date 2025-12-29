## Runs and results (artifacts policy)

Run artifacts are written under `_refactor/runs/` and are **gitignored by default** (to keep the repo light).
For traceability (e.g. paper snapshots / reproducible audits), you can optionally force-add selected run folders and commit them.

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
  run.manifest.json
  run.invocations.jsonl
```

### File semantics
- `results.jsonl`: minimal rows for fast aggregation.
- `results.provenance.jsonl`: optional full provenance (prompt, raw response, usage, timing, thinking text when available).
- `results.summary.json`: per-target aggregate stats (accuracy, token totals, etc).
- `run.manifest.json`: reproducibility snapshot (suite inputs + target config + matched pricing rate row).
- `run.invocations.jsonl`: append-only operational log of each `scripts/run.py` invocation that wrote into this folder (timestamp, submit-only vs live, `--limit`, etc). Useful when terminal history is lost.

### Async submission fields (OpenAI)
When running with `scripts/run.py --submit-only`, rows may include:
- `openai_response_id`: the `resp_...` id returned by the Responses API (used for later collection)
- `openai_response_status`: last observed server status (best-effort)
- `parsed_answer`: empty/pending until collection

Suggested terminology used in this repo:
- **Live mode**: blocking/polling run (default `scripts/run.py` behavior)
- **Async mode**: submit-only + collector (`--submit-only` + `scripts/collect_openai_submissions.py`)

To collect pending responses later:
```
python scripts/collect_openai_submissions.py --runs-dir runs
python scripts/collect_openai_submissions.py --runs-dir runs --watch-seconds 60
```

#### Recommended collector settings (practical)
- **Default**: use watch mode (`--watch-seconds 60`) so you don't hammer the API.
- **Large batches**: consider increasing the interval (e.g. 120s) and using `--limit` to cap how many pending ids are collected per run file per pass.
- **Small batches / “wait until done”**: use `--poll` only when you explicitly want the collector to block until each id is terminal.

To recover previously timed-out responses (when an id is present):
```
python scripts/recover_openai_timeouts.py
```

### Export for inspection
To export a provenance file into prompt/response text files:
```
python scripts/export_provenance.py --provenance runs/<suite>/<run>/<provider>/<model>/<thinking_mode>/results.provenance.jsonl --out reports/exports --limit 50 --no-raw
```

