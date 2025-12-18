from __future__ import annotations

import json
from pathlib import Path


def test_runner_writes_cost_totals_when_pricing_enabled(tmp_path, monkeypatch) -> None:
    from llmlog.runner import run_suite

    # Create a tiny dataset (header + 1 row)
    dataset = tmp_path / "ds.jsonl"
    dataset.write_text(
        "\n".join(
            [
                json.dumps(
                    [
                        "id",
                        "maxvarnr",
                        "maxlen",
                        "mustbehorn",
                        "issatisfiable",
                        "problem",
                        "proof",
                        "horn_units",
                    ]
                ),
                json.dumps([1, 2, 2, 0, 1, [[1], [-1, 2]], [], []]),
                "",
            ]
        )
    )

    # Use an existing prompt template from the repo (absolute path)
    repo = Path(__file__).resolve().parents[1]
    tmpl = (repo / "prompts" / "sat_decision__cnf_compact__answer_only.j2").resolve()
    pricing = (repo / "configs" / "pricing" / "openai_2025-12-18.yaml").resolve()

    suite_yaml = tmp_path / "suite.yaml"
    suite_yaml.write_text(
        "\n".join(
            [
                "name: cost_test",
                "task: sat_decision",
                "subset: mixed",
                "dataset:",
                f"  path: {dataset}",
                "  skip_rows: 1",
                "prompting:",
                "  render_policy: fixed",
                "  representation: cnf_compact",
                f"  template: {tmpl}",
                "  prompt_profile: direct",
                "  response_style: answer_only",
                "  answer_format: contradiction_satisfiable",
                "targets:",
                "  - provider: openai",
                "    model: gpt-5.2",
                "    temperature: 0",
                "    max_tokens: 1000",
                f"pricing_table: {pricing}",
                "output_pattern: runs/${name}/${run}/${provider}/${model}/${thinking_mode}/results.jsonl",
            ]
        )
    )

    # Avoid any network calls: stub provider call
    def fake_run_chat(**kwargs):
        return {
            "text": "satisfiable",
            "thinking_text": None,
            "provider": "openai",
            "model": "gpt-5.2",
            "finish_reason": "stop",
            "usage": {"input_tokens": 1000, "output_tokens": 500, "reasoning_tokens": 0},
            "raw_response": {},
        }

    import llmlog.runner as runner_mod

    monkeypatch.setattr(runner_mod, "run_chat", fake_run_chat)

    run_suite(
        suite_path=str(suite_yaml),
        run_id="run1",
        output_root=str(tmp_path),
        limit=1,
        dry_run=False,
        only_providers=["openai"],
        resume=False,
        lockstep=False,
    )

    summaries = list(tmp_path.rglob("results.summary.json"))
    assert summaries
    payload = json.loads(summaries[0].read_text())
    stats = payload["stats"]
    # gpt-5.2 rates: input $1.75/M, output $14/M (from seeded pricing file)
    assert abs(stats["cost_input_usd"] - 0.00175) < 1e-9
    assert abs(stats["cost_output_usd"] - 0.007) < 1e-9
    assert abs(stats["cost_total_usd"] - 0.00875) < 1e-9


