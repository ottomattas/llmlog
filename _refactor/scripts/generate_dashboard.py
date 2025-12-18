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

    from llmlog.analysis.dashboard import generate_html_dashboard

    ap = argparse.ArgumentParser(description="Generate a single-file HTML dashboard from aggregated results JSON.")
    ap.add_argument("--input", required=True, help="Aggregated JSON file (from scripts/aggregate_results.py)")
    ap.add_argument("--output", required=True, help="Output HTML path")
    args = ap.parse_args()

    aggregated = json.loads(Path(args.input).read_text())
    generate_html_dashboard(aggregated=aggregated, output_path=args.output)
    print(f"Wrote dashboard to: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


