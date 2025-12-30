from __future__ import annotations

import json


def test_combined_dashboard_data_excludes_pending_from_completed_accuracy(tmp_path) -> None:
    from llmlog.analysis.combined_dashboard import build_combined_dashboard_data

    runs = tmp_path / "runs"
    target_dir = runs / "suiteA" / "run1" / "openai" / "gpt-x" / "think_high"
    target_dir.mkdir(parents=True)

    (target_dir / "run.manifest.json").write_text(
        json.dumps(
            {
                "suite": "suiteA",
                "run": "run1",
                "thinking_mode": "think_high",
                "prompting": {"representation": "cnf_nl", "template": "prompts/sat_decision__cnf_nl__dpll_alg_linear.j2"},
                "target": {"provider": "openai", "model": "gpt-x"},
            }
        )
    )

    # All rows share same meta so they land in one group.
    base_meta = {"maxvars": 10, "maxlen": 4, "horn": 0, "satflag": 1}
    rows = [
        # pending: should be excluded from "completed" denom
        {"id": 1, "meta": base_meta, "openai_response_id": "resp_1", "parsed_answer": None, "error": None},
        # answered correct
        {"id": 2, "meta": base_meta, "parsed_answer": 1, "correct": True, "error": None},
        # unclear (no error)
        {"id": 3, "meta": base_meta, "parsed_answer": 2, "correct": None, "error": None},
        # error (should be excluded from "completed" denom)
        {"id": 4, "meta": base_meta, "parsed_answer": 2, "correct": None, "error": "boom"},
        "",
    ]
    (target_dir / "results.jsonl").write_text("\n".join([json.dumps(r) if isinstance(r, dict) else r for r in rows]))

    combined = build_combined_dashboard_data(runs_dir=str(runs))
    assert combined["metadata"]["results_files_scanned"] == 1
    assert len(combined["groups"]) == 1

    g = combined["groups"][0]
    c = g["counts"]
    assert c["total"] == 4
    assert c["pending"] == 1
    assert c["errors"] == 1
    assert c["answered"] == 1
    assert c["unclear"] == 1
    assert c["correct"] == 1

    # completed denom = answered + unclear = 2 -> accuracy 0.5
    assert c["denoms"]["completed"] == 2
    assert abs(float(c["accuracy"]["completed"]) - 0.5) < 1e-9


