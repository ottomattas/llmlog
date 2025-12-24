#!/usr/bin/env python3
"""
Generate neutral, paper-ready captions/descriptions for the generated figures.

Outputs:
  - experiments/paper_outputs/captions/captions.md
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _safe_filename(s: str) -> str:
    keep = []
    for ch in s:
        if ch.isalnum() or ch in ("-", "_", "."):
            keep.append(ch)
        else:
            keep.append("_")
    return "".join(keep)


def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _int(s: str) -> int:
    try:
        return int(float(s))
    except Exception:
        return 0


def _fmt_pct(x: str) -> str:
    try:
        if x == "":
            return ""
        return f"{float(x) * 100:.1f}%"
    except Exception:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate neutral captions for paper figures")
    ap.add_argument("--data-dir", default="experiments/paper_outputs/data", help="Data directory")
    ap.add_argument("--out-dir", default="experiments/paper_outputs", help="Output directory root")
    args = ap.parse_args()

    data_dir = Path(args.data_dir).resolve()
    out_dir = Path(args.out_dir).resolve()
    captions_dir = out_dir / "captions"
    _ensure_dir(captions_dir)

    prompt_index = _load_json(data_dir / "prompt_index.json")
    leaf_metrics = _load_csv(data_dir / "metrics_by_leaf.csv")

    # Group rows by model and prompt_id
    by_model_prompt: Dict[Tuple[str, str, str], List[Dict[str, str]]] = defaultdict(list)
    for r in leaf_metrics:
        key = ((r.get("provider") or "").strip(), (r.get("model") or "").strip(), (r.get("prompt_id") or "").strip())
        by_model_prompt[key].append(r)

    # Order models consistently
    models = sorted({(p, m) for (p, m, _pid) in by_model_prompt.keys()})

    md: List[str] = []
    md.append("## Figure descriptions (auto-generated)\n\n")
    md.append(
        "This file contains **neutral descriptions** of the generated per-model figures under "
        "`experiments/paper_outputs/figures/`.\n\n"
    )
    md.append("### Global notes (applies to all figures)\n\n")
    md.append("- Each figure page is a **grid of heatmaps**.\n")
    md.append("- **x-axis**: `maxlen` (clause length bucket)\n")
    md.append("- **y-axis**: `maxvars` (variable count bucket)\n")
    md.append("- **row facet**: `horn` flag (1 = Horn, 0 = non-Horn) when both appear for that prompt/model\n")
    md.append("- **column facet**: `thinking_mode` (e.g. `nothink`, `think-low`, `think-med`, `think-high`)\n")
    md.append("- **color** encodes the metric named in the page title/colorbar.\n")
    md.append("- **blank cells** indicate no data was available for that `(maxvars, maxlen)` bucket.\n")
    md.append(
        "- Ground truth is derived from `meta.satflag` in `results.jsonl` "
        "(1 = satisfiable, 0 = unsatisfiable/contradiction).\n"
    )
    md.append(
        "- Model outputs are **re-parsed** from `results.provenance.jsonl` `full_text` where available; "
        "unparseable outputs are counted as `unclear` and treated as incorrect in accuracy metrics.\n\n"
    )
    md.append(
        "Exact prompt instructions + representative example statement blocks are listed in "
        "`experiments/paper_outputs/prompts/prompt_catalog.md` (indexed by `prompt_id`).\n\n"
    )

    md.append("---\n\n")
    for provider, model in models:
        model_slug = _safe_filename(f"{provider}__{model}")
        md.append(f"### {provider}/{model}\n\n")
        md.append(f"- Report PDF: `experiments/paper_outputs/figures/model_reports/{model_slug}.pdf`\n")
        md.append(f"- PNG directory: `experiments/paper_outputs/figures/png/{model_slug}/`\n\n")

        prompt_ids = sorted({pid for (p, m, pid) in by_model_prompt.keys() if p == provider and m == model})
        for prompt_id in prompt_ids:
            rows = by_model_prompt[(provider, model, prompt_id)]

            thinking_modes = sorted({(r.get("thinking_mode") or "").strip() for r in rows})
            horns = sorted({(r.get("horn") or "").strip() for r in rows})
            n_total = sum(_int(r.get("total") or "0") for r in rows)

            pmeta = prompt_index.get(prompt_id, {}) if isinstance(prompt_index, dict) else {}
            prompt_style = ((pmeta.get("prompt_style") if isinstance(pmeta, dict) else "") or (rows[0].get("prompt_style") if rows else "")).strip()
            parse_family = ((pmeta.get("parse_family") if isinstance(pmeta, dict) else "") or (rows[0].get("parse_family") if rows else "")).strip()
            prompt_template = ((pmeta.get("prompt_template") if isinstance(pmeta, dict) else "") or (rows[0].get("prompt_template") if rows else "")).strip()

            md.append(f"#### {prompt_id}\n\n")
            md.append(f"- prompt_style: `{prompt_style}`\n")
            md.append(f"- parse_family: `{parse_family}`\n")
            if prompt_template:
                md.append(f"- prompt_template: `{prompt_template}`\n")
            md.append(f"- total examples aggregated (all thinking×horn): {n_total}\n")
            md.append(f"- thinking modes present: {', '.join([t or 'n/a' for t in thinking_modes])}\n")
            md.append(f"- horn flags present: {', '.join([h or 'n/a' for h in horns])}\n\n")

            base = f"experiments/paper_outputs/figures/png/{model_slug}/{prompt_id}"
            md.append("Figure pages (PNG):\n\n")
            md.append(f"- `{base}__accuracy.png`\n")
            md.append(f"- `{base}__sat_accuracy.png`\n")
            md.append(f"- `{base}__unsat_accuracy.png`\n\n")

            md.append("Captions (copy/paste starting points):\n\n")
            md.append(
                f"- **Overall accuracy** (`{base}__accuracy.png`): "
                f"Heatmaps of overall accuracy (correct/total) for {provider}/{model} under prompt condition {prompt_id} "
                f"(prompt_style={prompt_style}). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. "
                f"Axes are maxvars (y) and maxlen (x).\n"
            )
            md.append(
                f"- **Satisfiable accuracy** (`{base}__sat_accuracy.png`): "
                "Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), "
                "for the same model/prompt condition and faceting as above.\n"
            )
            md.append(
                f"- **Unsatisfiable accuracy** (`{base}__unsat_accuracy.png`): "
                "Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), "
                "for the same model/prompt condition and faceting as above.\n\n"
            )
            md.append(
                f"Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `{prompt_id}` "
                "for the exact instructions and example statements.\n\n"
            )

        md.append("---\n\n")

    out_path = captions_dir / "captions.md"
    out_path.write_text("".join(md), encoding="utf-8")
    print(f"Wrote: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

