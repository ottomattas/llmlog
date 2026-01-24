#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def _bootstrap_import_path() -> tuple[Path, Path]:
    """Allow running from repo root without installing the package.

    Returns: (repo_root, refactor_root)
    """
    here = Path(__file__).resolve()
    refactor_root = here.parents[1]
    repo_root = refactor_root.parent
    src = refactor_root / "src"
    sys.path.insert(0, str(src))
    return repo_root, refactor_root


def _load_run_selection(path: str) -> dict:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Run selection config not found: {p}")
    suffix = p.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        import yaml  # type: ignore

        obj = yaml.safe_load(p.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    if suffix == ".json":
        import json

        obj = json.loads(p.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    raise ValueError(f"Unsupported run selection format: {p.suffix} (use .yaml/.yml/.json)")


def main() -> int:
    repo_root, refactor_root = _bootstrap_import_path()

    from llmlog.analysis.paper_figures import generate_paper_figures

    ap = argparse.ArgumentParser(
        description=(
            "Generate reproducible paper figures (PDF) from `_refactor/runs/**/results.jsonl`.\n\n"
            "This script writes the figure files referenced by `article1/neus2025-article.tex`, e.g.:\n"
            "- figures/fig_representation_effects.pdf\n"
            "- figures/fig_prompting_effects.pdf\n"
            "- figures/fig_test_time_compute.pdf\n"
            "- figures/fig_model_comparison.pdf\n"
            "- figures/fig_supp_sat_unsat_asymmetry.pdf\n"
            "- figures/fig_supp_semantic_alignment_mismatch.pdf\n"
        )
    )
    ap.add_argument("--runs-dir", default=str(refactor_root / "runs"), help="Runs directory (default: _refactor/runs)")
    ap.add_argument(
        "--output-dir",
        default=str(refactor_root / "reports" / "paper_figures"),
        help="Output directory for figure PDFs (default: _refactor/reports/paper_figures)",
    )
    ap.add_argument(
        "--accuracy-mode",
        default="completed",
        choices=["completed", "answered", "nonpending"],
        help="Accuracy denominator (default: completed = answered+unclear; excludes pending+errors).",
    )
    ap.add_argument(
        "--include-suite",
        action="append",
        default=[],
        help="Only include this suite (repeatable). If omitted, include all suites.",
    )
    ap.add_argument(
        "--exclude-suite",
        action="append",
        default=[],
        help="Exclude this suite (repeatable).",
    )
    ap.add_argument(
        "--exclude-run-regex",
        default=r"smoke",
        help="Exclude runs whose run name matches this regex (default: 'smoke').",
    )
    ap.add_argument(
        "--run-selection",
        default=None,
        help=(
            "Optional YAML/JSON file that controls which run(s) are used per model.\n"
            "If omitted, the script will auto-load `run_selection.yaml` from `--output-dir` when present.\n"
            "A provenance report is written to paper_figures.selection.*"
        ),
    )
    ap.add_argument(
        "--watch-seconds",
        type=int,
        default=None,
        help="If set, regenerate figures every N seconds until interrupted.",
    )
    args = ap.parse_args()

    def one_pass() -> None:
        # Auto-load policy from the output folder if present.
        run_selection_path = args.run_selection
        if not run_selection_path:
            candidate = Path(args.output_dir).expanduser().resolve() / "run_selection.yaml"
            if candidate.exists():
                run_selection_path = str(candidate)
        run_selection = _load_run_selection(run_selection_path) if run_selection_path else None
        meta = generate_paper_figures(
            runs_dir=str(Path(args.runs_dir).resolve()),
            output_dir=str(Path(args.output_dir).resolve()),
            accuracy_mode=str(args.accuracy_mode),
            include_suites=[s for s in (args.include_suite or []) if s],
            exclude_suites=[s for s in (args.exclude_suite or []) if s],
            exclude_run_regex=str(args.exclude_run_regex),
            run_selection=run_selection,
        )
        out_dir = Path(meta.get("output_dir") or args.output_dir)
        print(f"Wrote paper figures to: {out_dir}")
        print(f"Metadata: {out_dir / 'paper_figures.meta.json'}")
        print(f"Selection: {out_dir / 'paper_figures.selection.md'}")

    if args.watch_seconds is None:
        one_pass()
        return 0

    while True:
        one_pass()
        time.sleep(float(args.watch_seconds))


if __name__ == "__main__":
    raise SystemExit(main())

