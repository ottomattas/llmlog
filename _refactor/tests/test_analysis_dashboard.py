from __future__ import annotations


def test_generate_html_dashboard_writes_file(tmp_path) -> None:
    from llmlog.analysis.dashboard import generate_html_dashboard

    aggregated = {
        "metadata": {"run_id": "run1"},
        "experiments": {"suiteA": {"name": "suiteA", "models": {}, "summary": {}}},
        "models": {"openai/gpt-x/nothink": {"provider": "openai", "model": "gpt-x", "thinking_mode": "nothink", "experiments": {"suiteA": {"accuracy": 0.5, "total": 2}}}},
        "summary": {"total_experiments": 1, "total_models": 1},
    }
    out = tmp_path / "dash.html"
    generate_html_dashboard(aggregated=aggregated, output_path=str(out))
    txt = out.read_text()
    assert "suiteA" in txt
    assert "openai/gpt-x/nothink" in txt


