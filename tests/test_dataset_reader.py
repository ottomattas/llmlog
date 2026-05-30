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


def test_filters_maxvars_maxlen_ids_and_case_limit() -> None:
    from llmlog.problems.filters import limit_per_case, only_ids, only_maxlen, only_maxvars
    from llmlog.problems.schema import ProblemRow

    rows = [
        ProblemRow(id=1, maxvarnr=10, maxlen=3, mustbehorn=1, issatisfiable=1, problem=[[1]], proof_or_model=None, horn_units=None, raw=[]),
        ProblemRow(id=2, maxvarnr=10, maxlen=3, mustbehorn=1, issatisfiable=0, problem=[[1]], proof_or_model=None, horn_units=None, raw=[]),
        ProblemRow(id=3, maxvarnr=20, maxlen=3, mustbehorn=1, issatisfiable=1, problem=[[1]], proof_or_model=None, horn_units=None, raw=[]),
        ProblemRow(id=4, maxvarnr=10, maxlen=5, mustbehorn=0, issatisfiable=1, problem=[[1]], proof_or_model=None, horn_units=None, raw=[]),
    ]

    assert [r.id for r in only_maxvars(rows, {10})] == [1, 2, 4]
    assert [r.id for r in only_maxlen(rows, {3})] == [1, 2, 3]
    assert [r.id for r in only_ids(rows, {"2", "4"})] == [2, 4]

    # Case key = (maxvarnr, maxlen, mustbehorn)
    # Here (10,3,1) appears twice; limit_per_case(1) should keep the first only.
    assert [r.id for r in limit_per_case(rows, 1)] == [1, 3, 4]


