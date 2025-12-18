## Analysis

### Aggregate results
Given a run id (the `${run}` segment in `runs/<suite>/<run>/...`):
```
python scripts/aggregate_results.py --run-id <run_id> --output reports/<run_id>.aggregated.json
```

### Generate a dashboard
```
python scripts/generate_dashboard.py --input reports/<run_id>.aggregated.json --output reports/<run_id>.dashboard.html
```

### Inspect prompts + reasoning
If you enabled provenance output, you can export individual prompts and responses:
```
python scripts/export_provenance.py --provenance runs/<suite>/<run>/<provider>/<model>/<thinking_mode>/results.provenance.jsonl --out reports/exports --limit 50 --no-raw
```

