#!/usr/bin/env python3
"""
Render condensed, cross-model figures for the paper.

Motivation:
  - The per-model heatmap PDFs are comprehensive but too verbose for main text.
  - Many heatmaps are sparse; line plots communicate sparse coverage better.

This script groups prompts into a small set of prompt families and renders
line charts: x=maxvars, y=accuracy, with separate panels for maxlen. Marker size
is proportional to sqrt(n) for the metric denominator, so sparse data is obvious.

Outputs (under --out-dir):
  - figures_condensed/condensed_reports/condensed__<family>.pdf
  - figures_condensed/png/<family>/*png
"""

from __future__ import annotations

import argparse
import math
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

from .common import iter_jsonl


PROVIDER_ORDER = ["anthropic", "google", "openai"]


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _safe_filename(s: str) -> str:
    keep = []
    for ch in s:
        if ch.isalnum() or ch in ("-", "_", "."):
            keep.append(ch)
        else:
            keep.append("_")
    return "".join(keep)


def _int(s: Optional[str]) -> Optional[int]:
    try:
        if s is None or s == "":
            return None
        return int(float(s))
    except Exception:
        return None


def _float(s: Optional[str]) -> Optional[float]:
    try:
        if s is None or s == "":
            return None
        return float(s)
    except Exception:
        return None


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_leaf_run_prompt_map(path: Path) -> Dict[str, str]:
    """
    Load results_relpath -> prompt_id mapping.
    """
    import csv

    m: Dict[str, str] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            rr = (r.get("results_relpath") or "").strip()
            pid = (r.get("prompt_id") or "").strip()
            if rr and pid:
                m[rr] = pid
    return m


def _prompt_family(prompt_id: str, prompt_index: Dict[str, Any]) -> str:
    meta = prompt_index.get(prompt_id, {})
    style = (meta.get("prompt_style") or "").strip()
    instr = (meta.get("instruction_text") or "").lower()

    # Special-case mismatch/unified-answer horn runs
    if style == "horn_if_then" and "unified answer rule" in instr:
        return "horn_unified_answer"

    if style == "horn_if_then":
        return "horn_if_then"
    if style == "cnf_v1":
        return "cnf_v1"
    if style == "cnf_v2":
        return "cnf_v2"
    return "other"


def _metric_denominator(row_counts: Dict[str, int], metric: str) -> int:
    if metric == "accuracy":
        return row_counts["total"]
    if metric == "sat_accuracy":
        return row_counts["sat_total"]
    if metric == "unsat_accuracy":
        return row_counts["unsat_total"]
    return row_counts["total"]


def _metric_value(row_counts: Dict[str, int], metric: str) -> float:
    if metric == "accuracy":
        d = row_counts["total"]
        return (row_counts["correct"] / d) if d > 0 else math.nan
    if metric == "sat_accuracy":
        d = row_counts["sat_total"]
        return (row_counts["sat_correct"] / d) if d > 0 else math.nan
    if metric == "unsat_accuracy":
        d = row_counts["unsat_total"]
        return (row_counts["unsat_correct"] / d) if d > 0 else math.nan
    return math.nan


def _segments_consecutive(xs: List[int]) -> List[List[int]]:
    if not xs:
        return []
    xs = sorted(xs)
    segs: List[List[int]] = [[xs[0]]]
    for x in xs[1:]:
        if x == segs[-1][-1] + 1:
            segs[-1].append(x)
        else:
            segs.append([x])
    return segs


def main() -> int:
    ap = argparse.ArgumentParser(description="Render condensed cross-model figures")
    ap.add_argument("--data-dir", default="experiments/paper_outputs/data", help="Data directory")
    ap.add_argument("--out-dir", default="experiments/paper_outputs", help="Output directory root")
    ap.add_argument(
        "--thinking",
        choices=["collapse_all", "nothink_only", "nothink_vs_thinking"],
        default="collapse_all",
        help="How to handle thinking_mode in condensed plots",
    )
    ap.add_argument("--min_n", type=int, default=0, help="Drop points with denominator n < min_n")
    args = ap.parse_args()

    data_dir = Path(args.data_dir).resolve()
    out_dir = Path(args.out_dir).resolve()

    reparsed_path = data_dir / "reparsed_rows.jsonl"
    leaf_run_prompt_map_path = data_dir / "leaf_run_prompt_map.csv"
    prompt_index = _load_json(data_dir / "prompt_index.json")

    out_root = out_dir / "figures_condensed"
    pdf_dir = out_root / "condensed_reports"
    png_dir = out_root / "png"
    _ensure_dir(pdf_dir)
    _ensure_dir(png_dir)

    # Aggregate counts across experiments/run_ids (and optionally across thinking modes).
    # We aggregate from reparsed_rows.jsonl so we can exclude provider-error rows (quota/rate_limit/etc),
    # which otherwise show up as misleading 0-accuracy points (they're "missing answers", not wrong answers).
    #
    # Key: (family, provider, model, thinking_bucket, horn, maxlen, maxvars)
    counts: Dict[Tuple[str, str, str, str, int, int, int], Dict[str, int]] = defaultdict(
        lambda: {
            "total": 0,
            "correct": 0,
            "unclear": 0,
            "sat_total": 0,
            "sat_correct": 0,
            "unsat_total": 0,
            "unsat_correct": 0,
            "error": 0,
        }
    )

    family_prompt_ids: Dict[str, set[str]] = defaultdict(set)

    def thinking_bucket(thinking_mode: str) -> str:
        t = (thinking_mode or "").strip()
        if args.thinking == "collapse_all":
            return "all"
        if args.thinking == "nothink_only":
            return "nothink" if (t == "" or t == "nothink") else "__drop__"
        if args.thinking == "nothink_vs_thinking":
            return "nothink" if (t == "" or t == "nothink") else "thinking"
        return "all"

    rr_to_prompt = _load_leaf_run_prompt_map(leaf_run_prompt_map_path)

    for r in iter_jsonl(reparsed_path):
        provider = (r.get("provider") or "").strip()
        model = (r.get("model") or "").strip()
        results_rel = (r.get("results_relpath") or "").strip()
        if not provider or not model or not results_rel:
            continue
        prompt_id = rr_to_prompt.get(results_rel, "")
        if not prompt_id:
            continue

        fam = _prompt_family(prompt_id, prompt_index)
        family_prompt_ids[fam].add(prompt_id)

        horn = _int(str(r.get("horn"))) if r.get("horn") is not None else None
        ml = _int(str(r.get("maxlen"))) if r.get("maxlen") is not None else None
        mv = _int(str(r.get("maxvars"))) if r.get("maxvars") is not None else None
        if horn is None or ml is None or mv is None:
            continue

        tb = thinking_bucket(r.get("thinking_mode") or "")
        if tb == "__drop__":
            continue

        key = (fam, provider, model, tb, horn, ml, mv)
        c = counts[key]

        has_error = bool((r.get("error") or "").strip())
        if has_error:
            # Count errors for transparency, but exclude from denominators
            c["error"] += 1
            continue

        c["total"] += 1
        if bool(r.get("is_unclear")):
            c["unclear"] += 1
        if bool(r.get("correct")):
            c["correct"] += 1

        sf = _int(str(r.get("satflag"))) if r.get("satflag") is not None else None
        if sf == 1:
            c["sat_total"] += 1
            if bool(r.get("correct")):
                c["sat_correct"] += 1
        elif sf == 0:
            c["unsat_total"] += 1
            if bool(r.get("correct")):
                c["unsat_correct"] += 1

    families = sorted(family_prompt_ids.keys())
    metrics = ["accuracy", "sat_accuracy", "unsat_accuracy"]

    for fam in families:
        fam_slug = _safe_filename(fam)
        fam_png_dir = png_dir / fam_slug
        _ensure_dir(fam_png_dir)

        prompt_ids = sorted(list(family_prompt_ids[fam]))
        prompt_ids_short = ", ".join(prompt_ids[:6]) + (" …" if len(prompt_ids) > 6 else "")

        pdf_path = pdf_dir / f"condensed__{fam_slug}.pdf"
        with PdfPages(pdf_path) as pdf:
            # Determine available thinking buckets for this family
            thinking_buckets = sorted({k[3] for k in counts.keys() if k[0] == fam})
            if not thinking_buckets:
                continue

            for tb in thinking_buckets:
                # Determine horn and maxlen coverage for this family+thinking
                horns = sorted({k[4] for k in counts.keys() if k[0] == fam and k[3] == tb})
                maxlens = sorted({k[5] for k in counts.keys() if k[0] == fam and k[3] == tb})
                providers = [p for p in PROVIDER_ORDER if any(k[1] == p for k in counts.keys() if k[0] == fam and k[3] == tb)]

                for horn in horns:
                    for metric in metrics:
                        fig = plt.figure(figsize=(16, 9), constrained_layout=False)
                        gs = fig.add_gridspec(nrows=2, ncols=1, height_ratios=[0.55, 3.45])

                        # Header
                        ax_hdr = fig.add_subplot(gs[0, 0])
                        ax_hdr.axis("off")
                        title = f"Condensed: family={fam} | thinking={tb} | horn={horn} | metric={metric}"
                        ax_hdr.text(0.0, 1.0, title, va="top", ha="left", fontsize=12, fontweight="bold")
                        ax_hdr.text(
                            0.0,
                            0.72,
                            "Line plots: x=maxvars, y=accuracy. Marker size ~ sqrt(n) for the metric denominator. "
                            "Line segments connect only consecutive maxvars values.",
                            va="top",
                            ha="left",
                            fontsize=9,
                        )
                        ax_hdr.text(
                            0.0,
                            0.42,
                            f"Aggregated across all runs (provider-error rows excluded). Prompt IDs included: {prompt_ids_short}",
                            va="top",
                            ha="left",
                            fontsize=8,
                        )
                        ax_hdr.text(
                            0.0,
                            0.12,
                            "Exact prompts: experiments/paper_outputs/prompts/prompt_catalog.md",
                            va="top",
                            ha="left",
                            fontsize=8,
                            alpha=0.75,
                        )

                        # Grid: provider rows × maxlen columns
                        sub = gs[1, 0].subgridspec(
                            nrows=max(1, len(providers)),
                            ncols=max(1, len(maxlens)),
                            wspace=0.25,
                            hspace=0.35,
                        )

                        for ri, provider in enumerate(providers):
                            # Collect models per provider
                            models = sorted({k[2] for k in counts.keys() if k[0] == fam and k[1] == provider and k[3] == tb and k[4] == horn})
                            colors = plt.get_cmap("tab10").colors
                            color_map = {m: colors[i % len(colors)] for i, m in enumerate(models)}

                            for ci, maxlen in enumerate(maxlens):
                                ax = fig.add_subplot(sub[ri, ci])
                                ax.set_ylim(0.0, 1.0)
                                ax.set_title(f"{provider} | maxlen={maxlen}", fontsize=9)
                                ax.grid(True, alpha=0.2, linewidth=0.5)
                                if ri == len(providers) - 1:
                                    ax.set_xlabel("maxvars", fontsize=9)
                                if ci == 0:
                                    ax.set_ylabel("accuracy", fontsize=9)

                                any_plotted = False

                                for m in models:
                                    xs: List[int] = []
                                    ys: List[float] = []
                                    ns: List[int] = []
                                    for mv in sorted({k[6] for k in counts.keys() if k[:6] == (fam, provider, m, tb, horn, maxlen)}):
                                        c = counts.get((fam, provider, m, tb, horn, maxlen, mv))
                                        if not c:
                                            continue
                                        den = _metric_denominator(c, metric)
                                        if den < args.min_n:
                                            continue
                                        y = _metric_value(c, metric)
                                        if math.isnan(y):
                                            continue
                                        xs.append(mv)
                                        ys.append(y)
                                        ns.append(den)

                                    if not xs:
                                        continue

                                    any_plotted = True
                                    # scatter points (size ~ sqrt(n))
                                    sizes = [12.0 + 3.0 * math.sqrt(max(1, n)) for n in ns]
                                    ax.scatter(xs, ys, s=sizes, color=color_map[m], alpha=0.7, linewidths=0.0)

                                    # connect consecutive segments
                                    for seg in _segments_consecutive(xs):
                                        if len(seg) < 2:
                                            continue
                                        idx = [xs.index(v) for v in seg]
                                        ax.plot([xs[i] for i in idx], [ys[i] for i in idx], color=color_map[m], alpha=0.6, linewidth=1.2)

                                # Legend once per provider row (first column)
                                if ci == 0 and models:
                                    ax.legend(
                                        models,
                                        fontsize=7,
                                        loc="upper left",
                                        frameon=False,
                                        ncol=1,
                                        title="models",
                                        title_fontsize=8,
                                    )

                                if not any_plotted:
                                    ax.text(0.5, 0.5, "no data", ha="center", va="center", fontsize=9, alpha=0.7)

                        fig.subplots_adjust(left=0.05, right=0.98, top=0.95, bottom=0.06)

                        pdf.savefig(fig)
                        png_name = _safe_filename(f"{fam}__{tb}__horn{horn}__{metric}.png")
                        fig.savefig(fam_png_dir / png_name, dpi=300)
                        plt.close(fig)

        print(f"Wrote condensed PDF: {pdf_path}")

    print(f"Condensed figures written under: {out_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


