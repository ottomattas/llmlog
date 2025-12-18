from __future__ import annotations

import json


def test_export_provenance_human_readable(tmp_path) -> None:
    from llmlog.exports import export_provenance_human_readable

    prov = tmp_path / "results.provenance.jsonl"
    prov.write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "id": 1,
                        "provider": "openai",
                        "model": "gpt-x",
                        "prompt": "P",
                        "completion_text": "C",
                        "thinking_text": "T",
                        "raw_response": {"k": "v"},
                    }
                ),
                "",
            ]
        )
    )

    out = tmp_path / "out"
    written = export_provenance_human_readable(provenance_path=str(prov), out_dir=str(out), include_raw_response=True)
    assert written

    base = out / "openai" / "gpt-x" / "1"
    assert (base / "prompt.txt").read_text() == "P"
    assert (base / "completion.txt").read_text() == "C"
    assert (base / "thinking.txt").read_text() == "T"
    assert json.loads((base / "raw_response.json").read_text()) == {"k": "v"}


