## Experiment matrix: openai_gpt-5.2-pro__think-high__prompt-matrix

- **Matrix config**: `configs/matrices/openai_gpt-5.2-pro__think-high__prompt-matrix.yaml`
- **Runs dir**: `runs`
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
| hornonly | horn_if_then | examples_only | `sat__repr-horn_if_then__subset-hornonly__prompt-examples_only__openai_gpt-5.2-pro__think-high` | MISSING | MISSING | MISSING |
| hornonly | horn_if_then | horn_alg_from | `sat__repr-horn_if_then__subset-hornonly__prompt-horn_alg_from__openai_gpt-5.2-pro__think-high` | MISSING | MISSING | MISSING |
| hornonly | horn_if_then | horn_alg_linear | `sat__repr-horn_if_then__subset-hornonly__prompt-horn_alg_linear__openai_gpt-5.2-pro__think-high` | MISSING | MISSING | MISSING |
| nonhornonly | cnf_compact | dpll_alg_from | `sat__repr-cnf_compact__subset-nonhornonly__prompt-dpll_alg_from__openai_gpt-5.2-pro__think-high` | MISSING | MISSING | MISSING |
| nonhornonly | cnf_compact | dpll_alg_linear | `sat__repr-cnf_compact__subset-nonhornonly__prompt-dpll_alg_linear__openai_gpt-5.2-pro__think-high` | DONE nonhorn_dpll_linear_cnf_compact_len3_vars10_50_case10 50/50 acc=0.72 | DONE nonhorn_dpll_linear_cnf_compact_len4_vars10_50_case10 50/50 acc=0.58 | DONE nonhorn_dpll_linear_cnf_compact_len5_vars10_50_case10 50/50 acc=0.50 |
| nonhornonly | cnf_compact | examples_only | `sat__repr-cnf_compact__subset-nonhornonly__prompt-examples_only__openai_gpt-5.2-pro__think-high` | ERRORS nonhorn_ex_only_cnf_compact_len3_vars10_50_case10 50/50 acc=0.80 (errors=4) | MISSING | MISSING |
| nonhornonly | cnf_nl | dpll_alg_from | `sat__repr-cnf_nl__subset-nonhornonly__prompt-dpll_alg_from__openai_gpt-5.2-pro__think-high` | MISSING | MISSING | MISSING |
| nonhornonly | cnf_nl | dpll_alg_linear | `sat__repr-cnf_nl__subset-nonhornonly__prompt-dpll_alg_linear__openai_gpt-5.2-pro__think-high` | ERRORS nonhorn_dpll_linear_cnf_nl_len3_vars10_50_case10 50/50 acc=0.75 (errors=2) | DONE nonhorn_dpll_linear_cnf_nl_len4_vars10_50_case10 50/50 acc=0.58 | DONE nonhorn_dpll_linear_cnf_nl_len5_vars10_50_case10 50/50 acc=0.50 |
| nonhornonly | cnf_nl | examples_only | `sat__repr-cnf_nl__subset-nonhornonly__prompt-examples_only__openai_gpt-5.2-pro__think-high` | ERRORS nonhorn_ex_only_cnf_nl_len3_vars10_50_case10 50/50 acc=0.85 (errors=9) | MISSING | MISSING |
| nonhornonly | horn_if_then | examples_only | `sat__repr-horn_if_then__subset-nonhornonly__prompt-examples_only__openai_gpt-5.2-pro__think-high` | MISSING | MISSING | MISSING |
| nonhornonly | horn_if_then | horn_alg_from | `sat__repr-horn_if_then__subset-nonhornonly__prompt-horn_alg_from__openai_gpt-5.2-pro__think-high` | MISSING | MISSING | MISSING |
| nonhornonly | horn_if_then | horn_alg_linear | `sat__repr-horn_if_then__subset-nonhornonly__prompt-horn_alg_linear__openai_gpt-5.2-pro__think-high` | MISSING | MISSING | MISSING |

