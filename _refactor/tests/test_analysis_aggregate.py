from __future__ import annotations

import json


def test_aggregate_runs_smoke(tmp_path) -> None:
    from llmlog.analysis.aggregate import aggregate_runs

    runs = tmp_path / "runs"
    suite = runs / "suiteA" / "run1" / "openai" / "gpt-x" / "nothink"
    suite.mkdir(parents=True)

    # Write minimal results + summary
    (suite / "results.jsonl").write_text(
        "\n".join(
            [
                json.dumps({"id": 1, "meta": {"maxvars": 10, "maxlen": 3, "horn": 1, "satflag": 1}, "correct": True}),
                json.dumps({"id": 2, "meta": {"maxvars": 10, "maxlen": 3, "horn": 1, "satflag": 0}, "correct": False}),
                "",
            ]
        )
    )
    (suite / "results.summary.json").write_text(
        json.dumps(
            {
                "suite": "suiteA",
                "run": "run1",
                "provider": "openai",
                "model": "gpt-x",
                "thinking_mode": "nothink",
                "stats": {"total": 2, "correct": 1, "unclear": 0, "input_tokens": 3, "output_tokens": 4, "reasoning_tokens": 0},
                "accuracy": 0.5,
            }
        )
    )

    agg = aggregate_runs(runs_dir=str(runs), run_id="run1")
    assert agg["summary"]["total_experiments"] == 1
    assert agg["summary"]["total_models"] == 1
    assert agg["metadata"]["dataset"]["horn_problems"] == 2
    assert agg["metadata"]["dataset"]["sat_problems"] == 1
    assert agg["metadata"]["dataset"]["unsat_problems"] == 1


