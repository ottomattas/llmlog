from __future__ import annotations


def test_run_chat_unsupported_provider() -> None:
    from llmlog.providers.router import run_chat

    try:
        run_chat(provider="nope", model="x", prompt="hi")
    except NotImplementedError as e:
        assert "Provider not supported" in str(e)
    else:
        raise AssertionError("Expected NotImplementedError")


def test_load_secrets_env_overlay(monkeypatch) -> None:
    from llmlog.providers.secrets import load_secrets

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    s = load_secrets(path="__does_not_exist__.json")
    assert s["openai"]["api_key"] == "test-key"


