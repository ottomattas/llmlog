#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _bootstrap_import_path() -> None:
    here = Path(__file__).resolve()
    refactor_root = here.parents[1]
    src = refactor_root / "src"
    sys.path.insert(0, str(src))


def main() -> int:
    _bootstrap_import_path()

    from llmlog.analysis.aggregate import aggregate_runs

    ap = argparse.ArgumentParser(description="Aggregate `_refactor/runs` results into a single JSON.")
    ap.add_argument("--runs-dir", default=str(Path(__file__).resolve().parents[1] / "runs"), help="Runs directory")
    ap.add_argument("--run-id", required=True, help="Run id (the ${run} segment)")
    ap.add_argument("--output", required=True, help="Output JSON path")
    args = ap.parse_args()

    agg = aggregate_runs(runs_dir=args.runs_dir, run_id=args.run_id)
    Path(args.output).write_text(json.dumps(agg, indent=2, ensure_ascii=False))
    print(f"Wrote aggregated results to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


