#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def _bootstrap_import_path() -> Path:
    """Allow running from repo root without installing the package.

    Returns the `_refactor/` root directory.
    """
    here = Path(__file__).resolve()
    refactor_root = here.parents[1]
    src = refactor_root / "src"
    sys.path.insert(0, str(src))
    return refactor_root


def main() -> int:
    refactor_root = _bootstrap_import_path()

    from llmlog.analysis.combined_dashboard import generate_combined_dashboard

    ap = argparse.ArgumentParser(
        description="Generate a single-file combined HTML dashboard from `_refactor/runs/**/results.jsonl`."
    )
    ap.add_argument("--runs-dir", default=str(refactor_root / "runs"), help="Runs directory (default: _refactor/runs)")
    ap.add_argument("--output", required=True, help="Output HTML path")
    ap.add_argument("--title", default="llmlog combined dashboard", help="HTML title")
    ap.add_argument(
        "--include-suite",
        action="append",
        default=[],
        help="Only include this suite (repeatable). If omitted, include all suites.",
    )
    ap.add_argument(
        "--exclude-suite",
        action="append",
        default=[],
        help="Exclude this suite (repeatable).",
    )
    ap.add_argument(
        "--watch-seconds",
        type=int,
        default=None,
        help="If set, regenerate the dashboard every N seconds until interrupted.",
    )
    args = ap.parse_args()

    def one_pass() -> None:
        generate_combined_dashboard(
            runs_dir=str(Path(args.runs_dir).resolve()),
            output_path=str(Path(args.output).resolve()),
            title=str(args.title),
            include_suites=[s for s in (args.include_suite or []) if s],
            exclude_suites=[s for s in (args.exclude_suite or []) if s],
        )
        print(f"Wrote combined dashboard: {args.output}")

    if args.watch_seconds is None:
        one_pass()
        return 0

    while True:
        one_pass()
        time.sleep(float(args.watch_seconds))


if __name__ == "__main__":
    raise SystemExit(main())


