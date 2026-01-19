from __future__ import annotations

import json
import math
import re
import time
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

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
from llmlog.problems.reader import iter_problem_rows  # noqa: E402


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
    show_legend: bool = True,
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
        if y_metric == "accuracy":
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

    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(True, alpha=0.25)
    ax.set_yscale(y_scale)
    if y_lim is not None:
        ax.set_ylim(*y_lim)
    if plotted > 0:
        if show_legend:
            ax.legend(fontsize=9, frameon=False)
    else:
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


def _write_placeholder_figure(path: Path, *, title: str, message: str) -> None:
    fig, ax = plt.subplots(1, 1, figsize=(7.2, 3.2))
    ax.axis("off")
    ax.set_title(title)
    ax.text(0.01, 0.7, message, va="top", ha="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)


def _make_color_map(keys: Sequence[str]) -> Dict[str, Any]:
    uniq = list(dict.fromkeys([str(k) for k in keys if k is not None]))
    if not uniq:
        return {}
    cmap = plt.get_cmap("tab20" if len(uniq) > 10 else "tab10")
    out: Dict[str, Any] = {}
    for i, k in enumerate(uniq):
        out[k] = cmap(i % cmap.N)
    return out


def _add_satflag_style_legend(ax: Any) -> None:
    # Add a tiny second legend describing line styles for SAT vs UNSAT.
    from matplotlib.lines import Line2D  # type: ignore

    handles = [
        Line2D([0], [0], color="#1a202c", lw=2.0, linestyle="-", label="satisfiable"),
        Line2D([0], [0], color="#1a202c", lw=2.0, linestyle="--", label="unsatisfiable"),
    ]
    # Preserve an existing series legend (Matplotlib replaces it on ax.legend()).
    prev = ax.get_legend()
    if prev is not None:
        prev.remove()
    ax.legend(handles=handles, loc="lower right", fontsize=8.5, frameon=False, title=None)
    if prev is not None:
        ax.add_artist(prev)


def _add_subset_style_legend(ax: Any) -> None:
    """Add a tiny legend describing line styles for Horn vs Non-Horn."""
    from matplotlib.lines import Line2D  # type: ignore

    handles = [
        Line2D([0], [0], color="#1a202c", lw=2.0, linestyle="-", label="Horn"),
        Line2D([0], [0], color="#1a202c", lw=2.0, linestyle="--", label="Non-Horn"),
    ]
    prev = ax.get_legend()
    if prev is not None:
        prev.remove()
    ax.legend(handles=handles, loc="lower right", fontsize=8.5, frameon=False, title=None)
    if prev is not None:
        ax.add_artist(prev)


def _plot_accuracy_subset_overlay(
    ax: Any,
    *,
    groups: Sequence[Dict[str, Any]],
    base_filters: Mapping[str, Any],
    series_field: str,
    x_field: str,
    y_mode: str,
    exclude_run_regex: Optional[str],
    allowed_series_horn: Optional[Sequence[str]] = None,
    allowed_series_nonhorn: Optional[Sequence[str]] = None,
    preferred_series_order: Optional[Sequence[str]] = None,
    min_trials: int = 1,
    show_ci95: bool = True,
    marker_size_by_trials: bool = True,
    show_legend: bool = False,
    show_subset_style_legend: bool = False,
    label_map: Optional[Mapping[str, str]] = None,
    title: str = "",
    x_label: str = "# vars (n)",
    y_label: str = "Accuracy",
) -> Dict[str, Any]:
    """Plot overall accuracy with Horn vs Non-Horn overlaid (line style encodes subset)."""
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

    meta: Dict[str, Any] = {"horn_rows": len(horn_rows), "nonhorn_rows": len(nonhorn_rows)}

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
        show_legend=show_legend,
        line_style="-",
        color_map=color_map,
        label_map=label_map,
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
        show_legend=False,  # avoid duplicate legend entries
        line_style="--",
        color_map=color_map,
        label_map=label_map,
        allowed_series=allowed_series_nonhorn,
        preferred_series_order=preferred_series_order,
        title=title,
        x_label=x_label,
        y_label=y_label,
        y_lim=(-0.05, 1.05),
        y_scale="linear",
    )
    if show_subset_style_legend:
        _add_subset_style_legend(ax)
    return meta


def _plot_accuracy_collapsed(
    ax: Any,
    *,
    groups: Sequence[Dict[str, Any]],
    base_filters: Mapping[str, Any],
    series_field: str,
    x_field: str,
    y_mode: str,
    exclude_run_regex: Optional[str],
    allowed_series: Optional[Sequence[str]] = None,
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
    """Plot overall accuracy (SAT+UNSAT combined) per series."""
    rows = _filter_groups(groups, filters=base_filters, exclude_run_regex=exclude_run_regex)
    series_vals = sorted({str(r.get(series_field) or "unknown") for r in rows})
    color_map = _make_color_map(series_vals)
    meta: Dict[str, Any] = {"rows": len(rows)}
    meta["collapsed"] = _plot_line_panel(
        ax,
        rows=rows,
        series_field=series_field,
        x_field=x_field,
        y_metric="accuracy",
        y_mode=y_mode,
        min_trials=min_trials,
        show_ci95=show_ci95,
        marker_size_by_trials=marker_size_by_trials,
        show_legend=show_legend,
        line_style="-",
        color_map=color_map,
        label_map=label_map,
        allowed_series=allowed_series,
        preferred_series_order=preferred_series_order,
        title=title,
        x_label=x_label,
        y_label=y_label,
        # Give a margin so points at 0/1 are visible (not glued to the frame).
        y_lim=(-0.05, 1.05),
        y_scale="linear",
    )
    return meta


def _plot_accuracy_sat_unsat_overlay(
    ax: Any,
    *,
    groups: Sequence[Dict[str, Any]],
    base_filters: Mapping[str, Any],
    series_field: str,
    x_field: str,
    y_mode: str,
    exclude_run_regex: str,
    allowed_series: Optional[Sequence[str]] = None,
    preferred_series_order: Optional[Sequence[str]] = None,
    min_trials: int = 1,
    show_ci95: bool = True,
    marker_size_by_trials: bool = True,
    show_legend: bool = False,
    show_style_legend: bool = False,
    label_map: Optional[Mapping[str, str]] = None,
    title: str = "",
    x_label: str = "# vars (n)",
    y_label: str = "Accuracy",
) -> Dict[str, Any]:
    sat_rows = _filter_groups(groups, filters={**dict(base_filters), "satflag": 1}, exclude_run_regex=exclude_run_regex)
    unsat_rows = _filter_groups(groups, filters={**dict(base_filters), "satflag": 0}, exclude_run_regex=exclude_run_regex)
    series_vals = sorted({str(r.get(series_field) or "unknown") for r in (sat_rows + unsat_rows)})
    color_map = _make_color_map(series_vals)

    meta: Dict[str, Any] = {"sat_rows": len(sat_rows), "unsat_rows": len(unsat_rows)}

    meta["sat"] = _plot_line_panel(
        ax,
        rows=sat_rows,
        series_field=series_field,
        x_field=x_field,
        y_metric="accuracy",
        y_mode=y_mode,
        min_trials=min_trials,
        show_ci95=show_ci95,
        marker_size_by_trials=marker_size_by_trials,
        show_legend=show_legend,
        line_style="-",
        color_map=color_map,
        label_map=label_map,
        allowed_series=allowed_series,
        preferred_series_order=preferred_series_order,
        title=title,
        x_label=x_label,
        y_label=y_label,
        # Give a margin so points at 0/1 are visible (not glued to the frame).
        y_lim=(-0.05, 1.05),
        y_scale="linear",
    )
    meta["unsat"] = _plot_line_panel(
        ax,
        rows=unsat_rows,
        series_field=series_field,
        x_field=x_field,
        y_metric="accuracy",
        y_mode=y_mode,
        min_trials=min_trials,
        show_ci95=show_ci95,
        marker_size_by_trials=marker_size_by_trials,
        show_legend=False,  # avoid duplicate legend entries
        line_style="--",
        color_map=color_map,
        label_map=label_map,
        allowed_series=allowed_series,
        preferred_series_order=preferred_series_order,
        title=title,
        x_label=x_label,
        y_label=y_label,
        # Give a margin so points at 0/1 are visible (not glued to the frame).
        y_lim=(-0.05, 1.05),
        y_scale="linear",
    )

    # Optional small legend describing SAT vs UNSAT line styles.
    if show_style_legend:
        _add_satflag_style_legend(ax)
    return meta


def _figure_rq1(groups: Sequence[Dict[str, Any]], *, out_path: Path, accuracy_mode: str, exclude_run_regex: str) -> Dict[str, Any]:
    # Representation effects with Horn+Non-Horn overlaid (line style encodes subset),
    # and clause length maxlen as columns.
    #
    # Controlled target: OpenAI gpt-5.2-pro (think_high).
    base = {
        "provider": "openai",
        "model": "gpt-5.2-pro",
        "thinking_mode": "think_high",
        "prompt_label": "examples_only",
        # Include the baseline grid and (when present) extended-n slices.
        "maxvars": [10, 20, 30, 40, 50, 60, 80, 100],
    }
    lens = [3, 4, 5]
    fig, axes = plt.subplots(1, len(lens), figsize=(13.8, 3.6), sharex=True, sharey=True)
    meta: Dict[str, Any] = {"figure": "rq1", "output": str(out_path), "layout": {"rows": "combined subset", "cols": "maxlen"}}

    for j, maxlen in enumerate(lens):
        ax = axes[j]
        show_legend = bool(j == 0)
        title = f"k={maxlen}"
        m = _plot_accuracy_subset_overlay(
            ax,
            groups=groups,
            base_filters={**base, "maxlen": int(maxlen)},
            series_field="representation",
            x_field="maxvars",
            y_mode=accuracy_mode,
            exclude_run_regex=exclude_run_regex,
            preferred_series_order=["cnf_compact", "cnf_nl", "horn_if_then"],
            min_trials=3,
            show_ci95=False,
            marker_size_by_trials=False,
            show_legend=show_legend,
            show_subset_style_legend=show_legend,
            title=title,
            x_label="# vars (n)",
            y_label=f"Accuracy ({accuracy_mode})" if j == 0 else "",
        )
        meta[f"{maxlen}"] = m

    fig.suptitle("RQ1: Representation (OpenAI · gpt-5.2-pro · think=high · examples-only)")
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return meta


def _figure_rq2(groups: Sequence[Dict[str, Any]], *, out_path: Path, accuracy_mode: str, exclude_run_regex: str) -> Dict[str, Any]:
    # Prompting policy with Horn+Non-Horn overlaid (line style encodes subset),
    # and clause length maxlen as columns.
    #
    # Controlled target: OpenAI gpt-5.2-pro (think_high). Representation fixed to cnf_compact to isolate prompting.
    base = {
        "provider": "openai",
        "model": "gpt-5.2-pro",
        "thinking_mode": "think_high",
        "representation": "cnf_compact",
        # Include the baseline grid and (when present) extended-n slices.
        "maxvars": [10, 20, 30, 40, 50, 60, 80, 100],
    }
    lens = [3, 4, 5]
    fig, axes = plt.subplots(1, len(lens), figsize=(13.8, 3.6), sharex=True, sharey=True)
    meta: Dict[str, Any] = {"figure": "rq2", "output": str(out_path), "layout": {"rows": "combined subset", "cols": "maxlen"}}

    for j, maxlen in enumerate(lens):
        ax = axes[j]
        show_legend = bool(j == 0)
        title = f"k={maxlen}"

        m = _plot_accuracy_subset_overlay(
            ax,
            groups=groups,
            base_filters={**base, "maxlen": int(maxlen)},
            series_field="prompt_label",
            x_field="maxvars",
            y_mode=accuracy_mode,
            exclude_run_regex=exclude_run_regex,
            allowed_series_horn=["examples_only", "horn_alg_from", "horn_alg_linear"],
            allowed_series_nonhorn=["examples_only", "dpll_alg_from", "dpll_alg_linear"],
            preferred_series_order=["examples_only", "horn_alg_from", "horn_alg_linear", "dpll_alg_from", "dpll_alg_linear"],
            min_trials=3,
            show_ci95=False,
            marker_size_by_trials=False,
            show_legend=show_legend,
            show_subset_style_legend=show_legend,
            title=title,
            x_label="# vars (n)",
            y_label=f"Accuracy ({accuracy_mode})" if j == 0 else "",
        )
        meta[f"{maxlen}"] = m

    fig.suptitle("RQ2: Prompting policy (OpenAI · gpt-5.2-pro · think=high · cnf_compact)")
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return meta


def _figure_rq3(
    groups: Sequence[Dict[str, Any]],
    *,
    out_path: Path,
    accuracy_mode: str,
    exclude_run_regex: str,
) -> Dict[str, Any]:
    # Test-time compute / thinking vs accuracy and cost.
    #
    # Layout:
    # - columns: maxlen (3/4/5)
    # - row 1: overall accuracy (SAT+UNSAT combined), Horn+Non-Horn overlaid (line style)
    # - row 2: USD/item (log)
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
    color_map = _make_color_map(sorted(set(series_keys)))
    allowed_series = sorted(set(series_keys))

    nrows = 2
    ncols = len(lens)
    fig_h = 2.0 * nrows + 1.6
    fig, axes = plt.subplots(nrows, ncols, figsize=(13.8, fig_h), sharex=True)
    meta: Dict[str, Any] = {
        "figure": "rq3",
        "output": str(out_path),
        "layout": {"rows": "accuracy; cost", "cols": "maxlen"},
        "note": "RQ3 overlays Horn vs Non-Horn (line style).",
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
        show_legend = bool(j == 0)

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
            show_legend=show_legend,
            line_style="-",
            color_map=color_map,
            label_map=label_map,
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
            label_map=label_map,
            allowed_series=allowed_series,
            title="",
            x_label="",
            y_label="",
            y_lim=(-0.05, 1.05),
            y_scale="linear",
        )
        if show_legend:
            _add_subset_style_legend(ax_acc)

        if j == 0:
            ax_acc.set_ylabel(f"Accuracy ({accuracy_mode})")

        # Cost row
        ax_cost = axes[1][j]

        _plot_line_panel(
            ax_cost,
            rows=horn_rows,
            series_field="_series_target_key",
            x_field="maxvars",
            y_metric="cost_per_item_usd",
            y_mode="nonpending",
            min_trials=3,
            show_ci95=False,
            marker_size_by_trials=False,
            show_legend=False,
            line_style="-",
            color_map=color_map,
            label_map=label_map,
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
            y_metric="cost_per_item_usd",
            y_mode="nonpending",
            min_trials=3,
            show_ci95=False,
            marker_size_by_trials=False,
            show_legend=False,
            line_style="--",
            color_map=color_map,
            label_map=label_map,
            allowed_series=allowed_series,
            title="",
            x_label="",
            y_label="",
            y_lim=None,
            y_scale="log",
        )

        if j == 0:
            ax_cost.set_ylabel("USD / item (log)")
        ax_cost.set_xlabel("# vars (n)")

    fig.suptitle("RQ3: Test-time compute (OpenAI · Compact CNF · examples-only)")
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return meta


def _infer_subset_from_suite_name(suite: str) -> Optional[int]:
    s = str(suite or "")
    if "subset-hornonly" in s or "hornonly" in s:
        return 1
    if "subset-nonhornonly" in s or "nonhornonly" in s:
        return 0
    return None


def _estimate_dataset_ratio_m_over_n(
    *,
    refactor_root: Path,
    dataset_rel_path: str,
    skip_rows: int,
    only_maxvars: Optional[Sequence[int]],
    only_maxlen: Optional[Sequence[int]],
    mustbehorn: Optional[int],
) -> Optional[float]:
    ds_path = (refactor_root / str(dataset_rel_path)).resolve()
    if not ds_path.exists():
        return None
    mv_set = set(int(x) for x in (only_maxvars or []) if x is not None)
    ml_set = set(int(x) for x in (only_maxlen or []) if x is not None)
    for row in iter_problem_rows(str(ds_path), skip_rows=int(skip_rows or 0)):
        if row.problem is None or row.maxvarnr is None or row.maxlen is None:
            continue
        if mv_set and int(row.maxvarnr) not in mv_set:
            continue
        if ml_set and int(row.maxlen) not in ml_set:
            continue
        if mustbehorn is not None and row.mustbehorn is not None and int(row.mustbehorn) != int(mustbehorn):
            continue
        m = len(row.problem)
        n = int(row.maxvarnr) if int(row.maxvarnr) > 0 else None
        if not n:
            continue
        return float(m) / float(n)
    return None


def _figure_rq4(
    groups: Sequence[Dict[str, Any]],
    *,
    runs_dir: Path,
    out_path: Path,
    accuracy_mode: str,
    exclude_run_regex: str,
) -> Dict[str, Any]:
    """
    RQ4 requires ratio-sweep datasets. We support it when runs are present, but do not fail if absent.

    Heuristic: include any run where the dataset path or run name contains "ratio" or "phase".
    """
    # Look for manifests first.
    manifests = list(runs_dir.glob("**/run.manifest.json"))
    candidates: List[Dict[str, Any]] = []
    for mp in manifests:
        try:
            m = json.loads(mp.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(m, dict):
            continue
        run = str(m.get("run") or "")
        suite = str(m.get("suite") or "")
        ds = m.get("dataset") if isinstance(m.get("dataset"), dict) else {}
        ds_path = str(ds.get("path") or "")
        if exclude_run_regex and re.search(exclude_run_regex, run, re.IGNORECASE):
            continue
        hay = f"{run} {suite} {ds_path}".lower()
        if ("ratio" not in hay) and ("phase" not in hay):
            continue
        candidates.append(m)

    if not candidates:
        _write_placeholder_figure(
            out_path,
            title="RQ4: Hardness regimes / 3-SAT phase transition",
            message=(
                "No ratio-sweep runs detected yet.\n\n"
                "To enable this figure:\n"
                "- Generate k=3 non-Horn datasets at multiple m/n ratios (encode ratio in dataset name or run name, e.g. 'ratio4p25').\n"
                "- Run llmlog on each dataset.\n"
                "- Re-run this script; it will detect runs whose dataset path/run name contains 'ratio' or 'phase'."
            ),
        )
        return {"figure": "rq4", "output": str(out_path), "note": "placeholder_no_ratio_runs"}

    # Build points: x=ratio, y=accuracy (completed) aggregated over the run; series=target (provider/model/thinking).
    refactor_root = runs_dir.parents[0]
    points_rows: List[Dict[str, Any]] = []

    # Index group rows by (suite, run, provider, model, thinking_mode) so we can aggregate quickly.
    # Note: group rows include maxvars/maxlen/horn/satflag — for RQ4 we default to non-Horn k=3 UNSAT.
    for m in candidates:
        suite = str(m.get("suite") or "")
        run = str(m.get("run") or "")
        target = m.get("target") if isinstance(m.get("target"), dict) else {}
        provider = str(target.get("provider") or "")
        model = str(target.get("model") or "")
        thinking_mode = str(m.get("thinking_mode") or "")
        ds = m.get("dataset") if isinstance(m.get("dataset"), dict) else {}
        sel = m.get("dataset_selection") if isinstance(m.get("dataset_selection"), dict) else {}
        only_maxvars = sel.get("only_maxvars") if isinstance(sel.get("only_maxvars"), list) else None
        only_maxlen = sel.get("only_maxlen") if isinstance(sel.get("only_maxlen"), list) else None
        mustbehorn = _infer_subset_from_suite_name(suite)
        ratio = _estimate_dataset_ratio_m_over_n(
            refactor_root=refactor_root,
            dataset_rel_path=str(ds.get("path") or ""),
            skip_rows=_safe_int(ds.get("skip_rows")),
            only_maxvars=[int(x) for x in (only_maxvars or [])],
            only_maxlen=[int(x) for x in (only_maxlen or [])],
            mustbehorn=mustbehorn,
        )
        if ratio is None:
            continue

        # Pull matching rows from the combined groups (best-effort) and tag with ratio.
        for gr in _filter_groups(
            groups,
            filters={
                "suite": suite,
                "run": run,
                "provider": provider,
                "model": model,
                "thinking_mode": thinking_mode,
                "maxlen": 3,
                "horn": 0,
                "satflag": 0,
            },
            exclude_run_regex=exclude_run_regex,
        ):
            g2 = dict(gr)
            g2["ratio_m_over_n"] = float(ratio)
            g2["_series_target"] = f"{provider}/{model}/{thinking_mode}"
            points_rows.append(g2)

    if not points_rows:
        _write_placeholder_figure(
            out_path,
            title="RQ4: Hardness regimes / 3-SAT phase transition",
            message="Found candidate manifests, but could not extract usable (ratio, accuracy) points yet.",
        )
        return {"figure": "rq4", "output": str(out_path), "note": "placeholder_no_points"}

    fig, ax = plt.subplots(1, 1, figsize=(7.2, 3.4))
    meta = _plot_line_panel(
        ax,
        rows=points_rows,
        series_field="_series_target",
        x_field="ratio_m_over_n",
        y_metric="accuracy",
        y_mode=accuracy_mode,
        title="Non-Horn k=3 (UNSAT)",
        x_label="clause/variable ratio (m/n)",
        y_label=f"Accuracy ({accuracy_mode})",
        y_lim=(0.0, 1.0),
    )
    fig.suptitle("RQ4: Hardness regimes (phase-transition-style sweep)")
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return {"figure": "rq4", "output": str(out_path), "meta": meta, "points": len(points_rows)}


def _figure_rq5(groups: Sequence[Dict[str, Any]], *, out_path: Path, accuracy_mode: str, exclude_run_regex: str) -> Dict[str, Any]:
    # Cross-provider generality across Horn vs Non-Horn (rows) and maxlen (columns).
    #
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
    color_map = _make_color_map(sorted(label_map.keys()))

    fig, axes = plt.subplots(len(subsets), len(lens), figsize=(13.8, 6.6), sharex=True, sharey=True)
    meta: Dict[str, Any] = {
        "figure": "rq4_model_wise_consistency",
        "output": str(out_path),
        "layout": {"rows": "subset", "cols": "maxlen"},
        "note": "RQ4 includes thinking_mode as separate series (no averaging).",
    }

    for i, horn in enumerate(subsets):
        for j, maxlen in enumerate(lens):
            ax = axes[i][j]
            show_legend = bool(i == 0 and j == 0)
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

    fig.suptitle("RQ4: Model-wise consistency across providers (Compact CNF · examples-only · per-model)")
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return meta


def _figure_rq_failure_modes_sat_unsat_asymmetry(
    groups: Sequence[Dict[str, Any]],
    *,
    out_path: Path,
    accuracy_mode: str,
    exclude_run_regex: str,
) -> Dict[str, Any]:
    """
    RQ4-A: summarize satisfiable-skewed behavior across the evaluated matrix.

    To keep this stylistically consistent with RQ4-B, we summarize per target with grouped bars:
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

    # Stable target ordering (match RQ5 legend conventions).
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

    # Stack panels vertically so the full model labels are readable (match RQ4-B's x-axis style).
    fig, axes = plt.subplots(2, 1, figsize=(13.8, 6.2), sharex=True, sharey=True)
    meta: Dict[str, Any] = {"figure": "rq4_failure_modes_sat_unsat_asymmetry", "output": str(out_path)}

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

        sat_color = "#4a5568"
        unsat_color = "#e53e3e"
        hatch_map = {"examples": "", "algorithmic": "///"}

        # Collect per bar positions/values and ranges.
        bar_x: List[float] = []
        bar_y: List[float] = []
        err_lo: List[float] = []
        err_hi: List[float] = []
        bar_color: List[str] = []
        bar_hatch: List[str] = []
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
                bar_color.append(sat_color if int(sf) == 1 else unsat_color)
                bar_hatch.append(hatch_map.get(gname, ""))

        # Draw bars
        for x, y, c, h in zip(bar_x, bar_y, bar_color, bar_hatch):
            ax.bar([x], [y], width=w, color=c, alpha=0.85, edgecolor="#1a202c", linewidth=0.7, hatch=h, zorder=2)
        # Draw min-max whiskers
        ax.errorbar(bar_x, bar_y, yerr=[err_lo, err_hi], fmt="none", ecolor="#2d3748", elinewidth=1.1, capsize=2, alpha=0.8, zorder=3)

        ax.set_title(title)
        ax.set_ylim(-0.05, 1.05)
        ax.set_xticks(xs)
        # Match RQ4-B: show full model label along the bottom (only once, on the bottom panel).
        if ax is axes[1]:
            ax.set_xticklabels([_tlabel(p, m, tm) for (p, m, tm) in targets], rotation=0, ha="center", fontsize=9)
        else:
            ax.set_xticklabels([])
        ax.grid(True, axis="y", alpha=0.25)
        ax.set_ylabel(f"Accuracy ({accuracy_mode})")
        ax.set_xlabel("target model" if ax is axes[1] else "")

        # No extra per-target annotations (keep consistent with RQ4-B).

    # Two side legends, matching RQ4-B's style:
    # - left: SAT vs UNSAT (color)
    # - right: prompt type (hatch)
    from matplotlib.patches import Patch  # type: ignore

    # Place legends in the top margin (avoid covering bars).
    sat_unsat_handles = [
        Patch(facecolor="#4a5568", edgecolor="#1a202c", label="satisfiable"),
        Patch(facecolor="#e53e3e", edgecolor="#1a202c", label="unsatisfiable"),
    ]
    prompt_handles = [
        Patch(facecolor="#ffffff", edgecolor="#1a202c", hatch="", label="examples-only"),
        Patch(facecolor="#ffffff", edgecolor="#1a202c", hatch="///", label="algorithmic"),
    ]
    fig.legend(handles=sat_unsat_handles, loc="upper left", bbox_to_anchor=(0.01, 0.98), fontsize=9, frameon=False, title="label")
    fig.legend(handles=prompt_handles, loc="upper right", bbox_to_anchor=(0.99, 0.98), fontsize=9, frameon=False, title="prompt")

    fig.suptitle("RQ4-A: satisfiable/unsatisfiable asymmetry (mean ± range; examples vs algorithmic)")
    fig.tight_layout(rect=(0.0, 0.0, 1.0, 0.93))
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    meta["targets_horn"] = len(targets_horn)
    meta["targets_nonhorn"] = len(targets_nonhorn)
    return meta


def _figure_rq_failure_modes_semantic_alignment_brittleness(
    groups: Sequence[Dict[str, Any]],
    *,
    out_path: Path,
    accuracy_mode: str,
    exclude_run_regex: str,
) -> Dict[str, Any]:
    """
    RQ4-B: mismatch-control summary (Horn if--then rendering, aligned vs mismatched).
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

    colors = {1: "#3182ce", 0: "#dd6b20"}  # aligned(Horn)=blue, mismatched(Non-Horn)=orange
    hatches = {"examples_only": "", "horn_alg_from": "///", "horn_alg_linear": "xx"}

    n_plotted = 0
    for i, (provider, model, thinking_mode) in enumerate(targets):
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
                    color=colors[int(horn)],
                    edgecolor="#1a202c",
                    linewidth=0.8,
                    hatch=hatches.get(prompt, ""),
                    alpha=0.95,
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

    subset_handles = [
        Line2D([0], [0], color=colors[1], lw=8, label="aligned (Horn inputs)"),
        Line2D([0], [0], color=colors[0], lw=8, label="mismatched (Non-Horn inputs)"),
    ]
    prompt_handles = [
        Patch(facecolor="#ffffff", edgecolor="#1a202c", hatch=hatches["examples_only"], label="examples-only"),
        Patch(facecolor="#ffffff", edgecolor="#1a202c", hatch=hatches["horn_alg_from"], label="Horn alg (from)"),
        Patch(facecolor="#ffffff", edgecolor="#1a202c", hatch=hatches["horn_alg_linear"], label="Horn alg (linear)"),
    ]
    leg1 = ax.legend(handles=subset_handles, loc="upper left", fontsize=8.8, frameon=False, title="subset")
    ax.add_artist(leg1)
    ax.legend(handles=prompt_handles, loc="upper right", fontsize=8.8, frameon=False, title="prompt")

    ax.set_title("RQ4-B: Semantic alignment and brittleness (Horn if–then mismatch control)")
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)

    return {"figure": "rq4_failure_modes_semantic_alignment_brittleness", "output": str(out_path), "bars_plotted": int(n_plotted)}


def generate_paper_figures(
    *,
    runs_dir: str,
    output_dir: str,
    accuracy_mode: str = "completed",
    include_suites: Optional[Sequence[str]] = None,
    exclude_suites: Optional[Sequence[str]] = None,
    exclude_run_regex: str = r"smoke",
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
        "figures": [],
        "combined_metadata": combined.get("metadata"),
    }

    rq_representation_path = out_dir / "fig_rq_representation.pdf"
    rq_prompting_path = out_dir / "fig_rq_prompting.pdf"
    rq_test_time_compute_path = out_dir / "fig_rq_test-time_compute.pdf"
    rq_failure_modes_asym_path = out_dir / "fig_rq_failure_modes_sat_unsat_asymmetry.pdf"
    rq_failure_modes_align_path = out_dir / "fig_rq_failure_modes_semantic_alignment_brittleness.pdf"
    rq_cross_provider_path = out_dir / "fig_rq_cross-provider_consistency.pdf"

    meta["figures"].append(
        _figure_rq1(groups, out_path=rq_representation_path, accuracy_mode=accuracy_mode, exclude_run_regex=exclude_run_regex)
    )
    meta["figures"].append(_figure_rq2(groups, out_path=rq_prompting_path, accuracy_mode=accuracy_mode, exclude_run_regex=exclude_run_regex))
    meta["figures"].append(
        _figure_rq3(
            groups,
            out_path=rq_test_time_compute_path,
            accuracy_mode=accuracy_mode,
            exclude_run_regex=exclude_run_regex,
        )
    )
    meta["figures"].append(
        _figure_rq_failure_modes_sat_unsat_asymmetry(
            groups, out_path=rq_failure_modes_asym_path, accuracy_mode=accuracy_mode, exclude_run_regex=exclude_run_regex
        )
    )
    meta["figures"].append(
        _figure_rq_failure_modes_semantic_alignment_brittleness(
            groups, out_path=rq_failure_modes_align_path, accuracy_mode=accuracy_mode, exclude_run_regex=exclude_run_regex
        )
    )
    meta["figures"].append(
        _figure_rq5(groups, out_path=rq_cross_provider_path, accuracy_mode=accuracy_mode, exclude_run_regex=exclude_run_regex)
    )

    (out_dir / "paper_figures.meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")
    return meta

