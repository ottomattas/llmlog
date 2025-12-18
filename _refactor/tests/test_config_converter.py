from __future__ import annotations


def test_convert_experiments_config_dict_maps_style_and_parse() -> None:
    from llmlog.config.converter import convert_experiments_config_dict
    from llmlog.config.schema import AnswerFormat, Representation, Subset

    old = {
        "name": "horn_yn_hornonly",
        "input_file": "_refactor/datasets/validation/vars10_len3-5_hornmixed_per20_seed12345.jsonl",
        "filters": {"horn_only": True, "skip_rows": 1, "limit_rows": 10},
        "prompt": {"template": "prompts/_template_unified.j2", "style": "horn_if_then", "variables": {}},
        "parse": {"type": "yes_no"},
        "targets": [{"provider": "openai", "model": "gpt-5-mini-2025-08-07", "max_tokens": 1000}],
    }

    suite, target_set = convert_experiments_config_dict(old)
    assert suite.subset == Subset.hornonly
    assert suite.dataset.path == "datasets/validation/vars10_len3-5_hornmixed_per20_seed12345.jsonl"
    assert suite.prompting.representation == Representation.horn_rules  # type: ignore[attr-defined]
    assert suite.prompting.answer_format == AnswerFormat.yes_no  # type: ignore[attr-defined]
    assert target_set.targets[0].provider == "openai"


def test_convert_experiments_config_dict_maps_cnf_contradiction() -> None:
    from llmlog.config.converter import convert_experiments_config_dict
    from llmlog.config.schema import AnswerFormat, Representation

    old = {
        "name": "cnf2_contradiction_mixed",
        "input_file": "_refactor/datasets/validation/vars10_len3-5_hornmixed_per20_seed12345.jsonl",
        "filters": {"horn_only": False},
        "prompt": {"template": "prompts/_template_unified.j2", "style": "cnf_v2", "variables": {}},
        "parse": {"type": "contradiction"},
        "targets": [{"provider": "google", "model": "gemini-2.5-pro"}],
    }

    suite, _ = convert_experiments_config_dict(old)
    assert suite.prompting.representation == Representation.cnf_compact  # type: ignore[attr-defined]
    assert suite.prompting.answer_format == AnswerFormat.contradiction_satisfiable  # type: ignore[attr-defined]


