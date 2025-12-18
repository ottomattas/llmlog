from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text())


def _iter_jsonl(path: Path):
    with path.open("r") as f:
        for line in f:
            txt = line.strip()
            if not txt:
                continue
            try:
                yield json.loads(txt)
            except Exception:
                continue


def aggregate_runs(*, runs_dir: str, run_id: str) -> Dict[str, Any]:
    """Aggregate `_refactor/runs/<suite>/<run_id>/...` results into one JSON blob."""
    runs = Path(runs_dir)
    aggregated: Dict[str, Any] = {
        "metadata": {
            "run_id": run_id,
            "runs_dir": str(runs),
            "dataset": {
                "min_vars": None,
                "max_vars": None,
                "min_len": None,
                "max_len": None,
                "total_problems": 0,
                "horn_problems": 0,
                "nonhorn_problems": 0,
                "sat_problems": 0,
                "unsat_problems": 0,
            },
        },
        "experiments": {},  # suite_name -> data
        "models": {},  # model_key -> data
        "summary": {
            "total_experiments": 0,
            "total_models": 0,
        },
    }

    seen_problems: Set[Tuple[str, int, int]] = set()

    for suite_dir in sorted(runs.iterdir()):
        if not suite_dir.is_dir():
            continue
        suite_name = suite_dir.name
        run_dir = suite_dir / run_id
        if not run_dir.exists():
            continue

        exp_data: Dict[str, Any] = {
            "name": suite_name,
            "models": {},
            "summary": {"total_models": 0, "avg_accuracy": 0.0},
        }

        for summary_file in sorted(run_dir.rglob("results.summary.json")):
            summary = _read_json(summary_file)

            provider = summary.get("provider") or summary_file.parts[-4]
            model = summary.get("model") or summary_file.parts[-3]
            thinking_mode = summary.get("thinking_mode") or summary_file.parts[-2]

            model_key = f"{provider}/{model}/{thinking_mode}"

            # complexity breakdown from results.jsonl
            results_file = summary_file.parent / "results.jsonl"
            breakdown = defaultdict(lambda: {"total": 0, "correct": 0})
            if results_file.exists():
                for row in _iter_jsonl(results_file):
                    meta = row.get("meta") or {}
                    maxvars = meta.get("maxvars")
                    maxlen = meta.get("maxlen")
                    horn = meta.get("horn")
                    satflag = meta.get("satflag")

                    # dataset metadata
                    ds = aggregated["metadata"]["dataset"]
                    if isinstance(maxvars, int):
                        ds["min_vars"] = maxvars if ds["min_vars"] is None else min(ds["min_vars"], maxvars)
                        ds["max_vars"] = maxvars if ds["max_vars"] is None else max(ds["max_vars"], maxvars)
                    if isinstance(maxlen, int):
                        ds["min_len"] = maxlen if ds["min_len"] is None else min(ds["min_len"], maxlen)
                        ds["max_len"] = maxlen if ds["max_len"] is None else max(ds["max_len"], maxlen)

                    rid = row.get("id")
                    if rid is not None and horn is not None and satflag is not None:
                        try:
                            hk = int(horn)
                            sk = int(satflag)
                            key = (str(rid), hk, sk)
                            if key not in seen_problems:
                                seen_problems.add(key)
                                if hk == 1:
                                    ds["horn_problems"] += 1
                                elif hk == 0:
                                    ds["nonhorn_problems"] += 1
                                if sk == 1:
                                    ds["sat_problems"] += 1
                                elif sk == 0:
                                    ds["unsat_problems"] += 1
                        except Exception:
                            pass

                    if maxvars is not None:
                        try:
                            mv = int(maxvars)
                            breakdown[mv]["total"] += 1
                            if row.get("correct") is True:
                                breakdown[mv]["correct"] += 1
                        except Exception:
                            pass

            exp_data["models"][model_key] = {
                "provider": provider,
                "model": model,
                "thinking_mode": thinking_mode,
                "summary": summary,
                "complexity_breakdown": {
                    str(k): {
                        "accuracy": (v["correct"] / v["total"]) if v["total"] else 0.0,
                        "total": v["total"],
                        "correct": v["correct"],
                    }
                    for k, v in sorted(breakdown.items())
                },
            }

            if model_key not in aggregated["models"]:
                aggregated["models"][model_key] = {
                    "provider": provider,
                    "model": model,
                    "thinking_mode": thinking_mode,
                    "experiments": {},
                }
            aggregated["models"][model_key]["experiments"][suite_name] = {
                "accuracy": summary.get("accuracy", 0.0),
                "total": (summary.get("stats") or {}).get("total", 0),
                "correct": (summary.get("stats") or {}).get("correct", 0),
                "unclear": (summary.get("stats") or {}).get("unclear", 0),
                "input_tokens": (summary.get("stats") or {}).get("input_tokens", 0),
                "output_tokens": (summary.get("stats") or {}).get("output_tokens", 0),
                "reasoning_tokens": (summary.get("stats") or {}).get("reasoning_tokens", 0),
                "cache_creation_input_tokens": (summary.get("stats") or {}).get("cache_creation_input_tokens", 0),
                "cache_read_input_tokens": (summary.get("stats") or {}).get("cache_read_input_tokens", 0),
            }

            exp_data["summary"]["total_models"] += 1

        if exp_data["models"]:
            accuracies = [m["summary"].get("accuracy", 0.0) for m in exp_data["models"].values()]
            exp_data["summary"]["avg_accuracy"] = sum(accuracies) / len(accuracies) if accuracies else 0.0
            aggregated["experiments"][suite_name] = exp_data
            aggregated["summary"]["total_experiments"] += 1

    aggregated["summary"]["total_models"] = len(aggregated["models"])
    ds = aggregated["metadata"]["dataset"]
    ds["total_problems"] = ds["horn_problems"] + ds["nonhorn_problems"]
    return aggregated


