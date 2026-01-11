## Experiment matrix: anthropic_claude-opus-4-5-20251101__think-none__prompt-matrix

- **Matrix config**: `/Users/ottomattas/Downloads/repos/llmlog/_refactor/configs/matrices/anthropic_claude-opus-4-5-20251101__think-none__prompt-matrix.yaml`
- **Runs dir**: `/Users/ottomattas/Downloads/repos/llmlog/_refactor/runs`
- **maxvars**: `10,20,30,40,50`
- **lens**: `3,4,5`
- **case_limit**: `10`

Notes:
- Status is computed from **latest-per-id** rows in `results.jsonl` (append-only logs).
- `run.manifest.json` can be overwritten by later `--ids` reruns; this tool avoids relying on it for selection.

### Target: anthropic/claude-opus-4-5-20251101/think_none

| subset | repr | prompt | suite | len=3 | len=4 | len=5 |
| --- | --- | --- | --- | --- | --- | --- |
| hornonly | cnf_compact | examples_only | `sat__repr-cnf_compact__subset-hornonly__prompt-examples_only__anthropic_claude-opus-4-5-20251101__think-none` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.96 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.94 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.74 |
| hornonly | cnf_compact | horn_alg_from | `sat__repr-cnf_compact__subset-hornonly__prompt-horn_alg_from__anthropic_claude-opus-4-5-20251101__think-none` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.98 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=1.00 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.88 |
| hornonly | cnf_compact | horn_alg_linear | `sat__repr-cnf_compact__subset-hornonly__prompt-horn_alg_linear__anthropic_claude-opus-4-5-20251101__think-none` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=1.00 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.96 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.88 |
| hornonly | cnf_nl | examples_only | `sat__repr-cnf_nl__subset-hornonly__prompt-examples_only__anthropic_claude-opus-4-5-20251101__think-none` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=1.00 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.88 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.74 |
| hornonly | cnf_nl | horn_alg_from | `sat__repr-cnf_nl__subset-hornonly__prompt-horn_alg_from__anthropic_claude-opus-4-5-20251101__think-none` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.98 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=1.00 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.88 |
| hornonly | cnf_nl | horn_alg_linear | `sat__repr-cnf_nl__subset-hornonly__prompt-horn_alg_linear__anthropic_claude-opus-4-5-20251101__think-none` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.96 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.98 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.82 |
| hornonly | horn_if_then | examples_only | `sat__repr-horn_if_then__subset-hornonly__prompt-examples_only__anthropic_claude-opus-4-5-20251101__think-none` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=1.00 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=1.00 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.94 |
| hornonly | horn_if_then | horn_alg_from | `sat__repr-horn_if_then__subset-hornonly__prompt-horn_alg_from__anthropic_claude-opus-4-5-20251101__think-none` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=1.00 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.98 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.88 |
| hornonly | horn_if_then | horn_alg_linear | `sat__repr-horn_if_then__subset-hornonly__prompt-horn_alg_linear__anthropic_claude-opus-4-5-20251101__think-none` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=1.00 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=1.00 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.92 |
| nonhornonly | cnf_compact | dpll_alg_from | `sat__repr-cnf_compact__subset-nonhornonly__prompt-dpll_alg_from__anthropic_claude-opus-4-5-20251101__think-none` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.52 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 |
| nonhornonly | cnf_compact | dpll_alg_linear | `sat__repr-cnf_compact__subset-nonhornonly__prompt-dpll_alg_linear__anthropic_claude-opus-4-5-20251101__think-none` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.52 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.52 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 |
| nonhornonly | cnf_compact | examples_only | `sat__repr-cnf_compact__subset-nonhornonly__prompt-examples_only__anthropic_claude-opus-4-5-20251101__think-none` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.56 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 |
| nonhornonly | cnf_nl | dpll_alg_from | `sat__repr-cnf_nl__subset-nonhornonly__prompt-dpll_alg_from__anthropic_claude-opus-4-5-20251101__think-none` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.52 | UNCLEAR baseline_case10_len3_5_vars10_50 50/50 acc=0.49 (unclear=1) | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 |
| nonhornonly | cnf_nl | dpll_alg_linear | `sat__repr-cnf_nl__subset-nonhornonly__prompt-dpll_alg_linear__anthropic_claude-opus-4-5-20251101__think-none` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.52 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 |
| nonhornonly | cnf_nl | examples_only | `sat__repr-cnf_nl__subset-nonhornonly__prompt-examples_only__anthropic_claude-opus-4-5-20251101__think-none` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.54 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 |
| nonhornonly | horn_if_then | examples_only | `sat__repr-horn_if_then__subset-nonhornonly__prompt-examples_only__anthropic_claude-opus-4-5-20251101__think-none` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.46 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.54 |
| nonhornonly | horn_if_then | horn_alg_from | `sat__repr-horn_if_then__subset-nonhornonly__prompt-horn_alg_from__anthropic_claude-opus-4-5-20251101__think-none` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.56 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.56 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.52 |
| nonhornonly | horn_if_then | horn_alg_linear | `sat__repr-horn_if_then__subset-nonhornonly__prompt-horn_alg_linear__anthropic_claude-opus-4-5-20251101__think-none` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.46 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.40 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.44 |

