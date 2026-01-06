## Experiment matrix: openai_gpt-5.2-pro__think-high__prompt-matrix

- **Matrix config**: `/Users/ottomattas/Downloads/repos/llmlog/_refactor/configs/matrices/openai_gpt-5.2-pro__think-high__prompt-matrix.yaml`
- **Runs dir**: `/Users/ottomattas/Downloads/repos/llmlog/_refactor/runs`
- **maxvars**: `10,20,30,40,50`
- **lens**: `3,4,5`
- **case_limit**: `10`

Notes:
- Status is computed from **latest-per-id** rows in `results.jsonl` (append-only logs).
- `run.manifest.json` can be overwritten by later `--ids` reruns; this tool avoids relying on it for selection.

### Target: openai/gpt-5.2-pro/think_high

| subset | repr | prompt | suite | len=3 | len=4 | len=5 |
| --- | --- | --- | --- | --- | --- | --- |
| hornonly | cnf_compact | examples_only | `sat__repr-cnf_compact__subset-hornonly__prompt-examples_only__openai_gpt-5.2-pro__think-high` | DONE horn_ex_only_len3_vars10_50_case10 50/50 acc=1.00 | DONE horn_ex_only_len4_vars10_50_case10 50/50 acc=1.00 | DONE horn_ex_only_len5_vars10_50_case10 50/50 acc=1.00 |
| hornonly | cnf_compact | horn_alg_from | `sat__repr-cnf_compact__subset-hornonly__prompt-horn_alg_from__openai_gpt-5.2-pro__think-high` | MISSING | MISSING | MISSING |
| hornonly | cnf_compact | horn_alg_linear | `sat__repr-cnf_compact__subset-hornonly__prompt-horn_alg_linear__openai_gpt-5.2-pro__think-high` | DONE horn_alg_linear_cnf_compact_len3_vars10_50_case10 50/50 acc=1.00 | DONE horn_alg_linear_cnf_compact_len4_vars10_50_case10 50/50 acc=1.00 | DONE horn_alg_linear_cnf_compact_len5_vars10_50_case10 50/50 acc=1.00 |
| hornonly | cnf_nl | examples_only | `sat__repr-cnf_nl__subset-hornonly__prompt-examples_only__openai_gpt-5.2-pro__think-high` | MISSING | MISSING | MISSING |
| hornonly | cnf_nl | horn_alg_from | `sat__repr-cnf_nl__subset-hornonly__prompt-horn_alg_from__openai_gpt-5.2-pro__think-high` | MISSING | MISSING | MISSING |
| hornonly | cnf_nl | horn_alg_linear | `sat__repr-cnf_nl__subset-hornonly__prompt-horn_alg_linear__openai_gpt-5.2-pro__think-high` | DONE horn_alg_linear_cnf_nl_len3_vars10_50_case10 50/50 acc=1.00 | DONE horn_alg_linear_cnf_nl_len4_vars10_50_case10 50/50 acc=1.00 | DONE horn_alg_linear_cnf_nl_len5_vars10_50_case10 50/50 acc=1.00 |
| nonhornonly | cnf_compact | dpll_alg_from | `sat__repr-cnf_compact__subset-nonhornonly__prompt-dpll_alg_from__openai_gpt-5.2-pro__think-high` | MISSING | MISSING | MISSING |
| nonhornonly | cnf_compact | dpll_alg_linear | `sat__repr-cnf_compact__subset-nonhornonly__prompt-dpll_alg_linear__openai_gpt-5.2-pro__think-high` | DONE nonhorn_dpll_linear_cnf_compact_len3_vars10_50_case10 50/50 acc=0.72 | ERRORS nonhorn_dpll_linear_cnf_compact_len4_vars10_50_case10 50/50 acc=0.57 (errors=1) | DONE nonhorn_dpll_linear_cnf_compact_len5_vars10_50_case10 50/50 acc=0.50 |
| nonhornonly | cnf_compact | examples_only | `sat__repr-cnf_compact__subset-nonhornonly__prompt-examples_only__openai_gpt-5.2-pro__think-high` | ERRORS nonhorn_ex_only_cnf_compact_len3_vars10_50_case10 50/50 acc=0.92 (errors=11) | MISSING | MISSING |
| nonhornonly | cnf_nl | dpll_alg_from | `sat__repr-cnf_nl__subset-nonhornonly__prompt-dpll_alg_from__openai_gpt-5.2-pro__think-high` | MISSING | MISSING | MISSING |
| nonhornonly | cnf_nl | dpll_alg_linear | `sat__repr-cnf_nl__subset-nonhornonly__prompt-dpll_alg_linear__openai_gpt-5.2-pro__think-high` | ERRORS nonhorn_dpll_linear_cnf_nl_len3_vars10_50_case10 50/50 acc=0.80 (errors=6) | DONE nonhorn_dpll_linear_cnf_nl_len4_vars10_50_case10 50/50 acc=0.58 | DONE nonhorn_dpll_linear_cnf_nl_len5_vars10_50_case10 50/50 acc=0.50 |
| nonhornonly | cnf_nl | examples_only | `sat__repr-cnf_nl__subset-nonhornonly__prompt-examples_only__openai_gpt-5.2-pro__think-high` | ERRORS nonhorn_ex_only_cnf_nl_len3_vars10_50_case10 50/50 acc=0.85 (errors=9) | MISSING | MISSING |

