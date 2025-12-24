#!/usr/bin/env python3
"""
Render paper figures (PDF reports + PNGs) from aggregated metrics.

Figures are per model (provider+model), with sections per prompt_id, and a facet grid by thinking_mode.
Within each prompt_id we render three pages:
  - overall accuracy
  - SAT accuracy
  - UNSAT accuracy
Optionally: unclear_rate
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import textwrap
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

import matplotlib
matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402


@dataclass
class Counts:
    total: int = 0
    correct: int = 0
    unclear: int = 0
    sat_total: int = 0
    sat_correct: int = 0
    unsat_total: int = 0
    unsat_correct: int = 0


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


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_metrics_by_bucket(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


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


def _pick_example(prompt_examples: Dict[str, Any], prompt_id: str) -> Optional[Dict[str, Any]]:
    """
    Choose a compact example statement block for the prompt panel.
    Preference: horn=1 low, else horn=0 low, else any mid.
    """
    ex = prompt_examples.get(prompt_id)
    if not isinstance(ex, dict):
        return None
    for horn_key in ["1", "0"]:
        if horn_key in ex and isinstance(ex[horn_key], dict) and "low" in ex[horn_key]:
            return {"horn": int(horn_key), "level": "low", **ex[horn_key]["low"]}
    # fallback
    for horn_key, hv in ex.items():
        if isinstance(hv, dict) and "mid" in hv:
            return {"horn": int(horn_key), "level": "mid", **hv["mid"]}
    return None


def _truncate_lines(text: str, max_lines: int) -> str:
    lines = (text or "").splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[:max_lines] + ["..."])


def _wrap_block(text: str, width: int, max_lines: int) -> str:
    """
    Wrap a multi-line block to a fixed width (best-effort) and cap lines.
    Preserves existing line breaks but wraps long lines to avoid overlapping subpanels.
    """
    out_lines: List[str] = []
    for ln in (text or "").splitlines():
        ln = ln.rstrip()
        if not ln:
            out_lines.append("")
            continue
        out_lines.extend(textwrap.wrap(ln, width=width, break_long_words=False, replace_whitespace=False) or [ln])
        if len(out_lines) >= max_lines:
            break
    if len(out_lines) >= max_lines:
        out_lines = out_lines[: max_lines - 1] + ["..."]
    return "\n".join(out_lines)


def _metric_value(c: Counts, metric: str) -> float:
    if metric == "accuracy":
        return (c.correct / c.total) if c.total > 0 else math.nan
    if metric == "sat_accuracy":
        return (c.sat_correct / c.sat_total) if c.sat_total > 0 else math.nan
    if metric == "unsat_accuracy":
        return (c.unsat_correct / c.unsat_total) if c.unsat_total > 0 else math.nan
    if metric == "unclear_rate":
        return (c.unclear / c.total) if c.total > 0 else math.nan
    return math.nan


def main() -> int:
    ap = argparse.ArgumentParser(description="Render per-model PDF+PNG figures from metrics")
    ap.add_argument("--data-dir", default="experiments/paper_outputs/data", help="Data directory")
    ap.add_argument("--out-dir", default="experiments/paper_outputs", help="Output directory root")
    ap.add_argument("--include-unclear", action="store_true", help="Also render unclear_rate pages")
    ap.add_argument("--max-models", type=int, default=None, help="Limit number of models (debug)")
    args = ap.parse_args()

    data_dir = Path(args.data_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    figs_dir = out_dir / "figures"
    pdf_dir = figs_dir / "model_reports"
    png_dir = figs_dir / "png"
    _ensure_dir(pdf_dir)
    _ensure_dir(png_dir)

    metrics_path = data_dir / "metrics_by_bucket.csv"
    prompt_index = _load_json(data_dir / "prompt_index.json")
    prompt_examples = _load_json(data_dir / "prompt_examples.json")

    rows = _load_metrics_by_bucket(metrics_path)

    # Aggregate across (experiment, run_id) by summing counts for same cell.
    # Key: (provider, model, prompt_id, thinking_mode, horn, maxvars, maxlen)
    agg: Dict[Tuple[str, str, str, str, int, int, int], Counts] = defaultdict(Counts)
    prompt_meta: Dict[str, Dict[str, str]] = {}
    model_prompt_thinking_horns: Dict[Tuple[str, str, str], Dict[str, set]] = defaultdict(lambda: {"thinking": set(), "horn": set(), "maxvars": set(), "maxlen": set()})

    for r in rows:
        provider = (r.get("provider") or "").strip()
        model = (r.get("model") or "").strip()
        thinking = (r.get("thinking_mode") or "").strip()
        prompt_id = (r.get("prompt_id") or "").strip()

        horn = _int(r.get("horn"))
        mv = _int(r.get("maxvars"))
        ml = _int(r.get("maxlen"))
        if horn is None or mv is None or ml is None:
            continue

        key = (provider, model, prompt_id, thinking, horn, mv, ml)
        c = agg[key]
        c.total += int(_float(r.get("total")) or 0)
        c.correct += int(_float(r.get("correct")) or 0)
        c.unclear += int(_float(r.get("unclear")) or 0)
        c.sat_total += int(_float(r.get("sat_total")) or 0)
        c.sat_correct += int(_float(r.get("sat_correct")) or 0)
        c.unsat_total += int(_float(r.get("unsat_total")) or 0)
        c.unsat_correct += int(_float(r.get("unsat_correct")) or 0)

        prompt_meta.setdefault(
            prompt_id,
            {
                "prompt_template": (r.get("prompt_template") or "").strip(),
                "prompt_style": (r.get("prompt_style") or "").strip(),
                "parse_family": (r.get("parse_family") or "").strip(),
            },
        )

        mph = model_prompt_thinking_horns[(provider, model, prompt_id)]
        mph["thinking"].add(thinking)
        mph["horn"].add(horn)
        mph["maxvars"].add(mv)
        mph["maxlen"].add(ml)

    # Determine models present
    models = sorted({(p, m) for (p, m, _pid) in {(k[0], k[1], k[2]) for k in agg.keys()}})
    if args.max_models is not None:
        models = models[: args.max_models]

    # Consistent colormap for accuracy-like metrics
    cmap_acc = plt.get_cmap("viridis")
    cmap_unclear = plt.get_cmap("magma")

    for provider, model in models:
        # Collect prompt_ids for this model
        prompt_ids = sorted({k[2] for k in agg.keys() if k[0] == provider and k[1] == model})
        if not prompt_ids:
            continue

        model_slug = _safe_filename(f"{provider}__{model}")
        model_png_dir = png_dir / model_slug
        _ensure_dir(model_png_dir)

        pdf_path = pdf_dir / f"{model_slug}.pdf"
        with PdfPages(pdf_path) as pdf:
            for prompt_id in prompt_ids:
                pmeta = prompt_meta.get(prompt_id, {})
                # Metric pages: overall + SAT/UNSAT breakdown (satflag=1 vs satflag=0)
                metric_specs: List[Tuple[str, str]] = [
                    ("accuracy", "accuracy"),
                    ("sat_accuracy", "sat_accuracy"),
                    ("unsat_accuracy", "unsat_accuracy"),
                ]
                if args.include_unclear:
                    metric_specs.append(("unclear_rate", "unclear_rate"))

                pindex = prompt_index.get(prompt_id, {}) if isinstance(prompt_index, dict) else {}
                instr = (pindex.get("instruction_text") if isinstance(pindex, dict) else "") or ""
                instr = _truncate_lines(instr, max_lines=26)

                ex = _pick_example(prompt_examples, prompt_id)
                ex_block = ""
                ex_label = ""
                if ex and isinstance(ex, dict):
                    ex_block = _truncate_lines(ex.get("statements", ""), max_lines=18)
                    ex_label = f"Example (horn={ex.get('horn')}, {ex.get('level')}, maxvars={ex.get('maxvars')}, maxlen={ex.get('maxlen')}, satflag={ex.get('satflag')})"

                mph = model_prompt_thinking_horns.get((provider, model, prompt_id), {"thinking": set(), "horn": set(), "maxvars": set(), "maxlen": set()})
                thinking_modes = sorted([t for t in mph["thinking"] if t is not None])
                # Put empty thinking_mode (legacy) first
                if "" in thinking_modes:
                    thinking_modes = [""] + [t for t in thinking_modes if t != ""]
                horns = sorted(list(mph["horn"]))
                maxvars_vals = sorted(list(mph["maxvars"]))
                maxlen_vals = sorted(list(mph["maxlen"]))

                if not thinking_modes or not horns or not maxvars_vals or not maxlen_vals:
                    continue

                for metric, metric_slug in metric_specs:
                    fig = plt.figure(figsize=(16, 9), constrained_layout=False)
                    # Give the prompt panel more room, but keep heatmaps dominant.
                    gs = fig.add_gridspec(nrows=2, ncols=1, height_ratios=[1.6, 3.4])

                    # Prompt panel (two subpanels to avoid text overlap)
                    top = gs[0, 0].subgridspec(nrows=1, ncols=2, width_ratios=[1, 1], wspace=0.08)
                    ax_instr = fig.add_subplot(top[0, 0])
                    ax_ex = fig.add_subplot(top[0, 1])
                    for ax in (ax_instr, ax_ex):
                        ax.axis("off")

                    title = f"{provider}/{model} — {metric_slug} — {prompt_id} ({pmeta.get('prompt_style','')})"
                    ax_instr.text(0.0, 1.0, title, va="top", ha="left", fontsize=12, fontweight="bold")
                    ax_instr.text(
                        0.0,
                        0.86,
                        f"prompt_template={pmeta.get('prompt_template','')} | parse_family={pmeta.get('parse_family','')}",
                        va="top",
                        ha="left",
                        fontsize=9,
                    )
                    ax_instr.text(0.0, 0.76, "Instruction excerpt:", va="top", ha="left", fontsize=9, fontweight="bold")
                    if instr:
                        ax_instr.text(
                            0.0,
                            0.72,
                            _wrap_block(instr, width=78, max_lines=14),
                            va="top",
                            ha="left",
                            fontsize=7,
                            family="monospace",
                        )
                    else:
                        ax_instr.text(0.0, 0.72, "(no instruction text found)", va="top", ha="left", fontsize=7, family="monospace")

                    ex_title = ex_label or "Example statements:"
                    # Keep the example title short for layout.
                    if len(ex_title) > 110:
                        ex_title = ex_title[:107] + "..."
                    ax_ex.text(0.0, 1.0, ex_title, va="top", ha="left", fontsize=9, fontweight="bold")
                    if ex_block:
                        ax_ex.text(
                            0.0,
                            0.94,
                            _wrap_block(ex_block, width=78, max_lines=14),
                            va="top",
                            ha="left",
                            fontsize=7,
                            family="monospace",
                        )
                    else:
                        ax_ex.text(0.0, 0.94, "(no example statements found)", va="top", ha="left", fontsize=7, family="monospace")

                    fig.text(
                        0.05,
                        0.012,
                        "Full prompt text + more examples: experiments/paper_outputs/prompts/prompt_catalog.md",
                        va="bottom",
                        ha="left",
                        fontsize=8,
                        alpha=0.75,
                    )

                    # Heatmap grid
                    sub = gs[1, 0].subgridspec(nrows=len(horns), ncols=len(thinking_modes), wspace=0.15, hspace=0.25)
                    axs = []
                    mappable = None
                    vmin, vmax = (0.0, 1.0)
                    cmap = cmap_unclear if metric == "unclear_rate" else cmap_acc

                    for ri, horn in enumerate(horns):
                        for ci, thinking in enumerate(thinking_modes):
                            ax = fig.add_subplot(sub[ri, ci])
                            axs.append(ax)

                            mat = np.full((len(maxvars_vals), len(maxlen_vals)), np.nan, dtype=float)
                            total_n = 0
                            for yi, mv in enumerate(maxvars_vals):
                                for xi, ml in enumerate(maxlen_vals):
                                    c = agg.get((provider, model, prompt_id, thinking, horn, mv, ml))
                                    if not c or c.total <= 0:
                                        continue
                                    val = _metric_value(c, metric)
                                    mat[yi, xi] = val
                                    total_n += c.total

                            im = ax.imshow(
                                mat,
                                origin="lower",
                                aspect="auto",
                                vmin=vmin,
                                vmax=vmax,
                                cmap=cmap,
                            )
                            if mappable is None:
                                mappable = im

                            ax.set_xticks(range(len(maxlen_vals)))
                            ax.set_xticklabels([str(x) for x in maxlen_vals], fontsize=7)
                            ax.set_yticks(range(len(maxvars_vals)))
                            ax.set_yticklabels([str(y) for y in maxvars_vals], fontsize=7)

                            if ri == len(horns) - 1:
                                ax.set_xlabel("maxlen", fontsize=8)
                            if ci == 0:
                                ax.set_ylabel(f"maxvars (horn={horn})", fontsize=8)

                            thinking_label = thinking if thinking else "no_thinking_tag"
                            ax.set_title(f"{thinking_label} (n={total_n})", fontsize=8)

                    # Shared colorbar
                    if mappable is not None:
                        cbar = fig.colorbar(mappable, ax=axs, shrink=0.85, pad=0.02)
                        cbar.ax.tick_params(labelsize=8)
                        cbar.set_label(metric_slug, fontsize=9)

                    # Avoid tight_layout warnings with colorbars; use a light manual adjustment.
                    fig.subplots_adjust(left=0.05, right=0.98, top=0.96, bottom=0.06)

                    # Save to PDF and PNG
                    pdf.savefig(fig)
                    png_path = model_png_dir / f"{prompt_id}__{metric_slug}.png"
                    fig.savefig(png_path, dpi=300)
                    plt.close(fig)

        print(f"Wrote PDF: {pdf_path}")

    print(f"Figures written under: {figs_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


