#!/usr/bin/env python3
"""R3.1 error analysis: characterise the horn_alg_from satisfiable-instance
collapse for OpenAI gpt-5.2 (think=none) on Compact CNF (Horn subset).

Reads per-item provenance from llmlog (no new runs) and:
  - quantifies how wrong satisfiable items fail (declared contradiction vs unclear);
  - prints representative concluding excerpts of the model's output.

Usage (from the llmlog repo root):
    python scripts/extract_error_traces.py
    python scripts/extract_error_traces.py --llmlog /path/to/another/checkout
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

# This file lives in llmlog/scripts/. Default to that repo root.
_REPO = Path(__file__).resolve().parents[1]
LLMLOG = Path(os.environ.get("LLMLOG_DIR", str(_REPO))).expanduser()
RUNS = LLMLOG / "runs"
SUITE = "sat__repr-cnf_compact__subset-hornonly__prompt-horn_alg_from__openai_gpt-5.2__think-none"
RUN_IDS = [f"horn_alg_from_cnf_compact_len{k}_vars10_50_case10" for k in (3, 4, 5)]


def iter_jsonl(p: Path):
    with p.open() as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    yield json.loads(line)
                except Exception:
                    pass


def latest_by_id(p: Path):
    out = {}
    for row in iter_jsonl(p):
        rid = row.get("id")
        if rid is not None:
            out[str(rid)] = row
    return out


def tail(text: str, n: int = 700) -> str:
    text = (text or "").strip()
    return text if len(text) <= n else "…" + text[-n:]


def main():
    global LLMLOG, RUNS
    ap = argparse.ArgumentParser(
        description="Characterise the horn_alg_from satisfiable-instance collapse from a local llmlog clone.")
    ap.add_argument("--llmlog", default=None,
                    help="Path to an llmlog checkout (overrides $LLMLOG_DIR; default: this repo).")
    args = ap.parse_args()
    if args.llmlog:
        LLMLOG = Path(args.llmlog).expanduser()
        RUNS = LLMLOG / "runs"
    if not RUNS.is_dir():
        raise SystemExit(
            f"llmlog runs/ not found under '{LLMLOG}'. "
            "Pass --llmlog PATH or set the LLMLOG_DIR environment variable.")

    items = {}
    for run in RUN_IDS:
        base = RUNS / SUITE / run
        for pp in sorted(base.rglob("results.provenance.v2.jsonl")):
            items.update(latest_by_id(pp))

    sat_total = sat_correct = wrong_contra = wrong_unclear = wrong_other = 0
    contra_examples = []
    for rid, row in items.items():
        meta = row.get("meta") or {}
        if int(meta.get("satflag", -1)) != 1 or int(meta.get("horn", -1)) != 1:
            continue
        sat_total += 1
        correct = row.get("correct")
        parsed = row.get("parsed_answer")
        if correct is True:
            sat_correct += 1
            continue
        # wrong satisfiable item
        if parsed == 0:
            wrong_contra += 1
            contra_examples.append((rid, meta, row.get("completion_text") or ""))
        elif parsed == 2 or parsed is None:
            wrong_unclear += 1
        else:
            wrong_other += 1

    print("=" * 78)
    print("R3.1  horn_alg_from satisfiable-instance collapse (gpt-5.2 none, Compact CNF, Horn)")
    print("=" * 78)
    print(f"satisfiable items (completed)      : {sat_total}")
    print(f"  correct (answered 'satisfiable') : {sat_correct}  ({sat_correct/sat_total:.2%})")
    print(f"  WRONG -> declared 'contradiction': {wrong_contra}  ({wrong_contra/sat_total:.2%})")
    print(f"  WRONG -> unclear/unparsed        : {wrong_unclear}")
    print(f"  WRONG -> other                   : {wrong_other}")
    print(f"\nInterpretation: of the {sat_total - sat_correct} satisfiable errors, "
          f"{wrong_contra} are false 'contradiction' declarations "
          f"({wrong_contra/max(1,(sat_total-sat_correct)):.0%} of errors).")

    # show how often the model explicitly mentions 'contradiction' in its final reasoning
    mentions = sum(1 for _, _, t in contra_examples if re.search(r"contradiction", t, re.I))
    print(f"Of the {wrong_contra} false-contradiction outputs, {mentions} explicitly use the word 'contradiction'.")

    print("\n" + "-" * 78)
    print("Representative concluding excerpts (satisfiable instances wrongly called contradiction):")
    print("-" * 78)
    # pick a few spread across n
    contra_examples.sort(key=lambda e: (int(e[1].get("maxvars", 0)), int(e[1].get("maxlen", 0))))
    picks = contra_examples[:: max(1, len(contra_examples) // 4)][:4]
    for rid, meta, txt in picks:
        print(f"\n[id={rid}  n={meta.get('maxvars')}  k={meta.get('maxlen')}  horn=1 satflag=1]")
        print(tail(txt, 700))


if __name__ == "__main__":
    main()
