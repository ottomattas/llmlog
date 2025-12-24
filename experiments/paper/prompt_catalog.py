#!/usr/bin/env python3
"""
Build a prompt catalog from historical provenance files so every figure can show the exact prompt.

Outputs (under --out-dir):
  - prompts/prompt_catalog.md
  - data/prompt_index.json
  - data/leaf_run_prompt_map.csv
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .common import iter_jsonl, sha1_hex


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _split_prompt(prompt: str) -> Tuple[str, str]:
    """
    Returns (instruction_part, statements_part).
    If 'Statements:' is not found, statements_part is empty.
    """
    if not prompt:
        return ("", "")
    idx = prompt.find("Statements:")
    if idx < 0:
        return (prompt.strip(), "")
    instr = prompt[:idx].rstrip()
    stmts = prompt[idx + len("Statements:") :].lstrip("\n\r ").rstrip()
    return (instr, stmts)


def _load_leaf_runs_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _load_reparsed_rows(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for obj in iter_jsonl(path):
        rows.append(obj)
    return rows


def _get_prompt_for_id(prov_path: Path, pid: str) -> Optional[str]:
    for obj in iter_jsonl(prov_path):
        if str(obj.get("id")) == pid:
            p = obj.get("prompt")
            if isinstance(p, str):
                return p
            return None
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description="Build prompt catalog + prompt IDs for figures")
    ap.add_argument("--runs-dir", default="experiments/runs", help="Runs root directory")
    ap.add_argument("--out-dir", default="experiments/paper_outputs", help="Output directory root")
    ap.add_argument(
        "--data-dir",
        default="experiments/paper_outputs/data",
        help="Data directory (contains leaf_runs.csv and reparsed_rows.jsonl)",
    )
    ap.add_argument("--max-examples-per-horn", type=int, default=3, help="Examples per horn flag (low/mid/high)")
    args = ap.parse_args()

    runs_dir = Path(args.runs_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    data_dir = Path(args.data_dir).resolve()

    leaf_runs_path = data_dir / "leaf_runs.csv"
    reparsed_rows_path = data_dir / "reparsed_rows.jsonl"

    prompts_dir = out_dir / "prompts"
    _ensure_dir(prompts_dir)
    _ensure_dir(data_dir)

    prompt_catalog_md = prompts_dir / "prompt_catalog.md"
    prompt_index_json = data_dir / "prompt_index.json"
    leaf_prompt_map_csv = data_dir / "leaf_run_prompt_map.csv"
    prompt_examples_json = data_dir / "prompt_examples.json"

    leaf_runs = _load_leaf_runs_csv(leaf_runs_path)
    reparsed_rows = _load_reparsed_rows(reparsed_rows_path)

    # 1) Build prompt_id per leaf run by sampling one prompt from its provenance
    leaf_to_prompt_id: Dict[str, str] = {}  # results_relpath -> prompt_id
    prompt_index: Dict[str, Dict[str, Any]] = {}
    prompt_seen_leaf_runs: Dict[str, List[str]] = defaultdict(list)

    for lr in leaf_runs:
        results_rel = (lr.get("results_relpath") or "").strip()
        prov_rel = (lr.get("provenance_relpath") or "").strip()
        if not results_rel:
            continue
        if not prov_rel:
            # No provenance -> can't reliably extract prompt text; still create a stable ID for joins
            prompt_template = (lr.get("prompt_template") or "").strip()
            prompt_style = (lr.get("prompt_style") or "").strip()
            parse_family = (lr.get("parse_family") or "").strip()
            seed = f"{prompt_template}|{prompt_style}|{parse_family}|NO_PROVENANCE"
            pid = f"prompt_{sha1_hex(seed)[:10]}"
            leaf_to_prompt_id[results_rel] = pid
            prompt_index.setdefault(
                pid,
                {
                    "prompt_id": pid,
                    "prompt_template": prompt_template,
                    "prompt_style": prompt_style,
                    "parse_family": parse_family,
                    "instruction_text": "",
                    "has_provenance": False,
                },
            )
            prompt_seen_leaf_runs[pid].append(results_rel)
            continue

        prov_path = runs_dir / prov_rel
        sampled_prompt = None
        for obj in iter_jsonl(prov_path):
            p = obj.get("prompt")
            if isinstance(p, str) and p.strip():
                sampled_prompt = p
                break
        prompt_template = (lr.get("prompt_template") or "").strip()
        prompt_style = (lr.get("prompt_style") or "").strip()
        parse_family = (lr.get("parse_family") or "").strip()

        instr, _stmts = _split_prompt(sampled_prompt or "")
        instr_norm = instr.strip().replace("\r\n", "\n").replace("\r", "\n")
        seed = f"{prompt_template}|{prompt_style}|{parse_family}|" + instr_norm
        pid = f"prompt_{sha1_hex(seed)[:10]}"

        leaf_to_prompt_id[results_rel] = pid
        prompt_seen_leaf_runs[pid].append(results_rel)
        if pid not in prompt_index:
            prompt_index[pid] = {
                "prompt_id": pid,
                "prompt_template": prompt_template,
                "prompt_style": prompt_style,
                "parse_family": parse_family,
                "instruction_text": instr_norm,
                "has_provenance": True,
            }

    # 2) Choose low/mid/high examples per (prompt_id, horn)
    #    We use reparsed_rows.jsonl to find candidate problem IDs, then fetch prompt text from provenance.
    candidates: Dict[Tuple[str, int], List[Dict[str, Any]]] = defaultdict(list)
    for r in reparsed_rows:
        results_rel = (r.get("results_relpath") or "").strip()
        pid = leaf_to_prompt_id.get(results_rel)
        if not pid:
            continue
        horn = r.get("horn")
        if not isinstance(horn, int):
            continue
        mv = r.get("maxvars")
        ml = r.get("maxlen")
        if not isinstance(mv, int) or not isinstance(ml, int):
            continue
        candidates[(pid, horn)].append(
            {
                "id": str(r.get("id")),
                "maxvars": mv,
                "maxlen": ml,
                "satflag": r.get("satflag"),
                "provenance_relpath": (r.get("provenance_relpath") or "").strip(),
            }
        )

    examples: Dict[str, Dict[int, Dict[str, Any]]] = defaultdict(dict)  # prompt_id -> horn -> {low/mid/high}
    for (pid, horn), rows in candidates.items():
        if not rows:
            continue
        # Sort by (maxvars,maxlen) for low/high selection
        rows_sorted = sorted(rows, key=lambda x: (x["maxvars"], x["maxlen"]))
        low = rows_sorted[0]
        high = rows_sorted[-1]

        # Median by maxvars (choose an actual row closest to median maxvars)
        uniq_mvs = sorted({x["maxvars"] for x in rows_sorted})
        med_mv = uniq_mvs[len(uniq_mvs) // 2]
        mid_candidates = [x for x in rows_sorted if x["maxvars"] == med_mv]
        mid = mid_candidates[len(mid_candidates) // 2] if mid_candidates else rows_sorted[len(rows_sorted) // 2]

        examples[pid][horn] = {"low": low, "mid": mid, "high": high}

    # 3) Write leaf_run_prompt_map.csv
    with leaf_prompt_map_csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=[
                "results_relpath",
                "prompt_id",
                "prompt_template",
                "prompt_style",
                "parse_family",
                "has_provenance",
            ],
        )
        w.writeheader()
        for lr in leaf_runs:
            results_rel = (lr.get("results_relpath") or "").strip()
            if not results_rel:
                continue
            pid = leaf_to_prompt_id.get(results_rel)
            if not pid:
                continue
            meta = prompt_index.get(pid, {})
            w.writerow(
                {
                    "results_relpath": results_rel,
                    "prompt_id": pid,
                    "prompt_template": meta.get("prompt_template", lr.get("prompt_template", "")),
                    "prompt_style": meta.get("prompt_style", lr.get("prompt_style", "")),
                    "parse_family": meta.get("parse_family", lr.get("parse_family", "")),
                    "has_provenance": bool(meta.get("has_provenance")),
                }
            )

    # 4) Write prompt_index.json
    # Add convenience fields
    for pid, meta in prompt_index.items():
        meta["leaf_runs_count"] = len(prompt_seen_leaf_runs.get(pid, []))
    prompt_index_json.write_text(json.dumps(prompt_index, indent=2, ensure_ascii=False))

    # 5) Write prompt_catalog.md with example statement blocks
    #    Also write a machine-readable prompt_examples.json for figure generation.
    lines: List[str] = []
    lines.append("## Prompt catalog\n")
    lines.append(
        "This catalog lists each distinct prompt *condition* (template + style + answer-family + injected rules), "
        "so figures can reference the exact instructions given to the model.\n"
    )
    lines.append("\n")
    prompt_examples_out: Dict[str, Any] = {}

    for pid in sorted(prompt_index.keys()):
        meta = prompt_index[pid]
        lines.append(f"### {pid}\n")
        lines.append(f"- prompt_template: `{meta.get('prompt_template','')}`\n")
        lines.append(f"- prompt_style: `{meta.get('prompt_style','')}`\n")
        lines.append(f"- parse_family: `{meta.get('parse_family','')}`\n")
        lines.append(f"- leaf_runs_count: {meta.get('leaf_runs_count',0)}\n")
        lines.append("\n")

        instr = meta.get("instruction_text") or ""
        if instr:
            lines.append("Instruction text (before `Statements:`):\n\n")
            lines.append("```\n")
            lines.append(instr.strip() + "\n")
            lines.append("```\n\n")
        else:
            lines.append("_No provenance prompt text was available for this prompt_id._\n\n")

        # Examples by horn flag
        if pid in examples:
            prompt_examples_out.setdefault(pid, {})
            for horn, ex in sorted(examples[pid].items(), key=lambda kv: kv[0]):
                lines.append(f"Examples (horn={horn}):\n\n")
                horn_key = str(horn)
                prompt_examples_out[pid].setdefault(horn_key, {})
                for level in ["low", "mid", "high"]:
                    e = ex.get(level)
                    if not e:
                        continue
                    prov_rel = e.get("provenance_relpath") or ""
                    prompt_text = ""
                    stmts = ""
                    if prov_rel:
                        prov_path = runs_dir / prov_rel
                        ptxt = _get_prompt_for_id(prov_path, e["id"])
                        prompt_text = ptxt or ""
                        _instr2, stmts = _split_prompt(prompt_text)
                    mv = e.get("maxvars")
                    ml = e.get("maxlen")
                    sf = e.get("satflag")
                    lines.append(f"- {level}: maxvars={mv}, maxlen={ml}, satflag={sf}\n\n")
                    if stmts:
                        lines.append("```\n")
                        lines.append(stmts.strip() + "\n")
                        lines.append("```\n\n")
                        prompt_examples_out[pid][horn_key][level] = {
                            "maxvars": mv,
                            "maxlen": ml,
                            "satflag": sf,
                            "statements": stmts.strip(),
                        }
                    else:
                        lines.append("_Example statements unavailable (missing prompt text)._\\\n\n")
        lines.append("\n---\n\n")

    prompt_catalog_md.write_text("".join(lines), encoding="utf-8")
    prompt_examples_json.write_text(json.dumps(prompt_examples_out, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Wrote:\n- {prompt_catalog_md}\n- {prompt_index_json}\n- {leaf_prompt_map_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


