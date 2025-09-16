from typing import Any, Dict, Iterable, Iterator, List


def horn_only(rows: Iterable[List[Any]]) -> Iterator[List[Any]]:
    for row in rows:
        try:
            if int(row[3]) == 1:
                yield row
        except Exception:
            continue


def skip(rows: Iterable[List[Any]], n: int) -> Iterator[List[Any]]:
    it = iter(rows)
    for _ in range(max(0, n)):
        try:
            next(it)
        except StopIteration:
            return
    for r in it:
        yield r


def limit(rows: Iterable[List[Any]], n: int) -> Iterator[List[Any]]:
    count = 0
    for r in rows:
        if count >= n:
            break
        yield r
        count += 1


