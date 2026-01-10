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
    "cnf_compact": "CNF (compact)",
    "cnf_nl": "CNF (natural language)",
    "horn_if_then": "Horn (if–then)",
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
        (line,) = ax.plot(xsv, ys, linewidth=2.0, linestyle=line_style, color=color, label=label)
        color = line.get_color()
        if show_ci95 and y_metric == "accuracy" and yerr_lo and yerr_hi and len(yerr_lo) == len(xsv):
            ax.errorbar(
                xsv,
                ys,
                yerr=[yerr_lo, yerr_hi],
                fmt="none",
                ecolor=color,
                elinewidth=1.0,
                alpha=0.55,
                capsize=2,
            )
        if y_metric == "accuracy":
            if marker_size_by_trials and max_trials > 0 and tsv and len(tsv) == len(xsv):
                # Scale marker areas (s) so low-N points are visibly smaller.
                s_min = 18.0
                s_max = 70.0
                sizes = []
                for t in tsv:
                    frac = max(0.0, min(1.0, float(t) / float(max_trials)))
                    sizes.append(s_min + (s_max - s_min) * frac)
                ax.scatter(xsv, ys, s=sizes, color=color, edgecolors=color, alpha=0.9, zorder=3)
            else:
                ax.scatter(xsv, ys, s=36.0, color=color, edgecolors=color, alpha=0.9, zorder=3)
        plotted += 1

    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(True, alpha=0.25)
    ax.set_yscale(y_scale)
    if y_lim is not None:
        ax.set_ylim(*y_lim)
    if plotted > 0 and show_legend:
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
        if int(min_trials) > 1:
            notes.append(f"min N={int(min_trials)}")
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
        Line2D([0], [0], color="#1a202c", lw=2.0, linestyle="-", label="SAT"),
        Line2D([0], [0], color="#1a202c", lw=2.0, linestyle="--", label="UNSAT"),
    ]
    leg = ax.legend(handles=handles, loc="lower right", fontsize=8.5, frameon=False, title=None)
    ax.add_artist(leg)


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
        y_lim=(0.0, 1.0),
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
        y_lim=(0.0, 1.0),
        y_scale="linear",
    )

    # Optional small legend describing SAT vs UNSAT line styles.
    if show_style_legend:
        _add_satflag_style_legend(ax)
    return meta


def _figure_rq1(groups: Sequence[Dict[str, Any]], *, out_path: Path, accuracy_mode: str, exclude_run_regex: str) -> Dict[str, Any]:
    # Representation effects across Horn vs Non-Horn (rows) and clause length maxlen (columns).
    #
    # Controlled target: OpenAI gpt-5.2 (think_none) to avoid mixing provider/model effects into RQ1.
    base = {
        "provider": "openai",
        "model": "gpt-5.2*",
        "thinking_mode": "think_none",
        "prompt_label": "examples_only",
    }
    lens = [3, 4, 5]
    subsets = [1, 0]  # Horn, Non-Horn

    fig, axes = plt.subplots(len(subsets), len(lens), figsize=(13.8, 6.6), sharex=True, sharey=True)
    meta: Dict[str, Any] = {"figure": "rq1", "output": str(out_path), "layout": {"rows": "subset", "cols": "maxlen"}}

    for i, horn in enumerate(subsets):
        for j, maxlen in enumerate(lens):
            ax = axes[i][j]
            show_legend = bool(i == 0 and j == 0)
            title = f"{SUBSET_LABEL.get(int(horn), str(horn))} · len={maxlen}"
            m = _plot_accuracy_sat_unsat_overlay(
                ax,
                groups=groups,
                base_filters={**base, "horn": int(horn), "maxlen": int(maxlen)},
                series_field="representation",
                x_field="maxvars",
                y_mode=accuracy_mode,
                exclude_run_regex=exclude_run_regex,
                preferred_series_order=["cnf_compact", "cnf_nl", "horn_if_then"],
                min_trials=3,
                show_ci95=True,
                marker_size_by_trials=False,  # per-maxlen per-sat has fixed N≈5; keep clean
                show_legend=show_legend,
                show_style_legend=show_legend,
                title=title,
                x_label="# vars (n)",
                y_label=f"Accuracy ({accuracy_mode})",
            )
            meta[f"{horn}_{maxlen}"] = m

    fig.suptitle("RQ1: Representation (OpenAI · gpt-5.2 · think_none · examples-only)")
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return meta


def _figure_rq2(groups: Sequence[Dict[str, Any]], *, out_path: Path, accuracy_mode: str, exclude_run_regex: str) -> Dict[str, Any]:
    # Prompting policy across Horn vs Non-Horn (rows) and maxlen (columns).
    #
    # Controlled target: OpenAI gpt-5.2 (think_none). Representation fixed to cnf_compact to isolate prompting.
    base = {
        "provider": "openai",
        "model": "gpt-5.2*",
        "thinking_mode": "think_none",
        "representation": "cnf_compact",
    }
    lens = [3, 4, 5]
    subsets = [1, 0]

    fig, axes = plt.subplots(len(subsets), len(lens), figsize=(13.8, 6.6), sharex=True, sharey=True)
    meta: Dict[str, Any] = {"figure": "rq2", "output": str(out_path), "layout": {"rows": "subset", "cols": "maxlen"}}

    for i, horn in enumerate(subsets):
        for j, maxlen in enumerate(lens):
            ax = axes[i][j]
            show_legend = bool(i == 0 and j == 0)
            title = f"{SUBSET_LABEL.get(int(horn), str(horn))} · len={maxlen}"

            if int(horn) == 1:
                allowed = ["examples_only", "horn_alg_from", "horn_alg_linear"]
                pref = ["examples_only", "horn_alg_from", "horn_alg_linear"]
            else:
                allowed = ["examples_only", "dpll_alg_from", "dpll_alg_linear"]
                pref = ["examples_only", "dpll_alg_from", "dpll_alg_linear"]

            m = _plot_accuracy_sat_unsat_overlay(
                ax,
                groups=groups,
                base_filters={**base, "horn": int(horn), "maxlen": int(maxlen)},
                series_field="prompt_label",
                x_field="maxvars",
                y_mode=accuracy_mode,
                exclude_run_regex=exclude_run_regex,
                allowed_series=allowed,
                preferred_series_order=pref,
                min_trials=3,
                show_ci95=True,
                marker_size_by_trials=False,
                show_legend=show_legend,
                show_style_legend=show_legend,
                title=title,
                x_label="# vars (n)",
                y_label=f"Accuracy ({accuracy_mode})",
            )
            meta[f"{horn}_{maxlen}"] = m

    fig.suptitle("RQ2: Prompting policy (OpenAI · gpt-5.2 · think_none · cnf_compact)")
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
    include_latency_panel: bool,
) -> Dict[str, Any]:
    # Test-time compute / thinking vs accuracy, cost, and latency.
    #
    # Layout:
    # - columns: maxlen (3/4/5)
    # - rows: subset (Horn/Non-Horn) × metric (accuracy, cost/item, latency)
    #
    # We focus on UNSAT for the compute story (SAT is often saturated and hides the marginal benefit).
    base = {
        "provider": "openai",
        "representation": "cnf_compact",
        "prompt_label": "examples_only",
        "satflag": 0,
    }
    lens = [3, 4, 5]
    subsets = [1, 0]

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
        key = f"openai/{model}/{thinking_mode}"
        series_keys.append(key)
        tm_disp = thinking_mode.replace("think_", "") if thinking_mode else "?"
        label_map[key] = f"openai/{_short_openai_model(model)} ({tm_disp})"
    color_map = _make_color_map(sorted(set(series_keys)))

    metric_specs: List[Dict[str, Any]] = [
        {
            "name": "accuracy",
            "y_metric": "accuracy",
            "y_mode": str(accuracy_mode),
            "y_label": f"Accuracy ({accuracy_mode})",
            "y_scale": "linear",
            "y_lim": (0.0, 1.0),
            "show_ci95": True,
        },
        {
            "name": "cost",
            "y_metric": "cost_per_item_usd",
            "y_mode": "nonpending",
            "y_label": "USD / item",
            "y_scale": "log",
            "y_lim": None,
            "show_ci95": False,
        },
    ]
    if include_latency_panel:
        metric_specs.append(
            {
                "name": "latency",
                "y_metric": "latency_s_mean",
                "y_mode": "nonpending",
                "y_label": "Latency (s, mean)",
                "y_scale": "linear",
                "y_lim": None,
                "show_ci95": False,
            }
        )

    n_metric = len(metric_specs)
    nrows = len(subsets) * n_metric
    ncols = len(lens)
    fig_h = 2.0 * nrows + 1.8
    fig, axes = plt.subplots(nrows, ncols, figsize=(13.8, fig_h), sharex=True)
    meta: Dict[str, Any] = {
        "figure": "rq3",
        "output": str(out_path),
        "layout": {"rows": "subset×metric", "cols": "maxlen"},
        "note": "RQ3 focuses on UNSAT (satflag=0) to highlight marginal benefit of thinking/compute.",
    }

    # Normalize axes indexing when nrows/ncols == 1
    if nrows == 1:
        axes = [axes]
    if ncols == 1:
        axes = [[ax] for ax in axes]

    for si, horn in enumerate(subsets):
        for mi, spec in enumerate(metric_specs):
            row = si * n_metric + mi
            for j, maxlen in enumerate(lens):
                ax = axes[row][j]
                show_legend = bool(row == 0 and j == 0)
                # Column titles only on top row
                if row == 0:
                    ax.set_title(f"len={maxlen}")

                rows_slice = _filter_groups(
                    groups,
                    filters={**base, "horn": int(horn), "maxlen": int(maxlen)},
                    exclude_run_regex=exclude_run_regex,
                )
                for rr in rows_slice:
                    model = str(rr.get("model") or "")
                    thinking_mode = str(rr.get("thinking_mode") or "")
                    rr["_series_target_key"] = f"openai/{model}/{thinking_mode}"

                _plot_line_panel(
                    ax,
                    rows=rows_slice,
                    series_field="_series_target_key",
                    x_field="maxvars",
                    y_metric=str(spec["y_metric"]),
                    y_mode=str(spec["y_mode"]),
                    min_trials=3,
                    show_ci95=bool(spec["show_ci95"]) if spec["y_metric"] == "accuracy" else False,
                    marker_size_by_trials=False,
                    show_legend=show_legend,
                    line_style="-",
                    color_map=color_map,
                    label_map=label_map,
                    title="",
                    x_label="",
                    y_label="",
                    y_lim=spec.get("y_lim"),
                    y_scale=str(spec.get("y_scale") or "linear"),
                )

                # Left-side row labels on the first column only.
                if j == 0:
                    subset_name = SUBSET_LABEL.get(int(horn), str(horn))
                    ax.set_ylabel(f"{subset_name}\n{spec['y_label']}")

    # X labels only on bottom row
    for j, _ in enumerate(lens):
        axes[nrows - 1][j].set_xlabel("# vars (n)")

    fig.suptitle("RQ3: Test-time compute (OpenAI · cnf_compact · examples-only · UNSAT)")
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
    # - Accuracy uses NONPENDING denom so provider/API errors count against the point.
    base = {
        "representation": "cnf_compact",
        "prompt_label": "examples_only",
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

    fig, axes = plt.subplots(len(subsets), len(lens), figsize=(13.8, 6.6), sharex=True, sharey=True)
    meta: Dict[str, Any] = {
        "figure": "rq5",
        "output": str(out_path),
        "layout": {"rows": "subset", "cols": "maxlen"},
        "note": "RQ5 uses nonpending accuracy (errors count against denom) and includes thinking_mode as separate series.",
    }

    for i, horn in enumerate(subsets):
        for j, maxlen in enumerate(lens):
            ax = axes[i][j]
            show_legend = bool(i == 0 and j == 0)
            title = f"{SUBSET_LABEL.get(int(horn), str(horn))} · len={maxlen}"

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

            # We pass the whole groups list into the helper for sat/unsat filtering,
            # so use a base filter that matches only this (subset,maxlen) cell.
            m = _plot_accuracy_sat_unsat_overlay(
                ax,
                groups=rows_slice,  # already filtered by subset/maxlen; keep the helper simple
                base_filters={},
                series_field="_series_target_key",
                x_field="maxvars",
                y_mode="nonpending",
                exclude_run_regex=None,  # already applied
                min_trials=3,
                show_ci95=True,
                marker_size_by_trials=False,  # per-maxlen per-sat usually fixed N≈5
                show_legend=show_legend,
                show_style_legend=show_legend,
                label_map=label_map,
                title=title,
                x_label="# vars (n)",
                y_label="Accuracy (nonpending)",
            )
            meta[f"{horn}_{maxlen}"] = m

    fig.suptitle("RQ5: Cross-provider generality (cnf_compact · examples-only · per-model)")
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight")
    plt.close(fig)
    return meta


def generate_paper_figures(
    *,
    runs_dir: str,
    output_dir: str,
    accuracy_mode: str = "completed",
    include_suites: Optional[Sequence[str]] = None,
    exclude_suites: Optional[Sequence[str]] = None,
    exclude_run_regex: str = r"smoke",
    include_latency_panel_rq3: bool = True,
) -> Dict[str, Any]:
    """Generate the 5 "RQ figures" as standalone PDFs for the paper.

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

    rq1_path = out_dir / "fig_rq1.pdf"
    rq2_path = out_dir / "fig_rq2.pdf"
    rq3_path = out_dir / "fig_rq3.pdf"
    rq4_path = out_dir / "fig_rq4.pdf"
    rq5_path = out_dir / "fig_rq5.pdf"

    meta["figures"].append(_figure_rq1(groups, out_path=rq1_path, accuracy_mode=accuracy_mode, exclude_run_regex=exclude_run_regex))
    meta["figures"].append(_figure_rq2(groups, out_path=rq2_path, accuracy_mode=accuracy_mode, exclude_run_regex=exclude_run_regex))
    meta["figures"].append(
        _figure_rq3(
            groups,
            out_path=rq3_path,
            accuracy_mode=accuracy_mode,
            exclude_run_regex=exclude_run_regex,
            include_latency_panel=bool(include_latency_panel_rq3),
        )
    )
    meta["figures"].append(_figure_rq4(groups, runs_dir=runs_path, out_path=rq4_path, accuracy_mode=accuracy_mode, exclude_run_regex=exclude_run_regex))
    meta["figures"].append(_figure_rq5(groups, out_path=rq5_path, accuracy_mode=accuracy_mode, exclude_run_regex=exclude_run_regex))

    (out_dir / "paper_figures.meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True), encoding="utf-8")
    return meta

