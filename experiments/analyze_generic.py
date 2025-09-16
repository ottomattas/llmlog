#!/usr/bin/env python3

import sys
import json
from collections import OrderedDict, defaultdict
from typing import Dict, Any


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: ./experiments/analyze_generic.py experiments/runs/<name>/results.jsonl")
        return
    path = sys.argv[1]
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

    # Detailed results by maxvarnr/maxlen/hornflag
    print("Detailed results by maxvarnr/maxlen/hornflag:")
    print("Each sublist contains [problemcount,sat_correct,unsat_correct,unclear_answer_count]")
    counts: Dict[int, Dict[int, Dict[int, list]]] = OrderedDict()
    for obj in rows:
        meta = obj.get("meta") or {}
        mv = int(meta.get("maxvars")) if meta.get("maxvars") is not None else None
        ml = int(meta.get("maxlen")) if meta.get("maxlen") is not None else None
        hf = int(meta.get("horn")) if meta.get("horn") is not None else None
        sat = int(meta.get("satflag")) if meta.get("satflag") is not None else None
        parsed = obj.get("parsed_answer")
        if None in (mv, ml, hf, sat) or parsed is None:
            continue
        counts.setdefault(mv, OrderedDict()).setdefault(ml, OrderedDict()).setdefault(hf, [0, 0, 0, 0])
        rec = counts[mv][ml][hf]
        rec[0] += 1
        if parsed == 2:
            rec[3] += 1
        else:
            if sat == parsed:
                if sat == 1:
                    rec[1] += 1
                else:
                    rec[2] += 1

    for mv in counts:
        print(mv, ": ", json.dumps(counts[mv]).replace('"', ''))

    # Combined correctness by mv/ml/hf
    print("Correctness percentages by maxvarnr/maxlen/hornflag:")
    acc: Dict[int, Dict[int, Dict[int, list]]] = OrderedDict()
    for obj in rows:
        meta = obj.get("meta") or {}
        mv = int(meta.get("maxvars")) if meta.get("maxvars") is not None else None
        ml = int(meta.get("maxlen")) if meta.get("maxlen") is not None else None
        hf = int(meta.get("horn")) if meta.get("horn") is not None else None
        sat = int(meta.get("satflag")) if meta.get("satflag") is not None else None
        parsed = obj.get("parsed_answer")
        if None in (mv, ml, hf, sat) or parsed is None:
            continue
        acc.setdefault(mv, OrderedDict()).setdefault(ml, OrderedDict()).setdefault(hf, [0, 0])
        rec = acc[mv][ml][hf]
        rec[0] += 1
        if parsed != 2 and parsed == sat:
            rec[1] += 1

    for mv in acc:
        line = [f"mv={mv}"]
        for ml in acc[mv]:
            for hf in acc[mv][ml]:
                total, ok = acc[mv][ml][hf]
                pct = round(ok / total, 2) if total else 0.0
                tag = "horn" if hf == 1 else "gene"
                line.append(f"len{ml} {tag} {pct:3.2f}")
        print("  ".join(line))


if __name__ == "__main__":
    main()


