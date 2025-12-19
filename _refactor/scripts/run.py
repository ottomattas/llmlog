#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _bootstrap_import_path() -> None:
    # Allow running from repo root without installing the package.
    here = Path(__file__).resolve()
    refactor_root = here.parents[1]
    src = refactor_root / "src"
    sys.path.insert(0, str(src))


def main() -> int:
    _bootstrap_import_path()

    from llmlog.runner import run_suite
    from llmlog.preflight import estimate_cost_upper_bound_usd, preflight_suite

    ap = argparse.ArgumentParser(description="Run a `_refactor` suite config.")
    ap.add_argument("--suite", required=True, help="Path to a suite YAML (e.g. _refactor/configs/suites/<suite>.yaml)")
    ap.add_argument("--run", default=None, help="Run identifier injected into ${run} output paths")
    ap.add_argument("--out-root", default=None, help="Override output root directory (defaults to _refactor/)")
    ap.add_argument("--limit", type=int, default=None, help="Limit number of processed problems")
    ap.add_argument("--dry-run", action="store_true", help="Render prompts but do not call providers")
    ap.add_argument("--resume", action="store_true", help="Resume if results files already exist")
    ap.add_argument("--no-resume", action="store_true", help="Disable resume even if suite enables it")
    ap.add_argument("--lockstep", action="store_true", help="Run targets in lockstep per-problem")
    ap.add_argument("--only", type=str, default=None, help="Comma-separated providers to include (e.g. openai,google)")
    ap.add_argument("--preflight", action="store_true", help="Print selected targets + pricing info before running")
    ap.add_argument("--preflight-only", action="store_true", help="Print preflight info and exit (no run)")
    ap.add_argument("--estimate-cost", action="store_true", help="Estimate an upper bound USD cost (heuristic)")
    ap.add_argument(
        "--max-estimated-total-usd",
        type=float,
        default=None,
        help="Abort if the estimated upper bound exceeds this USD amount (requires pricing for all targets).",
    )
    args = ap.parse_args()

    only = [p.strip() for p in (args.only or "").split(",") if p.strip()] or None

    resume = None
    if args.resume:
        resume = True
    if args.no_resume:
        resume = False

    lockstep = True if args.lockstep else None

    if args.preflight or args.preflight_only or args.estimate_cost or args.max_estimated_total_usd is not None:
        pf = preflight_suite(suite_path=args.suite, limit=args.limit, only_providers=only)
        print(f"[preflight] suite={pf.suite_name} rows={pf.run_rows} avg_prompt_tokens_est~{pf.avg_prompt_tokens_est}")
        print(f"[preflight] pricing_table={pf.pricing_table or '(none)'}")
        for t in pf.targets:
            rate = t.pricing_rate
            if rate:
                print(
                    f"[preflight] {t.provider}/{t.model}/{t.thinking_mode} "
                    f"max_tokens={t.max_tokens} "
                    f"rate_in=${rate.get('input_per_million_usd')}/MTok rate_out=${rate.get('output_per_million_usd')}/MTok"
                )
            else:
                print(
                    f"[preflight] {t.provider}/{t.model}/{t.thinking_mode} max_tokens={t.max_tokens} rate=(missing)"
                )

        if args.estimate_cost or args.max_estimated_total_usd is not None:
            est = estimate_cost_upper_bound_usd(preflight=pf)
            print(f"[preflight] estimated_total_usd_upper_bound~{est['estimated_total_usd']:.6f}")
            missing = [x for x in est["per_target"] if x.get("estimated_total_usd") is None]
            if missing:
                print("[preflight] WARNING: missing pricing rates for some targets; estimate is incomplete.")

            if args.max_estimated_total_usd is not None:
                if missing:
                    raise SystemExit(
                        "Cannot enforce --max-estimated-total-usd because pricing is missing for some targets."
                    )
                if float(est["estimated_total_usd"]) > float(args.max_estimated_total_usd):
                    raise SystemExit(
                        f"Estimated upper bound ${est['estimated_total_usd']:.6f} exceeds threshold ${args.max_estimated_total_usd:.6f}"
                    )

        if args.preflight_only:
            return 0

    run_suite(
        suite_path=args.suite,
        run_id=args.run,
        output_root=args.out_root,
        limit=args.limit,
        dry_run=args.dry_run,
        only_providers=only,
        resume=resume,
        lockstep=lockstep,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


