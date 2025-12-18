from __future__ import annotations


def test_normalize_meta_openai_chat_shape() -> None:
    from llmlog.response_meta import normalize_meta

    raw = {
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
            "output_tokens_details": {"reasoning_tokens": 2},
        }
    }
    norm = normalize_meta("openai", "gpt-test", {"raw_response": raw, "usage": raw["usage"], "finish_reason": "stop"})
    assert norm["provider"] == "openai"
    assert norm["model"] == "gpt-test"
    assert norm["usage"]["input_tokens"] == 10
    assert norm["usage"]["output_tokens"] == 5
    assert norm["usage"]["reasoning_tokens"] == 2


def test_normalize_meta_gemini_usage_metadata() -> None:
    from llmlog.response_meta import normalize_meta

    raw = {"usageMetadata": {"promptTokenCount": 11, "candidatesTokenCount": 7, "thoughtsTokenCount": 3}}
    norm = normalize_meta("google", "gemini-test", {"raw_response": raw, "usage": raw["usageMetadata"], "finish_reason": None})
    assert norm["usage"]["input_tokens"] == 11
    assert norm["usage"]["output_tokens"] == 7
    assert norm["usage"]["reasoning_tokens"] == 3


def test_normalize_meta_anthropic_usage() -> None:
    from llmlog.response_meta import normalize_meta

    raw = {"usage": {"input_tokens": 9, "output_tokens": 20}, "content": [{"type": "text", "text": "ok"}]}
    norm = normalize_meta("anthropic", "claude-test", {"raw_response": raw, "usage": raw["usage"], "finish_reason": "end_turn"})
    assert norm["usage"]["input_tokens"] == 9
    assert norm["usage"]["output_tokens"] == 20
    # no thinking blocks => reasoning_tokens remains null
    assert norm["usage"]["reasoning_tokens"] is None


