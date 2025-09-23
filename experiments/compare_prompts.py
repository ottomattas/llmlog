#!/usr/bin/env python3

import argparse
import json
import difflib
from pathlib import Path
from typing import Any, List, Optional

import yaml


def read_problem(dataset: Path, skip_rows: int, index: int, horn_only: bool = False) -> List[Any]:
    with dataset.open("r") as f:
        lines = [ln.strip() for ln in f if ln.strip()]
    # emulate legacy/new behavior: skip header rows
    rows = [json.loads(ln) for ln in lines[skip_rows:]]
    if horn_only:
        rows = [r for r in rows if isinstance(r, list) and len(r) > 3 and r[3]]
    if not rows:
        raise SystemExit("No problems found after applying filters")
    i = max(1, index) - 1
    return rows[i]


def main() -> None:
    ap = argparse.ArgumentParser(description="Render one prompt via legacy and new paths and show a diff")
    ap.add_argument("--dataset", default=None)
    ap.add_argument("--skip", type=int, default=None, help="Header rows to skip")
    ap.add_argument("--index", type=int, default=1, help="1-based problem index after skipping/filters")
    ap.add_argument("--template", default=None)
    ap.add_argument("--style", default=None)
    ap.add_argument("--horn_only", action="store_true", help="Filter to horn-only before selecting index")
    ap.add_argument("--config", default=None, help="Path to new YAML config; overrides dataset/template/style/skip/horn_only")
    ap.add_argument("--legacy_module", required=True, help="Module with makeprompt(problem)")
    args = ap.parse_args()

    # Load from config if provided
    dataset: Optional[str] = args.dataset
    skip_rows: Optional[int] = args.skip
    template_path: Optional[str] = args.template
    style: Optional[str] = args.style
    horn_only_flag: bool = bool(args.horn_only)
    if args.config:
        raw = yaml.safe_load(Path(args.config).read_text())
        dataset = raw.get("input_file", dataset)
        # filters
        filters = raw.get("filters", {}) or {}
        skip_rows = filters.get("skip_rows", 0 if skip_rows is None else skip_rows)
        horn_only_flag = bool(filters.get("horn_only", horn_only_flag))
        # prompt
        prompt = raw.get("prompt", {}) or {}
        template_path = prompt.get("template", template_path)
        style = prompt.get("style", style)
    # Defaults
    if dataset is None:
        dataset = "data/problems_dist20_v1.js"
    if skip_rows is None:
        skip_rows = 1
    if template_path is None:
        template_path = "prompts/exp2_cnf_v2_contradiction.j2"
    if style is None:
        style = "cnf_v2"

    problem = read_problem(Path(dataset), int(skip_rows), int(args.index), horn_only=horn_only_flag)

    # legacy prompt
    legacy = __import__(args.legacy_module, fromlist=["makeprompt"])  # type: ignore
    legacy_prompt = legacy.makeprompt(problem)

    # new prompt (local renderer to avoid importing runner dependencies)
    def render_prompt_local(prob: List[Any], template_text: str, style: Optional[str]) -> str:
        clauses = prob[5]
        if style in (None, "horn_if_then"):
            lines: List[str] = []
            for clause in clauses:
                pos: List[int] = []
                neg: List[int] = []
                for var in clause:
                    if var > 0:
                        pos.append(var)
                    else:
                        neg.append(var)
                if pos and not neg and len(pos) == 1:
                    s = f"p{pos[0]}"
                    lines.append(s)
                elif neg and not pos:
                    prem = " and ".join([f"p{0 - el}" for el in neg])
                    lines.append(f"if {prem} then p0")
                elif neg and len(pos) == 1:
                    prem = " and ".join([f"p{0 - el}" for el in neg])
                    lines.append(f"if {prem} then p{pos[0]}")
                else:
                    raise RuntimeError(f"Cannot handle clause (maybe not horn?): {clause}")
            body = "\n".join(lines)
            return template_text.replace("{{ clauses }}", body)
        elif style == "cnf_v1":
            lines: List[str] = []
            for clause in clauses:
                parts: List[str] = []
                for var in clause:
                    if var > 0:
                        parts.append(f"p{var} is true")
                    else:
                        parts.append(f"p{0 - var} is false")
                lines.append(" or ".join(parts) + ".")
            body = "\n".join(lines)
            return template_text.replace("{{ clauses }}", body)
        elif style == "cnf_v2":
            lines: List[str] = []
            for clause in clauses:
                parts: List[str] = []
                for var in clause:
                    parts.append(f"p{var}" if var > 0 else f"not(p{0 - var})")
                lines.append(" or ".join(parts) + ".")
            body = "\n".join(lines)
            return template_text.replace("{{ clauses }}", body)
        else:
            raise RuntimeError(f"Unsupported style for comparison: {style}")

    tmpl_text = Path(template_path).read_text()
    new_prompt = render_prompt_local(problem, tmpl_text, style)

    print("=== LEGACY ===\n" + legacy_prompt)
    print("\n=== NEW ===\n" + new_prompt)

    print("\n=== UNIFIED DIFF (legacy vs new) ===")
    diff = difflib.unified_diff(
        legacy_prompt.splitlines(),
        new_prompt.splitlines(),
        fromfile="legacy",
        tofile="new",
        lineterm="",
    )
    for line in diff:
        print(line)


if __name__ == "__main__":
    main()


