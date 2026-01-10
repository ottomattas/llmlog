from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


PROVENANCE_SCHEMA = "llmlog.provenance.v2"
PROVENANCE_SCHEMA_VERSION = 2


def provenance_v2_path_for_results(results_path: Path) -> Path:
    """Return the v2 provenance path corresponding to a results.jsonl path.

    results.jsonl -> results.provenance.v2.jsonl
    """
    p = str(results_path)
    if p.endswith(".jsonl"):
        base = p[: -len(".jsonl")]
        return Path(base + ".provenance.v2.jsonl")
    return Path(p + ".provenance.v2.jsonl")


def infer_run_info_from_results_path(results_path: Path) -> Dict[str, str]:
    """Best-effort extraction of suite/run/provider/model/thinking from the default output layout."""
    try:
        parts = results_path.resolve().parts
    except Exception:
        parts = results_path.parts

    runs_idxs = [i for i, seg in enumerate(parts) if seg == "runs"]
    if not runs_idxs:
        return {}
    i = runs_idxs[-1]
    # runs/<suite>/<run>/<provider>/<model>/<thinking>/results.jsonl
    if len(parts) >= i + 7:
        return {
            "suite": parts[i + 1],
            "run": parts[i + 2],
            "provider_dir": parts[i + 3],
            "model_dir": parts[i + 4],
            "thinking_mode_dir": parts[i + 5],
        }
    return {}


_RFC3339_RE = re.compile(
    r"^(?P<base>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})"
    r"(?:\.(?P<frac>\d+))?"
    r"(?P<tz>Z|[+-]\d{2}:\d{2})$"
)


def _parse_rfc3339(ts: Any) -> Optional[datetime]:
    """Parse RFC3339 timestamps with optional nanosecond fractions.

    Examples:
    - 2026-01-10T15:28:48.931079975Z
    - 2026-01-10T15:27:03.635472Z
    - 2026-01-10T15:28:11.704565+00:00
    """
    if not isinstance(ts, str):
        return None
    s = ts.strip()
    if not s:
        return None
    m = _RFC3339_RE.match(s)
    if not m:
        try:
            return datetime.fromisoformat(s)
        except Exception:
            return None
    base = m.group("base")
    frac = m.group("frac") or ""
    tz = m.group("tz")
    if tz == "Z":
        tz = "+00:00"
    if frac:
        frac6 = (frac + "000000")[:6]
        s2 = f"{base}.{frac6}{tz}"
    else:
        s2 = f"{base}{tz}"
    try:
        return datetime.fromisoformat(s2)
    except Exception:
        return None


def _duration_ms_from_rfc3339(start_ts: Any, end_ts: Any) -> Optional[int]:
    a = _parse_rfc3339(start_ts)
    b = _parse_rfc3339(end_ts)
    if a is None or b is None:
        return None
    try:
        return int((b - a).total_seconds() * 1000)
    except Exception:
        return None


def _duration_ms_from_openai(created_at: Any, completed_at: Any) -> Optional[int]:
    try:
        if created_at is None or completed_at is None:
            return None
        return int((int(completed_at) - int(created_at)) * 1000)
    except Exception:
        return None


def _unwrap_openai_response(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict) and isinstance(raw.get("response"), dict):
        return raw["response"]
    return raw if isinstance(raw, dict) else {}


def _extract_openai_response_id(raw: Any) -> Optional[str]:
    try:
        obj = _unwrap_openai_response(raw)
        rid = obj.get("id")
        return str(rid) if rid else None
    except Exception:
        return None


def _extract_google_response_id(raw: Any) -> Optional[str]:
    try:
        if isinstance(raw, dict) and raw.get("responseId"):
            return str(raw.get("responseId"))
    except Exception:
        pass
    return None


def _extract_google_thought_signature(raw: Any) -> Optional[str]:
    try:
        if not isinstance(raw, dict):
            return None
        candidates = raw.get("candidates") or []
        if not isinstance(candidates, list) or not candidates:
            return None
        c0 = candidates[0] if isinstance(candidates[0], dict) else {}
        parts = ((c0.get("content") or {}).get("parts")) or []
        if not isinstance(parts, list):
            return None
        for p in parts:
            if isinstance(p, dict) and p.get("thoughtSignature"):
                return str(p.get("thoughtSignature"))
    except Exception:
        pass
    return None


def _extract_google_finish_reason(raw: Any) -> Optional[str]:
    try:
        if not isinstance(raw, dict):
            return None
        candidates = raw.get("candidates") or []
        if not isinstance(candidates, list) or not candidates:
            return None
        c0 = candidates[0] if isinstance(candidates[0], dict) else {}
        fr = c0.get("finishReason")
        return str(fr) if fr else None
    except Exception:
        return None


def _extract_anthropic_message_id(raw: Any) -> Optional[str]:
    try:
        if isinstance(raw, dict) and raw.get("id"):
            return str(raw.get("id"))
    except Exception:
        pass
    return None


def build_provenance_v2_row(
    *,
    base: Dict[str, Any],
    results_path: Optional[Path],
    event: str,
    http: Optional[Dict[str, Any]] = None,
    job_meta: Optional[Dict[str, Any]] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a provenance v2 record from an existing v1-style provenance row.

    This is intentionally additive: we keep the v1 keys (prompt/completion/usage/raw_response/…)
    while adding structured fields for job ids, timing sources, and provider-specific extras.
    """
    out: Dict[str, Any] = dict(base)
    out["schema"] = PROVENANCE_SCHEMA
    out["schema_version"] = PROVENANCE_SCHEMA_VERSION
    out["event"] = str(event)

    if results_path is not None:
        info = infer_run_info_from_results_path(results_path)
        for k in ("suite", "run", "provider_dir", "model_dir", "thinking_mode_dir"):
            if info.get(k) is not None:
                out.setdefault(k, info.get(k))

    if extra:
        for k, v in extra.items():
            out[k] = v

    provider_l = str(out.get("provider") or "").lower()
    submission_id = out.get("submission_id")
    submission_status = out.get("submission_status")
    custom_id = out.get("submission_custom_id")
    sub_index = out.get("submission_index")
    openai_resp_id = out.get("openai_response_id")
    openai_status = out.get("openai_response_status")
    raw = out.get("raw_response")

    # Provider output ids / small provider extras (do NOT require storing raw_response on disk).
    openai_obj = _unwrap_openai_response(raw) if provider_l == "openai" else {}
    provider_output: Dict[str, Any] = {"id": None, "kind": None}
    if provider_l == "openai":
        rid = _extract_openai_response_id(raw) or (str(openai_resp_id) if openai_resp_id else None)
        provider_output.update(
            {
                "id": rid,
                "kind": "openai.response",
                "service_tier": openai_obj.get("service_tier"),
                "background": openai_obj.get("background"),
                "created_at": openai_obj.get("created_at"),
                "completed_at": openai_obj.get("completed_at"),
                "reasoning_effort": (openai_obj.get("reasoning") or {}).get("effort")
                if isinstance(openai_obj.get("reasoning"), dict)
                else None,
            }
        )
    elif provider_l in ("google", "gemini"):
        provider_output.update(
            {
                "id": _extract_google_response_id(raw),
                "kind": "google.generate_content_response",
                "finish_reason": _extract_google_finish_reason(raw),
                "thought_signature": _extract_google_thought_signature(raw),
            }
        )
    elif provider_l == "anthropic":
        provider_output.update(
            {
                "id": _extract_anthropic_message_id(raw),
                "kind": "anthropic.message",
            }
        )

    # Job container (submit-only batch operation/batch id, or per-request id for OpenAI).
    job_kind = None
    job_id = None
    job_status = None
    if provider_l == "openai":
        job_kind = "openai.response"
        job_id = openai_resp_id or submission_id or provider_output.get("id")
        job_status = openai_status or submission_status or openai_obj.get("status")
    elif provider_l == "anthropic":
        if isinstance(submission_id, str) and submission_id.startswith("msgbatch_"):
            job_kind = "anthropic.message_batch"
            job_id = submission_id
            job_status = submission_status
        else:
            job_kind = "anthropic.message"
            job_id = provider_output.get("id") or submission_id
            job_status = submission_status
    elif provider_l in ("google", "gemini"):
        if isinstance(submission_id, str) and submission_id.startswith("batches/"):
            job_kind = "google.batch_operation"
            job_id = submission_id
            job_status = submission_status
        else:
            job_kind = "google.generate_content"
            job_id = provider_output.get("id") or submission_id
            job_status = submission_status
    else:
        job_kind = "unknown"
        job_id = submission_id or provider_output.get("id")
        job_status = submission_status

    job: Dict[str, Any] = {
        "id": job_id,
        "kind": job_kind,
        "status": job_status,
        "custom_id": custom_id,
        "index": sub_index,
    }
    if job_meta:
        job["metadata"] = job_meta
    out["job"] = job
    out["provider_output"] = provider_output

    # Timing: keep v1 timing_ms if present, otherwise derive best-effort.
    timing_ms = out.get("timing_ms")
    timing_src = "v1.timing_ms" if timing_ms is not None else None
    if timing_ms is None:
        # OpenAI: created_at/completed_at
        if provider_l == "openai":
            timing_ms = _duration_ms_from_openai(openai_obj.get("created_at"), openai_obj.get("completed_at"))
            if timing_ms is not None:
                timing_src = "openai.created_at_to_completed_at"
        # Batch-level timing (Google/Anthropic) from job metadata.
        if timing_ms is None and isinstance(job_meta, dict):
            if provider_l in ("google", "gemini"):
                timing_ms = _duration_ms_from_rfc3339(job_meta.get("createTime"), job_meta.get("endTime"))
                if timing_ms is not None:
                    timing_src = "google.batch.createTime_to_endTime"
            if provider_l == "anthropic":
                timing_ms = _duration_ms_from_rfc3339(job_meta.get("created_at"), job_meta.get("ended_at"))
                if timing_ms is not None:
                    timing_src = "anthropic.batch.created_at_to_ended_at"
        # End-to-end (submit -> collect) when available.
        if timing_ms is None:
            e = _parse_rfc3339(out.get("ts"))
            s = _parse_rfc3339(out.get("submit_ts"))
            if e is not None and s is not None:
                try:
                    timing_ms = int((e - s).total_seconds() * 1000)
                    timing_src = "collector.submit_ts_to_ts"
                except Exception:
                    pass

    out["timing_ms"] = timing_ms
    out["timing_ms_source"] = timing_src

    if http is not None:
        out["http"] = http

    return out

