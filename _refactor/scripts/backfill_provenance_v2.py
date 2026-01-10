#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterator, Optional, Sequence


def _bootstrap_import_path() -> Path:
    """Allow running from repo root without installing the package.

    Returns the `_refactor/` root directory.
    """
    here = Path(__file__).resolve()
    refactor_root = here.parents[1]
    src = refactor_root / "src"
    sys.path.insert(0, str(src))
    return refactor_root


def _iter_jsonl(path: Path) -> Iterator[Dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            txt = line.strip()
            if not txt:
                continue
            try:
                obj = json.loads(txt)
            except Exception:
                continue
            if isinstance(obj, dict):
                yield obj


def _infer_event_from_v1_row(row: Dict[str, Any]) -> str:
    """Best-effort mapping of legacy (v1-style) rows to v2 `event`.

    We only need a coarse mapping for analysis; the important part is that
    we preserve v1 fields and add v2 structural fields.
    """
    # Collector scripts write submit_ts on "collect" rows.
    if row.get("submit_ts") is not None:
        return "collect"

    # Submit-only placeholder rows have a submission id and no parsed answer yet.
    parsed = row.get("parsed_answer")
    if parsed is None and not row.get("error") and (row.get("openai_response_id") or row.get("submission_id")):
        return "submit"

    # Default: live-mode attempt / generic attempt row.
    return "attempt"


def _suite_from_run_dir(*, runs_dir: Path, run_dir: Path) -> str:
    """Extract suite name from runs/<suite>/<run>/<provider>/<model>/<thinking>/."""
    try:
        rel = run_dir.resolve().relative_to(runs_dir.resolve())
    except Exception:
        try:
            rel = run_dir.relative_to(runs_dir)
        except Exception:
            return ""
    return str(rel.parts[0]) if rel.parts else ""


def _write_v2_from_v1(
    *,
    prov1_path: Path,
    results_path: Optional[Path],
    prov2_path: Path,
    migrate_tag: Optional[str],
) -> Dict[str, int]:
    """Convert a v1 provenance file to v2 in a streaming way.

    Writes to a temp file first, then atomically replaces the destination.
    """
    from llmlog.provenance_v2 import build_provenance_v2_row

    tmp_path = prov2_path.with_suffix(prov2_path.suffix + ".tmp")
    try:
        tmp_path.unlink(missing_ok=True)  # type: ignore[arg-type]
    except Exception:
        # If unlink fails (older Python or perms), we just overwrite below.
        pass

    wrote = 0
    skipped = 0

    with tmp_path.open("w", encoding="utf-8") as out:
        for row in _iter_jsonl(prov1_path):
            event = _infer_event_from_v1_row(row)
            extra = {"migrated_from_v1": True}
            if migrate_tag:
                extra["migration_tag"] = migrate_tag
            try:
                v2_row = build_provenance_v2_row(
                    base=row,
                    results_path=results_path,
                    event=event,
                    http=None,
                    job_meta=None,
                    extra=extra,
                )
            except Exception:
                skipped += 1
                continue
            out.write(json.dumps(v2_row, ensure_ascii=False) + "\n")
            wrote += 1

    tmp_path.replace(prov2_path)
    return {"wrote": wrote, "skipped": skipped}


def main(argv: Optional[Sequence[str]] = None) -> int:
    refactor_root = _bootstrap_import_path()

    ap = argparse.ArgumentParser(
        description=(
            "Backfill provenance v2 files for existing runs by converting "
            "`runs/**/results.provenance.jsonl` -> `results.provenance.v2.jsonl`.\n\n"
            "This keeps v1 files intact and is safe to re-run (skips when v2 exists unless --overwrite)."
        )
    )
    ap.add_argument("--runs-dir", default=str(refactor_root / "runs"), help="Runs directory (default: _refactor/runs)")
    ap.add_argument("--dry-run", action="store_true", help="Do not write files; just report what would change.")
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing v2 provenance files.")
    ap.add_argument("--limit", type=int, default=None, help="Max number of run folders to backfill.")
    ap.add_argument(
        "--include-suite",
        action="append",
        default=[],
        help="Only backfill suites with this name (repeatable). If omitted, includes all suites.",
    )
    ap.add_argument(
        "--exclude-suite",
        action="append",
        default=[],
        help="Exclude suites with this name (repeatable).",
    )
    ap.add_argument(
        "--migration-tag",
        default=None,
        help="Optional string tag written into each v2 row as `migration_tag` (for audits).",
    )
    args = ap.parse_args(list(argv) if argv is not None else None)

    runs_dir = Path(args.runs_dir).resolve()
    if not runs_dir.exists():
        raise FileNotFoundError(f"Runs dir not found: {runs_dir}")

    include = {s for s in (args.include_suite or []) if s}
    exclude = {s for s in (args.exclude_suite or []) if s}

    # Imports after sys.path bootstrapping
    from llmlog.provenance_v2 import provenance_v2_path_for_results

    prov1_paths = sorted(runs_dir.glob("**/results.provenance.jsonl"))
    if not prov1_paths:
        print(f"backfill_provenance_v2: no v1 provenance files found under {runs_dir}")
        return 0

    total_seen = 0
    total_candidate = 0
    total_changed = 0
    total_skipped_existing = 0
    total_skipped_suite = 0
    total_missing_results = 0
    total_rows_written = 0
    total_rows_skipped = 0

    processed = 0

    for prov1_path in prov1_paths:
        total_seen += 1
        run_dir = prov1_path.parent
        suite = _suite_from_run_dir(runs_dir=runs_dir, run_dir=run_dir)
        if include and suite not in include:
            total_skipped_suite += 1
            continue
        if exclude and suite in exclude:
            total_skipped_suite += 1
            continue

        results_path = run_dir / "results.jsonl"
        if not results_path.exists():
            # We can still write v2, but run-info inference will be weaker.
            total_missing_results += 1
            results_path_opt: Optional[Path] = None
            prov2_path = run_dir / "results.provenance.v2.jsonl"
        else:
            results_path_opt = results_path
            prov2_path = provenance_v2_path_for_results(results_path)

        if prov2_path.exists() and not args.overwrite:
            total_skipped_existing += 1
            continue

        total_candidate += 1
        processed += 1
        if args.limit is not None and processed > int(args.limit):
            break

        if args.dry_run:
            print(f"DRY-RUN backfill: {prov1_path} -> {prov2_path}")
            continue

        prov2_path.parent.mkdir(parents=True, exist_ok=True)
        out = _write_v2_from_v1(
            prov1_path=prov1_path,
            results_path=results_path_opt,
            prov2_path=prov2_path,
            migrate_tag=(str(args.migration_tag) if args.migration_tag else None),
        )
        total_changed += 1
        total_rows_written += int(out.get("wrote", 0))
        total_rows_skipped += int(out.get("skipped", 0))

    print(
        "backfill_provenance_v2: "
        f"seen_v1={total_seen} "
        f"candidate={total_candidate} "
        f"changed={total_changed} "
        f"skipped_existing_v2={total_skipped_existing} "
        f"skipped_suite={total_skipped_suite} "
        f"missing_results_jsonl={total_missing_results} "
        f"rows_written={total_rows_written} "
        f"rows_skipped={total_rows_skipped} "
        f"dry_run={bool(args.dry_run)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

