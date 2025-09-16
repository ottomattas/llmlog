#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate problems dataset via legacy makeproblems.py")
    ap.add_argument("--output", required=True, help="Output path (e.g., data/problems_dist20_v1.js)")
    ap.add_argument("--script", default="_legacy/makeproblems.py", help="Path to legacy makeproblems.py")
    args = ap.parse_args()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    cmd = [sys.executable, args.script]
    with out.open("w") as f:
        proc = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        print(proc.stderr)
        sys.exit(proc.returncode)
    print(f"Wrote dataset to {out}")


if __name__ == "__main__":
    main()


