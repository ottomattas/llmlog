#!/usr/bin/env python3
"""
Aggregate re-parsed rows into bucketed metrics for tables and figures.

Inputs (from experiments/paper_outputs/data):
  - reparsed_rows.jsonl
  - leaf_run_prompt_map.csv

Outputs (to experiments/paper_outputs/data):
  - metrics_by_bucket.csv
  - metrics_by_leaf.csv
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Tuple

from .common import iter_jsonl, safe_int


@dataclass
class Counts:
    total: int = 0
    correct: int = 0
    unclear: int = 0
    # Ground-truth breakdown by satisfiable flag:
    # satflag == 1 => satisfiable (and for horn-style prompts this corresponds to answer 'no')
    # satflag == 0 => unsatisfiable/contradiction (and for horn-style prompts this corresponds to answer 'yes')
    sat_total: int = 0
    sat_correct: int = 0
    unsat_total: int = 0
    unsat_correct: int = 0


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _load_prompt_map(path: Path) -> Dict[str, Dict[str, str]]:
    m: Dict[str, Dict[str, str]] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            key = (row.get("results_relpath") or "").strip()
            if not key:
                continue
            m[key] = row
    return m


def _rate(n: int, d: int) -> Optional[float]:
    if d <= 0:
        return None
    return n / d


def main() -> int:
    ap = argparse.ArgumentParser(description="Aggregate reparsed rows into metrics tables")
    ap.add_argument("--data-dir", default="experiments/paper_outputs/data", help="Data directory")
    args = ap.parse_args()

    data_dir = Path(args.data_dir).resolve()
    _ensure_dir(data_dir)

    reparsed_path = data_dir / "reparsed_rows.jsonl"
    prompt_map_path = data_dir / "leaf_run_prompt_map.csv"

    out_bucket = data_dir / "metrics_by_bucket.csv"
    out_leaf = data_dir / "metrics_by_leaf.csv"

    prompt_map = _load_prompt_map(prompt_map_path)

    # Keyed by (experiment, run_id, provider, model, thinking_mode, prompt_id, horn, maxvars, maxlen)
    bucket_counts: Dict[Tuple, Counts] = defaultdict(Counts)
    # Keyed by (experiment, run_id, provider, model, thinking_mode, prompt_id)
    leaf_counts: Dict[Tuple, Counts] = defaultdict(Counts)

    # Also remember prompt_style/parse_family for prompt_id (for output columns)
    prompt_meta: Dict[str, Dict[str, str]] = {}

    for row in iter_jsonl(reparsed_path):
        results_rel = (row.get("results_relpath") or "").strip()
        pm = prompt_map.get(results_rel)
        if pm is None:
            # Unknown leaf run; skip
            continue
        prompt_id = (pm.get("prompt_id") or "").strip()
        if not prompt_id:
            continue

        prompt_meta.setdefault(
            prompt_id,
            {
                "prompt_style": (pm.get("prompt_style") or "").strip(),
                "parse_family": (pm.get("parse_family") or "").strip(),
                "prompt_template": (pm.get("prompt_template") or "").strip(),
            },
        )

        exp = (row.get("experiment") or "").strip()
        run_id = (row.get("run_id") or "").strip()
        provider = (row.get("provider") or "").strip()
        model = (row.get("model") or "").strip()
        thinking = (row.get("thinking_mode") or "").strip()

        horn = safe_int(row.get("horn"))
        mv = safe_int(row.get("maxvars"))
        ml = safe_int(row.get("maxlen"))
        sf = safe_int(row.get("satflag"))

        if horn is None or mv is None or ml is None:
            continue

        correct = bool(row.get("correct"))
        unclear = bool(row.get("is_unclear"))

        bkey = (exp, run_id, provider, model, thinking, prompt_id, horn, mv, ml)
        lkey = (exp, run_id, provider, model, thinking, prompt_id)

        for key, store in ((bkey, bucket_counts), (lkey, leaf_counts)):
            c = store[key]
            c.total += 1
            if correct:
                c.correct += 1
            if unclear:
                c.unclear += 1
            if sf == 1:
                c.sat_total += 1
                if correct:
                    c.sat_correct += 1
            elif sf == 0:
                c.unsat_total += 1
                if correct:
                    c.unsat_correct += 1

    bucket_fields = [
        "experiment",
        "run_id",
        "provider",
        "model",
        "thinking_mode",
        "prompt_id",
        "prompt_template",
        "prompt_style",
        "parse_family",
        "horn",
        "maxvars",
        "maxlen",
        "total",
        "correct",
        "accuracy",
        "unclear",
        "unclear_rate",
        "sat_total",
        "sat_correct",
        "sat_accuracy",
        "unsat_total",
        "unsat_correct",
        "unsat_accuracy",
    ]

    with out_bucket.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=bucket_fields)
        w.writeheader()
        for key in sorted(bucket_counts.keys()):
            exp, run_id, provider, model, thinking, prompt_id, horn, mv, ml = key
            meta = prompt_meta.get(prompt_id, {})
            c = bucket_counts[key]
            w.writerow(
                {
                    "experiment": exp,
                    "run_id": run_id,
                    "provider": provider,
                    "model": model,
                    "thinking_mode": thinking,
                    "prompt_id": prompt_id,
                    "prompt_template": meta.get("prompt_template", ""),
                    "prompt_style": meta.get("prompt_style", ""),
                    "parse_family": meta.get("parse_family", ""),
                    "horn": horn,
                    "maxvars": mv,
                    "maxlen": ml,
                    "total": c.total,
                    "correct": c.correct,
                    "accuracy": _rate(c.correct, c.total),
                    "unclear": c.unclear,
                    "unclear_rate": _rate(c.unclear, c.total),
                    "sat_total": c.sat_total,
                    "sat_correct": c.sat_correct,
                    "sat_accuracy": _rate(c.sat_correct, c.sat_total),
                    "unsat_total": c.unsat_total,
                    "unsat_correct": c.unsat_correct,
                    "unsat_accuracy": _rate(c.unsat_correct, c.unsat_total),
                }
            )

    leaf_fields = [
        "experiment",
        "run_id",
        "provider",
        "model",
        "thinking_mode",
        "prompt_id",
        "prompt_template",
        "prompt_style",
        "parse_family",
        "total",
        "correct",
        "accuracy",
        "unclear",
        "unclear_rate",
        "sat_total",
        "sat_correct",
        "sat_accuracy",
        "unsat_total",
        "unsat_correct",
        "unsat_accuracy",
    ]

    with out_leaf.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=leaf_fields)
        w.writeheader()
        for key in sorted(leaf_counts.keys()):
            exp, run_id, provider, model, thinking, prompt_id = key
            meta = prompt_meta.get(prompt_id, {})
            c = leaf_counts[key]
            w.writerow(
                {
                    "experiment": exp,
                    "run_id": run_id,
                    "provider": provider,
                    "model": model,
                    "thinking_mode": thinking,
                    "prompt_id": prompt_id,
                    "prompt_template": meta.get("prompt_template", ""),
                    "prompt_style": meta.get("prompt_style", ""),
                    "parse_family": meta.get("parse_family", ""),
                    "total": c.total,
                    "correct": c.correct,
                    "accuracy": _rate(c.correct, c.total),
                    "unclear": c.unclear,
                    "unclear_rate": _rate(c.unclear, c.total),
                    "sat_total": c.sat_total,
                    "sat_correct": c.sat_correct,
                    "sat_accuracy": _rate(c.sat_correct, c.sat_total),
                    "unsat_total": c.unsat_total,
                    "unsat_correct": c.unsat_correct,
                    "unsat_accuracy": _rate(c.unsat_correct, c.unsat_total),
                }
            )

    print(f"Wrote:\n- {out_bucket}\n- {out_leaf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


