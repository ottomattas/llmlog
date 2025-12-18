from __future__ import annotations

from typing import Iterable, Iterator, List, TypeVar

from .schema import ProblemRow

T = TypeVar("T")


def horn_only(rows: Iterable[ProblemRow]) -> Iterator[ProblemRow]:
    for row in rows:
        if row.mustbehorn == 1:
            yield row


def nonhorn_only(rows: Iterable[ProblemRow]) -> Iterator[ProblemRow]:
    for row in rows:
        if row.mustbehorn == 0:
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


