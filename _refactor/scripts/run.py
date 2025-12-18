#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _bootstrap_import_path() -> None:
    # Allow running from repo root without installing the package.
    here = Path(__file__).resolve()
    refactor_root = here.parents[1]
    src = refactor_root / "src"
    sys.path.insert(0, str(src))


def main() -> int:
    _bootstrap_import_path()

    from llmlog.runner import run_suite

    ap = argparse.ArgumentParser(description="Run a `_refactor` suite config.")
    ap.add_argument("--suite", required=True, help="Path to a suite YAML (e.g. _refactor/configs/suites/<suite>.yaml)")
    ap.add_argument("--run", default=None, help="Run identifier injected into ${run} output paths")
    ap.add_argument("--out-root", default=None, help="Override output root directory (defaults to _refactor/)")
    ap.add_argument("--limit", type=int, default=None, help="Limit number of processed problems")
    ap.add_argument("--dry-run", action="store_true", help="Render prompts but do not call providers")
    ap.add_argument("--resume", action="store_true", help="Resume if results files already exist")
    ap.add_argument("--no-resume", action="store_true", help="Disable resume even if suite enables it")
    ap.add_argument("--lockstep", action="store_true", help="Run targets in lockstep per-problem")
    ap.add_argument("--only", type=str, default=None, help="Comma-separated providers to include (e.g. openai,google)")
    args = ap.parse_args()

    only = [p.strip() for p in (args.only or "").split(",") if p.strip()] or None

    resume = None
    if args.resume:
        resume = True
    if args.no_resume:
        resume = False

    lockstep = True if args.lockstep else None

    run_suite(
        suite_path=args.suite,
        run_id=args.run,
        output_root=args.out_root,
        limit=args.limit,
        dry_run=args.dry_run,
        only_providers=only,
        resume=resume,
        lockstep=lockstep,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


