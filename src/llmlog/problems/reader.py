from __future__ import annotations

import json
from typing import Any, Iterator, List, Optional, Sequence

from .schema import ProblemRow


def read_jsonl_values(path: str) -> Iterator[Any]:
    """Yield parsed JSON values from a JSONL/JS-array-per-line file.

    Compatibility target: experiments.runner.read_jsonl_rows

    Behavior:
    - Empty lines are skipped.
    - If the first non-empty line is not JSON, it is skipped (header/malformed).
    - Later malformed lines are skipped.
    """
    with open(path, "r") as f:
        header_skipped = False
        for line in f:
            txt = line.strip()
            if not txt:
                continue
            try:
                yield json.loads(txt)
            except Exception:
                if not header_skipped:
                    header_skipped = True
                    continue
                continue


def iter_problem_arrays(path: str) -> Iterator[List[Any]]:
    """Yield list rows from a dataset file (including header row if present)."""
    for val in read_jsonl_values(path):
        if isinstance(val, list):
            yield val


def iter_problem_rows(path: str, *, skip_rows: int = 0) -> Iterator[ProblemRow]:
    """Yield typed problem rows, skipping header/malformed rows safely.

    - Applies `skip_rows` first (mirrors existing config semantics).
    - Skips any header row if detected.
    - Skips rows that cannot be parsed into the 8-column schema.
    """
    it: Iterator[Sequence[Any]] = iter_problem_arrays(path)
    for _ in range(max(0, int(skip_rows or 0))):
        try:
            next(it)
        except StopIteration:
            return

    for row in it:
        if ProblemRow.is_header_row(row):
            continue
        try:
            yield ProblemRow.from_array(row)
        except Exception:
            continue


def read_problem_row_at_index(
    path: str,
    *,
    index_1_based: int,
    skip_rows: int = 0,
    horn_only: bool = False,
    nonhorn_only: bool = False,
) -> Optional[ProblemRow]:
    """Convenience helper for debugging/exports: fetch a single row by index after filtering."""
    if horn_only and nonhorn_only:
        raise ValueError("horn_only and nonhorn_only cannot both be true")
    i0 = max(1, int(index_1_based)) - 1
    rows = iter_problem_rows(path, skip_rows=skip_rows)
    if horn_only:
        rows = (r for r in rows if r.mustbehorn == 1)
    if nonhorn_only:
        rows = (r for r in rows if r.mustbehorn == 0)
    for idx, r in enumerate(rows):
        if idx == i0:
            return r
    return None


