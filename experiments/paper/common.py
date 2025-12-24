from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional, Tuple

PROVIDERS = {"openai", "anthropic", "google"}


def sha1_hex(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8", errors="ignore")).hexdigest()


def normalize_id(x: Any) -> str:
    # Results/provenance ids are ints in most runs; normalize to string for joins.
    return str(x)


def safe_int(x: Any) -> Optional[int]:
    try:
        if x is None:
            return None
        return int(x)
    except Exception:
        return None


def iter_jsonl(path: Path) -> Iterator[Dict[str, Any]]:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                yield obj


def classify_error(msg: Optional[str]) -> Optional[str]:
    if not msg:
        return None
    m = msg.lower()
    if "429" in m or "too many requests" in m or "rate limit" in m:
        return "rate_limit"
    if "overloaded" in m or "529" in m:
        return "overloaded"
    if "usage limits" in m or "quota" in m:
        return "quota"
    if "timeout" in m:
        return "timeout"
    if "remote end closed connection" in m:
        return "connection"
    return "error"


def extract_run_datetime_guess(run_id: str) -> Optional[Tuple[int, int, int, int, int]]:
    """
    Returns (year,month,day,hour,minute) if run_id contains a recognizable timestamp.
    Supports patterns like:
      - validation_20251020_2235
      - smoke-20251014-1444
      - full-20250929-1349
    """
    if not run_id:
        return None
    m = re.search(r"(?P<d>\d{8})[-_](?P<t>\d{4})", run_id)
    if not m:
        return None
    d = m.group("d")
    t = m.group("t")
    try:
        y = int(d[0:4])
        mo = int(d[4:6])
        da = int(d[6:8])
        hh = int(t[0:2])
        mm = int(t[2:4])
        return (y, mo, da, hh, mm)
    except Exception:
        return None


def parse_leaf_identifiers(path: Path, runs_dir: Path) -> Dict[str, str]:
    """
    Parse a leaf-run file path into identifiers. Works with both layouts:
      - .../<experiment>/<run_id>/<provider>/<model>/<thinking_mode>/results.jsonl
      - .../<experiment>/<run_id>/<provider>/<model>/results.jsonl
    Also works for legacy nesting under experiments/runs/legacy_samples/...
    """
    rel = path.relative_to(runs_dir)
    parts = rel.parts

    provider_idx: Optional[int] = None
    for i, p in enumerate(parts):
        if p in PROVIDERS:
            provider_idx = i
            break

    if provider_idx is None:
        return {
            "experiment": parts[0] if len(parts) > 0 else "",
            "run_id": parts[1] if len(parts) > 1 else "",
            "provider": "",
            "model": "",
            "thinking_mode": "",
            "relpath": str(rel),
        }

    experiment_parts = parts[: max(provider_idx - 1, 0)]
    experiment = "/".join(experiment_parts) if experiment_parts else (parts[0] if parts else "")
    run_id = parts[provider_idx - 1] if provider_idx - 1 >= 0 else ""
    provider = parts[provider_idx]
    model = parts[provider_idx + 1] if provider_idx + 1 < len(parts) else ""
    thinking_mode = "/".join(parts[provider_idx + 2 : -1]) if provider_idx + 2 < len(parts) - 1 else ""

    return {
        "experiment": experiment,
        "run_id": run_id,
        "provider": provider,
        "model": model,
        "thinking_mode": thinking_mode,
        "relpath": str(rel),
    }


def infer_prompt_style(experiment: str, prompt_template: str) -> str:
    e = (experiment or "").lower()
    pt = (prompt_template or "").lower()
    if "cnf1" in e or "cnf_v1" in pt or "cnf_v1" in e or "exp1_cnf_v1" in pt:
        return "cnf_v1"
    if "cnf2" in e or "cnf_v2" in pt or "cnf_v2" in e or "exp2_cnf_v2" in pt:
        return "cnf_v2"
    if "horn" in e or "horn" in pt:
        return "horn_if_then"
    return "unknown"


def infer_parse_family(experiment: str) -> str:
    """
    Infer which answer-family parser should be used for a leaf run.

    - yes_no: expects yes/no output (including parse.type=both where output is still yes/no)
    - contradiction: expects contradiction/satisfiable/unknown output
    """
    e = (experiment or "").lower()
    # CNF tasks in this repository are contradiction-style outputs.
    # Note: some experiment names don't include 'con' (e.g. openai_gpt5_2_high_cnf2_refactor, exp*_cnf_*).
    if "cnf" in e:
        return "contradiction"
    # Default horn/yn suites output yes/no (even for mismatches with parse.type=both)
    if "horn" in e:
        return "yes_no"
    # Fallback
    return "yes_no"


_PUNCT = ["\n", "\r", ",", ".", ":", ";", "!", "?", "(", ")", "[", "]", "{", "}", "'", '"', "`", "*", "_"]


def _tokenize(text: str) -> list[str]:
    t = (text or "").strip().lower()
    for ch in _PUNCT:
        t = t.replace(ch, " ")
    parts = [p for p in t.split(" ") if p]
    return parts


def parse_answer_last_token(text: str, family: str) -> int:
    """
    Parse answers robustly by looking for the last decisive token near the end.

    Returns:
      0 => YES / CONTRADICTION
      1 => NO / SATISFIABLE / UNKNOWN
      2 => unclear

    family:
      - 'yes_no': only accept yes/no tokens
      - 'contradiction': only accept contradiction/satisfiable/unknown tokens
    """
    if not text:
        return 2
    parts = _tokenize(text)
    if not parts:
        return 2

    tail = parts[-15:]
    yes_tokens = {"yes"}
    no_tokens = {"no"}
    contradiction_tokens = {"contradiction", "contradictory", "unsatisfiable", "inconsistent"}
    sat_tokens = {"satisfiable", "satisfied", "unknown", "uncertain"}

    for p in reversed(tail):
        if family == "yes_no":
            if p in yes_tokens:
                return 0
            if p in no_tokens:
                return 1
        elif family == "contradiction":
            if p in contradiction_tokens:
                return 0
            if p in sat_tokens:
                return 1
        else:
            # unknown family: accept either
            if p in yes_tokens:
                return 0
            if p in no_tokens:
                return 1
            if p in contradiction_tokens:
                return 0
            if p in sat_tokens:
                return 1
    return 2


