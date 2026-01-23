# Paper figure source report

- generated_at: `2026-01-23T11:35:44Z`
- accuracy_mode: `completed`
- runs_dir: `/Users/ottomattas/Downloads/repos/llmlog/_refactor/runs`

## Run-selection policy

```
{
  "default": {
    "strategy": "newest_with_data"
  },
  "targets": [
    {
      "match": {
        "model": "gemini-*",
        "provider": "google"
      },
      "use_only_run_substr": "rerun_20260119"
    }
  ]
}
```

## Runs used per target model

### `anthropic/claude-opus-4-5-20251101/think_none`
- **baseline_case10_len3_5_vars10_50**: 540 cells

### `google/gemini-3-flash-preview/think_minimal`
- **baseline_case10_len3_5_vars10_50_rerun_20260119**: 540 cells

### `google/gemini-3-pro-preview/think_high`
- **baseline_case10_len3_5_vars10_50_rerun_20260119**: 540 cells

### `openai/gpt-5.2-2025-12-11/think_none`
- **baseline_case10_len3_vars10_50**: 60 cells
- **baseline_case10_len4_vars10_50**: 60 cells
- **baseline_case10_len5_vars10_50**: 60 cells
- **horn_alg_from_cnf_compact_len3_vars10_50_case10**: 10 cells
- **horn_alg_from_cnf_compact_len4_vars10_50_case10**: 10 cells
- **horn_alg_from_cnf_compact_len5_vars10_50_case10**: 10 cells
- **horn_alg_from_cnf_nl_len3_vars10_50_case10**: 10 cells
- **horn_alg_from_cnf_nl_len4_vars10_50_case10**: 10 cells
- **horn_alg_from_cnf_nl_len5_vars10_50_case10**: 10 cells
- **horn_alg_linear_cnf_compact_len3_vars10_50_case10**: 10 cells
- **horn_alg_linear_cnf_compact_len4_vars10_50_case10**: 10 cells
- **horn_alg_linear_cnf_compact_len5_vars10_50_case10**: 10 cells
- **horn_alg_linear_cnf_nl_len3_vars10_50_case10**: 10 cells
- **horn_alg_linear_cnf_nl_len4_vars10_50_case10**: 10 cells
- **horn_alg_linear_cnf_nl_len5_vars10_50_case10**: 10 cells
- **horn_ex_only_cnf_compact_len3_vars10_50_case10**: 10 cells
- **horn_ex_only_cnf_compact_len4_vars10_50_case10**: 10 cells
- **horn_ex_only_cnf_compact_len5_vars10_50_case10**: 10 cells
- **horn_ex_only_cnf_nl_len3_vars10_50_case10**: 10 cells
- **horn_ex_only_cnf_nl_len4_vars10_50_case10**: 10 cells
- **horn_ex_only_cnf_nl_len5_vars10_50_case10**: 10 cells
- **nonhorn_dpll_from_cnf_compact_len3_vars10_50_case10**: 10 cells
- **nonhorn_dpll_from_cnf_compact_len4_vars10_50_case10**: 10 cells
- **nonhorn_dpll_from_cnf_compact_len5_vars10_50_case10**: 10 cells
- **nonhorn_dpll_from_cnf_nl_len3_vars10_50_case10**: 10 cells
- **nonhorn_dpll_from_cnf_nl_len4_vars10_50_case10**: 10 cells
- **nonhorn_dpll_from_cnf_nl_len5_vars10_50_case10**: 10 cells
- **nonhorn_dpll_linear_cnf_compact_len3_vars10_50_case10**: 10 cells
- **nonhorn_dpll_linear_cnf_compact_len4_vars10_50_case10**: 10 cells
- **nonhorn_dpll_linear_cnf_compact_len5_vars10_50_case10**: 10 cells
- **nonhorn_dpll_linear_cnf_nl_len3_vars10_50_case10**: 10 cells
- **nonhorn_dpll_linear_cnf_nl_len4_vars10_50_case10**: 10 cells
- **nonhorn_dpll_linear_cnf_nl_len5_vars10_50_case10**: 10 cells
- **nonhorn_ex_only_cnf_compact_len3_vars10_50_case10**: 10 cells
- **nonhorn_ex_only_cnf_compact_len4_vars10_50_case10**: 10 cells
- **nonhorn_ex_only_cnf_compact_len5_vars10_50_case10**: 10 cells
- **nonhorn_ex_only_cnf_nl_len3_vars10_50_case10**: 10 cells
- **nonhorn_ex_only_cnf_nl_len4_vars10_50_case10**: 10 cells
- **nonhorn_ex_only_cnf_nl_len5_vars10_50_case10**: 10 cells

### `openai/gpt-5.2-pro/think_high`
- **horn_alg_linear_cnf_compact_len3_vars10_50_case10**: 10 cells
- **horn_alg_linear_cnf_compact_len4_vars10_50_case10**: 10 cells
- **horn_alg_linear_cnf_compact_len5_vars10_50_case10**: 10 cells
- **horn_alg_linear_cnf_nl_len3_vars10_50_case10**: 10 cells
- **horn_alg_linear_cnf_nl_len4_vars10_50_case10**: 10 cells
- **horn_alg_linear_cnf_nl_len5_vars10_50_case10**: 10 cells
- **horn_ex_only_len3_vars10_50_case10**: 10 cells
- **horn_ex_only_len4_vars10_50_case10**: 10 cells
- **horn_ex_only_len5_vars10_50_case10**: 10 cells
- **nonhorn_dpll_linear_cnf_compact_len3_vars10_50_case10**: 10 cells
- **nonhorn_dpll_linear_cnf_compact_len4_vars10_50_case10**: 10 cells
- **nonhorn_dpll_linear_cnf_compact_len5_vars10_50_case10**: 10 cells
- **nonhorn_dpll_linear_cnf_nl_len3_vars10_50_case10**: 10 cells
- **nonhorn_dpll_linear_cnf_nl_len4_vars10_50_case10**: 10 cells
- **nonhorn_dpll_linear_cnf_nl_len5_vars10_50_case10**: 10 cells
- **nonhorn_ex_only_cnf_compact_len3_vars10_50_case10**: 10 cells
- **nonhorn_ex_only_cnf_nl_len3_vars10_50_case10**: 10 cells
- **horn_alg_linear_cnf_compact_len3_vars60_80_100_case10**: 6 cells
- **horn_alg_linear_cnf_compact_len4_vars60_80_100_case10**: 6 cells
- **horn_alg_linear_cnf_compact_len5_vars60_80_100_case10**: 6 cells
- **horn_ex_only_len3_vars60_80_100_case10**: 6 cells
- **horn_ex_only_len4_vars60_80_100_case10**: 6 cells
- **horn_ex_only_len5_vars60_80_100_case10**: 6 cells
