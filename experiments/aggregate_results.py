#!/usr/bin/env python3
"""
Aggregate results from all experiments into a single JSON for dashboard.

Usage:
    python -m experiments.aggregate_results --run-id final_validation_test --output aggregated.json
    python -m experiments.aggregate_results --run-id validation_20251016 --output aggregated.json
"""

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Any


def aggregate_results(runs_dir: Path, run_id: str) -> Dict[str, Any]:
    """Aggregate all results from a specific run."""
    
    aggregated = {
        "metadata": {
            "run_id": run_id,
            "runs_dir": str(runs_dir),
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
            }
        },
        "experiments": {},
        "models": {},
        "summary": {
            "total_experiments": 0,
            "total_models": 0,
            "total_problems_processed": 0,
        }
    }
    
    # Track unique problems globally
    seen_problems = set()  # Track (problem_id, horn, satflag) tuples
    
    # Scan all experiments
    for exp_dir in sorted(runs_dir.iterdir()):
        if not exp_dir.is_dir():
            continue
        
        exp_name = exp_dir.name
        run_dir = exp_dir / run_id
        
        if not run_dir.exists():
            continue
        
        exp_data = {
            "name": exp_name,
            "models": {},
            "summary": {
                "total_models": 0,
                "avg_accuracy": 0,
                "total_unclear": 0,
            }
        }
        
        # Scan all model results
        for summary_file in sorted(run_dir.rglob("results.summary.json")):
            # Parse path: runs/<exp>/<run_id>/<provider>/<model>/<thinking>/results.summary.json
            parts = summary_file.parts
            provider_idx = -4
            model_idx = -3
            thinking_idx = -2
            
            provider = parts[provider_idx]
            model = parts[model_idx]
            thinking_mode = parts[thinking_idx]
            
            with open(summary_file) as f:
                summary_data = json.load(f)
            
            # Load detailed results for complexity breakdown
            results_file = summary_file.parent / "results.jsonl"
            complexity_breakdown = {}
            
            if results_file.exists():
                with open(results_file) as f:
                    for line in f:
                        try:
                            row = json.loads(line)
                            meta = row.get("meta", {})
                            maxvars = meta.get("maxvars")
                            maxlen = meta.get("maxlen")
                            horn = meta.get("horn")
                            satflag = meta.get("satflag")
                            parsed = row.get("parsed_answer")
                            
                            # Update dataset metadata from ANY row
                            if maxvars is not None:
                                if aggregated["metadata"]["dataset"]["min_vars"] is None or maxvars < aggregated["metadata"]["dataset"]["min_vars"]:
                                    aggregated["metadata"]["dataset"]["min_vars"] = maxvars
                                if aggregated["metadata"]["dataset"]["max_vars"] is None or maxvars > aggregated["metadata"]["dataset"]["max_vars"]:
                                    aggregated["metadata"]["dataset"]["max_vars"] = maxvars
                            
                            if maxlen is not None:
                                if aggregated["metadata"]["dataset"]["min_len"] is None or maxlen < aggregated["metadata"]["dataset"]["min_len"]:
                                    aggregated["metadata"]["dataset"]["min_len"] = maxlen
                                if aggregated["metadata"]["dataset"]["max_len"] is None or maxlen > aggregated["metadata"]["dataset"]["max_len"]:
                                    aggregated["metadata"]["dataset"]["max_len"] = maxlen
                            
                            # Count problem types (only once per unique problem ID)
                            problem_id = row.get("id")
                            if problem_id is not None and horn is not None and satflag is not None:
                                prob_key = (problem_id, horn, satflag)
                                if prob_key not in seen_problems:
                                    seen_problems.add(prob_key)
                                    
                                    if horn == 1:
                                        aggregated["metadata"]["dataset"]["horn_problems"] += 1
                                    elif horn == 0:
                                        aggregated["metadata"]["dataset"]["nonhorn_problems"] += 1
                                    
                                    if satflag == 1:
                                        aggregated["metadata"]["dataset"]["sat_problems"] += 1
                                    elif satflag == 0:
                                        aggregated["metadata"]["dataset"]["unsat_problems"] += 1
                            
                            # Complexity breakdown
                            if maxvars is not None and parsed is not None and satflag is not None:
                                if maxvars not in complexity_breakdown:
                                    complexity_breakdown[maxvars] = {"total": 0, "correct": 0}
                                complexity_breakdown[maxvars]["total"] += 1
                                if parsed != 2 and parsed == satflag:
                                    complexity_breakdown[maxvars]["correct"] += 1
                        except:
                            pass
            
            model_key = f"{provider}/{model}/{thinking_mode}"
            
            exp_data["models"][model_key] = {
                "provider": provider,
                "model": model,
                "thinking_mode": thinking_mode,
                "summary": summary_data,
                "complexity_breakdown": {
                    str(k): {
                        "accuracy": v["correct"] / v["total"] if v["total"] > 0 else 0,
                        "total": v["total"],
                        "correct": v["correct"]
                    }
                    for k, v in sorted(complexity_breakdown.items())
                }
            }
            
            # Add to global models dict
            if model_key not in aggregated["models"]:
                aggregated["models"][model_key] = {
                    "provider": provider,
                    "model": model,
                    "thinking_mode": thinking_mode,
                    "experiments": {}
                }
            
            aggregated["models"][model_key]["experiments"][exp_name] = {
                "accuracy": summary_data.get("accuracy", 0),
                "total": summary_data.get("total", 0),
                "correct": summary_data.get("correct", 0),
                "unclear": summary_data.get("unclear", 0),
            }
            
            exp_data["summary"]["total_models"] += 1
        
        # Calculate experiment summary
        if exp_data["models"]:
            accuracies = [m["summary"].get("accuracy", 0) for m in exp_data["models"].values()]
            exp_data["summary"]["avg_accuracy"] = sum(accuracies) / len(accuracies) if accuracies else 0
            exp_data["summary"]["total_unclear"] = sum(m["summary"].get("unclear", 0) for m in exp_data["models"].values())
            
            aggregated["experiments"][exp_name] = exp_data
            aggregated["summary"]["total_experiments"] += 1
    
    # Calculate global summary
    all_models = set()
    for exp_data in aggregated["experiments"].values():
        all_models.update(exp_data["models"].keys())
    aggregated["summary"]["total_models"] = len(all_models)
    
    # Calculate total unique problems
    dataset = aggregated["metadata"]["dataset"]
    dataset["total_problems"] = dataset["horn_problems"] + dataset["nonhorn_problems"]
    
    return aggregated


def main():
    parser = argparse.ArgumentParser(description="Aggregate experiment results")
    parser.add_argument(
        "--runs-dir",
        type=Path,
        default=Path("experiments/runs"),
        help="Path to runs directory"
    )
    parser.add_argument(
        "--run-id",
        required=True,
        help="Run identifier to aggregate (e.g., final_validation_test, validation_20251016)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("experiments/aggregated_results.json"),
        help="Output JSON file path"
    )
    
    args = parser.parse_args()
    
    print(f"Aggregating results from run: {args.run_id}")
    aggregated = aggregate_results(args.runs_dir, args.run_id)
    
    with open(args.output, "w") as f:
        json.dump(aggregated, f, indent=2)
    
    print(f"\n✓ Aggregated {aggregated['summary']['total_experiments']} experiments")
    print(f"✓ Found {aggregated['summary']['total_models']} unique model configurations")
    print(f"✓ Output written to: {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

