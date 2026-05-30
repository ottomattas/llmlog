from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Set


def iter_jsonl_dicts(path: str) -> Iterator[Dict[str, Any]]:
    p = Path(path)
    with p.open("r") as f:
        for line in f:
            txt = line.strip()
            if not txt:
                continue
            try:
                obj = json.loads(txt)
            except Exception:
                continue
            if isinstance(obj, dict):
                yield obj


def export_provenance_human_readable(
    *,
    provenance_path: str,
    out_dir: str,
    limit: Optional[int] = None,
    ids: Optional[Sequence[str]] = None,
    include_raw_response: bool = True,
) -> List[Path]:
    """Export a provenance JSONL into a browsable folder tree.

    Layout:
      out_dir/<provider>/<model>/<id>/
        prompt.txt
        completion.txt
        thinking.txt (optional)
        summary.json
        raw_response.json (optional)
    """
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    idset: Optional[Set[str]] = {str(x) for x in ids} if ids else None

    written: List[Path] = []
    count = 0
    for row in iter_jsonl_dicts(provenance_path):
        rid = row.get("id")
        if rid is None:
            continue
        rid_s = str(rid)
        if idset is not None and rid_s not in idset:
            continue

        provider = str(row.get("provider") or "unknown_provider")
        model = str(row.get("model") or "unknown_model")
        base = out / provider / model / rid_s
        base.mkdir(parents=True, exist_ok=True)

        prompt = row.get("prompt") or ""
        completion = row.get("completion_text") or ""
        thinking = row.get("thinking_text") or ""

        (base / "prompt.txt").write_text(str(prompt))
        (base / "completion.txt").write_text(str(completion))
        if thinking:
            (base / "thinking.txt").write_text(str(thinking))

        summary = dict(row)
        if not include_raw_response:
            summary.pop("raw_response", None)
        (base / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False))
        if include_raw_response and row.get("raw_response") is not None:
            (base / "raw_response.json").write_text(json.dumps(row.get("raw_response"), indent=2, ensure_ascii=False))

        written.append(base)
        count += 1
        if limit is not None and count >= int(limit):
            break

    return written


