#!/usr/bin/env python3

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Generate problems dataset via configurable makeproblems.py")
    ap.add_argument("--output", required=True, help="Output path (e.g., data/problems_dist20_v1.js)")
    ap.add_argument("--script", default="experiments/makeproblems.py", help="Path to makeproblems.py (parametrized)")
    # pass-through flags for the generator
    ap.add_argument("--vars", dest="vars", default=None, help="Variable counts list/range, e.g. 10-20 or 10,12,15")
    ap.add_argument("--clens", dest="clens", default=None, help="Clause lengths list/range, e.g. 3-5 or 3,4,5")
    ap.add_argument("--horn", dest="horn", choices=["only","mixed"], default=None, help="Horn-only or mixed problems")
    ap.add_argument("--percase", dest="percase", type=int, default=None, help="Problems per case (even number)")
    ap.add_argument("--seed", dest="seed", type=int, default=None, help="Random seed")
    ap.add_argument("--workers", dest="workers", type=int, default=None, help="Parallel worker processes for case generation")
    ap.add_argument("--no-proof", dest="no_proof", action="store_true", help="Skip resolution proof construction (faster)")
    args = ap.parse_args()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)

    cmd = [sys.executable, args.script]
    if args.vars:
        cmd += ["--vars", args.vars]
    if args.clens:
        cmd += ["--clens", args.clens]
    if args.horn:
        cmd += ["--horn", args.horn]
    if args.percase is not None:
        cmd += ["--percase", str(args.percase)]
    if args.seed is not None:
        cmd += ["--seed", str(args.seed)]
    if args.workers is not None:
        cmd += ["--workers", str(args.workers)]
    if args.no_proof:
        cmd += ["--no-proof"]
    with out.open("w") as f:
        proc = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
    if proc.returncode != 0:
        print(proc.stderr)
        sys.exit(proc.returncode)
    print(f"Wrote dataset to {out}")


if __name__ == "__main__":
    main()


