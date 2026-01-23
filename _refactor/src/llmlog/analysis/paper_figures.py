from __future__ import annotations

import json
import hashlib
import math
import re
import time
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

try:
    # Force a non-interactive backend for CI and headless runs.
    import matplotlib

    matplotlib.use("Agg")  # must be set before pyplot import
    import matplotlib.pyplot as plt  # noqa: E402
except Exception as e:  # pragma: no cover
    raise SystemExit(
        "matplotlib is required to generate paper figures.\n"
        "Install dependencies with:\n"
        "  pip install -r _refactor/requirements.txt\n"
        f"Import error: {e}"
    ) from e

from llmlog.analysis.combined_dashboard import build_combined_dashboard_data  # noqa: E402


REP_LABEL: Mapping[str, str] = {
    "cnf_compact": "Compact CNF",
    "cnf_nl": "Natural Language CNF",
    "horn_if_then": "If-then CNF",
}

PROMPT_LABEL: Mapping[str, str] = {
    "examples_only": "examples-only",
    "horn_alg_from": "Horn alg (from)",
    "horn_alg_linear": "Horn alg (linear)",
    "dpll_alg_from": "DPLL (from)",
    "dpll_alg_linear": "DPLL (linear)",
}

SUBSET_LABEL: Mapping[int, str] = {
    1: "Horn",
    0: "Non-Horn",
}

# Consistent legend styling across all figures.
LEGEND_LOC = "lower right"
LEGEND_FONTSIZE = 8.5
LEGEND_KW = {
    "loc": LEGEND_LOC,
    "fontsize": LEGEND_FONTSIZE,
    "frameon": False,
    "borderaxespad": 0.2,
    "handlelength": 2.0,
    "labelspacing": 0.25,
    "handletextpad": 0.4,
    "columnspacing": 0.9,
}

# Stable, cross-figure target palette (match Figure 4 / cross-provider figure).
# Keys are "{provider}/{model}/{thinking_mode}" (using full model ids, not shortened labels).
TARGET_COLOR: Mapping[str, str] = {
    # Requested palette:
    # - Claude: orange
    # - Gemini Flash: yellow
    # - Gemini Pro: green
    # - GPT-5.2: red
    # - GPT-5.2-pro: blue
    "anthropic/claude-opus-4-5-20251101/think_none": "#ff7f0e",  # orange
    "google/gemini-3-flash-preview/think_minimal": "#f1c40f",  # yellow (gold)
    "google/gemini-3-pro-preview/think_high": "#2ca02c",  # green
    "openai/gpt-5.2-2025-12-11/think_none": "#d62728",  # red
    "openai/gpt-5.2-pro/think_high": "#1f77b4",  # blue
}


def _utc_now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _safe_int(x: Any) -> int:
    try:
        return int(x) if x is not None else 0
    except Exception:
        return 0


def _safe_float(x: Any) -> float:
    try:
        return float(x) if x is not None else 0.0
    except Exception:
        return 0.0


def _short_openai_model(model: str) -> str:
    """
    Make OpenAI model labels stable in plots.

    Examples:
    - "gpt-5.2-2025-12-11" -> "gpt-5.2"
    - "gpt-5.2-pro" -> "gpt-5.2-pro"
    """
    m = str(model or "")
    m = m.strip()
    m2 = re.match(r"^(gpt-\d+(?:\.\d+)?)(?:-\d{4}-\d{2}-\d{2})$", m)
    return m2.group(1) if m2 else m


def _pretty_series_label(series_field: str, raw_value: str) -> str:
    v = str(raw_value or "")
    if series_field == "representation":
        return REP_LABEL.get(v, v)
    if series_field == "prompt_label":
        return PROMPT_LABEL.get(v, v)
    return v


def _match_value(value: Any, allowed: Any) -> bool:
    if allowed is None:
        return True
    if allowed == "all":
        return True
    if isinstance(allowed, (list, tuple, set)):
        return any(_match_value(value, a) for a in allowed)
    if callable(allowed):
        try:
            return bool(allowed(value))
        except Exception:
            return False
    if isinstance(allowed, str):
        s = str(value)
        # Glob support: allow "gpt-5.2*" etc.
        if "*" in allowed or "?" in allowed:
            return fnmatch(s, allowed)
        return s == allowed
    return value == allowed


def _filter_groups(
    groups: Sequence[Dict[str, Any]],
    *,
    filters: Mapping[str, Any],
    exclude_run_regex: Optional[str] = None,
    exclude_suite_regex: Optional[str] = None,
) -> List[Dict[str, Any]]:
    rex_run = re.compile(exclude_run_regex, re.IGNORECASE) if exclude_run_regex else None
    rex_suite = re.compile(exclude_suite_regex, re.IGNORECASE) if exclude_suite_regex else None
    out: List[Dict[str, Any]] = []
    for g in groups:
        run = str(g.get("run") or "")
        suite = str(g.get("suite") or "")
        if rex_run and rex_run.search(run):
            continue
        if rex_suite and rex_suite.search(suite):
            continue
        ok = True
        for k, allowed in (filters or {}).items():
            if not _match_value(g.get(k), allowed):
                ok = False
                break
        if ok:
            out.append(g)
    return out


@dataclass
class AggCounts:
    total: int = 0
    pending: int = 0
    errors: int = 0
    answered: int = 0
    unclear: int = 0
    correct: int = 0
    attempts_total: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    cost_total_usd: float = 0.0
    cost_input_usd: float = 0.0
    cost_output_usd: float = 0.0
    reasoning_usd_estimate: float = 0.0
    latency_ms_sum: float = 0.0
    latency_n: int = 0

    def add_counts(self, d: Mapping[str, Any]) -> None:
        self.total += _safe_int(d.get("total"))
        self.pending += _safe_int(d.get("pending"))
        self.errors += _safe_int(d.get("errors"))
        self.answered += _safe_int(d.get("answered"))
        self.unclear += _safe_int(d.get("unclear"))
        self.correct += _safe_int(d.get("correct"))
        self.attempts_total += _safe_int(d.get("attempts_total"))
        self.input_tokens += _safe_int(d.get("input_tokens"))
        self.output_tokens += _safe_int(d.get("output_tokens"))
        self.reasoning_tokens += _safe_int(d.get("reasoning_tokens"))
        self.cache_creation_input_tokens += _safe_int(d.get("cache_creation_input_tokens"))
        self.cache_read_input_tokens += _safe_int(d.get("cache_read_input_tokens"))
        self.cost_total_usd += _safe_float(d.get("cost_total_usd"))
        self.cost_input_usd += _safe_float(d.get("cost_input_usd"))
        self.cost_output_usd += _safe_float(d.get("cost_output_usd"))
        self.reasoning_usd_estimate += _safe_float(d.get("reasoning_usd_estimate"))
        self.latency_ms_sum += _safe_float(d.get("latency_ms_sum"))
        self.latency_n += _safe_int(d.get("latency_n"))

    @property
    def denom_completed(self) -> int:
        return int(self.answered + self.unclear)

    @property
    def denom_nonpending(self) -> int:
        return int(self.total - self.pending)

    def accuracy(self, mode: str) -> Optional[float]:
        if mode == "answered":
            denom = int(self.answered)
        elif mode == "nonpending":
            denom = int(self.denom_nonpending)
        else:
            # default: completed
            denom = int(self.denom_completed)
        return (float(self.correct) / float(denom)) if denom > 0 else None

    def cost_per_correct_usd(self) -> Optional[float]:
        return (float(self.cost_total_usd) / float(self.correct)) if self.correct > 0 else None

    def reasoning_cost_per_correct_usd(self) -> Optional[float]:
        return (float(self.reasoning_usd_estimate) / float(self.correct)) if self.correct > 0 else None

    def latency_s_mean(self) -> Optional[float]:
        if self.latency_n <= 0:
            return None
        return (float(self.latency_ms_sum) / float(self.latency_n)) / 1000.0

    def cost_per_item_usd(self, mode: str) -> Optional[float]:
        """Average spend per item under a chosen denominator.

        - mode=nonpending: denom = total - pending (includes errors)
        - mode=completed: denom = answered + unclear (excludes errors)
        - mode=answered: denom = answered
        """
        if mode == "answered":
            denom = int(self.answered)
        elif mode == "nonpending":
            denom = int(self.denom_nonpending)
        else:
            denom = int(self.denom_completed)
        return (float(self.cost_total_usd) / float(denom)) if denom > 0 else None


def _aggregate_series(
    rows: Sequence[Dict[str, Any]],
    *,
    series_field: str,
    x_field: str,
    allowed_series: Optional[Sequence[str]] = None,
) -> Dict[str, Dict[float, AggCounts]]:
    """
    Return:
      series_name -> (x_value -> AggCounts)
    """
    allowed_set = set(allowed_series) if allowed_series else None
    out: Dict[str, Dict[float, AggCounts]] = {}
    for r in rows:
        sraw = str(r.get(series_field) or "unknown")
        if allowed_set is not None and sraw not in allowed_set:
            continue
        xv = r.get(x_field)
        if xv is None:
            continue
        try:
            x = float(xv)
        except Exception:
            continue
        cd = r.get("counts") or {}
        if not isinstance(cd, dict):
            continue
        per_series = out.get(sraw)
        if per_series is None:
            per_series = {}
            out[sraw] = per_series
        agg = per_series.get(x)
        if agg is None:
            agg = AggCounts()
            per_series[x] = agg
        agg.add_counts(cd)
    return out


def _series_order(actual: Sequence[str], preferred: Optional[Sequence[str]]) -> List[str]:
    if not preferred:
        return sorted(set(actual))
    pref = [p for p in preferred if p in actual]
    rest = sorted([a for a in set(actual) if a not in set(pref)])
    return pref + rest


def _plot_line_panel(
    ax: Any,
    *,
    rows: Sequence[Dict[str, Any]],
    series_field: str,
    x_field: str,
    y_metric: str,
    y_mode: str,
    min_trials: int = 1,
    show_ci95: bool = False,
    marker_size_by_trials: bool = False,
    show_markers: bool = False,
    show_chance_baseline: bool = True,
    annotate_overlap_y_values: Optional[Sequence[float]] = (0.5, 1.0),
    annotate_overlap_min_count: int = 2,
    annotate_overlap_tol: float = 1e-9,
    show_legend: bool = True,
    show_empty_message: bool = True,
    line_style: str = "-",
    color_map: Optional[Mapping[str, Any]] = None,
    label_map: Optional[Mapping[str, str]] = None,
    allowed_series: Optional[Sequence[str]] = None,
    preferred_series_order: Optional[Sequence[str]] = None,
    title: str,
    x_label: str,
    y_label: str,
    y_lim: Optional[Tuple[float, float]] = None,
    y_scale: str = "linear",
) -> Dict[str, Any]:
    def wilson95(k: int, n: int) -> Optional[Tuple[float, float]]:
        if n <= 0:
            return None
        # 95% normal approximation
        z = 1.959963984540054
        phat = float(k) / float(n)
        denom = 1.0 + (z * z) / float(n)
        center = (phat + (z * z) / (2.0 * float(n))) / denom
        half = (
            z
            * math.sqrt((phat * (1.0 - phat) + (z * z) / (4.0 * float(n))) / float(n))
            / denom
        )
        lo = max(0.0, center - half)
        hi = min(1.0, center + half)
        return (lo, hi)

    def trials_for_point(c: AggCounts) -> Optional[int]:
        if y_metric != "accuracy":
            return None
        if y_mode == "answered":
            return int(c.answered)
        if y_mode == "nonpending":
            return int(c.denom_nonpending)
        return int(c.denom_completed)

    series_map = _aggregate_series(rows, series_field=series_field, x_field=x_field, allowed_series=allowed_series)
    series_names = _series_order(list(series_map.keys()), preferred_series_order)

    # Add a chance baseline for balanced binary decisions (accuracy only).
    if show_chance_baseline and y_metric == "accuracy":
        if not getattr(ax, "_llmlog_has_chance_baseline", False):
            ax.axhline(0.5, color="#718096", lw=1.0, linestyle="--", alpha=0.35, zorder=0, label="_chance")
            setattr(ax, "_llmlog_has_chance_baseline", True)

    # Marker shapes to help distinguish overlapping series.
    # (We keep SAT vs UNSAT distinguished by line style in the calling overlay helper.)
    if series_field == "representation":
        marker_map = {"cnf_compact": "o", "cnf_nl": "s", "horn_if_then": "^"}
    elif series_field == "prompt_label":
        marker_map = {
            "examples_only": "o",
            "horn_alg_from": "s",
            "horn_alg_linear": "^",
            "dpll_alg_from": "s",
            "dpll_alg_linear": "^",
        }
    else:
        marker_cycle = ["o", "s", "^", "D", "v", "<", ">", "p", "h", "*"]
        marker_map = {s: marker_cycle[i % len(marker_cycle)] for i, s in enumerate(series_names)}

    # Reduce overplotting by applying a small, consistent x-offset ("dodge") per series.
    # This preserves ordering while making coincident 0/1 (or identical) lines visible.
    uniq_xs: List[float] = sorted({float(x) for pts in series_map.values() for x in pts.keys()})
    x_step = None
    if len(uniq_xs) >= 2:
        diffs = [b - a for a, b in zip(uniq_xs, uniq_xs[1:]) if (b - a) > 0]
        x_step = min(diffs) if diffs else None
    if x_step is None:
        x_step = 1.0
    span = float(x_step) * 0.08  # e.g. 10 -> 0.8
    if len(series_names) <= 1:
        x_offset_map = {series_names[0]: 0.0} if series_names else {}
    else:
        step = (2.0 * span) / float(len(series_names) - 1)
        x_offset_map = {s: (-span + float(i) * step) for i, s in enumerate(series_names)}

    all_trials: List[int] = []
    if marker_size_by_trials and y_metric == "accuracy":
        for pts in series_map.values():
            for c in pts.values():
                t = trials_for_point(c)
                if t is not None and t >= int(min_trials):
                    all_trials.append(int(t))
    max_trials = max(all_trials) if all_trials else 0

    plotted = 0
    for s in series_names:
        pts = series_map.get(s) or {}
        xs = sorted(pts.keys())
        ys: List[float] = []
        xsv: List[float] = []
        yerr_lo: List[float] = []
        yerr_hi: List[float] = []
        tsv: List[int] = []
        for x in xs:
            c = pts[x]
            if y_metric == "accuracy":
                trials = trials_for_point(c)
                if trials is not None and int(trials) < int(min_trials):
                    continue
                y = c.accuracy(y_mode)
            elif y_metric == "cost_per_correct_usd":
                y = c.cost_per_correct_usd()
            elif y_metric == "cost_per_item_usd":
                y = c.cost_per_item_usd(y_mode)
            elif y_metric == "cost_total_usd":
                y = float(c.cost_total_usd)
            elif y_metric == "reasoning_cost_per_correct_usd":
                y = c.reasoning_cost_per_correct_usd()
            elif y_metric == "latency_s_mean":
                y = c.latency_s_mean()
            else:
                y = None
            if y is None or (isinstance(y, float) and (math.isnan(y) or math.isinf(y))):
                continue
            xsv.append(float(x))
            ys.append(float(y))
            if y_metric == "accuracy":
                trials = trials_for_point(c) or 0
                tsv.append(int(trials))
                if show_ci95:
                    ci = wilson95(int(c.correct), int(trials))
                    if ci is None:
                        yerr_lo.append(0.0)
                        yerr_hi.append(0.0)
                    else:
                        lo, hi = ci
                        yerr_lo.append(max(0.0, float(y) - lo))
                        yerr_hi.append(max(0.0, hi - float(y)))
        if not xsv:
            continue
        label = (label_map or {}).get(s) if label_map and s in label_map else _pretty_series_label(series_field, s)
        color = (color_map or {}).get(s) if color_map else None
        xoff = float(x_offset_map.get(s, 0.0))
        xsv2 = [float(x) + xoff for x in xsv]
        (line,) = ax.plot(xsv2, ys, linewidth=2.0, linestyle=line_style, color=color, label=label)
        color = line.get_color()
        if show_ci95 and y_metric == "accuracy" and yerr_lo and yerr_hi and len(yerr_lo) == len(xsv):
            ax.errorbar(
                xsv2,
                ys,
                yerr=[yerr_lo, yerr_hi],
                fmt="none",
                ecolor=color,
                elinewidth=1.0,
                alpha=0.55,
                capsize=2,
            )
        if y_metric == "accuracy" and show_markers:
            marker = marker_map.get(s, "o")
            if marker_size_by_trials and max_trials > 0 and tsv and len(tsv) == len(xsv):
                # Scale marker areas (s) so low-N points are visibly smaller.
                s_min = 18.0
                s_max = 70.0
                sizes = []
                for t in tsv:
                    frac = max(0.0, min(1.0, float(t) / float(max_trials)))
                    sizes.append(s_min + (s_max - s_min) * frac)
                ax.scatter(
                    xsv2,
                    ys,
                    s=sizes,
                    marker=marker,
                    facecolors="none",
                    edgecolors=color,
                    linewidths=1.6,
                    alpha=0.95,
                    zorder=3,
                )
            else:
                ax.scatter(
                    xsv2,
                    ys,
                    s=42.0,
                    marker=marker,
                    facecolors="none",
                    edgecolors=color,
                    linewidths=1.6,
                    alpha=0.95,
                    zorder=3,
                )
        plotted += 1

    # If many series sit exactly at the chance level, they will perfectly overlap.
    # Add a small multiplicity annotation so the reader knows there are multiple coincident lines.
    if (
        y_metric == "accuracy"
        and annotate_overlap_y_values
        and series_names
        and uniq_xs
    ):
        # Allow one overlap annotation per (metric,line_style) on a given axis.
        key = f"{y_metric}:{line_style}"
        annotated = getattr(ax, "_llmlog_overlap_annotated_keys", set())
        if key not in annotated:
            for y_target in [float(y) for y in (annotate_overlap_y_values or [])]:
                best_x: Optional[float] = None
                best_n = 0
                for x in uniq_xs:
                    n_at = 0
                    for s in series_names:
                        c = (series_map.get(s) or {}).get(float(x))
                        if c is None:
                            continue
                        trials = trials_for_point(c)
                        if trials is not None and int(trials) < int(min_trials):
                            continue
                        yv = c.accuracy(y_mode)
                        if yv is None:
                            continue
                        if abs(float(yv) - float(y_target)) <= float(annotate_overlap_tol):
                            n_at += 1
                    # Prefer the rightmost x on ties so the annotation sits away from the y-axis.
                    if n_at > best_n or (n_at == best_n and best_x is not None and float(x) > float(best_x)):
                        best_n = int(n_at)
                        best_x = float(x)

                if best_x is None or best_n < int(annotate_overlap_min_count):
                    continue

                # Place label slightly offset from the overlapped value.
                if y_target >= 0.95:
                    y_annot = float(y_target) - 0.05
                    va = "top"
                else:
                    y_annot = float(y_target) + 0.03
                    va = "bottom"
                x_annot = float(best_x) + float(x_step) * 0.15

                ax.text(
                    x_annot,
                    y_annot,
                    f"×{best_n}",
                    ha="left",
                    va=va,
                    fontsize=9,
                    color="#2d3748",
                    bbox={"facecolor": "white", "alpha": 0.65, "edgecolor": "none", "pad": 0.25},
                    zorder=6,
                )

            annotated.add(key)
            setattr(ax, "_llmlog_overlap_annotated_keys", annotated)

    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(True, alpha=0.25)
    ax.set_yscale(y_scale)
    if y_lim is not None:
        ax.set_ylim(*y_lim)
    if plotted > 0:
        if show_legend:
            ax.legend(**LEGEND_KW)
    else:
        if show_empty_message:
            # Avoid "mysteriously empty" panels: explain why nothing was plotted.
            ax.text(
                0.02,
                0.98,
                "No plottable points\n(after filters / metric undefined)",
                transform=ax.transAxes,
                ha="left",
                va="top",
                fontsize=9,
                color="#4a5568",
            )
    if plotted > 0 and y_metric == "accuracy":
        notes: List[str] = []
        if show_ci95:
            notes.append("95% CI")
        if marker_size_by_trials:
            notes.append("marker size ∝ N")
        if notes:
            ax.text(
                0.02,
                0.02,
                " · ".join(notes),
                transform=ax.transAxes,
                ha="left",
                va="bottom",
                fontsize=8.5,
                color="#4a5568",
            )

    return {
        "series": series_names,
        "plotted_series": plotted,
        "total_rows": len(rows),
    }


def _save_paper_figure(fig: Any, out_path: Path, *, dpi: int = 200) -> None:
    """Save the paper PDF plus a small PNG thumbnail for quick viewing."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, bbox_inches="tight")

    thumbs_dir = out_path.parent / "_thumbs"
    thumbs_dir.mkdir(parents=True, exist_ok=True)
    thumb_path = thumbs_dir / f"{out_path.name}.png"  # e.g., fig_x.pdf.png
    fig.savefig(thumb_path, bbox_inches="tight", dpi=dpi)


def _make_color_map(keys: Sequence[str]) -> Dict[str, Any]:
    uniq = list(dict.fromkeys([str(k) for k in keys if k is not None]))
    if not uniq:
        return {}
    cmap = plt.get_cmap("tab20" if len(uniq) > 10 else "tab10")
    out: Dict[str, Any] = {}
    for i, k in enumerate(uniq):
        out[k] = cmap(i % cmap.N)
    return out


def _make_target_color_map(keys: Sequence[str]) -> Dict[str, Any]:
    """Color-map for target series keys, stable across figures."""
    uniq = list(dict.fromkeys([str(k) for k in keys if k is not None]))
    if not uniq:
        return {}

    cmap = plt.get_cmap("tab20")

    out: Dict[str, Any] = {}
    for k in uniq:
        if k in TARGET_COLOR:
            out[k] = TARGET_COLOR[k]
            continue
        # Deterministic fallback (stable across runs / subsets of keys).
        h = hashlib.md5(k.encode("utf-8")).hexdigest()
        idx = int(h[:8], 16) % int(cmap.N)
        out[k] = cmap(int(idx))
    return out


def _tint(color: Any, t: float) -> Any:
    """Blend a color toward white by factor t in [0,1]."""
    from matplotlib.colors import to_rgb  # type: ignore

    tt = max(0.0, min(1.0, float(t)))
    r, g, b = to_rgb(color)
    return (r + (1.0 - r) * tt, g + (1.0 - g) * tt, b + (1.0 - b) * tt)


def _dedupe_legend(handles: Sequence[Any], labels: Sequence[str]) -> Tuple[List[Any], List[str]]:
    seen: Set[str] = set()
    out_h: List[Any] = []
    out_l: List[str] = []
    for h, l in zip(handles, labels):
        if not l or l.startswith("_"):
            continue
        if l in seen:
            continue
        seen.add(l)
        out_h.append(h)
        out_l.append(l)
    return out_h, out_l


def _subset_style_handles() -> Tuple[List[Any], List[str]]:
    """Legend handles for Horn vs Non-Horn line styles."""
    from matplotlib.lines import Line2D  # type: ignore

    handles = [
        Line2D([0], [0], color="#1a202c", lw=2.0, linestyle="-", label="Horn"),
        Line2D([0], [0], color="#1a202c", lw=2.0, linestyle="--", label="Non-Horn"),
    ]
    labels = [h.get_label() for h in handles]
    return handles, labels


def _apply_legend(ax: Any, handles: Sequence[Any], labels: Sequence[str], *, ncol: int = 1) -> None:
    if not handles or not labels:
        return
    kw = dict(LEGEND_KW)
    kw["ncol"] = int(ncol)
    ax.legend(handles, labels, **kw)


def _apply_usd_axis_format(ax: Any) -> None:
    """Format a y-axis with USD tick labels (works well on log axes)."""
    from matplotlib.ticker import FuncFormatter  # type: ignore

    def fmt(y: float, _pos: int) -> str:
        try:
            v = float(y)
        except Exception:
            return ""
        if v <= 0.0 or math.isnan(v) or math.isinf(v):
            return ""
        if v >= 1.0:
            return f"${v:g}"
        if v >= 0.01:
            return f"${v:.2f}"
        if v >= 0.001:
            return f"${v:.3f}"
        # sub-cent: show cents
        return f"{v * 100.0:.2f}¢"

    ax.yaxis.set_major_formatter(FuncFormatter(fmt))


def _plot_accuracy_subset_overlay(
    ax: Any,
    *,
    groups: Sequence[Dict[str, Any]],
    base_filters: Mapping[str, Any],
    series_field: str,
    x_field: str,
    y_mode: str,
    exclude_run_regex: Optional[str],
    series_color_map: Optional[Mapping[str, Any]] = None,
    allowed_series_horn: Optional[Sequence[str]] = None,
    allowed_series_nonhorn: Optional[Sequence[str]] = None,
    preferred_series_order: Optional[Sequence[str]] = None,
    min_trials: int = 1,
    show_ci95: bool = True,
    marker_size_by_trials: bool = True,
    show_legend: bool = False,
    label_map: Optional[Mapping[str, str]] = None,
    title: str = "",
    x_label: str = "# vars (n)",
    y_label: str = "Accuracy",
) -> Dict[str, Any]:
    """Plot overall accuracy with Horn vs Non-Horn overlaid.

    Legend labels are explicit (e.g., "Horn Compact CNF", "Non-Horn Compact CNF") so the reader does not have to
    combine a separate subset key (line style) with a separate series key (color/marker).
    """
    horn_rows = _filter_groups(
        groups,
        filters={**dict(base_filters), "horn": 1},
        exclude_run_regex=exclude_run_regex,
    )
    nonhorn_rows = _filter_groups(
        groups,
        filters={**dict(base_filters), "horn": 0},
        exclude_run_regex=exclude_run_regex,
    )

    # Colors are keyed only by the series field (e.g., representation or prompt_label).
    series_vals = sorted({str(r.get(series_field) or "unknown") for r in (horn_rows + nonhorn_rows)})
    color_map = _make_color_map(series_vals)
    if series_color_map:
        for k, v in series_color_map.items():
            if k in color_map:
                color_map[k] = v

    meta: Dict[str, Any] = {"horn_rows": len(horn_rows), "nonhorn_rows": len(nonhorn_rows)}

    def base_label(s: str) -> str:
        return (label_map or {}).get(s) if label_map and s in label_map else _pretty_series_label(series_field, s)

    horn_label_map = {s: f"Horn {base_label(s)}" for s in series_vals}
    nonhorn_label_map = {s: f"Non-Horn {base_label(s)}" for s in series_vals}

    meta["horn"] = _plot_line_panel(
        ax,
        rows=horn_rows,
        series_field=series_field,
        x_field=x_field,
        y_metric="accuracy",
        y_mode=y_mode,
        min_trials=min_trials,
        show_ci95=show_ci95,
        marker_size_by_trials=marker_size_by_trials,
        show_legend=False,
        show_empty_message=False,
        line_style="-",
        color_map=color_map,
        label_map=horn_label_map,
        allowed_series=allowed_series_horn,
        preferred_series_order=preferred_series_order,
        title=title,
        x_label=x_label,
        y_label=y_label,
        y_lim=(-0.05, 1.05),
        y_scale="linear",
    )
    meta["nonhorn"] = _plot_line_panel(
        ax,
        rows=nonhorn_rows,
        series_field=series_field,
        x_field=x_field,
        y_metric="accuracy",
        y_mode=y_mode,
        min_trials=min_trials,
        show_ci95=show_ci95,
        marker_size_by_trials=marker_size_by_trials,
        show_legend=False,
        show_empty_message=False,
        line_style="--",
        color_map=color_map,
        label_map=nonhorn_label_map,
        allowed_series=allowed_series_nonhorn,
        preferred_series_order=preferred_series_order,
        title=title,
        x_label=x_label,
        y_label=y_label,
        y_lim=(-0.05, 1.05),
        y_scale="linear",
    )
    # Avoid confusing "empty panel" notes when only one subset is present.
    horn_plotted = bool(meta["horn"].get("plotted_series", 0))
    nonhorn_plotted = bool(meta["nonhorn"].get("plotted_series", 0))
    if not horn_plotted and not nonhorn_plotted:
        ax.text(
            0.02,
            0.98,
            "No plottable points\n(after filters / metric undefined)",
            transform=ax.transAxes,
            ha="left",
            va="top",
            fontsize=9,
            color="#4a5568",
        )
    elif horn_plotted and not nonhorn_plotted:
        msg = "Non-Horn: not run" if len(nonhorn_rows) == 0 else "Non-Horn: filtered / metric undefined"
        ax.text(0.02, 0.98, msg, transform=ax.transAxes, ha="left", va="top", fontsize=9, color="#4a5568")
    elif nonhorn_plotted and not horn_plotted:
        msg = "Horn: not run" if len(horn_rows) == 0 else "Horn: filtered / metric undefined"
        ax.text(0.02, 0.98, msg, transform=ax.transAxes, ha="left", va="top", fontsize=9, color="#4a5568")
    if show_legend:
        handles, labels = ax.get_legend_handles_labels()
        label_to_handle = {l: h for h, l in zip(handles, labels) if l and not l.startswith("_")}

        ordered: List[str] = []
        for s in _series_order(series_vals, preferred_series_order):
            hl = horn_label_map.get(s, f"Horn {base_label(s)}")
            nl = nonhorn_label_map.get(s, f"Non-Horn {base_label(s)}")
            if hl in label_to_handle:
                ordered.append(hl)
            if nl in label_to_handle:
                ordered.append(nl)

        _apply_legend(ax, [label_to_handle[l] for l in ordered], ordered, ncol=1)
    return meta


def _figure_representation_effects(
    groups: Sequence[Dict[str, Any]], *, out_path: Path, accuracy_mode: str, exclude_run_regex: str
) -> Dict[str, Any]:
    """Representation effects (controlled target; Horn vs Non-Horn overlay)."""
    # Controlled target: OpenAI gpt-5.2-pro (think_high).
    base = {
        "provider": "openai",
        "model": "gpt-5.2-pro",
        "thinking_mode": "think_high",
        "prompt_label": "examples_only",
        # Include the baseline grid and (when present) extended-n slices.
        "maxvars": [10, 20, 30, 40, 50, 60, 80, 100],
    }
    # Use the model's global base color, then create representation-specific tints.
    base_key = f"{base['provider']}/{base['model']}/{base['thinking_mode']}"
    base_color = _make_target_color_map([str(base_key)]).get(str(base_key), "#4a5568")
    rep_tints = {"cnf_compact": 0.0, "cnf_nl": 0.45, "horn_if_then": 0.7}
    rep_color_map = {k: _tint(base_color, t) for k, t in rep_tints.items()}
    # Paper simplification: show k=3 only (k=4/5 adds little given current coverage).
    lens = [3]
    fig, axes = plt.subplots(1, len(lens), figsize=(6.6, 3.6), sharex=True, sharey=True)
    if len(lens) == 1:
        axes = [axes]
    meta: Dict[str, Any] = {
        "figure": "representation_effects",
        "output": str(out_path),
        "layout": {"rows": "combined subset", "cols": "maxlen"},
    }

    for j, maxlen in enumerate(lens):
        ax = axes[j]
        show_legend = True
        title = f"k={maxlen}"
        m = _plot_accuracy_subset_overlay(
            ax,
            groups=groups,
            base_filters={**base, "maxlen": int(maxlen)},
            series_field="representation",
            x_field="maxvars",
            y_mode=accuracy_mode,
            exclude_run_regex=exclude_run_regex,
            series_color_map=rep_color_map,
            preferred_series_order=["cnf_compact", "cnf_nl", "horn_if_then"],
            min_trials=3,
            show_ci95=False,
            marker_size_by_trials=False,
            show_legend=show_legend,
            title=title,
            x_label="# vars (n)",
            y_label=f"Accuracy ({accuracy_mode})" if j == 0 else "",
        )
        meta[f"{maxlen}"] = m

    fig.suptitle("Representation effects (OpenAI · gpt-5.2-pro · think=high · examples-only; k=3)")
    fig.tight_layout()
    _save_paper_figure(fig, out_path)
    plt.close(fig)
    return meta


def _figure_prompting_effects(
    groups: Sequence[Dict[str, Any]], *, out_path: Path, accuracy_mode: str, exclude_run_regex: str
) -> Dict[str, Any]:
    """Prompting-policy effects (controlled target; Horn vs Non-Horn overlay)."""
    # Controlled target: OpenAI gpt-5.2-pro (think_high). Representation fixed to cnf_compact to isolate prompting.
    base = {
        "provider": "openai",
        "model": "gpt-5.2-pro",
        "thinking_mode": "think_high",
        "representation": "cnf_compact",
        # Include the baseline grid and (when present) extended-n slices.
        "maxvars": [10, 20, 30, 40, 50, 60, 80, 100],
    }
    # Use the model's global base color, then create prompt-type tints.
    base_key = f"{base['provider']}/{base['model']}/{base['thinking_mode']}"
    base_color = _make_target_color_map([str(base_key)]).get(str(base_key), "#4a5568")
    prompt_tints = {
        "examples_only": 0.0,
        "horn_alg_linear": 0.35,
        "dpll_alg_linear": 0.35,
        "horn_alg_from": 0.65,
        "dpll_alg_from": 0.65,
    }
    prompt_color_map = {k: _tint(base_color, t) for k, t in prompt_tints.items()}
    lens = [3, 4, 5]
    fig, axes = plt.subplots(1, len(lens), figsize=(13.8, 3.6), sharex=True, sharey=True)
    meta: Dict[str, Any] = {
        "figure": "prompting_effects",
        "output": str(out_path),
        "layout": {"rows": "combined subset", "cols": "maxlen"},
    }

    for j, maxlen in enumerate(lens):
        ax = axes[j]
        show_legend = True
        title = f"k={maxlen}"

        m = _plot_accuracy_subset_overlay(
            ax,
            groups=groups,
            base_filters={**base, "maxlen": int(maxlen)},
            series_field="prompt_label",
            x_field="maxvars",
            y_mode=accuracy_mode,
            exclude_run_regex=exclude_run_regex,
            series_color_map=prompt_color_map,
            allowed_series_horn=["examples_only", "horn_alg_from", "horn_alg_linear"],
            allowed_series_nonhorn=["examples_only", "dpll_alg_from", "dpll_alg_linear"],
            preferred_series_order=["examples_only", "horn_alg_from", "horn_alg_linear", "dpll_alg_from", "dpll_alg_linear"],
            min_trials=3,
            show_ci95=False,
            marker_size_by_trials=False,
            show_legend=show_legend,
            title=title,
            x_label="# vars (n)",
            y_label=f"Accuracy ({accuracy_mode})" if j == 0 else "",
        )
        meta[f"{maxlen}"] = m

    fig.suptitle("Prompting-policy effects (OpenAI · gpt-5.2-pro · think=high · Compact CNF)")
    fig.tight_layout()
    _save_paper_figure(fig, out_path)
    plt.close(fig)
    return meta


def _figure_test_time_compute(
    groups: Sequence[Dict[str, Any]],
    *,
    out_path: Path,
    accuracy_mode: str,
    exclude_run_regex: str,
) -> Dict[str, Any]:
    """Test-time compute vs accuracy and cost (OpenAI; Horn vs Non-Horn overlay)."""
    #
    # Layout:
    # - columns: maxlen (3/4/5)
    # - row 1: overall accuracy (SAT+UNSAT combined), Horn+Non-Horn overlaid (line style)
    # - row 2: USD/slice (log)
    base = {
        "provider": "openai",
        "representation": "cnf_compact",
        "prompt_label": "examples_only",
        # Include the baseline grid and (when present) extended-n slices.
        "maxvars": [10, 20, 30, 40, 50, 60, 80, 100],
    }
    lens = [3, 4, 5]
    subsets = [1, 0]  # Horn, Non-Horn

    # Build stable series keys and labels for all OpenAI targets in this slice.
    label_map: Dict[str, str] = {}
    series_keys: List[str] = []
    for r in groups:
        if r.get("provider") != "openai":
            continue
        if r.get("representation") != "cnf_compact":
            continue
        if r.get("prompt_label") != "examples_only":
            continue
        model = str(r.get("model") or "")
        thinking_mode = str(r.get("thinking_mode") or "")
        # Keep the compute figure focused on the paired low/high compute variants.
        if _short_openai_model(model) not in {"gpt-5.2", "gpt-5.2-pro"}:
            continue
        key = f"openai/{model}/{thinking_mode}"
        series_keys.append(key)
        tm_disp = thinking_mode.replace("think_", "") if thinking_mode else "?"
        label_map[key] = f"openai/{_short_openai_model(model)} ({tm_disp})"
    color_map = _make_target_color_map(sorted(set(series_keys)))
    allowed_series = sorted(set(series_keys))

    nrows = 2
    ncols = len(lens)
    fig_h = 2.0 * nrows + 1.6
    fig, axes = plt.subplots(nrows, ncols, figsize=(13.8, fig_h), sharex=True)
    meta: Dict[str, Any] = {
        "figure": "test_time_compute",
        "output": str(out_path),
        "layout": {"rows": "accuracy; cost", "cols": "maxlen"},
        "note": "Overlays Horn vs Non-Horn (line style).",
    }

    # Normalize axes indexing when nrows/ncols == 1
    if nrows == 1:
        axes = [axes]
    if ncols == 1:
        axes = [[ax] for ax in axes]

    for j, maxlen in enumerate(lens):
        # Accuracy row
        ax_acc = axes[0][j]
        ax_acc.set_title(f"k={maxlen}")
        show_legend = True

        def _prep_slice(horn: int) -> List[Dict[str, Any]]:
            rs = _filter_groups(
                groups,
                filters={**base, "horn": int(horn), "maxlen": int(maxlen)},
                exclude_run_regex=exclude_run_regex,
            )
            for rr in rs:
                model = str(rr.get("model") or "")
                thinking_mode = str(rr.get("thinking_mode") or "")
                rr["_series_target_key"] = f"openai/{model}/{thinking_mode}"
            return rs

        horn_rows = _prep_slice(1)
        nonhorn_rows = _prep_slice(0)

        horn_label_map = {k: f"Horn {label_map.get(k, k)}" for k in allowed_series}
        nonhorn_label_map = {k: f"Non-Horn {label_map.get(k, k)}" for k in allowed_series}

        _plot_line_panel(
            ax_acc,
            rows=horn_rows,
            series_field="_series_target_key",
            x_field="maxvars",
            y_metric="accuracy",
            y_mode=str(accuracy_mode),
            min_trials=3,
            show_ci95=False,
            marker_size_by_trials=False,
            show_legend=False,
            line_style="-",
            color_map=color_map,
            label_map=horn_label_map,
            allowed_series=allowed_series,
            title="",
            x_label="",
            y_label="",
            y_lim=(-0.05, 1.05),
            y_scale="linear",
        )
        _plot_line_panel(
            ax_acc,
            rows=nonhorn_rows,
            series_field="_series_target_key",
            x_field="maxvars",
            y_metric="accuracy",
            y_mode=str(accuracy_mode),
            min_trials=3,
            show_ci95=False,
            marker_size_by_trials=False,
            show_legend=False,
            line_style="--",
            color_map=color_map,
            label_map=nonhorn_label_map,
            allowed_series=allowed_series,
            title="",
            x_label="",
            y_label="",
            y_lim=(-0.05, 1.05),
            y_scale="linear",
        )
        if show_legend:
            h, l = ax_acc.get_legend_handles_labels()
            label_to_handle = {lbl: hh for hh, lbl in zip(h, l) if lbl and not lbl.startswith("_")}
            ordered_keys = sorted(set(allowed_series), key=lambda k: str(label_map.get(k, k)))
            ordered_labels: List[str] = []
            for k in ordered_keys:
                hl = horn_label_map.get(k)
                nl = nonhorn_label_map.get(k)
                if hl and hl in label_to_handle:
                    ordered_labels.append(hl)
                if nl and nl in label_to_handle:
                    ordered_labels.append(nl)
            _apply_legend(ax_acc, [label_to_handle[x] for x in ordered_labels], ordered_labels, ncol=1)

        if j == 0:
            ax_acc.set_ylabel(f"Accuracy ({accuracy_mode})")

        # Cost row
        ax_cost = axes[1][j]

        _plot_line_panel(
            ax_cost,
            rows=horn_rows,
            series_field="_series_target_key",
            x_field="maxvars",
            y_metric="cost_total_usd",
            y_mode="nonpending",
            min_trials=3,
            show_ci95=False,
            marker_size_by_trials=False,
            show_legend=False,
            line_style="-",
            color_map=color_map,
            label_map=horn_label_map,
            allowed_series=allowed_series,
            title="",
            x_label="",
            y_label="",
            y_lim=None,
            y_scale="log",
        )
        _plot_line_panel(
            ax_cost,
            rows=nonhorn_rows,
            series_field="_series_target_key",
            x_field="maxvars",
            y_metric="cost_total_usd",
            y_mode="nonpending",
            min_trials=3,
            show_ci95=False,
            marker_size_by_trials=False,
            show_legend=False,
            line_style="--",
            color_map=color_map,
            label_map=nonhorn_label_map,
            allowed_series=allowed_series,
            title="",
            x_label="",
            y_label="",
            y_lim=None,
            y_scale="log",
        )

        if j == 0:
            ax_cost.set_ylabel("USD / slice (10 items; log)")
        ax_cost.set_xlabel("# vars (n)")
        _apply_usd_axis_format(ax_cost)
        if show_legend:
            h2, l2 = ax_cost.get_legend_handles_labels()
            label_to_handle2 = {lbl: hh for hh, lbl in zip(h2, l2) if lbl and not lbl.startswith("_")}
            ordered_keys = sorted(set(allowed_series), key=lambda k: str(label_map.get(k, k)))
            ordered_labels2: List[str] = []
            for k in ordered_keys:
                hl = horn_label_map.get(k)
                nl = nonhorn_label_map.get(k)
                if hl and hl in label_to_handle2:
                    ordered_labels2.append(hl)
                if nl and nl in label_to_handle2:
                    ordered_labels2.append(nl)
            _apply_legend(ax_cost, [label_to_handle2[x] for x in ordered_labels2], ordered_labels2, ncol=1)

    fig.suptitle("Test-time compute (OpenAI · Compact CNF · examples-only)")
    fig.tight_layout()
    _save_paper_figure(fig, out_path)
    plt.close(fig)
    return meta


def _figure_model_comparison(groups: Sequence[Dict[str, Any]], *, out_path: Path, accuracy_mode: str, exclude_run_regex: str) -> Dict[str, Any]:
    """Model comparison under a fixed task setting (no averaging across targets)."""
    # Paper honesty rules:
    # - Series = provider/model/thinking_mode (NO averaging).
    # - Accuracy uses the same denominator as tables by default (completed = answered+unclear).
    base = {
        "representation": "cnf_compact",
        "prompt_label": "examples_only",
        # Keep figures aligned with the baseline grid used in the paper tables/captions.
        "maxvars": [10, 20, 30, 40, 50],
    }
    lens = [3, 4, 5]
    subsets = [1, 0]

    # Precompute label map for all targets seen in this slice so legend labels are readable.
    label_map: Dict[str, str] = {}
    for r in groups:
        if r.get("representation") != "cnf_compact":
            continue
        if r.get("prompt_label") != "examples_only":
            continue
        provider = str(r.get("provider") or "")
        model = str(r.get("model") or "")
        thinking_mode = str(r.get("thinking_mode") or "")
        key = f"{provider}/{model}/{thinking_mode}"
        tm_disp = thinking_mode.replace("think_", "") if thinking_mode else "?"
        model_disp = _short_openai_model(model) if provider == "openai" else model
        label_map[key] = f"{provider}/{model_disp} ({tm_disp})"
    color_map = _make_target_color_map(sorted(label_map.keys()))

    fig, axes = plt.subplots(len(subsets), len(lens), figsize=(13.8, 6.6), sharex=True, sharey=True)
    meta: Dict[str, Any] = {
        "figure": "model_comparison",
        "output": str(out_path),
        "layout": {"rows": "subset", "cols": "maxlen"},
        "note": "Includes thinking_mode as separate series (no averaging).",
    }

    for i, horn in enumerate(subsets):
        for j, maxlen in enumerate(lens):
            ax = axes[i][j]
            show_legend = True
            title = f"{SUBSET_LABEL.get(int(horn), str(horn))} · k={maxlen}"

            # Synthesize a stable per-model series key in the row dicts.
            # We do this by filtering, then adding fields for plotting.
            rows_slice = _filter_groups(
                groups,
                filters={**base, "horn": int(horn), "maxlen": int(maxlen)},
                exclude_run_regex=exclude_run_regex,
            )
            for rr in rows_slice:
                provider = str(rr.get("provider") or "")
                model = str(rr.get("model") or "")
                thinking_mode = str(rr.get("thinking_mode") or "")
                rr["_series_target_key"] = f"{provider}/{model}/{thinking_mode}"

            m = _plot_line_panel(
                ax,
                rows=rows_slice,
                series_field="_series_target_key",
                x_field="maxvars",
                y_metric="accuracy",
                y_mode=str(accuracy_mode),
                min_trials=3,
                show_ci95=False,
                marker_size_by_trials=False,  # per-maxlen per-sat usually fixed N≈5
                show_legend=show_legend,
                line_style="-",
                color_map=color_map,
                label_map=label_map,
                title=title,
                x_label="# vars (n)",
                y_label=f"Accuracy ({accuracy_mode})",
                y_lim=(-0.05, 1.05),
                y_scale="linear",
            )
            meta[f"{horn}_{maxlen}"] = m

    fig.suptitle("Model comparison under a fixed task setting (Compact CNF · examples-only · per-model)")
    fig.tight_layout()
    _save_paper_figure(fig, out_path)
    plt.close(fig)
    return meta


def _figure_supp_sat_unsat_asymmetry(
    groups: Sequence[Dict[str, Any]],
    *,
    out_path: Path,
    accuracy_mode: str,
    exclude_run_regex: str,
) -> Dict[str, Any]:
    """
    Supplementary: summarize satisfiable/unsatisfiable asymmetry across the evaluated matrix.

    We summarize per target with grouped bars:
    - color: satisfiable vs unsatisfiable
    - hatch: examples-only vs algorithmic prompting (Horn: Horn-alg variants; Non-Horn: DPLL variants)
    """
    # Restrict to the baseline grid used in the paper.
    base_rows = _filter_groups(
        groups,
        filters={"maxvars": [10, 20, 30, 40, 50], "maxlen": [3, 4, 5]},
        exclude_run_regex=exclude_run_regex,
    )

    # Aggregate counts per (config, maxlen, suite+run) so we can combine either:
    # - one run that covers all maxlen values (len3_5), or
    # - three runs split by length (len3, len4, len5),
    # without double-counting if multiple runs exist.
    per_run_len: Dict[
        Tuple[str, str, str, str, str, int, int, str, str],
        Dict[int, AggCounts],
    ] = {}
    for r in base_rows:
        provider = str(r.get("provider") or "")
        model = str(r.get("model") or "")
        thinking_mode = str(r.get("thinking_mode") or "")
        rep = str(r.get("representation") or "")
        prompt = str(r.get("prompt_label") or "")
        horn = int(r.get("horn") or 0)
        maxlen = int(r.get("maxlen") or 0)
        suite = str(r.get("suite") or "")
        run = str(r.get("run") or "")
        satflag = int(r.get("satflag") or 0)
        cd = r.get("counts") or {}
        if not isinstance(cd, dict):
            continue
        k = (provider, model, thinking_mode, rep, prompt, horn, maxlen, suite, run)
        by_sat = per_run_len.get(k)
        if by_sat is None:
            by_sat = {}
            per_run_len[k] = by_sat
        agg = by_sat.get(satflag)
        if agg is None:
            agg = AggCounts()
            by_sat[satflag] = agg
        agg.add_counts(cd)

    # For each (config,maxlen), keep only the single best-covered run (typically total=50).
    best_len: Dict[
        Tuple[str, str, str, str, str, int, int],
        Tuple[int, AggCounts, AggCounts],
    ] = {}
    for (provider, model, thinking_mode, rep, prompt, horn, maxlen, _suite, _run), by_sat in per_run_len.items():
        sat = by_sat.get(1)
        unsat = by_sat.get(0)
        if sat is None or unsat is None:
            continue
        total = int(sat.total + unsat.total)
        key = (provider, model, thinking_mode, rep, prompt, horn, int(maxlen))
        prev = best_len.get(key)
        if prev is None or total > int(prev[0]):
            best_len[key] = (total, sat, unsat)

    # Combine maxlen slices (3/4/5) to get the baseline N=150 aggregate per config.
    from collections import defaultdict

    combined_sat: Dict[Tuple[str, str, str, str, str, int], AggCounts] = defaultdict(AggCounts)
    combined_unsat: Dict[Tuple[str, str, str, str, str, int], AggCounts] = defaultdict(AggCounts)
    present_maxlen: Dict[Tuple[str, str, str, str, str, int], set[int]] = defaultdict(set)
    for (provider, model, thinking_mode, rep, prompt, horn, maxlen), (_total, sat, unsat) in best_len.items():
        key = (provider, model, thinking_mode, rep, prompt, horn)
        combined_sat[key].add_counts(sat.__dict__)
        combined_unsat[key].add_counts(unsat.__dict__)
        present_maxlen[key].add(int(maxlen))

    # Collect per-target distributions across configurations, grouped by prompt type.
    #
    # prompt_group:
    # - "examples": prompt_label == examples_only
    # - "algorithmic": Horn-alg variants on Horn, DPLL variants on Non-Horn
    per_target: Dict[Tuple[str, str, str, int, str, int], List[float]] = {}
    # key: (provider, model, thinking_mode, horn, prompt_group, satflag) -> list[acc over configs]
    for (provider, model, thinking_mode, rep, prompt, horn), sat in combined_sat.items():
        unsat = combined_unsat.get((provider, model, thinking_mode, rep, prompt, horn))
        if unsat is None:
            continue
        if present_maxlen.get((provider, model, thinking_mode, rep, prompt, horn), set()) != {3, 4, 5}:
            continue
        if int(sat.total + unsat.total) != 150:
            continue
        if int(horn) == 0 and str(rep) == "horn_if_then":
            # Exclude the deliberate mismatch rendering from the Non-Horn panel.
            continue

        prompt_s = str(prompt or "")
        if prompt_s == "examples_only":
            prompt_group = "examples"
        else:
            if int(horn) == 1 and prompt_s in {"horn_alg_from", "horn_alg_linear"}:
                prompt_group = "algorithmic"
            elif int(horn) == 0 and prompt_s in {"dpll_alg_from", "dpll_alg_linear"}:
                prompt_group = "algorithmic"
            else:
                # Not part of the baseline prompt set for this subset.
                continue

        sat_acc = sat.accuracy(str(accuracy_mode))
        unsat_acc = unsat.accuracy(str(accuracy_mode))
        if sat_acc is None or unsat_acc is None:
            continue

        for satflag, acc in [(1, float(sat_acc)), (0, float(unsat_acc))]:
            k = (str(provider), str(model), str(thinking_mode), int(horn), str(prompt_group), int(satflag))
            per_target.setdefault(k, []).append(float(acc))

    # Stable target ordering (consistent across figures).
    def _tlabel(p: str, m: str, tm: str) -> str:
        tm_disp = tm.replace("think_", "") if tm else "?"
        m_disp = _short_openai_model(m) if p == "openai" else m
        return f"{p}/{m_disp} ({tm_disp})"

    def _target_sort_key(t: Tuple[str, str, str, int]) -> Tuple[int, str, str, str]:
        p, m, tm, _horn = t
        p_order = {"anthropic": 0, "google": 1, "openai": 2}.get(p, 9)
        return (p_order, p, m, tm)

    targets_all = sorted({(k[0], k[1], k[2], k[3]) for k in per_target.keys()}, key=_target_sort_key)
    targets_horn = [t for t in targets_all if int(t[3]) == 1]
    targets_nonhorn = [t for t in targets_all if int(t[3]) == 0]

    # Stack panels vertically so the full model labels are readable.
    fig, axes = plt.subplots(2, 1, figsize=(13.8, 6.2), sharex=True, sharey=True)
    meta: Dict[str, Any] = {"figure": "supp_sat_unsat_asymmetry", "output": str(out_path)}

    # Use the same target order on both panels so labels align visually.
    targets_by_model: List[Tuple[str, str, str]] = sorted({(k[0], k[1], k[2]) for k in per_target.keys()}, key=lambda t: _target_sort_key((t[0], t[1], t[2], 0)))

    for ax, targets, title, horn in [
        (axes[0], targets_by_model, "Horn subset", 1),
        (axes[1], targets_by_model, "Non-Horn subset", 0),
    ]:
        xs = list(range(len(targets)))
        # Build 4 bars per target: (examples vs algorithmic) × (satisfiable vs unsatisfiable).
        groups = ["examples", "algorithmic"]
        satflags = [1, 0]  # satisfiable, unsatisfiable
        w = 0.16
        gap = 0.04
        # Within each target i, lay out bars centered around i.
        base_offsets = [-1.5, -0.5, 0.5, 1.5]  # 4 bars
        offsets = [o * (w + gap) for o in base_offsets]

        hatch_map = {"examples": "", "algorithmic": "///"}
        # Encode sat/unsat via opacity (unsat more opaque), and prompt group via hatch.
        alpha_by_satflag = {1: 0.35, 0: 0.9}  # satisfiable, unsatisfiable

        # Collect per bar positions/values and ranges.
        bar_x: List[float] = []
        bar_y: List[float] = []
        err_lo: List[float] = []
        err_hi: List[float] = []
        bar_color: List[str] = []
        bar_hatch: List[str] = []
        bar_alpha: List[float] = []
        n_cfgs: List[int] = []

        for i, (p, m, tm) in enumerate(targets):
            # count how many configs contribute (min across the four buckets that exist)
            counts = []
            for gname in groups:
                for sf in satflags:
                    vals = per_target.get((p, m, tm, int(horn), gname, int(sf))) or []
                    counts.append(len(vals))
            n_cfgs.append(int(min(counts) if counts else 0))

            for bi, (gname, sf) in enumerate([(groups[0], 1), (groups[0], 0), (groups[1], 1), (groups[1], 0)]):
                vals = per_target.get((p, m, tm, int(horn), gname, int(sf))) or []
                target_key = f"{p}/{m}/{tm}"
                target_color = _make_target_color_map([target_key]).get(target_key, "#4a5568")
                if not vals:
                    # still reserve spacing
                    bar_x.append(float(i) + float(offsets[bi]))
                    bar_y.append(float("nan"))
                    err_lo.append(0.0)
                    err_hi.append(0.0)
                else:
                    mean = float(sum(vals) / float(len(vals)))
                    bar_x.append(float(i) + float(offsets[bi]))
                    bar_y.append(mean)
                    err_lo.append(mean - float(min(vals)))
                    err_hi.append(float(max(vals)) - mean)
                bar_color.append(str(target_color))
                bar_hatch.append(hatch_map.get(gname, ""))
                bar_alpha.append(float(alpha_by_satflag.get(int(sf), 0.85)))

        # Draw bars
        for x, y, c, h, a in zip(bar_x, bar_y, bar_color, bar_hatch, bar_alpha):
            ax.bar([x], [y], width=w, color=c, alpha=float(a), edgecolor="#1a202c", linewidth=0.7, hatch=h, zorder=2)
        # Draw min-max whiskers
        ax.errorbar(bar_x, bar_y, yerr=[err_lo, err_hi], fmt="none", ecolor="#2d3748", elinewidth=1.1, capsize=2, alpha=0.8, zorder=3)

        ax.set_title(title)
        ax.set_ylim(-0.05, 1.05)
        ax.set_xticks(xs)
        # Show full model label along the bottom (only once, on the bottom panel).
        if ax is axes[1]:
            ax.set_xticklabels([_tlabel(p, m, tm) for (p, m, tm) in targets], rotation=0, ha="center", fontsize=9)
        else:
            ax.set_xticklabels([])
        ax.grid(True, axis="y", alpha=0.25)
        ax.set_ylabel(f"Accuracy ({accuracy_mode})")
        ax.set_xlabel("target model" if ax is axes[1] else "")

        # No extra per-target annotations (keep consistent across supplementary figures).

    from matplotlib.patches import Patch  # type: ignore

    # Explicit legend entries (style only; colors in the bars are per-model).
    legend_color = "#4a5568"
    legend_handles = [
        Patch(
            facecolor=legend_color,
            edgecolor="#1a202c",
            hatch="",
            alpha=float(alpha_by_satflag.get(1, 0.35)),
            label="examples-only (satisfiable)",
        ),
        Patch(
            facecolor=legend_color,
            edgecolor="#1a202c",
            hatch="",
            alpha=float(alpha_by_satflag.get(0, 0.9)),
            label="examples-only (unsatisfiable)",
        ),
        Patch(
            facecolor=legend_color,
            edgecolor="#1a202c",
            hatch="///",
            alpha=float(alpha_by_satflag.get(1, 0.35)),
            label="algorithmic (satisfiable)",
        ),
        Patch(
            facecolor=legend_color,
            edgecolor="#1a202c",
            hatch="///",
            alpha=float(alpha_by_satflag.get(0, 0.9)),
            label="algorithmic (unsatisfiable)",
        ),
    ]
    legend_labels = [h.get_label() for h in legend_handles]
    for ax in axes:
        _apply_legend(ax, legend_handles, legend_labels, ncol=1)

    fig.suptitle("Supplementary: satisfiable/unsatisfiable asymmetry (mean ± range; examples vs algorithmic)")
    fig.tight_layout()
    _save_paper_figure(fig, out_path)
    plt.close(fig)
    meta["targets_horn"] = len(targets_horn)
    meta["targets_nonhorn"] = len(targets_nonhorn)
    return meta


def _figure_supp_semantic_alignment_mismatch(
    groups: Sequence[Dict[str, Any]],
    *,
    out_path: Path,
    accuracy_mode: str,
    exclude_run_regex: str,
) -> Dict[str, Any]:
    """
    Supplementary: semantic alignment mismatch control (Horn if--then negative control).
    """
    base_rows = _filter_groups(
        groups,
        filters={
            "representation": "horn_if_then",
            "prompt_label": ["examples_only", "horn_alg_from", "horn_alg_linear"],
            "maxvars": [10, 20, 30, 40, 50],
            "maxlen": [3, 4, 5],
        },
        exclude_run_regex=exclude_run_regex,
    )

    # Aggregate per (config,maxlen,suite+run) so we can combine either a single len3_5 run
    # or three separate len3/len4/len5 runs without double-counting.
    per_run_len: Dict[Tuple[str, str, str, str, int, int, str, str], AggCounts] = {}
    for r in base_rows:
        provider = str(r.get("provider") or "")
        model = str(r.get("model") or "")
        thinking_mode = str(r.get("thinking_mode") or "")
        prompt = str(r.get("prompt_label") or "")
        horn = int(r.get("horn") or 0)
        maxlen = int(r.get("maxlen") or 0)
        suite = str(r.get("suite") or "")
        run = str(r.get("run") or "")
        cd = r.get("counts") or {}
        if not isinstance(cd, dict):
            continue
        k = (provider, model, thinking_mode, prompt, horn, maxlen, suite, run)
        agg = per_run_len.get(k)
        if agg is None:
            agg = AggCounts()
            per_run_len[k] = agg
        agg.add_counts(cd)

    # Select the best-coverage run for each (config,maxlen) slice (typically total=50).
    best_len: Dict[Tuple[str, str, str, str, int, int], AggCounts] = {}
    for (provider, model, thinking_mode, prompt, horn, maxlen, _suite, _run), agg in per_run_len.items():
        k = (provider, model, thinking_mode, prompt, horn, int(maxlen))
        prev = best_len.get(k)
        if prev is None or int(agg.total) > int(prev.total):
            best_len[k] = agg

    # Combine maxlen slices (3/4/5) to match the baseline N=150 aggregate.
    from collections import defaultdict

    combined: Dict[Tuple[str, str, str, str, int], AggCounts] = defaultdict(AggCounts)
    present_maxlen: Dict[Tuple[str, str, str, str, int], set[int]] = defaultdict(set)
    for (provider, model, thinking_mode, prompt, horn, maxlen), agg in best_len.items():
        k = (provider, model, thinking_mode, prompt, horn)
        combined[k].add_counts(agg.__dict__)
        present_maxlen[k].add(int(maxlen))

    # Targets present in the data (sorted stably by provider then model label).
    targets: List[Tuple[str, str, str]] = sorted({(k[0], k[1], k[2]) for k in combined.keys()})
    prompts = ["examples_only", "horn_alg_from", "horn_alg_linear"]

    def tlabel(p: str, m: str, tm: str) -> str:
        tm_disp = tm.replace("think_", "") if tm else "?"
        m_disp = _short_openai_model(m) if p == "openai" else m
        return f"{p}/{m_disp} ({tm_disp})"

    x_centers = list(range(len(targets)))
    bar_w = 0.11
    n_bars = len(prompts) * 2  # aligned vs mismatched
    total_w = float(n_bars) * float(bar_w)
    start = -total_w / 2.0 + bar_w / 2.0

    fig, ax = plt.subplots(1, 1, figsize=(13.8, 4.2))
    ax.axhline(0.5, color="#718096", lw=1.2, alpha=0.8, linestyle="--")

    # Bars are colored by target model (global palette). Alignment/mismatch is encoded by opacity.
    alpha_by_subset = {1: 0.95, 0: 0.35}  # aligned(Horn inputs), mismatched(Non-Horn inputs)
    hatches = {"examples_only": "", "horn_alg_from": "///", "horn_alg_linear": "xx"}
    target_color_map = _make_target_color_map([f"{p}/{m}/{tm}" for (p, m, tm) in targets])

    n_plotted = 0
    for i, (provider, model, thinking_mode) in enumerate(targets):
        target_key = f"{provider}/{model}/{thinking_mode}"
        base_color = target_color_map.get(target_key, "#4a5568")
        for pi, prompt in enumerate(prompts):
            for si, horn in enumerate([1, 0]):  # aligned first, then mismatched
                idx = pi * 2 + si
                x = float(i) + start + float(idx) * float(bar_w)
                agg = combined.get((provider, model, thinking_mode, prompt, int(horn)))
                if agg is None:
                    continue
                if present_maxlen.get((provider, model, thinking_mode, prompt, int(horn)), set()) != {3, 4, 5}:
                    continue
                if int(agg.total) != 150:
                    continue
                acc = agg.accuracy(str(accuracy_mode))
                if acc is None:
                    continue
                ax.bar(
                    [x],
                    [float(acc)],
                    width=float(bar_w) * 0.92,
                    color=base_color,
                    edgecolor="#1a202c",
                    linewidth=0.8,
                    hatch=hatches.get(prompt, ""),
                    alpha=float(alpha_by_subset.get(int(horn), 0.85)),
                )
                n_plotted += 1

    ax.set_xlim(-0.6, float(len(targets)) - 0.4)
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel(f"Accuracy ({accuracy_mode})")
    ax.set_xticks(x_centers)
    ax.set_xticklabels([tlabel(*t) for t in targets], rotation=0, ha="center", fontsize=9)
    ax.grid(True, axis="y", alpha=0.25)

    from matplotlib.lines import Line2D  # type: ignore
    from matplotlib.patches import Patch  # type: ignore

    # Explicit legend entries: (subset × prompt). Bar colors are per-model.
    legend_handles: List[Any] = []
    legend_labels: List[str] = []
    for prompt in prompts:
        p_label = PROMPT_LABEL.get(prompt, prompt)
        hatch = hatches.get(prompt, "")
        for horn in [1, 0]:  # aligned then mismatched
            subset_label = "aligned" if int(horn) == 1 else "mismatched"
            legend_handles.append(
                Patch(
                    facecolor="#4a5568",
                    edgecolor="#1a202c",
                    hatch=hatch,
                    alpha=float(alpha_by_subset.get(int(horn), 0.85)),
                    label="",
                )
            )
            legend_labels.append(f"{subset_label} · {p_label}")
    _apply_legend(ax, legend_handles, legend_labels, ncol=1)

    ax.set_title("Supplementary: semantic alignment mismatch control (Horn if–then negative control)")
    fig.tight_layout()
    _save_paper_figure(fig, out_path)
    plt.close(fig)

    return {"figure": "supp_semantic_alignment_mismatch", "output": str(out_path), "bars_plotted": int(n_plotted)}


FigureFn = Callable[..., Dict[str, Any]]


@dataclass(frozen=True)
class FigureSpec:
    id: str
    filename: str
    fn: FigureFn


def generate_paper_figures(
    *,
    runs_dir: str,
    output_dir: str,
    accuracy_mode: str = "completed",
    include_suites: Optional[Sequence[str]] = None,
    exclude_suites: Optional[Sequence[str]] = None,
    exclude_run_regex: str = r"smoke",
    run_selection: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate standalone paper figures as PDFs.

    The figures are generated from `_refactor/runs/**/results.jsonl` (and provenance for spend/latency),
    and are intended to be re-run repeatedly as new results arrive.
    """
    runs_path = Path(runs_dir).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    combined = build_combined_dashboard_data(
        runs_dir=str(runs_path),
        include_suites=[s for s in (include_suites or []) if s],
        exclude_suites=[s for s in (exclude_suites or []) if s],
    )
    groups = combined.get("groups") or []
    if not isinstance(groups, list):
        groups = []

    # If multiple runs exist for the same suite cell, select a single "source of truth".
    #
    # Without this, `_aggregate_series()` will sum counts across runs for the same series+x pair,
    # effectively double-counting when old runs remain in `_refactor/runs/`.
    #
    # Selection is policy-driven via `run_selection` (YAML/JSON loaded by the CLI). If omitted,
    # we fall back to a sensible default: prefer newest run with usable data.

    def _as_str(x: Any) -> str:
        return str(x) if x is not None else ""

    def _as_dict(x: Any) -> Dict[str, Any]:
        return dict(x) if isinstance(x, Mapping) else {}

    def _run_date_yyyymmdd(run: str) -> int:
        m = re.search(r"(\d{8})(?!\d)", str(run))
        if not m:
            return 0
        try:
            return int(m.group(1))
        except Exception:
            return 0

    def _denom_for_mode(counts: Mapping[str, Any], mode: str) -> int:
        total = _safe_int(counts.get("total"))
        pending = _safe_int(counts.get("pending"))
        answered = _safe_int(counts.get("answered"))
        unclear = _safe_int(counts.get("unclear"))
        if mode == "answered":
            return int(answered)
        if mode == "nonpending":
            return int(max(0, total - pending))
        # default: completed
        return int(answered + unclear)

    def _glob_match(value: str, pat: Optional[str]) -> bool:
        if pat is None or pat == "" or pat == "all":
            return True
        return fnmatch(str(value), str(pat))

    def _select_rule(provider: str, model: str, thinking_mode: str) -> Dict[str, Any]:
        cfg = _as_dict(run_selection)
        rules = cfg.get("targets") or []
        if not isinstance(rules, list):
            rules = []
        for r in rules:
            if not isinstance(r, Mapping):
                continue
            match = _as_dict(r.get("match"))
            if not _glob_match(provider, _as_str(match.get("provider")) or None):
                continue
            if not _glob_match(model, _as_str(match.get("model")) or None):
                continue
            if not _glob_match(thinking_mode, _as_str(match.get("thinking_mode")) or None):
                continue
            return dict(r)
        return {}

    def _default_strategy() -> str:
        cfg = _as_dict(run_selection)
        d = _as_dict(cfg.get("default"))
        s = _as_str(d.get("strategy")) or ""
        return s or "newest_with_data"

    def _run_matches_substr(run: str, sub: Optional[str]) -> bool:
        if not sub:
            return False
        return str(sub) in str(run)

    def _run_matches_regex(run: str, pat: Optional[str]) -> bool:
        if not pat:
            return False
        try:
            return bool(re.search(str(pat), str(run)))
        except Exception:
            return False

    selected_by_cell: Dict[
        Tuple[str, str, str, str, str, str, int, int, int, int],
        Tuple[Tuple[int, int, int, int, int, str], Dict[str, Any]],
    ] = {}
    filtered_out = 0
    filtered_out_by_target: Dict[str, int] = {}
    for g in groups:
        if not isinstance(g, dict):
            continue
        suite = str(g.get("suite") or "")
        provider = str(g.get("provider") or "")
        model = str(g.get("model") or "")
        thinking_mode = str(g.get("thinking_mode") or "")
        rep = str(g.get("representation") or "")
        prompt = str(g.get("prompt_label") or "")
        horn = int(g.get("horn") or 0)
        satflag = int(g.get("satflag") or 0)
        maxvars = int(g.get("maxvars") or 0)
        maxlen = int(g.get("maxlen") or 0)
        run = str(g.get("run") or "")

        target_key = f"{provider}/{model}/{thinking_mode}"
        rule = _select_rule(provider, model, thinking_mode)
        use_only_substr = _as_str(rule.get("use_only_run_substr")) or None
        use_only_regex = _as_str(rule.get("use_only_run_regex")) or None
        prefer_substr = _as_str(rule.get("prefer_run_substr")) or None
        prefer_regex = _as_str(rule.get("prefer_run_regex")) or None
        strategy = _as_str(rule.get("strategy")) or _default_strategy()

        if use_only_substr and not _run_matches_substr(run, use_only_substr):
            filtered_out += 1
            filtered_out_by_target[target_key] = int(filtered_out_by_target.get(target_key, 0)) + 1
            continue
        if use_only_regex and not _run_matches_regex(run, use_only_regex):
            filtered_out += 1
            filtered_out_by_target[target_key] = int(filtered_out_by_target.get(target_key, 0)) + 1
            continue

        counts = g.get("counts") or {}
        if not isinstance(counts, dict):
            counts = {}
        denom = _denom_for_mode(counts, str(accuracy_mode))
        run_date = _run_date_yyyymmdd(run)
        total = _safe_int(counts.get("total"))
        has_data = 1 if int(denom) > 0 else 0
        preferred = 1 if (_run_matches_substr(run, prefer_substr) or _run_matches_regex(run, prefer_regex)) else 0

        cell_key = (suite, provider, model, thinking_mode, rep, prompt, horn, satflag, maxvars, maxlen)
        # Default: prefer newest run with usable data; policy can flip to best-coverage.
        if str(strategy) == "best_coverage":
            score = (int(has_data), int(preferred), int(denom), int(run_date), int(total), str(run))
        else:
            # newest_with_data (default)
            score = (int(has_data), int(preferred), int(run_date), int(denom), int(total), str(run))
        prev = selected_by_cell.get(cell_key)
        if prev is None or score > prev[0]:
            selected_by_cell[cell_key] = (score, g)

    groups_deduped = [v[1] for v in selected_by_cell.values()]

    # Build a human- and machine-readable "source report": which runs were chosen per target model.
    used_by_target: Dict[str, Dict[str, int]] = {}
    for g in groups_deduped:
        if not isinstance(g, dict):
            continue
        tk = f"{_as_str(g.get('provider'))}/{_as_str(g.get('model'))}/{_as_str(g.get('thinking_mode'))}"
        run = _as_str(g.get("run"))
        by_run = used_by_target.get(tk)
        if by_run is None:
            by_run = {}
            used_by_target[tk] = by_run
        by_run[run] = int(by_run.get(run, 0)) + 1

    # Global matplotlib style tuned for print.
    plt.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10,
            "legend.fontsize": 9,
        }
    )

    meta: Dict[str, Any] = {
        "generated_at": _utc_now_iso(),
        "runs_dir": str(runs_path),
        "output_dir": str(out_dir),
        "accuracy_mode": str(accuracy_mode),
        "exclude_run_regex": str(exclude_run_regex),
        "groups_total": int(len(groups)),
        "groups_deduped": int(len(groups_deduped)),
        "run_selection": dict(run_selection) if isinstance(run_selection, Mapping) else None,
        "groups_filtered_out_by_run_selection": int(filtered_out),
        "figures": [],
        "combined_metadata": combined.get("metadata"),
        "selection": {
            "filtered_out_by_target": dict(sorted(filtered_out_by_target.items(), key=lambda kv: kv[0])),
            "used_by_target": dict(sorted(used_by_target.items(), key=lambda kv: kv[0])),
        },
    }

    figure_specs: List[FigureSpec] = [
        FigureSpec(
            id="representation_effects",
            filename="fig_representation_effects.pdf",
            fn=_figure_representation_effects,
        ),
        FigureSpec(
            id="prompting_effects",
            filename="fig_prompting_effects.pdf",
            fn=_figure_prompting_effects,
        ),
        FigureSpec(
            id="test_time_compute",
            filename="fig_test_time_compute.pdf",
            fn=_figure_test_time_compute,
        ),
        FigureSpec(
            id="model_comparison",
            filename="fig_model_comparison.pdf",
            fn=_figure_model_comparison,
        ),
        FigureSpec(
            id="supp_sat_unsat_asymmetry",
            filename="fig_supp_sat_unsat_asymmetry.pdf",
            fn=_figure_supp_sat_unsat_asymmetry,
        ),
        FigureSpec(
            id="supp_semantic_alignment_mismatch",
            filename="fig_supp_semantic_alignment_mismatch.pdf",
            fn=_figure_supp_semantic_alignment_mismatch,
        ),
    ]

    for spec in figure_specs:
        out_path = out_dir / spec.filename
        fig_meta = spec.fn(
            groups_deduped,
            out_path=out_path,
            accuracy_mode=accuracy_mode,
            exclude_run_regex=exclude_run_regex,
        )
        # Normalize metadata keys for consistency.
        fig_meta["figure"] = spec.id
        fig_meta["output"] = str(out_path)
        meta["figures"].append(fig_meta)

    (out_dir / "paper_figures.meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")

    # Also write a focused selection report for auditing figure provenance.
    (out_dir / "paper_figures.selection.json").write_text(
        json.dumps(meta.get("selection") or {}, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    # Markdown view for quick inspection.
    lines: List[str] = []
    lines.append("# Paper figure source report")
    lines.append("")
    lines.append(f"- generated_at: `{meta.get('generated_at')}`")
    lines.append(f"- accuracy_mode: `{meta.get('accuracy_mode')}`")
    lines.append(f"- runs_dir: `{meta.get('runs_dir')}`")
    lines.append("")
    rs = meta.get("run_selection")
    if rs:
        lines.append("## Run-selection policy")
        lines.append("")
        lines.append("```")
        lines.append(json.dumps(rs, indent=2, sort_keys=True))
        lines.append("```")
        lines.append("")
    lines.append("## Runs used per target model")
    lines.append("")
    for target in sorted(used_by_target.keys()):
        lines.append(f"### `{target}`")
        by_run = used_by_target.get(target) or {}
        for run_name, n_cells in sorted(by_run.items(), key=lambda kv: (-int(kv[1]), kv[0])):
            lines.append(f"- **{run_name}**: {int(n_cells)} cells")
        lines.append("")
    (out_dir / "paper_figures.selection.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    return meta

