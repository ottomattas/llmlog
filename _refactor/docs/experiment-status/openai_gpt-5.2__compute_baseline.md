## Experiment matrix: openai_gpt-5.2__compute_baseline

- **Matrix config**: `/Users/ottomattas/Downloads/repos/llmlog/_refactor/configs/matrices/openai_gpt-5.2__compute_baseline.yaml`
- **Runs dir**: `/Users/ottomattas/Downloads/repos/llmlog/_refactor/runs`
- **maxvars**: `10,20,30,40,50`
- **lens**: `3,4,5`
- **case_limit**: `10`

Notes:
- Status is computed from **latest-per-id** rows in `results.jsonl` (append-only logs).
- `run.manifest.json` can be overwritten by later `--ids` reruns; this tool avoids relying on it for selection.

### Target: openai/gpt-5.2/think_none

| subset | repr | prompt | suite | len=3 | len=4 | len=5 |
| --- | --- | --- | --- | --- | --- | --- |
| hornonly | cnf_compact | examples_only | `sat__repr-cnf_compact__subset-hornonly__prompt-examples_only__openai_gpt-5.2__think-none` | MISSING | MISSING | MISSING |
| hornonly | cnf_compact | horn_alg_linear | `sat__repr-cnf_compact__subset-hornonly__prompt-horn_alg_linear__openai_gpt-5.2__think-none` | MISSING | MISSING | MISSING |
| nonhornonly | cnf_compact | dpll_alg_linear | `sat__repr-cnf_compact__subset-nonhornonly__prompt-dpll_alg_linear__openai_gpt-5.2__think-none` | MISSING | MISSING | MISSING |

### Target: openai/gpt-5.2-pro/think_high

| subset | repr | prompt | suite | len=3 | len=4 | len=5 |
| --- | --- | --- | --- | --- | --- | --- |
| hornonly | cnf_compact | examples_only | `sat__repr-cnf_compact__subset-hornonly__prompt-examples_only__openai_gpt-5.2-pro__think-high` | DONE horn_ex_only_len3_vars10_50_case10 50/50 acc=1.00 | DONE horn_ex_only_len4_vars10_50_case10 50/50 acc=1.00 | DONE horn_ex_only_len5_vars10_50_case10 50/50 acc=1.00 |
| hornonly | cnf_compact | horn_alg_linear | `sat__repr-cnf_compact__subset-hornonly__prompt-horn_alg_linear__openai_gpt-5.2-pro__think-high` | DONE horn_alg_linear_cnf_compact_len3_vars10_50_case10 50/50 acc=1.00 | DONE horn_alg_linear_cnf_compact_len4_vars10_50_case10 50/50 acc=1.00 | DONE horn_alg_linear_cnf_compact_len5_vars10_50_case10 50/50 acc=1.00 |
| nonhornonly | cnf_compact | dpll_alg_linear | `sat__repr-cnf_compact__subset-nonhornonly__prompt-dpll_alg_linear__openai_gpt-5.2-pro__think-high` | DONE nonhorn_dpll_linear_cnf_compact_len3_vars10_50_case10 50/50 acc=0.72 | ERRORS nonhorn_dpll_linear_cnf_compact_len4_vars10_50_case10 50/50 acc=0.57 (errors=1) | DONE nonhorn_dpll_linear_cnf_compact_len5_vars10_50_case10 50/50 acc=0.50 |

