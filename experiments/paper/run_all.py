#!/usr/bin/env python3
"""
One entrypoint to regenerate all paper outputs.

Run from repo root (recommended):
  venv/bin/python -m experiments.paper.run_all
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Run the full paper outputs pipeline")
    ap.add_argument("--runs-dir", default="experiments/runs", help="Runs root directory")
    ap.add_argument("--out-dir", default="experiments/paper_outputs", help="Output directory root")
    ap.add_argument("--include-full-text", action="store_true", help="Include full_text in reparsed_rows.jsonl (large)")
    ap.add_argument("--include-unclear-fig", action="store_true", help="Also render unclear_rate figure pages")
    args = ap.parse_args()

    runs_dir = args.runs_dir
    out_dir = args.out_dir
    data_dir = str(Path(out_dir) / "data")

    py = sys.executable

    ingest_cmd = [py, "-m", "experiments.paper.ingest_and_reparse", "--runs-dir", runs_dir, "--out-dir", out_dir]
    if args.include_full_text:
        ingest_cmd.append("--include-full-text")
    _run(ingest_cmd)

    _run([py, "-m", "experiments.paper.prompt_catalog", "--runs-dir", runs_dir, "--out-dir", out_dir, "--data-dir", data_dir])
    _run([py, "-m", "experiments.paper.aggregate_metrics", "--data-dir", data_dir])
    _run([py, "-m", "experiments.paper.render_tables", "--data-dir", data_dir, "--out-dir", out_dir])

    fig_cmd = [py, "-m", "experiments.paper.render_figures", "--data-dir", data_dir, "--out-dir", out_dir]
    if args.include_unclear_fig:
        fig_cmd.append("--include-unclear")
    _run(fig_cmd)

    _run([py, "-m", "experiments.paper.generate_captions", "--data-dir", data_dir, "--out-dir", out_dir])
    _run([py, "-m", "experiments.paper.gap_report", "--data-dir", data_dir, "--out-dir", out_dir])
    _run([py, "-m", "experiments.paper.render_condensed_figures", "--data-dir", data_dir, "--out-dir", out_dir])

    print(f"\nDone. Outputs in: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


