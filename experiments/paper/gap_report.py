#!/usr/bin/env python3
"""
Generate coverage gap reports and actionable rerun suggestions.

Outputs (under --out-dir):
  - gaps/gaps_by_group.csv
  - gaps/gaps_by_model_prompt.csv
  - gaps/run_recommendations.md
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from .common import iter_jsonl, safe_int


@dataclass
class LeafCoverage:
    total: int = 0
    unclear: int = 0
    maxvars: Set[int] = None  # type: ignore[assignment]
    maxlen: Set[int] = None  # type: ignore[assignment]
    horn: Set[int] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.maxvars is None:
            self.maxvars = set()
        if self.maxlen is None:
            self.maxlen = set()
        if self.horn is None:
            self.horn = set()


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _load_metrics_by_bucket(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _fmt_int_ranges(vals: Set[int]) -> str:
    if not vals:
        return ""
    xs = sorted(vals)
    ranges: List[str] = []
    start = prev = xs[0]
    for x in xs[1:]:
        if x == prev + 1:
            prev = x
            continue
        ranges.append(f"{start}-{prev}" if prev > start else f"{start}")
        start = prev = x
    ranges.append(f"{start}-{prev}" if prev > start else f"{start}")
    return ",".join(ranges)


def _missing_within_span(vals: Set[int]) -> Set[int]:
    if not vals:
        return set()
    lo = min(vals)
    hi = max(vals)
    return {x for x in range(lo, hi + 1) if x not in vals}


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate gap reports from paper_outputs data")
    ap.add_argument("--data-dir", default="experiments/paper_outputs/data", help="Data directory")
    ap.add_argument("--out-dir", default="experiments/paper_outputs", help="Output directory root")
    ap.add_argument("--runs-dir", default="experiments/runs", help="Runs root (for config path suggestions)")
    args = ap.parse_args()

    data_dir = Path(args.data_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    gaps_dir = out_dir / "gaps"
    _ensure_dir(gaps_dir)

    reparsed_path = data_dir / "reparsed_rows.jsonl"
    leaf_runs_path = data_dir / "leaf_runs.csv"
    metrics_bucket_path = data_dir / "metrics_by_bucket.csv"
    prompt_index_path = data_dir / "prompt_index.json"

    leaf_runs = _load_csv(leaf_runs_path)
    metrics_bucket = _load_metrics_by_bucket(metrics_bucket_path)
    prompt_index = json.loads(prompt_index_path.read_text(encoding="utf-8"))

    # Map leaf identity from leaf_runs.csv
    leaf_meta_by_results: Dict[str, Dict[str, str]] = {}
    for lr in leaf_runs:
        rr = (lr.get("results_relpath") or "").strip()
        if rr:
            leaf_meta_by_results[rr] = lr

    # 1) Coverage by leaf run (results_relpath)
    cov_by_leaf: Dict[str, LeafCoverage] = defaultdict(LeafCoverage)
    group_by_leaf: Dict[str, Tuple[str, str]] = {}
    for obj in iter_jsonl(reparsed_path):
        results_rel = (obj.get("results_relpath") or "").strip()
        if not results_rel:
            continue
        exp = (obj.get("experiment") or "").strip()
        run_id = (obj.get("run_id") or "").strip()
        group_by_leaf[results_rel] = (exp, run_id)

        c = cov_by_leaf[results_rel]
        c.total += 1
        if bool(obj.get("is_unclear")):
            c.unclear += 1
        mv = safe_int(obj.get("maxvars"))
        ml = safe_int(obj.get("maxlen"))
        hf = safe_int(obj.get("horn"))
        if mv is not None:
            c.maxvars.add(mv)
        if ml is not None:
            c.maxlen.add(ml)
        if hf is not None:
            c.horn.add(hf)

    # 2) Group unions (experiment, run_id)
    group_union_maxvars: Dict[Tuple[str, str], Set[int]] = defaultdict(set)
    group_union_maxlen: Dict[Tuple[str, str], Set[int]] = defaultdict(set)
    group_union_horn: Dict[Tuple[str, str], Set[int]] = defaultdict(set)
    group_expected_total: Dict[Tuple[str, str], int] = defaultdict(int)

    for leaf, (exp, run_id) in group_by_leaf.items():
        gk = (exp, run_id)
        c = cov_by_leaf.get(leaf)
        if not c:
            continue
        group_union_maxvars[gk].update(c.maxvars)
        group_union_maxlen[gk].update(c.maxlen)
        group_union_horn[gk].update(c.horn)
        if c.total > group_expected_total[gk]:
            group_expected_total[gk] = c.total

    # 3) Write gaps_by_group.csv (leaf-level missingness vs group union)
    gaps_by_group_csv = gaps_dir / "gaps_by_group.csv"
    group_fields = [
        "experiment",
        "run_id",
        "provider",
        "model",
        "thinking_mode",
        "results_relpath",
        "provenance_relpath",
        "total",
        "expected_total",
        "missing_rows_vs_group",
        "unclear",
        "present_maxvars",
        "missing_maxvars_vs_group",
        "present_maxlen",
        "missing_maxlen_vs_group",
        "present_horn",
        "missing_horn_vs_group",
        "provenance_error_rows",
        "provenance_full_text_empty_rows",
        "config_path_guess",
    ]

    # Repo root + config dir (best-effort)
    repo_root = Path(__file__).resolve().parents[2]
    configs_root = repo_root / "experiments" / "configs"

    group_rows: List[Dict[str, Any]] = []
    for results_rel, (exp, run_id) in sorted(group_by_leaf.items()):
        c = cov_by_leaf.get(results_rel)
        if not c:
            continue
        meta = leaf_meta_by_results.get(results_rel, {})
        gk = (exp, run_id)
        expected = group_expected_total.get(gk, c.total)
        missing_rows = max(0, expected - c.total)

        miss_mv = group_union_maxvars[gk] - c.maxvars
        miss_ml = group_union_maxlen[gk] - c.maxlen
        miss_hf = group_union_horn[gk] - c.horn

        cfg_guess = configs_root / Path(exp).with_suffix(".yaml")
        cfg_guess_str = str(cfg_guess) if cfg_guess.exists() else ""

        group_rows.append(
            {
                "experiment": exp,
                "run_id": run_id,
                "provider": meta.get("provider", ""),
                "model": meta.get("model", ""),
                "thinking_mode": meta.get("thinking_mode", ""),
                "results_relpath": results_rel,
                "provenance_relpath": meta.get("provenance_relpath", ""),
                "total": c.total,
                "expected_total": expected,
                "missing_rows_vs_group": missing_rows,
                "unclear": c.unclear,
                "present_maxvars": _fmt_int_ranges(c.maxvars),
                "missing_maxvars_vs_group": _fmt_int_ranges(miss_mv),
                "present_maxlen": _fmt_int_ranges(c.maxlen),
                "missing_maxlen_vs_group": _fmt_int_ranges(miss_ml),
                "present_horn": _fmt_int_ranges(c.horn),
                "missing_horn_vs_group": _fmt_int_ranges(miss_hf),
                "provenance_error_rows": meta.get("provenance_error_rows", ""),
                "provenance_full_text_empty_rows": meta.get("provenance_full_text_empty_rows", ""),
                "config_path_guess": cfg_guess_str,
            }
        )

    with gaps_by_group_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=group_fields)
        w.writeheader()
        for r in group_rows:
            w.writerow(r)

    # 4) Global coverage gaps by (model, prompt_id, thinking_mode, horn, maxlen): missing maxvars inside span
    # Read from metrics_by_bucket.csv and aggregate across run_id/experiment by summing total.
    present_mvs: Dict[Tuple[str, str, str, str, int, int], Set[int]] = defaultdict(set)
    # also track total counts for context
    cell_total: Dict[Tuple[str, str, str, str, int, int, int], int] = defaultdict(int)  # +maxvars
    prompt_style_by_id: Dict[str, str] = {}

    for r in metrics_bucket:
        provider = (r.get("provider") or "").strip()
        model = (r.get("model") or "").strip()
        thinking = (r.get("thinking_mode") or "").strip()
        prompt_id = (r.get("prompt_id") or "").strip()
        horn = safe_int(r.get("horn"))
        maxlen = safe_int(r.get("maxlen"))
        maxvars = safe_int(r.get("maxvars"))
        total = safe_int(r.get("total")) or 0
        if horn is None or maxlen is None or maxvars is None:
            continue
        if total <= 0:
            continue
        k = (provider, model, prompt_id, thinking, horn, maxlen)
        present_mvs[k].add(maxvars)
        cell_total[(provider, model, prompt_id, thinking, horn, maxlen, maxvars)] += total
        prompt_style_by_id.setdefault(prompt_id, (r.get("prompt_style") or "").strip())

    gaps_by_model_csv = gaps_dir / "gaps_by_model_prompt.csv"
    model_fields = [
        "provider",
        "model",
        "prompt_id",
        "prompt_style",
        "thinking_mode",
        "horn",
        "maxlen",
        "present_maxvars",
        "missing_maxvars_within_span",
        "missing_count",
        "present_count",
        "min_maxvars",
        "max_maxvars",
        "span_size",
        "missing_ratio",
        "gap_kind",
    ]

    model_rows: List[Dict[str, Any]] = []
    for k, mvs in sorted(present_mvs.items()):
        provider, model, prompt_id, thinking, horn, maxlen = k
        missing = _missing_within_span(mvs)
        if not missing:
            continue
        span_size = (max(mvs) - min(mvs) + 1) if mvs else 0
        missing_ratio = (len(missing) / span_size) if span_size > 0 else 0.0
        gap_kind = "internal_hole" if missing_ratio <= 0.5 else "sparse_span"
        model_rows.append(
            {
                "provider": provider,
                "model": model,
                "prompt_id": prompt_id,
                "prompt_style": prompt_style_by_id.get(prompt_id, ""),
                "thinking_mode": thinking,
                "horn": horn,
                "maxlen": maxlen,
                "present_maxvars": _fmt_int_ranges(mvs),
                "missing_maxvars_within_span": _fmt_int_ranges(missing),
                "missing_count": len(missing),
                "present_count": len(mvs),
                "min_maxvars": min(mvs) if mvs else "",
                "max_maxvars": max(mvs) if mvs else "",
                "span_size": span_size,
                "missing_ratio": f"{missing_ratio:.3f}",
                "gap_kind": gap_kind,
            }
        )

    with gaps_by_model_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=model_fields)
        w.writeheader()
        for r in model_rows:
            w.writerow(r)

    # 5) Run recommendations
    rec_md = gaps_dir / "run_recommendations.md"
    lines: List[str] = []
    lines.append("## Run recommendations (auto-generated)\n\n")
    lines.append(
        "This file proposes concrete next steps to fill gaps detected in historical results. "
        "It does **not** interpret performance; it only targets coverage/completeness.\n\n"
    )

    # A) Incomplete leaf runs within a group (missing rows vs expected)
    incomplete = [r for r in group_rows if int(r.get("missing_rows_vs_group", 0)) > 0]
    incomplete = sorted(incomplete, key=lambda r: int(r.get("missing_rows_vs_group", 0)), reverse=True)
    lines.append("### A) Resume incomplete leaf runs\n\n")
    if not incomplete:
        lines.append("No incomplete leaf runs detected (by rowcount vs group max).\n\n")
    else:
        lines.append("The following leaf runs have fewer rows than the maximum seen within their (experiment, run_id) group.\n\n")
        for r in incomplete[:50]:
            exp = r["experiment"]
            run_id = r["run_id"]
            provider = r.get("provider", "")
            model = r.get("model", "")
            thinking = r.get("thinking_mode", "")
            missing_rows = r.get("missing_rows_vs_group", "")
            cfg = r.get("config_path_guess", "")

            lines.append(f"- {exp} / {run_id} / {provider} / {model} / {thinking}: missing_rows={missing_rows}\n")
            if cfg:
                lines.append("  - Suggested command:\n\n")
                lines.append("```bash\n")
                lines.append(
                    f"venv/bin/python -m experiments.runner --config {Path(cfg).as_posix()} "
                    f"--run {run_id} --resume --only {provider} --models {provider}:{model}\n"
                )
                lines.append("```\n")
            else:
                lines.append("  - No config path guess available (non-standard experiment name/layout).\n")
        if len(incomplete) > 50:
            lines.append(f"\n(Showing top 50 by missing rows; total incomplete leaf runs: {len(incomplete)})\n\n")

    # B) Leaf runs with recorded API errors / empty outputs
    lines.append("\n### B) Leaf runs with API errors / empty outputs in provenance\n\n")
    noisy = []
    for r in group_rows:
        e = str(r.get("provenance_error_rows") or "").strip()
        z = str(r.get("provenance_full_text_empty_rows") or "").strip()
        if e.isdigit() and int(e) > 0:
            noisy.append((int(e), "errors", r))
        elif z.isdigit() and int(z) > 0:
            noisy.append((int(z), "empty_text", r))
    noisy = sorted(noisy, key=lambda t: t[0], reverse=True)
    if not noisy:
        lines.append("No provenance error/empty_text rows recorded in leaf_runs.csv.\n\n")
    else:
        lines.append("These runs recorded provider errors and/or empty full_text in provenance. Rerunning may improve completeness.\n\n")
        for count, kind, r in noisy[:50]:
            exp = r["experiment"]
            run_id = r["run_id"]
            provider = r.get("provider", "")
            model = r.get("model", "")
            thinking = r.get("thinking_mode", "")
            cfg = r.get("config_path_guess", "")
            lines.append(f"- {exp} / {run_id} / {provider} / {model} / {thinking}: {kind}={count}\n")
            if cfg:
                lines.append("  - Suggested command (rerun/resume):\n\n")
                lines.append("```bash\n")
                lines.append(
                    f"venv/bin/python -m experiments.runner --config {Path(cfg).as_posix()} "
                    f"--run {run_id} --resume --only {provider} --models {provider}:{model}\n"
                )
                lines.append("```\n")
        if len(noisy) > 50:
            lines.append(f"\n(Showing top 50 by count; total flagged leaf runs: {len(noisy)})\n\n")

    # C) Global internal-span holes (missing maxvars within min..max for some condition)
    lines.append("\n### C) Global internal-span holes (missing maxvars within observed span)\n\n")
    lines.append(
        "The following rows indicate that, for a given (model, prompt_id, thinking_mode, horn, maxlen), "
        "some maxvars values within the observed min..max range are missing. These are good targets for "
        "**resume/rerun** if they were caused by interruptions.\n\n"
    )
    internal = [r for r in model_rows if r.get("gap_kind") == "internal_hole"]
    sparse = [r for r in model_rows if r.get("gap_kind") == "sparse_span"]
    for r in internal[:80]:
        lines.append(
            f"- {r['provider']}/{r['model']} prompt={r['prompt_id']} thinking={r['thinking_mode'] or 'n/a'} "
            f"horn={r['horn']} maxlen={r['maxlen']}: missing_maxvars={r['missing_maxvars_within_span']}\n"
        )
    if len(internal) > 80:
        lines.append(f"\n(Showing first 80 rows; total rows with internal-span holes: {len(internal)})\n\n")
    if sparse:
        lines.append(
            f"\nNote: {len(sparse)} additional rows are classified as `sparse_span` (many missing values across a large span), "
            "which often reflects intentionally separate datasets (e.g., vars10/vars20/vars30) rather than an interrupted run.\n\n"
        )

    rec_md.write_text("".join(lines), encoding="utf-8")

    print(f"Wrote:\n- {gaps_by_group_csv}\n- {gaps_by_model_csv}\n- {rec_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


