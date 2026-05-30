from __future__ import annotations

import re
from collections import defaultdict
from typing import Iterable, Iterator, List, Optional, Set, Tuple, TypeVar

from .schema import ProblemRow

T = TypeVar("T")

_RANGE_RE = re.compile(r"^\s*(-?\d+)\s*-\s*(-?\d+)\s*$")


def horn_only(rows: Iterable[ProblemRow]) -> Iterator[ProblemRow]:
    for row in rows:
        if row.mustbehorn == 1:
            yield row


def nonhorn_only(rows: Iterable[ProblemRow]) -> Iterator[ProblemRow]:
    for row in rows:
        if row.mustbehorn == 0:
            yield row


def parse_int_list_spec(spec: Optional[str]) -> List[int]:
    """Parse an integer list/range spec into a list of ints.

    Supported formats:
    - Range: "3-10"
    - List: "3,4,7"
    - Mixed: "3-5,7" or "1,2-4"
    """
    s = (spec or "").strip()
    if not s:
        return []
    parts = [p.strip() for p in s.split(",") if p.strip()]
    out: List[int] = []
    for part in parts:
        m = _RANGE_RE.match(part)
        if m:
            start = int(m.group(1))
            end = int(m.group(2))
            if end < start:
                start, end = end, start
            out.extend(list(range(start, end + 1)))
            continue
        out.append(int(part))
    return out


def parse_int_set_spec(spec: Optional[str]) -> Set[int]:
    return set(parse_int_list_spec(spec))


def parse_str_set_spec(spec: Optional[str]) -> Set[str]:
    if not spec:
        return set()
    return {p.strip() for p in str(spec).split(",") if p.strip()}


def only_ids(rows: Iterable[ProblemRow], ids: Set[str]) -> Iterator[ProblemRow]:
    """Filter rows by row.id (string compare)."""
    if not ids:
        yield from rows
        return
    want = {str(x) for x in ids}
    for row in rows:
        if str(row.id) in want:
            yield row


def only_maxvars(rows: Iterable[ProblemRow], maxvars: Set[int]) -> Iterator[ProblemRow]:
    if not maxvars:
        yield from rows
        return
    want = {int(x) for x in maxvars}
    for row in rows:
        if row.maxvarnr is None:
            continue
        if int(row.maxvarnr) in want:
            yield row


def only_maxlen(rows: Iterable[ProblemRow], maxlen: Set[int]) -> Iterator[ProblemRow]:
    if not maxlen:
        yield from rows
        return
    want = {int(x) for x in maxlen}
    for row in rows:
        if row.maxlen is None:
            continue
        if int(row.maxlen) in want:
            yield row


def limit_per_case(rows: Iterable[ProblemRow], n: int) -> Iterator[ProblemRow]:
    """Limit rows per "case" = (maxvarnr, maxlen, mustbehorn).

    This supports iterative drilldown runs on the full dataset while keeping
    a roughly balanced selection across the chosen grid.
    """
    n_i = int(n)
    if n_i <= 0:
        return
        yield  # pragma: no cover

    counts: dict[Tuple[Optional[int], Optional[int], Optional[int]], int] = defaultdict(int)
    for row in rows:
        key = (row.maxvarnr, row.maxlen, row.mustbehorn)
        if counts[key] >= n_i:
            continue
        counts[key] += 1
        yield row


def skip(rows: Iterable[T], n: int) -> Iterator[T]:
    it = iter(rows)
    for _ in range(max(0, int(n))):
        try:
            next(it)
        except StopIteration:
            return
    for r in it:
        yield r


def limit(rows: Iterable[T], n: int) -> Iterator[T]:
    count = 0
    for r in rows:
        if count >= int(n):
            break
        yield r
        count += 1


