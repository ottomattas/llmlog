#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _bootstrap_import_path() -> None:
    here = Path(__file__).resolve()
    refactor_root = here.parents[1]
    src = refactor_root / "src"
    sys.path.insert(0, str(src))


def main() -> int:
    _bootstrap_import_path()

    from llmlog.exports import export_provenance_human_readable

    ap = argparse.ArgumentParser(description="Export provenance JSONL to human-readable files.")
    ap.add_argument("--provenance", required=True, help="Path to a *.provenance.jsonl file")
    ap.add_argument("--out", required=True, help="Output directory")
    ap.add_argument("--limit", type=int, default=None, help="Limit number of exported rows")
    ap.add_argument("--id", dest="ids", action="append", default=None, help="Filter to specific id(s); repeatable")
    ap.add_argument("--no-raw", action="store_true", help="Do not write raw_response.json")
    args = ap.parse_args()

    export_provenance_human_readable(
        provenance_path=args.provenance,
        out_dir=args.out,
        limit=args.limit,
        ids=args.ids,
        include_raw_response=(not args.no_raw),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


