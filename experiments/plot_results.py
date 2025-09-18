#!/usr/bin/env python3

import os
import json
from collections import defaultdict
from typing import Dict, Tuple

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


def main() -> None:
    acc = collect("experiments/runs")
    plot(acc, "experiments/plots")
    print("Wrote plots to experiments/plots")


if __name__ == "__main__":
    main()




