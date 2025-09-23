#!/usr/bin/env python3

import argparse
import json
import os
from typing import Dict, Any, List


def read_rows(path: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r") as f:
        for line in f:
            t = line.strip()
            if not t:
                continue
            try:
                rows.append(json.loads(t))
            except Exception:
                continue
    return rows


def write_rows(path: str, rows: List[Dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract failed/unclear rows to a new JSONL for reruns")
    ap.add_argument("input", help="Path to an existing results.jsonl")
    ap.add_argument("output", help="Path to write rerun.jsonl (ids+meta)")
    ap.add_argument("--include-errors", action="store_true", help="Include rows with non-null error")
    ap.add_argument("--include-unclear", action="store_true", help="Include rows with parsed_answer==2")
    ap.add_argument("--dataset", type=str, default=None, help="Path to original dataset (problems_dist*.js)")
    ap.add_argument("--output-dataset", type=str, default=None, help="Path to write subset dataset filtered by failed ids")
    args = ap.parse_args()

    rows = read_rows(args.input)
    out: List[Dict[str, Any]] = []
    for r in rows:
        pa = r.get("parsed_answer")
        err = r.get("error")
        if (args.include_errors and err) or (args.include_unclear and pa == 2):
            out.append({
                "id": r.get("id"),
                "meta": r.get("meta"),
                "provider": r.get("provider"),
                "model": r.get("model"),
                "error": err,
                "parsed_answer": pa,
            })
    write_rows(args.output, out)

    # Optionally produce a subset dataset file compatible with runner input
    if args.dataset and args.output_dataset:
        failed_ids = set([r.get("id") for r in out])
        subset_lines: List[str] = []
        with open(args.dataset, "r") as f:
            for line in f:
                t = line.strip()
                if not t:
                    continue
                if t.startswith("[") and "]" in t:
                    try:
                        arr = json.loads(t)
                        # dataset rows are arrays where index 0 is id
                        if isinstance(arr, list) and arr and arr[0] in failed_ids:
                            subset_lines.append(line.rstrip("\n"))
                    except Exception:
                        # header or malformed lines are ignored
                        continue
        if subset_lines:
            os.makedirs(os.path.dirname(args.output_dataset), exist_ok=True)
            with open(args.output_dataset, "w") as f:
                # write the original header if present
                with open(args.dataset, "r") as df:
                    header = df.readline().strip()
                    if header:
                        try:
                            json.loads(header)
                            f.write(header + "\n")
                        except Exception:
                            pass
                for ln in subset_lines:
                    f.write(ln + "\n")
        else:
            print("No matching dataset rows found for failed ids.")


if __name__ == "__main__":
    main()


