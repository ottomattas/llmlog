from __future__ import annotations

from pathlib import Path


def test_iter_problem_arrays_includes_header_row() -> None:
    from llmlog.problems.reader import iter_problem_arrays

    fixture = Path(__file__).parent / "fixtures" / "problems_fixture.jsonl"
    rows = list(iter_problem_arrays(str(fixture)))
    assert isinstance(rows[0], list)
    assert rows[0][0] == "id"


def test_iter_problem_rows_skips_header_and_parses_rows() -> None:
    from llmlog.problems.reader import iter_problem_rows

    fixture = Path(__file__).parent / "fixtures" / "problems_fixture.jsonl"
    rows = list(iter_problem_rows(str(fixture), skip_rows=0))
    assert len(rows) == 2
    assert rows[0].id == 1
    assert rows[0].mustbehorn == 1
    assert rows[0].issatisfiable == 1
    assert rows[1].id == 2
    assert rows[1].mustbehorn == 0
    assert rows[1].issatisfiable == 0


def test_filters_horn_only_and_nonhorn_only() -> None:
    from llmlog.problems.filters import horn_only, nonhorn_only
    from llmlog.problems.reader import iter_problem_rows

    fixture = Path(__file__).parent / "fixtures" / "problems_fixture.jsonl"
    rows = list(iter_problem_rows(str(fixture), skip_rows=0))
    assert [r.id for r in horn_only(rows)] == [1]
    assert [r.id for r in nonhorn_only(rows)] == [2]


