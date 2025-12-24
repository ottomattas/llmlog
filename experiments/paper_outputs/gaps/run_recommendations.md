## Run recommendations (auto-generated)

This file proposes concrete next steps to fill gaps detected in historical results. It does **not** interpret performance; it only targets coverage/completeness.

### A) Resume incomplete leaf runs

The following leaf runs have fewer rows than the maximum seen within their (experiment, run_id) group.

- openai_gpt5_2_high_cnf2_refactor / vars10 / openai / gpt-5.2 / : missing_rows=35
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/openai_gpt5_2_high_cnf2_refactor.yaml --run vars10 --resume --only openai --models openai:gpt-5.2
```
- anthropic_cheap_cnf2_con_hornonly / cheap_20251027_2133 / anthropic / claude-haiku-4-5-20251001 / think-high: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/anthropic_cheap_cnf2_con_hornonly.yaml --run cheap_20251027_2133 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- anthropic_cheap_cnf2_con_hornonly / cheap_20251027_2133 / anthropic / claude-haiku-4-5-20251001 / think-med: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/anthropic_cheap_cnf2_con_hornonly.yaml --run cheap_20251027_2133 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- anthropic_cheap_horn_yn_hornonly / cheap_20251027_2133 / anthropic / claude-haiku-4-5-20251001 / think-high: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/anthropic_cheap_horn_yn_hornonly.yaml --run cheap_20251027_2133 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- anthropic_cheap_horn_yn_mixed / cheap_20251027_2133 / anthropic / claude-haiku-4-5-20251001 / think-high: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/anthropic_cheap_horn_yn_mixed.yaml --run cheap_20251027_2133 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- cnf1_con_hornonly / validation_20251016_0357 / anthropic / claude-opus-4-1-20250805 / think-med: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_hornonly.yaml --run validation_20251016_0357 --resume --only anthropic --models anthropic:claude-opus-4-1-20250805
```
- cnf1_con_hornonly / validation_20251016_0357 / openai / gpt-5-pro-2025-10-06 / think-high: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_hornonly.yaml --run validation_20251016_0357 --resume --only openai --models openai:gpt-5-pro-2025-10-06
```
- cnf1_con_mixed / validation_20251020_2235 / google / gemini-2.5-flash / think-med: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_mixed.yaml --run validation_20251020_2235 --resume --only google --models google:gemini-2.5-flash
```
- cnf1_con_mixed / validation_20251020_2235 / google / gemini-2.5-pro / think-high: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_mixed.yaml --run validation_20251020_2235 --resume --only google --models google:gemini-2.5-pro
```
- cnf2_con_mixed / validation_20251020_2235 / google / gemini-2.5-pro / think-high: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_mixed.yaml --run validation_20251020_2235 --resume --only google --models google:gemini-2.5-pro
```
- google_cheap_cnf2_con_hornonly / cheap_20251027_2133 / google / gemini-2.5-flash-lite / think-high: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/google_cheap_cnf2_con_hornonly.yaml --run cheap_20251027_2133 --resume --only google --models google:gemini-2.5-flash-lite
```
- google_cheap_cnf2_con_hornonly / cheap_20251027_2133 / google / gemini-2.5-flash-lite / think-med: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/google_cheap_cnf2_con_hornonly.yaml --run cheap_20251027_2133 --resume --only google --models google:gemini-2.5-flash-lite
```
- google_cheap_cnf2_con_mixed / cheap_20251027_2133 / google / gemini-2.5-flash-lite / think-high: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/google_cheap_cnf2_con_mixed.yaml --run cheap_20251027_2133 --resume --only google --models google:gemini-2.5-flash-lite
```
- google_cheap_horn_yn_hornonly / cheap_20251027_2133 / google / gemini-2.5-flash-lite / think-high: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/google_cheap_horn_yn_hornonly.yaml --run cheap_20251027_2133 --resume --only google --models google:gemini-2.5-flash-lite
```
- google_cheap_horn_yn_hornonly / cheap_20251027_2133 / google / gemini-2.5-flash-lite / think-med: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/google_cheap_horn_yn_hornonly.yaml --run cheap_20251027_2133 --resume --only google --models google:gemini-2.5-flash-lite
```
- google_cheap_horn_yn_mixed / cheap_20251027_2133 / google / gemini-2.5-flash-lite / think-high: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/google_cheap_horn_yn_mixed.yaml --run cheap_20251027_2133 --resume --only google --models google:gemini-2.5-flash-lite
```
- horn_yn_mixed / smoke / openai / gpt-5-pro-2025-10-06 / think-high: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/horn_yn_mixed.yaml --run smoke --resume --only openai --models openai:gpt-5-pro-2025-10-06
```
- horn_yn_mixed / streamtest_20251027_2037 / anthropic / claude-sonnet-4-5-20250929 / think-high: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/horn_yn_mixed.yaml --run streamtest_20251027_2037 --resume --only anthropic --models anthropic:claude-sonnet-4-5-20250929
```
- horn_yn_mixed / validation_20251020_2235 / google / gemini-2.5-pro / think-high: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/horn_yn_mixed.yaml --run validation_20251020_2235 --resume --only google --models google:gemini-2.5-pro
```
- openai_cheap_cnf2_con_hornonly / cheap_20251027_2133 / openai / gpt-5-nano-2025-08-07 / think-high: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/openai_cheap_cnf2_con_hornonly.yaml --run cheap_20251027_2133 --resume --only openai --models openai:gpt-5-nano-2025-08-07
```
- openai_cheap_cnf2_con_mixed / cheap_20251027_2133 / openai / gpt-5-nano-2025-08-07 / nothink: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/openai_cheap_cnf2_con_mixed.yaml --run cheap_20251027_2133 --resume --only openai --models openai:gpt-5-nano-2025-08-07
```
- openai_cheap_cnf2_con_mixed / cheap_20251027_2133 / openai / gpt-5-nano-2025-08-07 / think-high: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/openai_cheap_cnf2_con_mixed.yaml --run cheap_20251027_2133 --resume --only openai --models openai:gpt-5-nano-2025-08-07
```
- openai_cheap_cnf2_con_mixed / cheap_20251027_2133 / openai / gpt-5-nano-2025-08-07 / think-medium: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/openai_cheap_cnf2_con_mixed.yaml --run cheap_20251027_2133 --resume --only openai --models openai:gpt-5-nano-2025-08-07
```
- openai_cheap_horn_yn_mixed / cheap_20251027_2133 / openai / gpt-5-nano-2025-08-07 / think-high: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/openai_cheap_horn_yn_mixed.yaml --run cheap_20251027_2133 --resume --only openai --models openai:gpt-5-nano-2025-08-07
```
- openai_cheap_horn_yn_mixed / cheap_20251027_2133 / openai / gpt-5-nano-2025-08-07 / think-medium: missing_rows=1
  - Suggested command:

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/openai_cheap_horn_yn_mixed.yaml --run cheap_20251027_2133 --resume --only openai --models openai:gpt-5-nano-2025-08-07
```

### B) Leaf runs with API errors / empty outputs in provenance

These runs recorded provider errors and/or empty full_text in provenance. Rerunning may improve completeness.

- horn_yn_mixed / validation_20251020_2235 / openai / gpt-5-2025-08-07 / think-high: errors=255
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/horn_yn_mixed.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-2025-08-07
```
- cnf2_con_mixed / validation_20251020_2235 / openai / gpt-5-2025-08-07 / think-high: errors=251
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_mixed.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-2025-08-07
```
- cnf1_con_mixed / validation_20251020_2235 / openai / gpt-5-2025-08-07 / think-high: errors=243
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_mixed.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-2025-08-07
```
- horn_yn_mixed / validation_20251020_2235 / anthropic / claude-haiku-4-5-20251001 / nothink: errors=242
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/horn_yn_mixed.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- horn_yn_mixed / validation_20251020_2235 / anthropic / claude-haiku-4-5-20251001 / think-low: errors=242
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/horn_yn_mixed.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- horn_yn_mixed / validation_20251020_2235 / anthropic / claude-haiku-4-5-20251001 / think-med: errors=242
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/horn_yn_mixed.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- horn_yn_mixed / validation_20251020_2235 / anthropic / claude-sonnet-4-5-20250929 / think-high: errors=242
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/horn_yn_mixed.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-sonnet-4-5-20250929
```
- horn_yn_mixed / validation_20251020_2235 / openai / gpt-5-2025-08-07 / think-medium: errors=240
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/horn_yn_mixed.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-2025-08-07
```
- cnf2_con_mixed / validation_20251020_2235 / openai / gpt-5-2025-08-07 / think-medium: errors=238
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_mixed.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-2025-08-07
```
- horn_yn_mixed / validation_20251020_2235 / openai / gpt-5-mini-2025-08-07 / think-low: errors=236
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/horn_yn_mixed.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-mini-2025-08-07
```
- horn_yn_mixed / validation_20251020_2235 / openai / gpt-5-nano-2025-08-07 / nothink: errors=236
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/horn_yn_mixed.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-nano-2025-08-07
```
- cnf1_con_mixed / validation_20251020_2235 / openai / gpt-5-2025-08-07 / think-medium: errors=229
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_mixed.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-2025-08-07
```
- cnf2_con_mixed / validation_20251020_2235 / anthropic / claude-haiku-4-5-20251001 / nothink: errors=227
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_mixed.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- cnf2_con_mixed / validation_20251020_2235 / anthropic / claude-haiku-4-5-20251001 / think-low: errors=227
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_mixed.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- cnf2_con_mixed / validation_20251020_2235 / anthropic / claude-haiku-4-5-20251001 / think-med: errors=227
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_mixed.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- cnf2_con_mixed / validation_20251020_2235 / anthropic / claude-sonnet-4-5-20250929 / think-high: errors=227
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_mixed.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-sonnet-4-5-20250929
```
- cnf2_con_mixed / validation_20251020_2235 / openai / gpt-5-mini-2025-08-07 / think-low: errors=225
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_mixed.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-mini-2025-08-07
```
- cnf2_con_mixed / validation_20251020_2235 / openai / gpt-5-nano-2025-08-07 / nothink: errors=225
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_mixed.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-nano-2025-08-07
```
- cnf1_con_mixed / validation_20251020_2235 / anthropic / claude-haiku-4-5-20251001 / nothink: errors=218
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_mixed.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- cnf1_con_mixed / validation_20251020_2235 / anthropic / claude-haiku-4-5-20251001 / think-low: errors=218
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_mixed.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- cnf1_con_mixed / validation_20251020_2235 / anthropic / claude-haiku-4-5-20251001 / think-med: errors=218
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_mixed.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- cnf1_con_mixed / validation_20251020_2235 / anthropic / claude-sonnet-4-5-20250929 / think-high: errors=218
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_mixed.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-sonnet-4-5-20250929
```
- cnf1_con_mixed / validation_20251020_2235 / openai / gpt-5-mini-2025-08-07 / think-low: errors=216
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_mixed.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-mini-2025-08-07
```
- cnf1_con_mixed / validation_20251020_2235 / openai / gpt-5-nano-2025-08-07 / nothink: errors=216
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_mixed.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-nano-2025-08-07
```
- horn_yn_mixed / validation_20251020_2235 / google / gemini-2.5-pro / think-high: errors=157
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/horn_yn_mixed.yaml --run validation_20251020_2235 --resume --only google --models google:gemini-2.5-pro
```
- horn_yn_hornonly / validation_20251016_0357 / openai / gpt-5-pro-2025-10-06 / think-high: errors=153
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/horn_yn_hornonly.yaml --run validation_20251016_0357 --resume --only openai --models openai:gpt-5-pro-2025-10-06
```
- cnf1_con_mixed / validation_20251020_2235 / google / gemini-2.5-pro / think-high: errors=134
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_mixed.yaml --run validation_20251020_2235 --resume --only google --models google:gemini-2.5-pro
```
- cnf2_con_mixed / validation_20251020_2235 / google / gemini-2.5-pro / think-high: errors=132
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_mixed.yaml --run validation_20251020_2235 --resume --only google --models google:gemini-2.5-pro
```
- cnf1_con_hornonly / validation_20251020_2235 / openai / gpt-5-2025-08-07 / think-high: errors=109
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_hornonly.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-2025-08-07
```
- cnf1_con_hornonly / validation_20251020_2235 / anthropic / claude-haiku-4-5-20251001 / nothink: errors=105
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_hornonly.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- cnf1_con_hornonly / validation_20251020_2235 / anthropic / claude-haiku-4-5-20251001 / think-low: errors=105
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_hornonly.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- cnf1_con_hornonly / validation_20251020_2235 / anthropic / claude-haiku-4-5-20251001 / think-med: errors=105
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_hornonly.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- cnf1_con_hornonly / validation_20251020_2235 / anthropic / claude-sonnet-4-5-20250929 / think-high: errors=105
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_hornonly.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-sonnet-4-5-20250929
```
- cnf1_con_hornonly / validation_20251020_2235 / openai / gpt-5-2025-08-07 / think-medium: errors=104
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_hornonly.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-2025-08-07
```
- cnf1_con_hornonly / validation_20251020_2235 / openai / gpt-5-mini-2025-08-07 / think-low: errors=103
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_hornonly.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-mini-2025-08-07
```
- cnf1_con_hornonly / validation_20251020_2235 / openai / gpt-5-nano-2025-08-07 / nothink: errors=103
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_hornonly.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-nano-2025-08-07
```
- legacy_samples/exp6_horn_yesno / full-20250929-1349 / google / gemini-2.5-pro / : empty_text=97
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/legacy_samples/exp6_horn_yesno.yaml --run full-20250929-1349 --resume --only google --models google:gemini-2.5-pro
```
- cnf2_con_hornonly / validation_20251020_2235 / anthropic / claude-haiku-4-5-20251001 / nothink: errors=95
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_hornonly.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- cnf2_con_hornonly / validation_20251020_2235 / anthropic / claude-haiku-4-5-20251001 / think-low: errors=95
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_hornonly.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- cnf2_con_hornonly / validation_20251020_2235 / anthropic / claude-haiku-4-5-20251001 / think-med: errors=95
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_hornonly.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-haiku-4-5-20251001
```
- cnf2_con_hornonly / validation_20251020_2235 / anthropic / claude-sonnet-4-5-20250929 / think-high: errors=95
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_hornonly.yaml --run validation_20251020_2235 --resume --only anthropic --models anthropic:claude-sonnet-4-5-20250929
```
- cnf2_con_hornonly / validation_20251020_2235 / openai / gpt-5-2025-08-07 / think-high: errors=92
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_hornonly.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-2025-08-07
```
- cnf2_con_hornonly / validation_20251020_2235 / openai / gpt-5-2025-08-07 / think-medium: errors=88
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_hornonly.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-2025-08-07
```
- cnf2_con_hornonly / validation_20251020_2235 / openai / gpt-5-mini-2025-08-07 / think-low: errors=87
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_hornonly.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-mini-2025-08-07
```
- cnf2_con_hornonly / validation_20251020_2235 / openai / gpt-5-nano-2025-08-07 / nothink: errors=87
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_hornonly.yaml --run validation_20251020_2235 --resume --only openai --models openai:gpt-5-nano-2025-08-07
```
- cnf1_con_hornonly / validation_20251020_2235 / google / gemini-2.5-pro / think-high: errors=78
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf1_con_hornonly.yaml --run validation_20251020_2235 --resume --only google --models google:gemini-2.5-pro
```
- cnf2_con_hornonly / validation_20251020_2235 / google / gemini-2.5-pro / think-high: errors=65
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/cnf2_con_hornonly.yaml --run validation_20251020_2235 --resume --only google --models google:gemini-2.5-pro
```
- openai_gpt5_2_high_cnf2_refactor / vars40 / openai / gpt-5.2-pro-2025-12-11 / : errors=28
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/openai_gpt5_2_high_cnf2_refactor.yaml --run vars40 --resume --only openai --models openai:gpt-5.2-pro-2025-12-11
```
- openai_gpt5_2_high_cnf2_refactor / vars50 / openai / gpt-5.2-pro-2025-12-11 / : errors=27
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/openai_gpt5_2_high_cnf2_refactor.yaml --run vars50 --resume --only openai --models openai:gpt-5.2-pro-2025-12-11
```
- openai_gpt5_2_high_cnf2_refactor / vars20 / openai / gpt-5.2-pro-2025-12-11 / : errors=25
  - Suggested command (rerun/resume):

```bash
venv/bin/python -m experiments.runner --config /Users/ottomattas/Downloads/repos/llmlog/experiments/configs/openai_gpt5_2_high_cnf2_refactor.yaml --run vars20 --resume --only openai --models openai:gpt-5.2-pro-2025-12-11
```

(Showing top 50 by count; total flagged leaf runs: 85)


### C) Global internal-span holes (missing maxvars within observed span)

The following rows indicate that, for a given (model, prompt_id, thinking_mode, horn, maxlen), some maxvars values within the observed min..max range are missing. These are good targets for **resume/rerun** if they were caused by interruptions.


Note: 2 additional rows are classified as `sparse_span` (many missing values across a large span), which often reflects intentionally separate datasets (e.g., vars10/vars20/vars30) rather than an interrupted run.

