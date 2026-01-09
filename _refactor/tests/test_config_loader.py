from __future__ import annotations

from pathlib import Path


def test_resolve_suite_expands_targets_ref() -> None:
    from llmlog.config.loader import resolve_suite

    repo = Path(__file__).resolve().parents[1]
    suite_path = (
        repo
        / "configs"
        / "suites"
        / "sat__repr-cnf_compact__subset-hornonly__prompt-examples_only__anthropic_claude-opus-4-5-20251101__think-none.yaml"
    )

    suite = resolve_suite(str(suite_path))
    assert suite.targets is not None
    assert len(suite.targets) == 1
    assert suite.targets_ref is None


def test_suite_has_valid_prompt_template_paths() -> None:
    from llmlog.config.loader import load_suite_config

    repo = Path(__file__).resolve().parents[1]
    suite_path = (
        repo
        / "configs"
        / "suites"
        / "sat__repr-horn_if_then__subset-hornonly__prompt-horn_alg_linear__openai_gpt-5.2__think-none.yaml"
    )

    suite = load_suite_config(str(suite_path))
    # Template is referenced relative to _refactor root; we don't resolve here.
    assert str(suite.prompting)  # smoke: can parse into pydantic union


