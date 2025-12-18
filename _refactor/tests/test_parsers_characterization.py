from __future__ import annotations


def test_yes_no_parser_characterization() -> None:
    # Mirrors current behavior in experiments/parsers.py
    from llmlog.parsers import parse_yes_no

    assert parse_yes_no("yes") == 0
    assert parse_yes_no("YES.") == 0
    assert parse_yes_no("no") == 1
    assert parse_yes_no("No!") == 1
    assert parse_yes_no("maybe") == 2
    assert parse_yes_no("") == 2


def test_contradiction_parser_characterization() -> None:
    from llmlog.parsers import parse_contradiction

    assert parse_contradiction("contradiction") == 0
    assert parse_contradiction("... contradiction.") == 0
    assert parse_contradiction("satisfiable") == 1
    assert parse_contradiction("unknown") == 1  # current parser treats unknown-ish as satisfiable/1
    assert parse_contradiction("") == 2


def test_both_parser_characterization() -> None:
    from llmlog.parsers import parse_both

    assert parse_both("yes") == 0
    assert parse_both("no") == 1
    assert parse_both("contradiction") == 0
    assert parse_both("satisfiable") == 1
    assert parse_both("garbage") == 2


