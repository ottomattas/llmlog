from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def _acc_class(acc: float) -> str:
    if acc >= 0.99:
        return "acc-100"
    if acc >= 0.9:
        return "acc-90"
    if acc >= 0.75:
        return "acc-75"
    if acc >= 0.5:
        return "acc-50"
    return "acc-low"


def generate_html_dashboard(*, aggregated: Dict[str, Any], output_path: str) -> None:
    """Generate a single-file HTML dashboard (no server required)."""
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    experiments = aggregated.get("experiments", {}) or {}
    models = aggregated.get("models", {}) or {}
    exp_names = sorted(experiments.keys())
    model_keys = sorted(models.keys())

    html: List[str] = []
    html.append("<!DOCTYPE html>")
    html.append("<html><head><meta charset='utf-8'/>")
    html.append("<title>llmlog dashboard</title>")
    html.append(
        "<style>"
        "body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,sans-serif;background:#f5f7fa;padding:20px}"
        ".card{background:#fff;border-radius:10px;padding:20px;margin-bottom:20px;box-shadow:0 2px 4px rgba(0,0,0,.06)}"
        "table{width:100%;border-collapse:collapse;font-size:13px}"
        "th,td{border:1px solid #e2e8f0;padding:8px;text-align:center}"
        "th{background:#f7fafc;position:sticky;top:0}"
        ".exp-name{text-align:left;font-weight:600;background:#f7fafc}"
        ".acc-100{background:#48bb78;color:#fff;font-weight:700}"
        ".acc-90{background:#68d391;color:#fff}"
        ".acc-75{background:#f6e05e}"
        ".acc-50{background:#fc8181;color:#fff}"
        ".acc-low{background:#f56565;color:#fff;font-weight:700}"
        ".muted{color:#718096}"
        "</style>"
    )
    html.append("</head><body>")

    meta = aggregated.get("metadata", {})
    html.append("<div class='card'>")
    html.append(f"<h2>llmlog dashboard</h2>")
    html.append(
        f"<div class='muted'>run_id: <b>{meta.get('run_id','')}</b> · suites: <b>{len(exp_names)}</b> · targets: <b>{len(model_keys)}</b></div>"
    )
    html.append("</div>")

    html.append("<div class='card'>")
    html.append("<h3>Accuracy matrix</h3>")
    html.append("<div style='overflow:auto;max-height:70vh'>")
    html.append("<table><thead><tr><th>suite</th>")
    for mk in model_keys:
        html.append(f"<th>{mk}</th>")
    html.append("</tr></thead><tbody>")
    for exp in exp_names:
        html.append(f"<tr><td class='exp-name'>{exp}</td>")
        for mk in model_keys:
            cell = models.get(mk, {}).get("experiments", {}).get(exp)
            if not cell:
                html.append("<td></td>")
                continue
            acc = float(cell.get("accuracy", 0.0) or 0.0)
            cls = _acc_class(acc)
            total = cell.get("total", 0)
            html.append(f"<td class='{cls}' title='n={total}'>{acc*100:.1f}%</td>")
        html.append("</tr>")
    html.append("</tbody></table></div></div>")

    html.append("<div class='card'>")
    html.append("<h3>Raw aggregated JSON</h3>")
    html.append("<details><summary>Show data</summary>")
    html.append("<pre style='white-space:pre-wrap'>")
    html.append(json.dumps(aggregated, indent=2, ensure_ascii=False))
    html.append("</pre></details></div>")

    html.append("</body></html>")
    out.write_text("\n".join(html), encoding="utf-8")


