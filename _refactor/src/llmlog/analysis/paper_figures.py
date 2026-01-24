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
    "horn_alg_from": "Horn algorithm (from)",
    "horn_alg_linear": "Horn algorithm (linear)",
    "dpll_alg_from": "DPLL algorithm (from)",
    "dpll_alg_linear": "DPLL algorithm (linear)",
}

SUBSET_LABEL: Mapping[int, str] = {
    1: "Horn",
    0: "Non-Horn",
}

# Consistent legend styling across all figures.
LEGEND_LOC = "lower right"
LEGEND_FONTSIZE = 7
LEGEND_KW = {
    "loc": LEGEND_LOC,
    "fontsize": LEGEND_FONTSIZE,
    "frameon": True,
    "borderaxespad": 0.1,
    "handlelength": 2.0,
    "labelspacing": 0.25,
    "handletextpad": 0.4,
    "columnspacing": 0.9,
}

# Line overlap aid: draw a subtle "halo" (background-colored stroke) behind lines.
# This improves readability when series are very close without changing the data.
LINE_HALO: bool = True
LINE_HALO_EXTRA_PTS: float = 2.0  # added to the line linewidth (in points)

# When multiple series have exactly coincident line segments, halo alone can't reveal them.
# For those segments we render a small "bundle" by separating coincident segments in *display*
# coordinates (y only) so each series remains visible without x jitter.
OVERLAP_BUNDLE_SEP_PX: float = 4.0

# Supplementary figures: optional extra x-range on the right so the in-panel
# bottom-right legend can sit in whitespace (instead of covering the last bars).
# This is applied by extending xlim; it does not change any data positions.
SUPP_LEGEND_RIGHT_PAD = 0.9

# Standard figure-level legend placement (bottom, centered).
# Using shared anchors keeps the vertical rhythm consistent across main figures.
FIG_LEGEND_Y_SINGLE = 0.02
FIG_LEGEND_Y_SERIES = 0.055
FIG_LEGEND_Y_SUBSET = 0.015

# Global figure policy:
# Only plot accuracy points when we have at least N completed trials (answered+unclear by default).
# This reduces visual emphasis on very low-completion / error-prone cells.
DEFAULT_MIN_TRIALS: int = 5

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


def _pretty_provider(provider: str) -> str:
    p = str(provider or "").strip().lower()
    return {"openai": "OpenAI", "google": "Google", "anthropic": "Anthropic"}.get(p, provider)


def _pretty_thinking_mode(thinking_mode: str) -> str:
    tm = str(thinking_mode or "").strip()
    if not tm:
        return "?"
    return tm.replace("think_", "")


def _pretty_model_name(provider: str, model: str) -> str:
    p = str(provider or "").strip().lower()
    m = str(model or "").strip()
    return _short_openai_model(m) if p == "openai" else m


def _format_target_label(provider: str, model: str, thinking_mode: str, *, multiline: bool) -> str:
    """Unified labeling for provider/model/thinking across all figures.

    - multiline=False (legends): "OpenAI gpt-5.2-pro (high)"
    - multiline=True (x-ticks): "OpenAI\\ngpt-5.2-pro (high)"
      (provider on line 1; model+thinking on line 2)
    """
    p_disp = _pretty_provider(provider)
    m_disp = _pretty_model_name(provider, model)
    tm_disp = _pretty_thinking_mode(thinking_mode)
    if multiline:
        return f"{p_disp}\n{m_disp} ({tm_disp})"
    return f"{p_disp} {m_disp} ({tm_disp})"


def _set_figure_header(fig: Any, *, title: str, context: Optional[str] = None) -> None:
    """Consistent header across figures: main title + optional context line.

    Uses fixed physical offsets (inches) so spacing is consistent across figures
    with different sizes/aspect ratios.
    """
    # Tunables (inches, measured down from the top of the figure).
    title_y_in = 0.25
    context_y_in = 0.55

    w_in = float(fig.get_size_inches()[0] if hasattr(fig, "get_size_inches") else 0.0) or 10.0
    h_in = float(fig.get_size_inches()[1] if hasattr(fig, "get_size_inches") else 0.0) or 6.0
    y_title = 1.0 - (float(title_y_in) / float(h_in))
    y_context = 1.0 - (float(context_y_in) / float(h_in))

    # Font sizes scale mildly with figure width so small single-panel figures don't
    # look "shouty" relative to multi-panel figures.
    if float(w_in) < 8.0:
        title_fs = 12
        ctx_fs = 9
    elif float(w_in) < 11.5:
        title_fs = 13
        ctx_fs = 9.5
    else:
        title_fs = 14
        ctx_fs = 10

    fig.suptitle(str(title), y=float(y_title), fontsize=int(title_fs))
    if context:
        fig.text(
            0.5,
            float(y_context),
            str(context),
            ha="center",
            va="top",
            fontsize=float(ctx_fs),
            color="#4a5568",
        )


def _tight_layout_standard(fig: Any, *, footer_in: float = 0.0) -> None:
    """Standardize spacing between header/plot/footer using inches."""
    header_in = 0.3  # reserved band for title + context
    h_in = float(fig.get_size_inches()[1] if hasattr(fig, "get_size_inches") else 0.0) or 6.0

    top = 1.0 - (float(header_in) / float(h_in))
    bottom = (float(footer_in) / float(h_in)) if float(footer_in) > 0 else 0.0
    # Clamp to sane bounds (avoid tight_layout errors on tiny figures).
    top = max(0.4, min(0.98, float(top)))
    bottom = max(0.0, min(0.4, float(bottom)))

    fig.tight_layout(rect=[0.0, float(bottom), 1.0, float(top)])


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
    min_trials: int = DEFAULT_MIN_TRIALS,
    show_ci95: bool = False,
    marker_size_by_trials: bool = False,
    show_markers: bool = False,
    # If set, force a single marker glyph for all series in this panel.
    # Useful for controlled-target figures where provider is fixed (e.g., OpenAI only),
    # so multiple marker shapes would misleadingly suggest multiple providers.
    marker_override: Optional[str] = None,
    # When multiple markers land on the same (x,y), separate them by stacking in y
    # (in display/pixel space) while keeping x exactly aligned to the data.
    marker_stack_y: bool = False,
    marker_stack_sep_px: float = 6.0,
    marker_stack_tol_px: float = 1.25,
    # When points coincide (same x and y across series), markers can still overlap.
    # A small x-jitter (as a fraction of the typical x-step) makes ties visible
    # without changing the y-values or the line geometry.
    marker_x_jitter_frac: float = 0.0,
    show_chance_baseline: bool = True,
    # Overlap strategy:
    # - stripe_overlaps: render coincident segments as a multi-color "striped" line (no x/y displacement)
    #   so the reader can see multiple series occupy the same curve.
    stripe_overlaps: bool = False,
    stripe_tol: float = 1e-9,
    show_legend: bool = True,
    show_empty_message: bool = True,
    line_style: str = "-",
    color_map: Optional[Mapping[str, Any]] = None,
    label_map: Optional[Mapping[str, str]] = None,
    allowed_series: Optional[Sequence[str]] = None,
    preferred_series_order: Optional[Sequence[str]] = None,
    # Labeling strategy:
    # - direct_labels: draw series labels at the right edge (endpoints), avoiding legend clutter.
    #   Especially helpful when lines are close/overlapping.
    direct_labels: bool = False,
    direct_label_values: bool = False,
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
    series_index: Dict[str, int] = {str(s): int(i) for i, s in enumerate(series_names)}

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
        # For target series keys ("provider/model/thinking"), match marker by provider.
        marker_map = _make_target_marker_map(series_names)
    if marker_override:
        marker_map = {str(s): str(marker_override) for s in series_names}

    all_trials: List[int] = []
    if marker_size_by_trials and y_metric == "accuracy":
        for pts in series_map.values():
            for c in pts.values():
                t = trials_for_point(c)
                if t is not None and t >= int(min_trials):
                    all_trials.append(int(t))
    max_trials = max(all_trials) if all_trials else 0

    # Typical x spacing (used for optional marker-only jitter).
    uniq_x: List[float] = sorted({float(x) for pts in series_map.values() for x in (pts.keys() if isinstance(pts, dict) else [])})
    x_step = 1.0
    if len(uniq_x) >= 2:
        diffs = [float(uniq_x[i + 1] - uniq_x[i]) for i in range(len(uniq_x) - 1)]
        diffs = [d for d in diffs if d > 0]
        if diffs:
            diffs_sorted = sorted(diffs)
            x_step = float(diffs_sorted[len(diffs_sorted) // 2])

    def _maybe_apply_line_halo(line: Any) -> None:
        """Add a background-colored halo to improve overlap readability."""
        if not LINE_HALO:
            return
        try:
            from matplotlib import patheffects as pe  # type: ignore

            bg = ax.get_facecolor()
            lw = float(line.get_linewidth()) if hasattr(line, "get_linewidth") else float(base_lw)
            line.set_path_effects(
                [
                    pe.Stroke(linewidth=float(lw) + float(LINE_HALO_EXTRA_PTS), foreground=bg),
                    pe.Normal(),
                ]
            )
        except Exception:
            # If path effects aren't available for some backend, just skip.
            return

    def _marker_xs(series_name: str, xs: Sequence[float]) -> List[float]:
        jf = float(marker_x_jitter_frac)
        if jf == 0.0:
            return [float(x) for x in xs]
        n = max(1, len(series_names))
        idx = int(series_index.get(str(series_name), 0))
        # Centered offsets: [-2,-1,0,1,2] * step * frac (for n=5).
        offset_units = float(idx) - (float(n - 1) / 2.0)
        # NOTE: marker_x_jitter_frac may be negative; this is useful to separate two overlays
        # (e.g., Horn vs Non-Horn) without changing y-values.
        dx = offset_units * jf * float(x_step)
        return [float(x) + dx for x in xs]

    def _stack_marker_ys(xs: Sequence[float], ys: Sequence[float]) -> List[float]:
        """Return ys adjusted by stacking only at colliding points.

        Stacking is done in display coordinates (pixels) and then mapped back to data y,
        so it works for both linear and log axes. X positions remain unchanged.
        """
        if not marker_stack_y:
            return [float(y) for y in ys]
        if not xs or not ys or len(xs) != len(ys):
            return [float(y) for y in ys]

        # Group indices by exact x (these are our discrete grid points).
        by_x: Dict[float, List[int]] = {}
        for i, x in enumerate(xs):
            by_x.setdefault(float(x), []).append(int(i))

        out = [float(y) for y in ys]
        sep = float(marker_stack_sep_px)
        tol = float(marker_stack_tol_px)
        if sep <= 0:
            return out

        for x, idxs in by_x.items():
            if len(idxs) <= 1:
                continue
            # Compute y in display coords so we can cluster "same spot" robustly.
            pts = []
            for i in idxs:
                y = float(ys[i])
                if math.isnan(y) or math.isinf(y):
                    continue
                y_px = float(ax.transData.transform((float(x), float(y)))[1])
                pts.append((i, y, y_px))
            if len(pts) <= 1:
                continue

            pts.sort(key=lambda t: t[2])  # by y_px
            clusters: List[List[Tuple[int, float, float]]] = []
            for it in pts:
                if not clusters:
                    clusters.append([it])
                    continue
                # Same-pixel-position cluster: if within tol pixels of the cluster's first point.
                if abs(float(it[2]) - float(clusters[-1][0][2])) <= tol:
                    clusters[-1].append(it)
                else:
                    clusters.append([it])

            for cl in clusters:
                if len(cl) <= 1:
                    continue
                k = len(cl)
                # Centered offsets: [-1.5, -0.5, 0.5, 1.5] * sep (for k=4).
                for j, (i, y, y_px) in enumerate(cl):
                    off = (float(j) - (float(k - 1) / 2.0)) * sep
                    new_disp = (float(x), float(y_px) + float(off))
                    # Map back to data space to get the adjusted y.
                    y_new = float(ax.transData.inverted().transform(new_disp)[1])
                    out[int(i)] = float(y_new)
        return out

    base_lw = 2.0
    cmap: Dict[str, Any] = _make_color_map(series_names)
    if color_map:
        for k, v in color_map.items():
            if k in cmap:
                cmap[k] = v

    plotted = 0
    per_series_x: Dict[str, List[float]] = {}
    per_series_y: Dict[str, List[float]] = {}
    per_series_y_by_x: Dict[str, Dict[float, float]] = {}
    per_series_ci: Dict[str, Tuple[List[float], List[float]]] = {}
    per_series_trials: Dict[str, List[int]] = {}

    for s in series_names:
        pts = series_map.get(s) or {}
        xs = sorted(pts.keys())
        xsv: List[float] = []
        ys: List[float] = []
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
        per_series_x[str(s)] = xsv
        per_series_y[str(s)] = ys
        per_series_y_by_x[str(s)] = {float(x): float(y) for x, y in zip(xsv, ys)}
        per_series_ci[str(s)] = (yerr_lo, yerr_hi)
        per_series_trials[str(s)] = tsv
        plotted += 1

    if plotted > 0 and y_metric == "accuracy" and stripe_overlaps:
        # Render overlapping segments as multi-color stripes (no x/y displacement).
        # Each stripe gets ~1/K of the normal linewidth when K series overlap.
        segments: Dict[Tuple[float, float], List[Tuple[str, float, float]]] = {}
        for s, xsv in per_series_x.items():
            y_by_x = per_series_y_by_x.get(s) or {}
            for i in range(len(xsv) - 1):
                x0 = float(xsv[i])
                x1 = float(xsv[i + 1])
                y0 = float(y_by_x.get(x0, float("nan")))
                y1 = float(y_by_x.get(x1, float("nan")))
                if math.isnan(y0) or math.isnan(y1):
                    continue
                segments.setdefault((x0, x1), []).append((s, y0, y1))

        def sidx(name: str) -> int:
            try:
                return int(series_names.index(name))
            except Exception:
                return 10**9

        for (x0, x1), items in sorted(segments.items(), key=lambda kv: (kv[0][0], kv[0][1])):
            # Cluster by identical (y0,y1) segments (within tolerance).
            items_sorted = sorted(items, key=lambda t: (t[1], t[2], sidx(t[0])))
            clusters: List[List[Tuple[str, float, float]]] = []
            for it in items_sorted:
                placed = False
                for cl in clusters:
                    if abs(float(it[1]) - float(cl[0][1])) <= float(stripe_tol) and abs(float(it[2]) - float(cl[0][2])) <= float(
                        stripe_tol
                    ):
                        cl.append(it)
                        placed = True
                        break
                if not placed:
                    clusters.append([it])

            for cl in clusters:
                s_list = [str(t[0]) for t in cl]
                y0 = float(cl[0][1])
                y1 = float(cl[0][2])
                if len(cl) == 1:
                    s = s_list[0]
                    ln = ax.plot(
                        [x0, x1],
                        [y0, y1],
                        linewidth=base_lw,
                        linestyle=line_style,
                        color=cmap.get(s),
                        solid_capstyle="round",
                        solid_joinstyle="round",
                        label="_nolegend_",
                    )
                    if ln:
                        _maybe_apply_line_halo(ln[0])
                    continue

                ordered = sorted(s_list, key=sidx)
                k = int(len(ordered))
                sep_px = float(OVERLAP_BUNDLE_SEP_PX)
                # Separate coincident segments in y (display space) so the reader can see
                # that multiple series occupy the same curve over this span.
                try:
                    p0 = ax.transData.transform((float(x0), float(y0)))
                    p1 = ax.transData.transform((float(x1), float(y1)))
                    x0_px, y0_px = float(p0[0]), float(p0[1])
                    x1_px, y1_px = float(p1[0]), float(p1[1])
                    inv = ax.transData.inverted()
                except Exception:
                    x0_px = y0_px = x1_px = y1_px = 0.0
                    inv = None

                for j, s in enumerate(ordered):
                    off = (float(j) - (float(k - 1) / 2.0)) * float(sep_px)
                    if inv is not None:
                        y0_d = float(inv.transform((float(x0_px), float(y0_px) + float(off)))[1])
                        y1_d = float(inv.transform((float(x1_px), float(y1_px) + float(off)))[1])
                    else:
                        # Fallback: tiny additive y offset in data space (should be rare).
                        y0_d = float(y0) + float(off) * 1e-3
                        y1_d = float(y1) + float(off) * 1e-3
                    ax.plot(
                        [x0, x1],
                        [y0_d, y1_d],
                        linewidth=base_lw,
                        linestyle=line_style,
                        color=cmap.get(s),
                        solid_capstyle="round",
                        solid_joinstyle="round",
                        label="_nolegend_",
                        zorder=3,
                    )
    else:
        # Standard: one line per series.
        for s in series_names:
            xsv = per_series_x.get(str(s))
            ys = per_series_y.get(str(s))
            if not xsv or not ys:
                continue
            label = (label_map or {}).get(s) if label_map and s in label_map else _pretty_series_label(series_field, str(s))
            ln = ax.plot(
                xsv,
                ys,
                linewidth=base_lw,
                linestyle=line_style,
                color=cmap.get(str(s)),
                label=label,
                solid_capstyle="round",
                solid_joinstyle="round",
            )
            if ln:
                _maybe_apply_line_halo(ln[0])

    # Error bars / markers (draw on top; do not affect legend).
    for s in series_names:
        xsv = per_series_x.get(str(s))
        ys = per_series_y.get(str(s))
        if not xsv or not ys:
            continue
        yerr_lo, yerr_hi = per_series_ci.get(str(s), ([], []))
        color = cmap.get(str(s))
        xsv_mark = _marker_xs(str(s), xsv)
        ys_mark = _stack_marker_ys(xsv_mark, ys) if show_markers else ys
        if show_ci95 and y_metric == "accuracy" and yerr_lo and yerr_hi and len(yerr_lo) == len(xsv):
            ax.errorbar(
                xsv_mark,
                ys,
                yerr=[yerr_lo, yerr_hi],
                fmt="none",
                ecolor=color,
                elinewidth=1.0,
                alpha=0.55,
                capsize=2,
                label="_nolegend_",
            )
        if y_metric == "accuracy" and show_markers:
            tsv = per_series_trials.get(str(s), [])
            marker = marker_map.get(str(s), "o")
            if marker_size_by_trials and max_trials > 0 and tsv and len(tsv) == len(xsv):
                s_min = 18.0
                s_max = 70.0
                sizes = []
                for t in tsv:
                    frac = max(0.0, min(1.0, float(t) / float(max_trials)))
                    sizes.append(s_min + (s_max - s_min) * frac)
                ax.scatter(
                    xsv_mark,
                    ys_mark,
                    s=sizes,
                    marker=marker,
                    facecolors="none",
                    edgecolors=color,
                    linewidths=1.6,
                    alpha=0.95,
                    zorder=4,
                    label="_nolegend_",
                )
            else:
                ax.scatter(
                    xsv_mark,
                    ys_mark,
                    s=42.0,
                    marker=marker,
                    facecolors="none",
                    edgecolors=color,
                    linewidths=1.6,
                    alpha=0.95,
                    zorder=4,
                    label="_nolegend_",
                )

    # If we used striped rendering, add one legend handle per series.
    if plotted > 0 and y_metric == "accuracy" and stripe_overlaps:
        for s in series_names:
            if str(s) not in per_series_x:
                continue
            label = (label_map or {}).get(s) if label_map and s in label_map else _pretty_series_label(series_field, str(s))
            if show_markers:
                mkr = marker_map.get(str(s), "o")
                ax.plot(
                    [],
                    [],
                    linewidth=base_lw,
                    linestyle=line_style,
                    color=cmap.get(str(s)),
                    marker=mkr,
                    markersize=6.0,
                    markerfacecolor="none",
                    markeredgecolor=cmap.get(str(s)),
                    label=label,
                )
            else:
                ax.plot(
                    [],
                    [],
                    linewidth=base_lw,
                    linestyle=line_style,
                    color=cmap.get(str(s)),
                    label=label,
                )

    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.grid(True, alpha=0.25)
    ax.set_yscale(y_scale)
    if y_lim is not None:
        ax.set_ylim(*y_lim)

    def _direct_label_text(label: str, y: float) -> str:
        if not direct_label_values:
            return str(label)
        if y_metric == "accuracy":
            return f"{label} {y:.2f}"
        return str(label)

    def _apply_direct_labels() -> None:
        # Place labels at series endpoints, with a simple vertical repel to keep them readable.
        if plotted <= 0:
            return
        items: List[Tuple[str, float, float, Any]] = []  # (label, x_last, y_last, color)
        for s in series_names:
            xsv = per_series_x.get(str(s))
            ys = per_series_y.get(str(s))
            if not xsv or not ys:
                continue
            label = (label_map or {}).get(s) if label_map and s in label_map else _pretty_series_label(series_field, str(s))
            x_last = float(xsv[-1])
            y_last = float(ys[-1])
            if math.isnan(y_last) or math.isinf(y_last):
                continue
            items.append((str(label), x_last, y_last, cmap.get(str(s))))
        if not items:
            return

        x_min = min(x for _lbl, x, _y, _c in items)
        x_max = max(x for _lbl, x, _y, _c in items)
        x_range = float(x_max - x_min)
        x_pad = (0.035 * x_range) if x_range > 0 else 0.6

        y0, y1 = ax.get_ylim()
        y_lo = float(min(y0, y1))
        y_hi = float(max(y0, y1))
        # Keep label positions inside the visible frame.
        y_margin = 0.01 * float(y_hi - y_lo) if (y_hi - y_lo) > 0 else 0.01

        if str(y_scale) == "log":
            # Repel in log space for nicer spacing on log axes.
            def ly(v: float) -> float:
                return math.log10(max(v, 1e-12))

            def uy(v: float) -> float:
                return 10.0 ** v

            items_sorted = sorted(items, key=lambda t: ly(float(t[2])))
            min_sep = 0.085  # ~20% ratio
            placed_log: List[float] = []
            for lbl, x, y, c in items_sorted:
                yy = ly(float(y))
                if placed_log:
                    yy = max(yy, placed_log[-1] + float(min_sep))
                placed_log.append(yy)
            # Backward pass to keep within upper bound
            hi_log = ly(max(y_hi - y_margin, 1e-12))
            lo_log = ly(max(y_lo + y_margin, 1e-12))
            for i in range(len(placed_log) - 1, -1, -1):
                if placed_log[i] > hi_log:
                    placed_log[i] = hi_log
                if i > 0 and placed_log[i - 1] > placed_log[i] - float(min_sep):
                    placed_log[i - 1] = placed_log[i] - float(min_sep)
            placed_log = [max(lo_log, min(hi_log, v)) for v in placed_log]

            for (lbl, x, y, c), yy_log in zip(items_sorted, placed_log):
                y_text = uy(float(yy_log))
                ax.plot([x, x + x_pad * 0.6], [y, y_text], color=c, lw=0.9, alpha=0.65, zorder=5)
                ax.text(
                    x + x_pad,
                    y_text,
                    _direct_label_text(lbl, float(y)),
                    color=c,
                    fontsize=9,
                    va="center",
                    ha="left",
                    zorder=6,
                )
        else:
            items_sorted = sorted(items, key=lambda t: float(t[2]))
            min_sep = 0.022 * float(y_hi - y_lo) if (y_hi - y_lo) > 0 else 0.02
            placed: List[float] = []
            for lbl, x, y, c in items_sorted:
                yy = float(y)
                if placed:
                    yy = max(yy, placed[-1] + float(min_sep))
                placed.append(yy)
            # Backward pass to keep within upper bound
            hi = float(y_hi - y_margin)
            lo = float(y_lo + y_margin)
            for i in range(len(placed) - 1, -1, -1):
                if placed[i] > hi:
                    placed[i] = hi
                if i > 0 and placed[i - 1] > placed[i] - float(min_sep):
                    placed[i - 1] = placed[i] - float(min_sep)
            placed = [max(lo, min(hi, v)) for v in placed]

            for (lbl, x, y, c), y_text in zip(items_sorted, placed):
                ax.plot([x, x + x_pad * 0.6], [y, y_text], color=c, lw=0.9, alpha=0.65, zorder=5)
                ax.text(
                    x + x_pad,
                    y_text,
                    _direct_label_text(lbl, float(y)),
                    color=c,
                    fontsize=9,
                    va="center",
                    ha="left",
                    zorder=6,
                )

        # Ensure right margin for labels.
        cur_x0, cur_x1 = ax.get_xlim()
        ax.set_xlim(cur_x0, max(cur_x1, x_max + x_pad * 3.0))

    if plotted > 0:
        if direct_labels:
            _apply_direct_labels()
        elif show_legend:
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
        if int(min_trials) > 1:
            notes.append(f"N≥{int(min_trials)}")
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


def _make_marker_map(keys: Sequence[str]) -> Dict[str, str]:
    """Deterministic marker map for series keys (stable across figures/runs)."""
    uniq = list(dict.fromkeys([str(k) for k in keys if k is not None]))
    if not uniq:
        return {}
    # Chosen for print legibility at small sizes.
    markers = ["o", "s", "^", "D", "v", "<", ">", "p", "h", "*", "X", "P"]
    out: Dict[str, str] = {}
    for k in uniq:
        h = hashlib.md5(k.encode("utf-8")).hexdigest()
        idx = int(h[:8], 16) % int(len(markers))
        out[k] = str(markers[int(idx)])
    return out


def _make_target_marker_map(keys: Sequence[str]) -> Dict[str, str]:
    """Marker-map for target series keys, stable across figures.

    Convention (matches provider palette semantics):
    - Anthropic: triangle
    - Google: circle
    - OpenAI: square
    """
    uniq = list(dict.fromkeys([str(k) for k in keys if k is not None]))
    if not uniq:
        return {}

    by_provider = {
        "anthropic": "^",  # triangle up
        "google": "o",  # circle
        "openai": "s",  # square
    }

    out: Dict[str, str] = {}
    for k in uniq:
        provider = str(k).split("/", 1)[0].strip().lower() if "/" in str(k) else ""
        m = by_provider.get(provider)
        if m:
            out[k] = m
            continue
        # Deterministic fallback for unknown providers / non-target keys.
        h = hashlib.md5(k.encode("utf-8")).hexdigest()
        markers = ["o", "s", "^", "D", "v", "<", ">", "p", "h", "*", "X", "P"]
        idx = int(h[:8], 16) % int(len(markers))
        out[k] = str(markers[int(idx)])
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


def _combined_subset_series_legend(
    *,
    series: Sequence[Tuple[str, str, Any]],
    subset_order: Sequence[Tuple[str, str]] = (("Horn", "-"), ("Non-Horn", "--")),
    marker: str = "s",
    lw: float = 2.4,
    markersize: float = 6.0,
) -> Tuple[List[Any], List[str]]:
    """Legend entries that fully specify (subset × series).

    `series` items are (series_key, display_label, color).
    Each legend label becomes e.g. "Horn · examples-only", so readers do not need
    to mentally combine a separate subset key with a separate series key.
    """
    from matplotlib.lines import Line2D  # type: ignore

    handles: List[Any] = []
    labels: List[str] = []
    for subset_label, linestyle in subset_order:
        for _k, disp, color in series:
            handles.append(
                Line2D(
                    [0],
                    [0],
                    color=color,
                    lw=float(lw),
                    linestyle=str(linestyle),
                    marker=str(marker),
                    markersize=float(markersize),
                    markerfacecolor="none",
                    markeredgecolor=color,
                )
            )
            labels.append(f"{subset_label} · {disp}")
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
    min_trials: int = DEFAULT_MIN_TRIALS,
    show_ci95: bool = True,
    marker_size_by_trials: bool = True,
    show_markers: bool = False,
    marker_override: Optional[str] = None,
    marker_x_jitter_frac: float = 0.0,
    marker_stack_y: bool = False,
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

    horn_label_map = {s: f"Horn · {base_label(s)}" for s in series_vals}
    nonhorn_label_map = {s: f"Non-Horn · {base_label(s)}" for s in series_vals}

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
        show_markers=show_markers,
        marker_override=marker_override,
        marker_x_jitter_frac=0.0,
        marker_stack_y=marker_stack_y,
        stripe_overlaps=True,
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
        show_markers=show_markers,
        marker_override=marker_override,
        marker_x_jitter_frac=0.0,
        marker_stack_y=marker_stack_y,
        stripe_overlaps=True,
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
            hl = horn_label_map.get(s, f"Horn · {base_label(s)}")
            nl = nonhorn_label_map.get(s, f"Non-Horn · {base_label(s)}")
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
    # Keep main-figure typography consistent: use the same wide format as other main figures,
    # even when we show a single panel.
    fig, axes = plt.subplots(1, len(lens), figsize=(13.8, 3.6), sharex=True, sharey=True)
    if len(lens) == 1:
        axes = [axes]
    meta: Dict[str, Any] = {
        "figure": "representation_effects",
        "output": str(out_path),
        "layout": {"rows": "combined subset", "cols": "maxlen"},
    }

    for j, maxlen in enumerate(lens):
        ax = axes[j]
        show_legend = False  # use a single figure-level legend
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
            min_trials=DEFAULT_MIN_TRIALS,
            show_ci95=False,
            marker_size_by_trials=False,
            show_markers=True,
            marker_override="s",  # OpenAI (controlled target)
            marker_x_jitter_frac=0.0,
            marker_stack_y=True,
            show_legend=show_legend,
            title=title,
            x_label="# vars (n)",
            y_label=f"Accuracy ({accuracy_mode})" if j == 0 else "",
        )
        meta[f"{maxlen}"] = m

    target = _format_target_label(str(base["provider"]), str(base["model"]), str(base["thinking_mode"]), multiline=False)
    _set_figure_header(
        fig,
        title="Representation effects",
        context=(
            "Subset: Horn + Non-Horn · Representation: Compact CNF vs Natural Language CNF · "
            f"Prompt: examples-only · Targets: {target}"
        ),
    )

    # In-panel legend (bottom-right): list fully specified entries so no mental combining is required.
    rep_series_keys = ["cnf_compact", "cnf_nl"]
    series = [(s, _pretty_series_label("representation", str(s)), rep_color_map.get(str(s), "#4a5568")) for s in rep_series_keys]
    for ax in axes:
        # Only list series actually present in this panel (avoid "ghost" legend entries).
        _handles_present, _labels_present = ax.get_legend_handles_labels()
        present = {str(lbl) for lbl in _labels_present if lbl and not str(lbl).startswith("_")}
        h, l = _combined_subset_series_legend(series=series, marker="s")
        keep = [(hh, ll) for hh, ll in zip(h, l) if ll in present]
        if keep:
            _apply_legend(ax, [hh for hh, _ll in keep], [ll for _hh, ll in keep], ncol=1)

    _tight_layout_standard(fig)
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
        show_legend = False  # use a single figure-level legend
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
            min_trials=DEFAULT_MIN_TRIALS,
            show_ci95=False,
            marker_size_by_trials=False,
            show_markers=True,
            marker_override="s",  # OpenAI (controlled target)
            marker_x_jitter_frac=0.0,
            marker_stack_y=True,
            show_legend=show_legend,
            title=title,
            x_label="# vars (n)",
            y_label=f"Accuracy ({accuracy_mode})" if j == 0 else "",
        )
        meta[f"{maxlen}"] = m

    target = _format_target_label(str(base["provider"]), str(base["model"]), str(base["thinking_mode"]), multiline=False)
    _set_figure_header(
        fig,
        title="Prompting-policy effects",
        context=(
            "Subset: Horn + Non-Horn · Representation: Compact CNF · "
            f"Prompt: examples-only + algorithmic variants · Targets: {target}"
        ),
    )

    # In-panel legend (bottom-right): list fully specified entries (3 Horn + 3 Non-Horn).
    from matplotlib.lines import Line2D  # type: ignore

    horn_series = ["examples_only", "horn_alg_from", "horn_alg_linear"]
    nonhorn_series = ["examples_only", "dpll_alg_from", "dpll_alg_linear"]

    def _make_prompt_legend() -> Tuple[List[Any], List[str]]:
        hh: List[Any] = []
        ll: List[str] = []
        for s in horn_series:
            color = prompt_color_map.get(str(s), "#4a5568")
            disp = _pretty_series_label("prompt_label", str(s))
            hh.append(
                Line2D(
                    [0],
                    [0],
                    color=color,
                    lw=2.4,
                    linestyle="-",
                    marker="s",
                    markersize=6.0,
                    markerfacecolor="none",
                    markeredgecolor=color,
                )
            )
            ll.append(f"Horn · {disp}")
        for s in nonhorn_series:
            color = prompt_color_map.get(str(s), "#4a5568")
            disp = _pretty_series_label("prompt_label", str(s))
            hh.append(
                Line2D(
                    [0],
                    [0],
                    color=color,
                    lw=2.4,
                    linestyle="--",
                    marker="s",
                    markersize=6.0,
                    markerfacecolor="none",
                    markeredgecolor=color,
                )
            )
            ll.append(f"Non-Horn · {disp}")
        return hh, ll

    for ax in axes:
        # Only list series actually present in this panel (avoid "ghost" legend entries).
        _handles_present, _labels_present = ax.get_legend_handles_labels()
        present = {str(lbl) for lbl in _labels_present if lbl and not str(lbl).startswith("_")}
        h, l = _make_prompt_legend()
        keep = [(hh, ll) for hh, ll in zip(h, l) if ll in present]
        if keep:
            _apply_legend(ax, [hh for hh, _ll in keep], [ll for _hh, ll in keep], ncol=1)

    _tight_layout_standard(fig)
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
        label_map[key] = _format_target_label("openai", str(model), str(thinking_mode), multiline=False)
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

        horn_label_map = {k: f"Horn · {label_map.get(k, k)}" for k in allowed_series}
        nonhorn_label_map = {k: f"Non-Horn · {label_map.get(k, k)}" for k in allowed_series}

        _plot_line_panel(
            ax_acc,
            rows=horn_rows,
            series_field="_series_target_key",
            x_field="maxvars",
            y_metric="accuracy",
            y_mode=str(accuracy_mode),
            min_trials=DEFAULT_MIN_TRIALS,
            show_ci95=False,
            marker_size_by_trials=False,
            show_markers=True,
            marker_x_jitter_frac=0.0,
            marker_stack_y=True,
            stripe_overlaps=True,
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
            min_trials=DEFAULT_MIN_TRIALS,
            show_ci95=False,
            marker_size_by_trials=False,
            show_markers=True,
            marker_x_jitter_frac=0.0,
            marker_stack_y=True,
            stripe_overlaps=True,
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

        # Set panel title *after* plotting; `_plot_line_panel(..., title="")` clears titles.
        ax_acc.set_title(f"k={maxlen}")

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
            min_trials=DEFAULT_MIN_TRIALS,
            show_ci95=False,
            marker_size_by_trials=False,
            show_markers=False,
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
            min_trials=DEFAULT_MIN_TRIALS,
            show_ci95=False,
            marker_size_by_trials=False,
            show_markers=False,
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

        # Match the model-comparison figure: show k labels on both rows.
        # Set title after plotting; `_plot_line_panel(..., title="")` clears titles.
        ax_cost.set_title(f"k={maxlen}")

        if j == 0:
            ax_cost.set_ylabel("USD / slice (10 items; log)")
        ax_cost.set_xlabel("# vars (n)")
        _apply_usd_axis_format(ax_cost)

    ordered_keys = sorted(set(allowed_series), key=lambda k: str(label_map.get(k, k)))
    target_disp = " + ".join([str(label_map.get(k, k)) for k in ordered_keys]) if ordered_keys else "see legend"
    _set_figure_header(
        fig,
        title="Test-time compute",
        context=f"Subset: Horn + Non-Horn · Representation: Compact CNF · Prompt: examples-only · Targets: {target_disp}",
    )
    # In-panel legends (bottom-right): show the combined subset×model legend inside each subplot.
    from matplotlib.lines import Line2D  # type: ignore
    marker_map = _make_target_marker_map(ordered_keys)

    def _make_compute_legend() -> Tuple[List[Any], List[str]]:
        hh: List[Any] = []
        ll: List[str] = []
        for subset_label, linestyle in (("Horn", "-"), ("Non-Horn", "--")):
            for k in ordered_keys:
                color = color_map.get(k, "#4a5568")
                hh.append(
                    Line2D(
                        [0],
                        [0],
                        color=color,
                        lw=2.4,
                        linestyle=str(linestyle),
                        marker=marker_map.get(k, "s"),
                        markersize=6.0,
                        markerfacecolor="none",
                        markeredgecolor=color,
                    )
                )
                ll.append(f"{subset_label} · {label_map.get(k, k)}")
        return hh, ll

    for row in axes:
        for ax in row:
            # Only list series actually present in this panel (avoid "ghost" legend entries).
            _handles_present, _labels_present = ax.get_legend_handles_labels()
            present = {str(lbl) for lbl in _labels_present if lbl and not str(lbl).startswith("_")}
            h, l = _make_compute_legend()
            keep = [(hh, ll) for hh, ll in zip(h, l) if ll in present]
            if keep:
                _apply_legend(ax, [hh for hh, _ll in keep], [ll for _hh, ll in keep], ncol=1)

    _tight_layout_standard(fig)
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
        label_map[key] = _format_target_label(provider, model, thinking_mode, multiline=False)
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
                min_trials=DEFAULT_MIN_TRIALS,
                show_ci95=False,
                marker_size_by_trials=False,  # per-maxlen per-sat usually fixed N≈5
                show_markers=True,
                marker_x_jitter_frac=0.0,
                marker_stack_y=True,
                stripe_overlaps=True,
                show_legend=True,
                line_style="-",
                color_map=color_map,
                label_map=label_map,
                title=title,
                x_label="# vars (n)",
                y_label=f"Accuracy ({accuracy_mode})",
                y_lim=(-0.05, 1.05),
                y_scale="linear",
            )
            # Only show ticks for evaluated n values (avoid implying intermediate points like 15/25/35).
            try:
                ax.set_xticks([float(x) for x in (base.get("maxvars") or [])])
            except Exception:
                pass
            meta[f"{horn}_{maxlen}"] = m

    _set_figure_header(
        fig,
        title="Model comparison under a fixed task setting",
        context="Subset: Horn + Non-Horn · Representation: Compact CNF · Prompt: examples-only · Targets: see legend",
    )
    _tight_layout_standard(fig)
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
        return _format_target_label(p, m, tm, multiline=True)

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
        (axes[0], targets_by_model, "Horn", 1),
        (axes[1], targets_by_model, "Non-Horn", 0),
    ]:
        # Chance baseline (balanced SAT/UNSAT mix).
        ax.axhline(0.5, color="#718096", lw=1.0, linestyle="--", alpha=0.35, zorder=1)
        # Add right-side padding so the bottom-right legend doesn't overlap the last bar group.
        # This effectively shifts the bars left in view without altering data positions.
        x_right_pad = float(SUPP_LEGEND_RIGHT_PAD)
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
        # Encode sat/unsat via opacity (satisfiable more opaque), and prompt group via hatch.
        alpha_by_satflag = {1: 0.9, 0: 0.35}  # satisfiable, unsatisfiable

        # Collect per bar positions/values and ranges.
        bar_x: List[float] = []
        bar_y: List[float] = []
        err_lo: List[float] = []
        err_hi: List[float] = []
        bar_color: List[str] = []
        bar_hatch: List[str] = []
        bar_alpha: List[float] = []
        n_cfgs: List[int] = []
        present_styles: set[Tuple[str, int]] = set()  # (prompt_group, satflag)

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
                    present_styles.add((str(gname), int(sf)))
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
        ax.set_xlim(-0.6, float(len(targets)) - 0.4 + float(x_right_pad))
        # Show full model label along the bottom (only once, on the bottom panel).
        if ax is axes[1]:
            ax.set_xticklabels([_tlabel(p, m, tm) for (p, m, tm) in targets], rotation=0, ha="center", fontsize=8.5)
        else:
            ax.set_xticklabels([])
        ax.grid(True, axis="y", alpha=0.25)
        ax.set_ylabel(f"Accuracy ({accuracy_mode})")
        # No x-axis label text (tick labels already provide target names).
        ax.set_xlabel("")

        # No extra per-target annotations (keep consistent across supplementary figures).

        from matplotlib.patches import Patch  # type: ignore

        # Explicit legend entries (style only; colors in the bars are per-model).
        # Filter to only styles actually present in this panel (avoid "ghost" legend entries).
        legend_color = "#4a5568"
        legend_entries: List[Tuple[Tuple[str, int], str, str]] = [
            (("examples", 1), "examples-only · satisfiable", ""),
            (("examples", 0), "examples-only · unsatisfiable", ""),
            (("algorithmic", 1), "algorithmic · satisfiable", "///"),
            (("algorithmic", 0), "algorithmic · unsatisfiable", "///"),
        ]
        legend_handles: List[Any] = []
        legend_labels: List[str] = []
        for (gname, sf), label, hatch in legend_entries:
            if (str(gname), int(sf)) not in present_styles:
                continue
            legend_handles.append(
                Patch(
                    facecolor=legend_color,
                    edgecolor="#1a202c",
                    hatch=hatch,
                    alpha=float(alpha_by_satflag.get(int(sf), 0.85)),
                    label=label,
                )
            )
            legend_labels.append(label)
        if legend_handles:
            _apply_legend(ax, legend_handles, legend_labels, ncol=1)

    _set_figure_header(
        fig,
        title="Supplementary: satisfiable/unsatisfiable asymmetry",
        context=(
            "Subset: Horn + Non-Horn · Representation: Compact CNF + Natural Language CNF"
            " (+ If-then CNF on Horn only) · Prompt: examples-only vs algorithmic · Targets: see x-axis"
        ),
    )
    _tight_layout_standard(fig)
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
        return _format_target_label(p, m, tm, multiline=True)

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
    n_plotted_by_combo: Dict[Tuple[str, int], int] = defaultdict(int)  # (prompt, horn) -> count
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
                n_plotted_by_combo[(str(prompt), int(horn))] += 1

    # Add right-side padding so the bottom-right legend doesn't overlap the last bar group.
    # Semantic-mismatch has fewer bars per target, so it needs less whitespace than SAT/UNSAT.
    # This effectively shifts the bars left in view without altering data positions.
    x_right_pad = float(SUPP_LEGEND_RIGHT_PAD) * 0.8
    ax.set_xlim(-0.6, float(len(targets)) - 0.4 + float(x_right_pad))
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel(f"Accuracy ({accuracy_mode})")
    ax.set_xticks(x_centers)
    ax.set_xticklabels([tlabel(*t) for t in targets], rotation=0, ha="center", fontsize=8.5)
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
            if int(n_plotted_by_combo.get((str(prompt), int(horn)), 0)) <= 0:
                continue
            legend_handles.append(
                Patch(
                    facecolor="#4a5568",
                    edgecolor="#1a202c",
                    hatch=hatch,
                    alpha=float(alpha_by_subset.get(int(horn), 0.85)),
                    label="",
                )
            )
            # Keep wording consistent with other supplementary legends: main factor, then condition.
            legend_labels.append(f"{p_label} · {subset_label}")
    _apply_legend(ax, legend_handles, legend_labels, ncol=1)

    _set_figure_header(
        fig,
        title="Supplementary: semantic alignment mismatch control",
        context="Subset: aligned vs mismatched · Representation: If-then CNF · Prompt: examples-only + Horn algorithm variants · Targets: see x-axis",
    )
    _tight_layout_standard(fig)
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

