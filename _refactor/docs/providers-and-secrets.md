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

When available, provider-returned thinking text is captured as `thinking_text` in provenance output (currently: Anthropic).

