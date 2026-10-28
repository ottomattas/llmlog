#!/usr/bin/env python3
"""Compute Wilson 95% confidence intervals for the headline comparisons
emphasised in neus2025-article.tex (R2.3).

Counts are recomputed from the exact per-item logs in the `llmlog` repo,
replicating the paper's own classifier (src/llmlog/analysis/combined_dashboard.py):
  per latest-row-per-id:
    total += 1
    if pending: pending += 1; continue        # (openai_response_id or submission_id) and parsed_answer is None and no error
    if error:   errors  += 1; continue
    if parsed_answer in {0,1}: answered += 1 else: unclear += 1
    if correct is True: correct += 1
  completed = answered + unclear               # accuracy denominator (excludes pending + errors)

Significance is read directly from the intervals: for every emphasised
comparison the two 95% CIs are disjoint.

No new model runs are performed; this only post-processes existing logs.

Usage (from the llmlog repo root):
    python scripts/compute_claim_support_stats.py
    python scripts/compute_claim_support_stats.py --llmlog /path/to/another/checkout
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
from typing import Iterable

# This file lives in llmlog/scripts/. Default to that repo root.
_REPO = Path(__file__).resolve().parents[1]
LLMLOG = Path(os.environ.get("LLMLOG_DIR", str(_REPO))).expanduser()
RUNS = LLMLOG / "runs"


# ---------- log reading + canonical classifier ----------
def _iter_jsonl(path: Path) -> Iterable[dict]:
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception:
                continue


def _latest_by_id(path: Path) -> dict:
    latest: dict = {}
    for row in _iter_jsonl(path):
        rid = row.get("id")
        if rid is None:
            continue
        latest[str(rid)] = row
    return latest


def _is_pending(row: dict) -> bool:
    if row.get("error"):
        return False
    return bool((row.get("openai_response_id") or row.get("submission_id")) and row.get("parsed_answer") is None)


def accumulate(specs, *, horn=None, satflag=None, maxlen=None) -> dict:
    """specs: list of (suite, run). Filters: horn/satflag ints, maxlen set."""
    c = dict(total=0, pending=0, errors=0, answered=0, unclear=0, correct=0)
    for suite, run in specs:
        base = RUNS / suite / run
        files = sorted(base.rglob("results.jsonl"))
        if not files:
            raise FileNotFoundError(f"no results.jsonl under {base}")
        for rp in files:
            for row in _latest_by_id(rp).values():
                meta = row.get("meta") or {}
                h, s, ml = meta.get("horn"), meta.get("satflag"), meta.get("maxlen")
                if h is None or s is None or ml is None:
                    continue
                if horn is not None and int(h) != horn:
                    continue
                if satflag is not None and int(s) != satflag:
                    continue
                if maxlen is not None and int(ml) not in maxlen:
                    continue
                c["total"] += 1
                if _is_pending(row):
                    c["pending"] += 1
                    continue
                if row.get("error"):
                    c["errors"] += 1
                    continue
                p = row.get("parsed_answer")
                try:
                    pi = int(p) if p is not None else None
                except Exception:
                    pi = None
                if pi is None or pi == 2:
                    c["unclear"] += 1
                else:
                    c["answered"] += 1
                if row.get("correct") is True:
                    c["correct"] += 1
    c["completed"] = c["answered"] + c["unclear"]
    return c


def kn(c: dict):
    """Return (correct, completed) = (k, n) under the completed denominator."""
    return c["correct"], c["completed"]


# ---------- statistics (pure python, no scipy) ----------
def wilson(k: int, n: int, z: float = 1.959963984540054):
    if n == 0:
        return (None, None)
    phat = k / n
    denom = 1 + z * z / n
    center = (phat + z * z / (2 * n)) / denom
    half = (z * math.sqrt((phat * (1 - phat) + z * z / (4 * n)) / n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def cis_disjoint(ciA, ciB) -> bool:
    """True iff the two 95% intervals do not overlap (the significance criterion used in the paper)."""
    return (ciA[1] < ciB[0]) or (ciB[1] < ciA[0])


def report_compare(label, kA, nA, kB, nB, *, labA, labB):
    accA, accB = kA / nA, kB / nB
    ciA, ciB = wilson(kA, nA), wilson(kB, nB)
    disjoint = cis_disjoint(ciA, ciB)
    print(f"\n### {label}")
    print(f"  {labA:42s} {kA:3d}/{nA:<3d} = {accA:.3f}  Wilson95 [{ciA[0]:.3f}, {ciA[1]:.3f}]")
    print(f"  {labB:42s} {kB:3d}/{nB:<3d} = {accB:.3f}  Wilson95 [{ciB[0]:.3f}, {ciB[1]:.3f}]")
    print(f"  95% CIs disjoint: {'yes' if disjoint else 'NO'}")
    return dict(kA=kA, nA=nA, kB=kB, nB=nB, accA=accA, accB=accB, ciA=ciA, ciB=ciB, disjoint=disjoint)


def report_single(label, k, n):
    acc = k / n
    ci = wilson(k, n)
    print(f"  {label:42s} {k:3d}/{n:<3d} = {acc:.3f}  Wilson95 [{ci[0]:.3f}, {ci[1]:.3f}]")
    return dict(k=k, n=n, acc=acc, ci=ci)


# ---------- run specs (paper's exact selection; see fig_*.txt sidecars) ----------
def horn_ex_gpt52():
    return [("sat__repr-cnf_compact__subset-hornonly__prompt-examples_only__openai_gpt-5.2__think-none",
             f"horn_ex_only_cnf_compact_len{k}_vars10_50_case10") for k in (3, 4, 5)]


def horn_ex_pro():
    return [("sat__repr-cnf_compact__subset-hornonly__prompt-examples_only__openai_gpt-5.2-pro__think-high",
             f"horn_ex_only_len{k}_vars10_50_case10") for k in (3, 4, 5)]


def horn_algfrom_gpt52():
    return [("sat__repr-cnf_compact__subset-hornonly__prompt-horn_alg_from__openai_gpt-5.2__think-none",
             f"horn_alg_from_cnf_compact_len{k}_vars10_50_case10") for k in (3, 4, 5)]


def nonhorn_ex_gpt52():
    return [("sat__repr-cnf_compact__subset-nonhornonly__prompt-examples_only__openai_gpt-5.2__think-none",
             f"nonhorn_ex_only_cnf_compact_len{k}_vars10_50_case10") for k in (3, 4, 5)]


def nonhorn_ex_pro():
    return [("sat__repr-cnf_compact__subset-nonhornonly__prompt-examples_only__openai_gpt-5.2-pro__think-high",
             "nonhorn_ex_only_cnf_compact_len3_vars10_50_case10")]


def horn_ex_nl_gpt52():
    return [("sat__repr-cnf_nl__subset-hornonly__prompt-examples_only__openai_gpt-5.2__think-none",
             f"horn_ex_only_cnf_nl_len{k}_vars10_50_case10") for k in (3, 4, 5)]


def horn_ex_ifthen_gpt52():
    return [("sat__repr-horn_if_then__subset-hornonly__prompt-examples_only__openai_gpt-5.2__think-none",
             f"baseline_case10_len{k}_vars10_50") for k in (3, 4, 5)]


def main():
    global LLMLOG, RUNS
    ap = argparse.ArgumentParser(
        description="Recompute claim-support statistics from a local llmlog clone.")
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

    print("=" * 78)
    print("Recomputed per-cell counts (completed denominator) + Wilson 95% confidence intervals")
    print(f"Source: {LLMLOG} (post-hoc; no new runs)")
    print("=" * 78)

    # --- cells we need ---
    hg_sat = accumulate(horn_ex_gpt52(), horn=1, satflag=1)
    hg_uns = accumulate(horn_ex_gpt52(), horn=1, satflag=0)
    hg_all = accumulate(horn_ex_gpt52(), horn=1)
    hp_all = accumulate(horn_ex_pro(), horn=1)
    af_sat = accumulate(horn_algfrom_gpt52(), horn=1, satflag=1)
    af_uns = accumulate(horn_algfrom_gpt52(), horn=1, satflag=0)
    nh_sat_k3 = accumulate(nonhorn_ex_gpt52(), horn=0, satflag=1, maxlen={3})
    nh_uns_k3 = accumulate(nonhorn_ex_gpt52(), horn=0, satflag=0, maxlen={3})
    nhpro_sat_k3 = accumulate(nonhorn_ex_pro(), horn=0, satflag=1, maxlen={3})
    nhpro_uns_k3 = accumulate(nonhorn_ex_pro(), horn=0, satflag=0, maxlen={3})
    nl_uns = accumulate(horn_ex_nl_gpt52(), horn=1, satflag=0)
    it_uns = accumulate(horn_ex_ifthen_gpt52(), horn=1, satflag=0)

    # --- cross-validation against figure sidecars (must match exactly) ---
    print("\n[cross-validation vs fig_*.txt sidecars]")
    checks = [
        ("gpt-5.2 Horn ex sat   == 74/75", kn(hg_sat), (74, 75)),
        ("gpt-5.2 Horn ex unsat == 34/75", kn(hg_uns), (34, 75)),
        ("gpt-5.2-pro Horn ex   == 150/150", kn(hp_all), (150, 150)),
        ("gpt-5.2 Horn ex all   == 108/150", kn(hg_all), (108, 150)),
        ("gpt-5.2 alg_from sat  == 16/75", kn(af_sat), (16, 75)),
        ("gpt-5.2 alg_from unsat== 69/75", kn(af_uns), (69, 75)),
        ("gpt-5.2 NH k3 sat     == 25/25", kn(nh_sat_k3), (25, 25)),
        ("gpt-5.2 NH k3 unsat   == 0/25", kn(nh_uns_k3), (0, 25)),
        ("gpt-5.2 Horn NL unsat == 23/75", kn(nl_uns), (23, 75)),
        ("gpt-5.2 Horn ifthen u == 54/75", kn(it_uns), (54, 75)),
    ]
    ok = True
    for name, got, exp in checks:
        flag = "OK " if got == exp else "!! MISMATCH"
        if got != exp:
            ok = False
        print(f"  [{flag}] {name}  (got {got[0]}/{got[1]})")
    print(f"  --> cross-validation {'PASSED' if ok else 'FAILED'}")

    print("\n[gpt-5.2-pro Non-Horn k=3 examples-only (the one cell not in a sidecar split)]")
    print(f"  sat   : {nhpro_sat_k3}")
    print(f"  unsat : {nhpro_uns_k3}")

    # --- headline comparisons ---
    print("\n" + "=" * 78)
    print("HEADLINE COMPARISONS")
    print("=" * 78)

    report_compare(
        "C1  Horn overall, examples-only (key finding / Discussion): gpt-5.2-pro vs gpt-5.2",
        *kn(hp_all), *kn(hg_all), labA="gpt-5.2-pro (high)", labB="gpt-5.2 (none)")

    report_compare(
        "C2  Horn, gpt-5.2 (none), examples-only: satisfiable vs unsatisfiable (asymmetry)",
        *kn(hg_sat), *kn(hg_uns), labA="satisfiable", labB="unsatisfiable")

    report_compare(
        "C3  Horn unsat, gpt-5.2 (none): examples-only vs horn_alg_from (RQ2)",
        *kn(af_uns), *kn(hg_uns), labA="horn_alg_from (unsat)", labB="examples-only (unsat)")

    report_compare(
        "C4  Horn sat, gpt-5.2 (none): examples-only vs horn_alg_from (RQ2 collapse)",
        *kn(hg_sat), *kn(af_sat), labA="examples-only (sat)", labB="horn_alg_from (sat)")

    report_compare(
        "C5  Non-Horn k=3, gpt-5.2 (none), examples-only: satisfiable vs unsatisfiable (RQ4)",
        *kn(nh_sat_k3), *kn(nh_uns_k3), labA="satisfiable", labB="unsatisfiable")

    report_compare(
        "C6  Non-Horn k=3 unsat, examples-only: gpt-5.2-pro vs gpt-5.2 (RQ3 test-time)",
        *kn(nhpro_uns_k3), *kn(nh_uns_k3), labA="gpt-5.2-pro (high)", labB="gpt-5.2 (none)")

    report_compare(
        "C7  Horn unsat, gpt-5.2 (none), examples-only: If-then CNF vs Natural Language CNF (RQ1)",
        *kn(it_uns), *kn(nl_uns), labA="If-then CNF (unsat)", labB="Natural Language CNF (unsat)")


if __name__ == "__main__":
    main()
