from __future__ import annotations

from pathlib import Path


def _fixture_problem_row():
    from llmlog.problems.schema import ProblemRow

    # id, maxvarnr, maxlen, mustbehorn, issatisfiable, problem, proof_or_model, horn_units
    return ProblemRow.from_array(
        [
            1,
            4,
            2,
            1,
            1,
            [[1], [-2, 1], [-2, -1], [1, 2]],  # includes a non-Horn clause [1,2]
            [],
            [],
        ]
    )


def test_render_clauses_horn_rules_matches_legacy_style() -> None:
    from llmlog.prompts.render import render_clauses

    pr = _fixture_problem_row()
    txt = render_clauses(pr.problem or [], representation="horn_rules")
    # Facts/rules
    assert "p1." in txt
    assert "if p2 then p1." in txt
    assert "if p2 and p1 then p0." in txt
    # Non-Horn clause rendered as compact CNF inside Horn block
    assert "p1 or p2." in txt


def test_render_clauses_cnf_compact() -> None:
    from llmlog.prompts.render import render_clauses

    pr = _fixture_problem_row()
    txt = render_clauses(pr.problem or [], representation="cnf_compact")
    assert "p1." in txt
    assert "not(p2) or p1." in txt
    assert "not(p2) or not(p1)." in txt


def test_render_prompt_uses_template_and_injects_clauses() -> None:
    from llmlog.prompts.render import render_prompt

    pr = _fixture_problem_row()
    repo = Path(__file__).resolve().parents[1]
    template = repo / "prompts" / "sat_decision__cnf_compact__answer_only.j2"
    text = render_prompt(problem=pr, template_path=str(template), representation="cnf_compact")
    assert "Statements:" in text
    assert "not(p2) or p1." in text


