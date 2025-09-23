#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple


def load_summaries(root: Path, name: str, run_ids: List[str]) -> Dict[Tuple[str, str, str], Dict]:
    results: Dict[Tuple[str, str, str], Dict] = {}
    for run_id in run_ids:
        run_dir = root / name / run_id
        if not run_dir.exists():
            continue
        for summary in run_dir.rglob("*.summary.json"):
            try:
                data = json.loads(summary.read_text())
            except Exception:
                continue
            provider = data.get("provider") or summary.parts[-3]
            model = data.get("model") or summary.parts[-2]
            key = (run_id, provider, model)
            results[key] = data
    return results


def main() -> None:
    ap = argparse.ArgumentParser(description="Compare per-target summaries across runs")
    ap.add_argument("--name", required=True, help="Experiment name (e.g., exp8_horn_yesno)")
    ap.add_argument("--runs", required=True, help="Comma-separated run ids to compare (order matters)")
    ap.add_argument("--root", default="experiments/runs", help="Root runs directory")
    args = ap.parse_args()

    run_ids = [r.strip() for r in args.runs.split(",") if r.strip()]
    summaries = load_summaries(Path(args.root), args.name, run_ids)

    # Collect all provider/model combos
    combos: List[Tuple[str, str]] = []
    seen = set()
    for (rid, prov, mod) in summaries.keys():
        key = (prov, mod)
        if key not in seen:
            seen.add(key)
            combos.append(key)

    # Print table
    header = ["provider", "model"] + [f"acc@{rid}" for rid in run_ids]
    print("\t".join(header))
    for prov, mod in sorted(combos):
        row: List[str] = [prov, mod]
        baseline_acc = None
        for rid in run_ids:
            data = summaries.get((rid, prov, mod))
            acc = data.get("accuracy") if data else None
            if baseline_acc is None:
                baseline_acc = acc
                row.append(f"{acc:.3f}" if isinstance(acc, float) else "-")
            else:
                if isinstance(acc, float) and isinstance(baseline_acc, float):
                    delta = acc - baseline_acc
                    row.append(f"{acc:.3f} ({delta:+.3f})")
                else:
                    row.append(f"{acc:.3f}" if isinstance(acc, float) else "-")
        print("\t".join(row))


if __name__ == "__main__":
    main()


