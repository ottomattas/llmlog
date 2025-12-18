from __future__ import annotations

from pathlib import Path


def test_run_suite_dry_run_writes_outputs(tmp_path) -> None:
    from llmlog.runner import run_suite

    repo = Path(__file__).resolve().parents[1]
    suite = repo / "configs" / "suites" / "sat__repr-cnf_compact__subset-mixed.yaml"

    run_suite(
        suite_path=str(suite),
        run_id="test-run",
        output_root=str(tmp_path),
        limit=1,
        dry_run=True,
        only_providers=["openai"],
        resume=False,
        lockstep=True,
    )

    # At least one results file should exist for openai targets
    results_files = list(tmp_path.glob("runs/**/results.jsonl"))
    assert results_files, "Expected results.jsonl files to be written"
    # Each should contain 1 row (limit=1)
    for rf in results_files:
        lines = [ln for ln in rf.read_text().splitlines() if ln.strip()]
        assert len(lines) == 1


