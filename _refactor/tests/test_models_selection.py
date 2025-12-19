from __future__ import annotations


def test_pick_latest_anthropic_snapshots() -> None:
    from llmlog.models.selection import pick_latest_anthropic_snapshots

    ids = [
        "claude-sonnet-4-5-20250901",
        "claude-sonnet-4-5-20250929",
        "claude-haiku-4-5-20251001",
        "claude-haiku-4-5-20250915",
        "claude-opus-4-5-20251101",
        "claude-opus-4-5-20251015",
        # aliases or other shapes should be ignored by snapshot picker
        "claude-sonnet-4-5",
        "claude-3-7-sonnet-20250219",
    ]
    picked = pick_latest_anthropic_snapshots(ids)
    assert picked["sonnet"] == "claude-sonnet-4-5-20250929"
    assert picked["haiku"] == "claude-haiku-4-5-20251001"
    assert picked["opus"] == "claude-opus-4-5-20251101"


def test_pick_latest_openai_models() -> None:
    from llmlog.models.selection import pick_latest_openai_models

    ids = [
        "gpt-4o",
        "gpt-5.1",
        "gpt-5.2",
        "gpt-5.2-pro",
        "o4-mini",
    ]
    picked = pick_latest_openai_models(ids)
    assert picked["gpt_pro"] == "gpt-5.2-pro"
    assert picked["gpt_base"] == "gpt-5.2"
    assert picked["fast"] == "o4-mini"


def test_pick_latest_gemini_models_prefers_stable() -> None:
    from llmlog.models.selection import pick_latest_gemini_models

    ids = [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
        "gemini-3-flash-preview",
    ]
    picked = pick_latest_gemini_models(ids)
    # Version 3 is newer, but pro/flash stable aren't present; we should at least pick a flash preview.
    assert picked.get("flash_preview") == "gemini-3-flash-preview"


def test_pick_latest_gemini_models_picks_pro_and_flash_when_present() -> None:
    from llmlog.models.selection import pick_latest_gemini_models

    ids = [
        "gemini-2.0-flash",
        "gemini-2.0-pro",
        "gemini-2.5-flash",
        "gemini-2.5-pro",
    ]
    picked = pick_latest_gemini_models(ids)
    assert picked["pro"] == "gemini-2.5-pro"
    assert picked["flash"] == "gemini-2.5-flash"



