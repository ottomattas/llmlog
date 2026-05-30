## Experiment matrix: openai_gpt-5.2__think-none__prompt-matrix

- **Matrix config**: `/Users/ottomattas/Downloads/repos/llmlog/configs/matrices/openai_gpt-5.2__think-none__prompt-matrix.yaml`
- **Runs dir**: `/Users/ottomattas/Downloads/repos/llmlog/runs`
- **maxvars**: `10,20,30,40,50`
- **lens**: `3,4,5`
- **case_limit**: `10`

Notes:
- Status is computed from **latest-per-id** rows in `results.jsonl` (append-only logs).
- `run.manifest.json` can be overwritten by later `--ids` reruns; this tool avoids relying on it for selection.

### Target: openai/gpt-5.2-2025-12-11/think_none

| subset | repr | prompt | suite | len=3 | len=4 | len=5 |
| --- | --- | --- | --- | --- | --- | --- |
| hornonly | cnf_compact | examples_only | `sat__repr-cnf_compact__subset-hornonly__prompt-examples_only__openai_gpt-5.2__think-none` | DONE horn_ex_only_cnf_compact_len3_vars10_50_case10 50/50 acc=0.90 | DONE horn_ex_only_cnf_compact_len4_vars10_50_case10 50/50 acc=0.68 | DONE horn_ex_only_cnf_compact_len5_vars10_50_case10 50/50 acc=0.58 |
| hornonly | cnf_compact | horn_alg_from | `sat__repr-cnf_compact__subset-hornonly__prompt-horn_alg_from__openai_gpt-5.2__think-none` | DONE horn_alg_from_cnf_compact_len3_vars10_50_case10 50/50 acc=0.52 | DONE horn_alg_from_cnf_compact_len4_vars10_50_case10 50/50 acc=0.56 | DONE horn_alg_from_cnf_compact_len5_vars10_50_case10 50/50 acc=0.62 |
| hornonly | cnf_compact | horn_alg_linear | `sat__repr-cnf_compact__subset-hornonly__prompt-horn_alg_linear__openai_gpt-5.2__think-none` | DONE horn_alg_linear_cnf_compact_len3_vars10_50_case10 50/50 acc=0.86 | DONE horn_alg_linear_cnf_compact_len4_vars10_50_case10 50/50 acc=0.72 | DONE horn_alg_linear_cnf_compact_len5_vars10_50_case10 50/50 acc=0.62 |
| hornonly | cnf_nl | examples_only | `sat__repr-cnf_nl__subset-hornonly__prompt-examples_only__openai_gpt-5.2__think-none` | DONE horn_ex_only_cnf_nl_len3_vars10_50_case10 50/50 acc=0.76 | DONE horn_ex_only_cnf_nl_len4_vars10_50_case10 50/50 acc=0.64 | DONE horn_ex_only_cnf_nl_len5_vars10_50_case10 50/50 acc=0.52 |
| hornonly | cnf_nl | horn_alg_from | `sat__repr-cnf_nl__subset-hornonly__prompt-horn_alg_from__openai_gpt-5.2__think-none` | DONE horn_alg_from_cnf_nl_len3_vars10_50_case10 50/50 acc=0.60 | DONE horn_alg_from_cnf_nl_len4_vars10_50_case10 50/50 acc=0.56 | DONE horn_alg_from_cnf_nl_len5_vars10_50_case10 50/50 acc=0.54 |
| hornonly | cnf_nl | horn_alg_linear | `sat__repr-cnf_nl__subset-hornonly__prompt-horn_alg_linear__openai_gpt-5.2__think-none` | DONE horn_alg_linear_cnf_nl_len3_vars10_50_case10 50/50 acc=0.64 | DONE horn_alg_linear_cnf_nl_len4_vars10_50_case10 50/50 acc=0.78 | DONE horn_alg_linear_cnf_nl_len5_vars10_50_case10 50/50 acc=0.62 |
| hornonly | horn_if_then | examples_only | `sat__repr-horn_if_then__subset-hornonly__prompt-examples_only__openai_gpt-5.2__think-none` | DONE baseline_case10_len3_vars10_50 50/50 acc=0.94 | DONE baseline_case10_len4_vars10_50 50/50 acc=0.90 | DONE baseline_case10_len5_vars10_50 50/50 acc=0.72 |
| hornonly | horn_if_then | horn_alg_from | `sat__repr-horn_if_then__subset-hornonly__prompt-horn_alg_from__openai_gpt-5.2__think-none` | DONE baseline_case10_len3_vars10_50 50/50 acc=0.72 | DONE baseline_case10_len4_vars10_50 50/50 acc=0.78 | DONE baseline_case10_len5_vars10_50 50/50 acc=0.86 |
| hornonly | horn_if_then | horn_alg_linear | `sat__repr-horn_if_then__subset-hornonly__prompt-horn_alg_linear__openai_gpt-5.2__think-none` | DONE baseline_case10_len3_vars10_50 50/50 acc=0.96 | DONE baseline_case10_len4_vars10_50 50/50 acc=0.82 | DONE baseline_case10_len5_vars10_50 50/50 acc=0.78 |
| nonhornonly | cnf_compact | dpll_alg_from | `sat__repr-cnf_compact__subset-nonhornonly__prompt-dpll_alg_from__openai_gpt-5.2__think-none` | DONE nonhorn_dpll_from_cnf_compact_len3_vars10_50_case10 50/50 acc=0.52 | DONE nonhorn_dpll_from_cnf_compact_len4_vars10_50_case10 50/50 acc=0.44 | DONE nonhorn_dpll_from_cnf_compact_len5_vars10_50_case10 50/50 acc=0.38 |
| nonhornonly | cnf_compact | dpll_alg_linear | `sat__repr-cnf_compact__subset-nonhornonly__prompt-dpll_alg_linear__openai_gpt-5.2__think-none` | DONE nonhorn_dpll_linear_cnf_compact_len3_vars10_50_case10 50/50 acc=0.52 | DONE nonhorn_dpll_linear_cnf_compact_len4_vars10_50_case10 50/50 acc=0.50 | DONE nonhorn_dpll_linear_cnf_compact_len5_vars10_50_case10 50/50 acc=0.50 |
| nonhornonly | cnf_compact | examples_only | `sat__repr-cnf_compact__subset-nonhornonly__prompt-examples_only__openai_gpt-5.2__think-none` | DONE nonhorn_ex_only_cnf_compact_len3_vars10_50_case10 50/50 acc=0.50 | DONE nonhorn_ex_only_cnf_compact_len4_vars10_50_case10 50/50 acc=0.50 | DONE nonhorn_ex_only_cnf_compact_len5_vars10_50_case10 50/50 acc=0.50 |
| nonhornonly | cnf_nl | dpll_alg_from | `sat__repr-cnf_nl__subset-nonhornonly__prompt-dpll_alg_from__openai_gpt-5.2__think-none` | DONE nonhorn_dpll_from_cnf_nl_len3_vars10_50_case10 50/50 acc=0.44 | DONE nonhorn_dpll_from_cnf_nl_len4_vars10_50_case10 50/50 acc=0.48 | DONE nonhorn_dpll_from_cnf_nl_len5_vars10_50_case10 50/50 acc=0.54 |
| nonhornonly | cnf_nl | dpll_alg_linear | `sat__repr-cnf_nl__subset-nonhornonly__prompt-dpll_alg_linear__openai_gpt-5.2__think-none` | DONE nonhorn_dpll_linear_cnf_nl_len3_vars10_50_case10 50/50 acc=0.50 | DONE nonhorn_dpll_linear_cnf_nl_len4_vars10_50_case10 50/50 acc=0.50 | DONE nonhorn_dpll_linear_cnf_nl_len5_vars10_50_case10 50/50 acc=0.50 |
| nonhornonly | cnf_nl | examples_only | `sat__repr-cnf_nl__subset-nonhornonly__prompt-examples_only__openai_gpt-5.2__think-none` | DONE nonhorn_ex_only_cnf_nl_len3_vars10_50_case10 50/50 acc=0.50 | DONE nonhorn_ex_only_cnf_nl_len4_vars10_50_case10 50/50 acc=0.50 | DONE nonhorn_ex_only_cnf_nl_len5_vars10_50_case10 50/50 acc=0.50 |
| nonhornonly | horn_if_then | examples_only | `sat__repr-horn_if_then__subset-nonhornonly__prompt-examples_only__openai_gpt-5.2__think-none` | DONE baseline_case10_len3_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len4_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len5_vars10_50 50/50 acc=0.52 |
| nonhornonly | horn_if_then | horn_alg_from | `sat__repr-horn_if_then__subset-nonhornonly__prompt-horn_alg_from__openai_gpt-5.2__think-none` | DONE baseline_case10_len3_vars10_50 50/50 acc=0.54 | DONE baseline_case10_len4_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len5_vars10_50 50/50 acc=0.50 |
| nonhornonly | horn_if_then | horn_alg_linear | `sat__repr-horn_if_then__subset-nonhornonly__prompt-horn_alg_linear__openai_gpt-5.2__think-none` | DONE baseline_case10_len3_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len4_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len5_vars10_50 50/50 acc=0.50 |

