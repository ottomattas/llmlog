## Providers and secrets

### Secrets
You can provide API keys via environment variables (recommended) or a local `secrets.json`.

Environment variables:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY` (or `GEMINI_API_KEY`)

`secrets.json` format:
```json
{
  "openai": { "api_key": "..." },
  "anthropic": { "api_key": "..." },
  "google": { "api_key": "..." }
}
```

See `src/llmlog/providers/secrets.py`.

### Provider router
The runner uses `llmlog.providers.router.run_chat()` to call a provider/model and normalize response metadata.

Providers implemented:
- `openai` (Chat Completions + Responses API best-effort for `gpt-5*`)
- `anthropic` (Anthropic SDK, streaming)
- `google` / `gemini` (Gemini generateContent endpoint)

### Thinking / reasoning options
Targets may include a `thinking` block:
- `enabled`: boolean
- `budget_tokens`: for Anthropic + Gemini (best-effort)
- `effort`: for OpenAI reasoning effort (`low|medium|high`)

### What we can (and can’t) save about “thinking”
**Anthropic (Claude)**:
- When extended thinking is enabled, Claude returns separate content blocks of type `thinking` (plus final `text` blocks). For Claude 4 models, this is **summarized thinking**; Claude Sonnet 3.7 returns full thinking. We store the returned thinking text as `thinking_text` in provenance. (See: [Anthropic extended thinking](https://platform.claude.com/docs/en/build-with-claude/extended-thinking))
- Token accounting: `usage.output_tokens` reflects billed output tokens (including thinking). This may not match the visible thinking summary length. (See: [Anthropic extended thinking](https://platform.claude.com/docs/en/build-with-claude/extended-thinking))
- We also preserve cache token fields (when present) like `cache_creation_input_tokens` and `cache_read_input_tokens` in provenance usage. (See: [Anthropic Messages API](https://platform.claude.com/docs/en/api/messages))

**Google Gemini**:
- We store `usageMetadata.thoughtsTokenCount` (normalized to `usage.reasoning_tokens`) when the API provides it. (See: [Gemini thinking](https://ai.google.dev/gemini-api/docs/thinking?hl=en))
- The API does not always expose “thinking text”; we attempt best-effort extraction if the response includes explicit thought parts, otherwise `thinking_text` is `null`. (See: [Gemini thinking](https://ai.google.dev/gemini-api/docs/thinking?hl=en))

**OpenAI**:
- We store provider usage including `output_tokens_details.reasoning_tokens` when available (normalized to `usage.reasoning_tokens`). (See: [OpenAI reasoning guide](https://platform.openai.com/docs/guides/reasoning#how-reasoning-works))
- “Hidden” reasoning tokens are typically **not returned as text**; when the API returns a reasoning summary block, we capture it as `thinking_text`. (See: [OpenAI reasoning guide](https://platform.openai.com/docs/guides/reasoning#how-reasoning-works))

