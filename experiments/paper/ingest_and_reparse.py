#!/usr/bin/env python3
"""
Ingest all historical runs under experiments/runs and (re)parse answers from provenance.

Primary source of truth for model outputs is results.provenance.jsonl (full_text).
We join each provenance row with the sibling results.jsonl to obtain ground-truth meta
(maxvars, maxlen, horn, satflag). When provenance is missing, we fall back to stored
parsed_answer from results.jsonl and mark reparse_source=stored.

Outputs (under --out-dir):
  - data/reparsed_rows.jsonl : one row per (leaf run × problem id)
  - data/leaf_runs.csv       : one row per leaf run
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, Optional

from .common import (
    classify_error,
    infer_parse_family,
    infer_prompt_style,
    iter_jsonl,
    normalize_id,
    parse_answer_last_token,
    parse_leaf_identifiers,
    safe_int,
)


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_jsonl_line(fp, obj: Dict[str, Any]) -> None:
    fp.write(json.dumps(obj, ensure_ascii=False) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser(description="Ingest all runs and reparse answers from provenance")
    ap.add_argument("--runs-dir", default="experiments/runs", help="Runs root directory")
    ap.add_argument("--out-dir", default="experiments/paper_outputs", help="Output directory root")
    ap.add_argument("--include-full-text", action="store_true", help="Include full_text in reparsed_rows.jsonl (large)")
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    data_dir = out_dir / "data"
    _ensure_dir(data_dir)

    out_rows_path = data_dir / "reparsed_rows.jsonl"
    out_leaf_path = data_dir / "leaf_runs.csv"

    # Identify all leaf-run directories (parents of results/provenance files)
    leaf_dirs = set()
    for p in runs_dir.rglob("results.jsonl"):
        leaf_dirs.add(p.parent)
    for p in runs_dir.rglob("results.provenance.jsonl"):
        leaf_dirs.add(p.parent)

    leaf_dirs_sorted = sorted(leaf_dirs)

    leaf_fields = [
        "experiment",
        "run_id",
        "provider",
        "model",
        "thinking_mode",
        "results_relpath",
        "provenance_relpath",
        "summary_relpath",
        "prompt_template",
        "prompt_style",
        "parse_family",
        "results_rows",
        "provenance_rows",
        "joined_rows",
        "results_only_rows",
        "provenance_only_rows",
        "provenance_error_rows",
        "provenance_full_text_empty_rows",
    ]

    with out_rows_path.open("w", encoding="utf-8") as out_rows_fp, out_leaf_path.open(
        "w", newline="", encoding="utf-8"
    ) as out_leaf_fp:
        leaf_writer = csv.DictWriter(out_leaf_fp, fieldnames=leaf_fields)
        leaf_writer.writeheader()

        for leaf_dir in leaf_dirs_sorted:
            results_path = leaf_dir / "results.jsonl"
            prov_path = leaf_dir / "results.provenance.jsonl"
            summary_path = leaf_dir / "results.summary.json"

            # Choose a canonical path for id parsing (prefer results.jsonl if present)
            canonical = results_path if results_path.exists() else (prov_path if prov_path.exists() else leaf_dir)
            ids = parse_leaf_identifiers(canonical, runs_dir)
            experiment = ids["experiment"]
            run_id = ids["run_id"]
            provider = ids["provider"]
            model = ids["model"]
            thinking_mode = ids["thinking_mode"]

            parse_family = infer_parse_family(experiment)

            # Load results meta and stored parsed_answer
            meta_by_id: Dict[str, Dict[str, Any]] = {}
            stored_parsed_by_id: Dict[str, Optional[int]] = {}
            results_rows = 0
            if results_path.exists():
                for obj in iter_jsonl(results_path):
                    pid = normalize_id(obj.get("id"))
                    meta_by_id[pid] = obj.get("meta") or {}
                    stored_parsed_by_id[pid] = safe_int(obj.get("parsed_answer"))
                    results_rows += 1

            # Load provenance and create joined rows
            seen_prov_ids = set()
            provenance_rows = 0
            provenance_error_rows = 0
            provenance_full_text_empty_rows = 0
            prompt_template = ""
            prompt_style = "unknown"

            joined_rows = 0
            provenance_only_rows = 0

            if prov_path.exists():
                for obj in iter_jsonl(prov_path):
                    provenance_rows += 1
                    pid = normalize_id(obj.get("id"))
                    seen_prov_ids.add(pid)

                    if not prompt_template:
                        prompt_template = str(obj.get("prompt_template") or "")
                        prompt_style = infer_prompt_style(experiment, prompt_template)

                    full_text = obj.get("full_text") or ""
                    err_msg = obj.get("error")
                    if err_msg:
                        provenance_error_rows += 1
                    if not full_text:
                        provenance_full_text_empty_rows += 1

                    meta = meta_by_id.get(pid) or {}
                    mv = safe_int(meta.get("maxvars"))
                    ml = safe_int(meta.get("maxlen"))
                    hf = safe_int(meta.get("horn"))
                    sf = safe_int(meta.get("satflag"))

                    stored = stored_parsed_by_id.get(pid)
                    reparsed = (
                        parse_answer_last_token(full_text, parse_family)
                        if (full_text and not err_msg)
                        else 2
                    )
                    reparse_source = "provenance" if (full_text and not err_msg) else "provenance_empty_or_error"

                    # If provenance did not yield a parse, fall back to stored parsed if available.
                    if reparsed == 2 and stored in (0, 1, 2):
                        reparsed = int(stored)
                        reparse_source = "stored"

                    correct = (sf in (0, 1) and reparsed in (0, 1) and int(sf) == int(reparsed))

                    row: Dict[str, Any] = {
                        "experiment": experiment,
                        "run_id": run_id,
                        "provider": provider or str(obj.get("provider") or ""),
                        "model": model or str(obj.get("model") or ""),
                        "thinking_mode": thinking_mode,
                        "results_relpath": str(results_path.relative_to(runs_dir)) if results_path.exists() else "",
                        "provenance_relpath": str(prov_path.relative_to(runs_dir)) if prov_path.exists() else "",
                        "summary_relpath": str(summary_path.relative_to(runs_dir)) if summary_path.exists() else "",
                        "id": pid,
                        "prompt_template": prompt_template,
                        "prompt_style": prompt_style,
                        "parse_family": parse_family,
                        "maxvars": mv,
                        "maxlen": ml,
                        "horn": hf,
                        "satflag": sf,
                        "parsed_answer_reparsed": reparsed,
                        "parsed_answer_stored": stored if stored in (0, 1, 2) else None,
                        "is_unclear": (reparsed == 2),
                        "correct": bool(correct),
                        "reparse_source": reparse_source,
                        "error": err_msg,
                        "error_class": classify_error(err_msg),
                        "timing_ms": safe_int(obj.get("timing_ms")),
                    }
                    if args.include_full_text:
                        row["full_text"] = full_text

                    _write_jsonl_line(out_rows_fp, row)
                    joined_rows += 1
                    if pid not in meta_by_id:
                        provenance_only_rows += 1

            # Emit rows that exist only in results.jsonl (no provenance)
            results_only_rows = 0
            for pid, meta in meta_by_id.items():
                if pid in seen_prov_ids:
                    continue
                results_only_rows += 1
                stored = stored_parsed_by_id.get(pid)
                mv = safe_int(meta.get("maxvars"))
                ml = safe_int(meta.get("maxlen"))
                hf = safe_int(meta.get("horn"))
                sf = safe_int(meta.get("satflag"))
                reparsed = int(stored) if stored in (0, 1, 2) else 2
                correct = (sf in (0, 1) and reparsed in (0, 1) and int(sf) == int(reparsed))

                if not prompt_template:
                    # provenance missing; still infer style from experiment name
                    prompt_style = infer_prompt_style(experiment, "")

                row = {
                    "experiment": experiment,
                    "run_id": run_id,
                    "provider": provider,
                    "model": model,
                    "thinking_mode": thinking_mode,
                    "results_relpath": str(results_path.relative_to(runs_dir)) if results_path.exists() else "",
                    "provenance_relpath": "",
                    "summary_relpath": str(summary_path.relative_to(runs_dir)) if summary_path.exists() else "",
                    "id": pid,
                    "prompt_template": prompt_template,
                    "prompt_style": prompt_style,
                    "parse_family": parse_family,
                    "maxvars": mv,
                    "maxlen": ml,
                    "horn": hf,
                    "satflag": sf,
                    "parsed_answer_reparsed": reparsed,
                    "parsed_answer_stored": stored if stored in (0, 1, 2) else None,
                    "is_unclear": (reparsed == 2),
                    "correct": bool(correct),
                    "reparse_source": "stored",
                    "error": None,
                    "error_class": None,
                    "timing_ms": None,
                }
                _write_jsonl_line(out_rows_fp, row)

            leaf_writer.writerow(
                {
                    "experiment": experiment,
                    "run_id": run_id,
                    "provider": provider,
                    "model": model,
                    "thinking_mode": thinking_mode,
                    "results_relpath": str(results_path.relative_to(runs_dir)) if results_path.exists() else "",
                    "provenance_relpath": str(prov_path.relative_to(runs_dir)) if prov_path.exists() else "",
                    "summary_relpath": str(summary_path.relative_to(runs_dir)) if summary_path.exists() else "",
                    "prompt_template": prompt_template,
                    "prompt_style": prompt_style,
                    "parse_family": parse_family,
                    "results_rows": results_rows,
                    "provenance_rows": provenance_rows,
                    "joined_rows": joined_rows,
                    "results_only_rows": results_only_rows,
                    "provenance_only_rows": provenance_only_rows,
                    "provenance_error_rows": provenance_error_rows,
                    "provenance_full_text_empty_rows": provenance_full_text_empty_rows,
                }
            )

    print(f"Wrote:\n- {out_rows_path}\n- {out_leaf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


