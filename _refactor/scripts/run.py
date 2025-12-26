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
    from llmlog.problems.filters import parse_int_set_spec, parse_str_set_spec

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
    ap.add_argument(
        "--maxvars",
        type=str,
        default=None,
        help="Filter dataset rows by maxvarnr (e.g. '10,20,30,40,50' or '35-45').",
    )
    ap.add_argument(
        "--maxlen",
        type=str,
        default=None,
        help="Filter dataset rows by maxlen (e.g. '3,4,5').",
    )
    ap.add_argument(
        "--ids",
        type=str,
        default=None,
        help="Filter dataset rows by id (comma-separated). Useful for drilling into specific items.",
    )
    ap.add_argument(
        "--case-limit",
        type=int,
        default=None,
        help="Max rows per case (maxvarnr,maxlen,mustbehorn) after filtering. Useful for quick sweeps.",
    )
    ap.add_argument(
        "--rerun-errors",
        action="store_true",
        help="When resuming, re-run rows whose latest recorded result has a non-null error field.",
    )
    ap.add_argument(
        "--rerun-unclear",
        action="store_true",
        help="When resuming, re-run rows whose latest recorded result has parsed_answer==2 (unclear).",
    )
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
    maxvars = parse_int_set_spec(args.maxvars) if args.maxvars else None
    maxlen = parse_int_set_spec(args.maxlen) if args.maxlen else None
    ids = parse_str_set_spec(args.ids) if args.ids else None
    case_limit = int(args.case_limit) if args.case_limit is not None else None
    rerun_errors = bool(args.rerun_errors)
    rerun_unclear = bool(args.rerun_unclear)

    resume = None
    if args.resume:
        resume = True
    if args.no_resume:
        resume = False

    lockstep = True if args.lockstep else None

    if args.preflight or args.preflight_only or args.estimate_cost or args.max_estimated_total_usd is not None:
        pf = preflight_suite(
            suite_path=args.suite,
            limit=args.limit,
            only_providers=only,
            only_maxvars=maxvars,
            only_maxlen=maxlen,
            only_ids=ids,
            case_limit=case_limit,
        )
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
            missing = [x for x in est["per_target"] if x.get("estimated_total_usd") is None]
            if est.get("estimated_total_usd") is None:
                print("[preflight] estimated_total_usd_upper_bound~(unknown; incomplete estimate)")
                print(
                    f"[preflight] estimated_total_usd_partial_known~{float(est.get('estimated_total_usd_partial') or 0.0):.6f}"
                )
            else:
                print(f"[preflight] estimated_total_usd_upper_bound~{float(est['estimated_total_usd']):.6f}")
            if missing:
                print("[preflight] WARNING: estimate is incomplete for some targets:")
                for x in missing:
                    note = x.get("note") or "missing estimate"
                    print(f"[preflight] - {x.get('provider')}/{x.get('model')}/{x.get('thinking_mode')}: {note}")

            if args.max_estimated_total_usd is not None:
                if missing or est.get("estimated_total_usd") is None:
                    raise SystemExit(
                        "Cannot enforce --max-estimated-total-usd because the estimate is incomplete (missing pricing and/or max_tokens)."
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
        only_maxvars=maxvars,
        only_maxlen=maxlen,
        only_ids=ids,
        case_limit=case_limit,
        rerun_errors=rerun_errors,
        rerun_unclear=rerun_unclear,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


