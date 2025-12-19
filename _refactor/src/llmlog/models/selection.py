from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple


_CLAUDE_SNAPSHOT_RE = re.compile(
    r"^claude-(?P<line>opus|sonnet|haiku)-(?P<ver>[0-9][0-9\-]*)-(?P<date>[0-9]{8})$"
)


def _as_int(s: str) -> Optional[int]:
    try:
        return int(s)
    except Exception:
        return None


def pick_latest_anthropic_snapshots(model_ids: Iterable[str]) -> Dict[str, str]:
    """Pick the newest snapshot id for each of {opus, sonnet, haiku}.

    Example ids from the docs:
    - claude-sonnet-4-5-20250929
    - claude-haiku-4-5-20251001
    - claude-opus-4-5-20251101
    """
    best: Dict[str, Tuple[int, str]] = {}
    for mid in model_ids:
        m = _CLAUDE_SNAPSHOT_RE.match(mid or "")
        if not m:
            continue
        line = m.group("line")
        date_s = m.group("date")
        date_i = _as_int(date_s)
        if date_i is None:
            continue
        cur = best.get(line)
        if cur is None or date_i > cur[0]:
            best[line] = (date_i, mid)
    return {line: mid for line, (_date, mid) in best.items()}


def _parse_semverish(id_: str, *, prefix: str) -> Optional[Tuple[int, int]]:
    # Parse "gpt-5.2-pro" -> (5, 2) (prefix="gpt-")
    m = re.match(rf"^{re.escape(prefix)}(?P<maj>[0-9]+)(?:\.(?P<min>[0-9]+))?", id_ or "")
    if not m:
        return None
    maj = _as_int(m.group("maj") or "")
    min_ = _as_int(m.group("min") or "0")
    if maj is None or min_ is None:
        return None
    return (maj, min_)


def pick_latest_openai_models(model_ids: Iterable[str]) -> Dict[str, str]:
    """Best-effort picks for OpenAI:

    - Latest gpt-<major>.<minor> version (preferring a "-pro" variant when present).
    - A fast baseline "o4-mini" when present.
    """
    ids = sorted({m for m in model_ids if isinstance(m, str) and m})

    # Choose latest gpt-* family by semver-ish parsing.
    best_ver: Optional[Tuple[int, int]] = None
    for mid in ids:
        ver = _parse_semverish(mid, prefix="gpt-")
        if ver is None:
            continue
        if best_ver is None or ver > best_ver:
            best_ver = ver

    out: Dict[str, str] = {}
    if best_ver is not None:
        maj, min_ = best_ver
        base = f"gpt-{maj}.{min_}"
        pro = f"{base}-pro"
        # Prefer pro when it exists.
        if pro in ids:
            out["gpt_pro"] = pro
        if base in ids:
            out["gpt_base"] = base
        # Fall back: any model starting with base (e.g., gpt-5.2-mini) could be added later.

    if "o4-mini" in ids:
        out["fast"] = "o4-mini"
    return out


def pick_latest_gemini_models(model_ids: Iterable[str]) -> Dict[str, str]:
    """Best-effort picks for Gemini:

    - Latest gemini-<major>.<minor> pro + flash variants when present.
    - If only flash exists for the latest version, include that.
    """
    ids = sorted({m for m in model_ids if isinstance(m, str) and m})
    gem = [m for m in ids if m.startswith("gemini-")]
    best_ver: Optional[Tuple[int, int]] = None
    for mid in gem:
        ver = _parse_semverish(mid, prefix="gemini-")
        if ver is None:
            continue
        if best_ver is None or ver > best_ver:
            best_ver = ver

    out: Dict[str, str] = {}
    if best_ver is None:
        return out
    maj, min_ = best_ver
    base = f"gemini-{maj}.{min_}"

    # Prefer stable ids (no "-preview") when available.
    pro = f"{base}-pro"
    flash = f"{base}-flash"
    if pro in gem:
        out["pro"] = pro
    if flash in gem:
        out["flash"] = flash

    # If no stable flash exists, allow preview for the latest major (common for new releases).
    if "flash" not in out:
        for cand in gem:
            if cand.startswith(f"gemini-{maj}-flash") or cand.startswith(f"{base}-flash"):
                if "preview" in cand or "exp" in cand:
                    out["flash_preview"] = cand
                    break

    return out


def select_default_latest_targets(models_by_provider: Dict[str, List[str]]) -> List[Dict[str, Any]]:
    """Create a small, sensible "latest models" target set from provider model inventories.

    This is intended for *fast experimentation*; for reproducible runs, prefer pinning
    specific snapshot IDs and committing them to `configs/targets/*.yaml`.
    """
    targets: List[Dict[str, Any]] = []

    # Anthropic: newest snapshot per line.
    anth = pick_latest_anthropic_snapshots(models_by_provider.get("anthropic") or [])
    for line, mid in sorted(anth.items()):
        if line == "haiku":
            targets.append(
                {
                    "provider": "anthropic",
                    "model": mid,
                    "temperature": 1,
                    "seed": 1234,
                    "max_tokens": 3000,
                    "thinking": {"enabled": True, "budget_tokens": 1024},
                }
            )
        else:
            targets.append(
                {
                    "provider": "anthropic",
                    "model": mid,
                    "temperature": 1,
                    "seed": 1234,
                    "max_tokens": 30000,
                    "thinking": {"enabled": True, "budget_tokens": 24576},
                }
            )

    # Gemini: latest pro/flash picks.
    gem = pick_latest_gemini_models(models_by_provider.get("google") or models_by_provider.get("gemini") or [])
    if "pro" in gem:
        targets.append(
            {
                "provider": "google",
                "model": gem["pro"],
                "temperature": 0,
                "seed": 1234,
                "max_tokens": 30000,
                "thinking": {"enabled": True, "budget_tokens": 24576},
            }
        )
    if "flash" in gem:
        targets.append(
            {
                "provider": "google",
                "model": gem["flash"],
                "temperature": 0,
                "seed": 1234,
                "max_tokens": 10000,
                "thinking": {"enabled": True, "budget_tokens": 8192},
            }
        )
    if "flash_preview" in gem:
        targets.append(
            {
                "provider": "google",
                "model": gem["flash_preview"],
                "temperature": 0,
                "seed": 1234,
                "max_tokens": 3000,
                "thinking": {"enabled": True, "budget_tokens": 1024},
            }
        )

    # OpenAI: latest gpt-<ver> (+ pro) and o4-mini baseline.
    oa = pick_latest_openai_models(models_by_provider.get("openai") or [])
    if "gpt_pro" in oa:
        targets.append(
            {
                "provider": "openai",
                "model": oa["gpt_pro"],
                "temperature": 0,
                "seed": 1234,
                "max_tokens": 30000,
                "thinking": {"enabled": True, "effort": "high"},
            }
        )
    if "gpt_base" in oa:
        targets.append(
            {
                "provider": "openai",
                "model": oa["gpt_base"],
                "temperature": 0,
                "seed": 1234,
                "max_tokens": 10000,
                "thinking": {"enabled": True, "effort": "medium"},
            }
        )
    if "fast" in oa:
        targets.append(
            {
                "provider": "openai",
                "model": oa["fast"],
                "temperature": 0,
                "seed": 1234,
                "max_tokens": 3000,
                "thinking": {"enabled": False},
            }
        )

    return targets



