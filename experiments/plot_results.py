#!/usr/bin/env python3

import os
import json
from collections import defaultdict
from typing import Any, DefaultDict, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_rows(path: str):
    rows = []
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows


def accuracy(rows) -> Tuple[int, int, float]:
    total = 0
    correct = 0
    for obj in rows:
        parsed = obj.get("parsed_answer")
        meta = obj.get("meta") or {}
        sat = meta.get("satflag")
        if parsed is None or sat is None:
            continue
        total += 1
        if parsed != 2 and int(parsed) == int(sat):
            correct += 1
    pct = (correct / total) if total else 0.0
    return total, correct, pct


def collect(run_root: str = "experiments/runs") -> Dict[str, Dict[str, float]]:
    acc: Dict[str, Dict[str, float]] = defaultdict(dict)
    for exp in sorted(os.listdir(run_root)):
        expdir = os.path.join(run_root, exp)
        if not os.path.isdir(expdir):
            continue
        for fname in os.listdir(expdir):
            if not fname.endswith(".jsonl"):
                continue
            path = os.path.join(expdir, fname)
            prov = fname.split("_")[0]
            rows = read_rows(path)
            total, correct, pct = accuracy(rows)
            # store as percentage 0-100
            acc[exp][f"{prov}"] = round(pct * 100, 1)
    return acc


def plot(acc: Dict[str, Dict[str, float]], outdir: str = "experiments/plots") -> None:
    os.makedirs(outdir, exist_ok=True)
    exps = sorted(acc.keys())
    providers = sorted({p for mp in acc.values() for p in mp.keys()})

    # Per-experiment bar chart
    for exp in exps:
        vals = [acc[exp].get(p, 0.0) for p in providers]
        fig, ax = plt.subplots(figsize=(6, 3))
        bars = ax.bar(providers, vals, color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"][: len(providers)])
        ax.set_ylim(0, 100)
        ax.set_ylabel("Accuracy (%)")
        ax.set_title(exp)
        for b, v in zip(bars, vals):
            ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1, str(v), ha="center", va="bottom", fontsize=9)
        fig.tight_layout()
        fig.savefig(os.path.join(outdir, f"{exp}.png"), dpi=150)
        plt.close(fig)

    # Overall grouped bar chart
    provs = providers
    exp_indices = range(len(exps))
    width = 0.8 / max(1, len(provs))
    fig, ax = plt.subplots(figsize=(10, 4))
    for i, p in enumerate(provs):
        vals = [acc[exp].get(p, 0.0) for exp in exps]
        ax.bar([x + i * width for x in exp_indices], vals, width=width, label=p)
    ax.set_xticks([x + (len(provs) - 1) * width / 2 for x in exp_indices])
    ax.set_xticklabels(exps, rotation=20, ha="right")
    ax.set_ylim(0, 100)
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Accuracy by experiment and provider")
    ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "overall.png"), dpi=150)
    plt.close(fig)


def _label_for(provider: str, model: str) -> str:
    # Compact multi-line label for readability
    return f"{provider}\n{model}"


def _scan_targets(name: str, run_id: str, run_root: str = "experiments/runs") -> List[Dict[str, Any]]:
    base = os.path.join(run_root, name, run_id)
    targets: List[Dict[str, Any]] = []
    if not os.path.isdir(base):
        return targets
    for dirpath, _dirnames, filenames in os.walk(base):
        if "results.jsonl" in filenames:
            # Expect structure: .../<name>/<run>/<provider>/<model>/
            parts = dirpath.split(os.sep)
            if len(parts) < 2:
                continue
            model = parts[-1]
            provider = parts[-2] if len(parts) >= 2 else "unknown"
            results_path = os.path.join(dirpath, "results.jsonl")
            summary_path = os.path.join(dirpath, "results.summary.json")
            targets.append({
                "provider": provider,
                "model": model,
                "results_path": results_path,
                "summary_path": summary_path if os.path.exists(summary_path) else None,
            })
    # Keep deterministic order by provider/model
    targets.sort(key=lambda t: (t["provider"], t["model"]))
    return targets


def _compute_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = 0
    correct = 0
    unclear = 0
    sat_total = 0
    sat_correct = 0
    unsat_total = 0
    unsat_correct = 0
    for obj in rows:
        parsed = obj.get("parsed_answer")
        meta = obj.get("meta") or {}
        satflag = meta.get("satflag")
        if parsed is None or satflag is None:
            continue
        total += 1
        is_unclear = (parsed == 2)
        if is_unclear:
            unclear += 1
        is_correct = (not is_unclear) and (int(parsed) == int(satflag))
        if is_correct:
            correct += 1
        try:
            sf = int(satflag)
            if sf == 1:
                sat_total += 1
                if is_correct:
                    sat_correct += 1
            elif sf == 0:
                unsat_total += 1
                if is_correct:
                    unsat_correct += 1
        except Exception:
            # ignore malformed satflag
            pass
    acc = (correct / total) if total else 0.0
    sat_acc = (sat_correct / sat_total) if sat_total else 0.0
    unsat_acc = (unsat_correct / unsat_total) if unsat_total else 0.0
    return {
        "total": total,
        "correct": correct,
        "unclear": unclear,
        "accuracy": acc,
        "sat_total": sat_total,
        "sat_correct": sat_correct,
        "sat_accuracy": sat_acc,
        "unsat_total": unsat_total,
        "unsat_correct": unsat_correct,
        "unsat_accuracy": unsat_acc,
    }


def _read_summary(summary_path: Optional[str]) -> Dict[str, Any]:
    if not summary_path or not os.path.exists(summary_path):
        return {}
    try:
        with open(summary_path, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def _collect_rows_by_model(targets: List[Dict[str, Any]]) -> Dict[Tuple[str, str], List[Dict[str, Any]]]:
    data: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
    for t in targets:
        rows = read_rows(t["results_path"]) if os.path.exists(t["results_path"]) else []
        data[(t["provider"], t["model"]) ] = rows
    return data


def plot_per_run(
    name: str,
    run_id: str,
    outdir: str = "experiments/plots",
    run_root: str = "experiments/runs",
    save_in_run: bool = False,
) -> None:
    targets = _scan_targets(name, run_id, run_root)
    if not targets:
        return
    # Decide destination directory
    if save_in_run:
        dest_dir = os.path.join(run_root, name, run_id, "_plots")
    else:
        dest_dir = os.path.join(outdir, name, run_id)
    os.makedirs(dest_dir, exist_ok=True)

    # Load rows and summaries
    rows_by_model = _collect_rows_by_model(targets)
    stats_by_model: Dict[Tuple[str, str], Dict[str, Any]] = {}
    timing_by_model: Dict[Tuple[str, str], Optional[float]] = {}
    for t in targets:
        key = (t["provider"], t["model"]) 
        stats_by_model[key] = _compute_stats(rows_by_model[key])
        s = _read_summary(t.get("summary_path"))
        timing_by_model[key] = s.get("avg_timing_ms") if isinstance(s, dict) else None

    labels = [_label_for(p, m) for (p, m) in stats_by_model.keys()]
    # Maintain order consistent with targets
    key_list = list(stats_by_model.keys())

    # 1) Overall accuracy (horizontal bar to avoid x-label overlap)
    acc_vals = [stats_by_model[k]["accuracy"] * 100.0 for k in key_list]
    h = max(4, 0.5 * len(labels))
    fig, ax = plt.subplots(figsize=(10, h))
    bars = ax.barh(labels, acc_vals)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Accuracy (%)")
    ax.set_title(f"{name} @ {run_id}: Overall accuracy by model")
    for b, v in zip(bars, acc_vals):
        ax.text(v + 1, b.get_y() + b.get_height() / 2, f"{v:.1f}", va="center", fontsize=9)
    ax.grid(axis='x', linestyle='--', alpha=0.4)
    fig.tight_layout()
    fig.savefig(os.path.join(dest_dir, "accuracy_by_model.png"), dpi=150, bbox_inches='tight')
    plt.close(fig)

    # 2) Stacked outcomes (horizontal stacked: correct / incorrect / unclear)
    totals = [stats_by_model[k]["total"] for k in key_list]
    corrects = [stats_by_model[k]["correct"] for k in key_list]
    unclears = [stats_by_model[k]["unclear"] for k in key_list]
    incorrects = [max(0, t - c - u) for t, c, u in zip(totals, corrects, unclears)]
    h = max(4, 0.6 * len(labels))
    fig, ax = plt.subplots(figsize=(12, h))
    b1 = ax.barh(labels, corrects, label="Correct", color="#2ca02c")
    b2 = ax.barh(labels, incorrects, left=corrects, label="Incorrect", color="#d62728")
    b3 = ax.barh(labels, unclears, left=[c + i for c, i in zip(corrects, incorrects)], label="Unclear", color="#7f7f7f")
    ax.set_xlabel("Count")
    ax.set_title(f"{name} @ {run_id}: Outcome breakdown by model")
    ax.legend(loc='upper right')
    ax.grid(axis='x', linestyle='--', alpha=0.4)
    fig.tight_layout()
    fig.savefig(os.path.join(dest_dir, "outcomes_stacked.png"), dpi=150, bbox_inches='tight')
    plt.close(fig)

    # 3) SAT vs UNSAT accuracy grouped bars
    sat_acc = [stats_by_model[k]["sat_accuracy"] * 100.0 for k in key_list]
    unsat_acc = [stats_by_model[k]["unsat_accuracy"] * 100.0 for k in key_list]
    x = list(range(len(labels)))
    width = 0.4
    fig_w = max(12, 0.8 * len(labels))
    fig, ax = plt.subplots(figsize=(fig_w, 5))
    ax.bar([i - width / 2 for i in x], sat_acc, width=width, label="SAT accuracy")
    ax.bar([i + width / 2 for i in x], unsat_acc, width=width, label="UNSAT accuracy")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=9)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Accuracy (%)")
    ax.set_title(f"{name} @ {run_id}: SAT vs UNSAT accuracy")
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    fig.tight_layout()
    fig.savefig(os.path.join(dest_dir, "sat_unsat_accuracy.png"), dpi=150, bbox_inches='tight')
    plt.close(fig)

    # 4) Avg timing per model (horizontal)
    timings = [timing_by_model.get(k) for k in key_list]
    if any(t is not None for t in timings):
        vals = [float(t) if isinstance(t, (int, float)) else 0.0 for t in timings]
        h = max(4, 0.5 * len(labels))
        fig, ax = plt.subplots(figsize=(10, h))
        bars = ax.barh(labels, vals)
        ax.set_xlabel("Avg response time (ms)")
        ax.set_title(f"{name} @ {run_id}: Average timing by model")
        for b, v in zip(bars, vals):
            ax.text(v + 5, b.get_y() + b.get_height() / 2, f"{v:.0f}", va="center", fontsize=9)
        ax.grid(axis='x', linestyle='--', alpha=0.4)
        fig.tight_layout()
        fig.savefig(os.path.join(dest_dir, "avg_timing_ms.png"), dpi=150, bbox_inches='tight')
        plt.close(fig)

    # 5) Complexity curves: accuracy vs maxvars and vs maxlen
    # Build per-model bins
    # Gather all unique values across all models for stable x-axis
    all_maxvars: List[int] = []
    all_maxlen: List[int] = []
    for rows in rows_by_model.values():
        for obj in rows:
            meta = obj.get("meta") or {}
            if isinstance(meta.get("maxvars"), int):
                all_maxvars.append(meta.get("maxvars"))
            if isinstance(meta.get("maxlen"), int):
                all_maxlen.append(meta.get("maxlen"))
    uniq_vars = sorted({v for v in all_maxvars})
    uniq_len = sorted({v for v in all_maxlen})

    def _acc_for_filter(rows: List[Dict[str, Any]], pred) -> float:
        total = 0
        correct = 0
        for obj in rows:
            meta = obj.get("meta") or {}
            if not pred(meta):
                continue
            parsed = obj.get("parsed_answer")
            satflag = meta.get("satflag")
            if parsed is None or satflag is None:
                continue
            total += 1
            if parsed != 2 and int(parsed) == int(satflag):
                correct += 1
        return (correct / total) if total else float("nan")

    # Plot accuracy vs maxvars
    if uniq_vars:
        fig_w = max(10, 1.8 * len(uniq_vars))
        fig, ax = plt.subplots(figsize=(fig_w, 4))
        for k in key_list:
            rows = rows_by_model[k]
            y = [_acc_for_filter(rows, lambda m, v=v: m.get("maxvars") == v) * 100.0 for v in uniq_vars]
            ax.plot(uniq_vars, y, marker="o", markersize=4, linewidth=1.5, label=_label_for(*k))
        ax.set_xlabel("maxvars (problem variable count upper bound)")
        ax.set_ylabel("Accuracy (%)")
        ax.set_title(f"{name} @ {run_id}: Accuracy vs problem maxvars")
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8)
        ax.set_ylim(0, 100)
        ax.grid(True, linestyle='--', alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(dest_dir, "accuracy_vs_maxvars.png"), dpi=150, bbox_inches='tight')
        plt.close(fig)

    # Plot accuracy vs maxlen
    if uniq_len:
        fig_w = max(10, 1.8 * len(uniq_len))
        fig, ax = plt.subplots(figsize=(fig_w, 4))
        for k in key_list:
            rows = rows_by_model[k]
            y = [_acc_for_filter(rows, lambda m, v=v: m.get("maxlen") == v) * 100.0 for v in uniq_len]
            ax.plot(uniq_len, y, marker="o", markersize=4, linewidth=1.5, label=_label_for(*k))
        ax.set_xlabel("maxlen (clause length upper bound)")
        ax.set_ylabel("Accuracy (%)")
        ax.set_title(f"{name} @ {run_id}: Accuracy vs problem maxlen")
        ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=8)
        ax.set_ylim(0, 100)
        ax.grid(True, linestyle='--', alpha=0.3)
        fig.tight_layout()
        fig.savefig(os.path.join(dest_dir, "accuracy_vs_maxlen.png"), dpi=150, bbox_inches='tight')
        plt.close(fig)

def main() -> None:
    import argparse

    ap = argparse.ArgumentParser(description="Plot experiment results")
    ap.add_argument("--name", help="Experiment name (e.g., exp6_horn_yesno)")
    ap.add_argument("--run", help="Run id (e.g., full-20250929-1349)")
    ap.add_argument("--runs_root", default="experiments/runs", help="Root runs directory")
    ap.add_argument("--outdir", default="experiments/plots", help="Output plots directory")
    ap.add_argument("--save-in-run", action="store_true", help="Save plots under <runs_root>/<name>/<run>/_plots")
    args = ap.parse_args()

    if args.name and args.run:
        plot_per_run(args.name, args.run, outdir=args.outdir, run_root=args.runs_root, save_in_run=args.save_in_run)
        target_dir = os.path.join(args.runs_root, args.name, args.run, "_plots") if args.save_in_run else os.path.join(args.outdir, args.name, args.run)
        print(f"Wrote plots to {target_dir}")
        return

    # Fallback: legacy aggregation across runs root (kept for backward compatibility)
    acc = collect(args.runs_root)
    plot(acc, args.outdir)
    print(f"Wrote plots to {args.outdir}")


if __name__ == "__main__":
    main()




