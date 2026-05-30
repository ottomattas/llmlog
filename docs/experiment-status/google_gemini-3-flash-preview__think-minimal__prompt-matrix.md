## Experiment matrix: google_gemini-3-flash-preview__think-minimal__prompt-matrix

- **Matrix config**: `configs/matrices/google_gemini-3-flash-preview__think-minimal__prompt-matrix.yaml`
- **Runs dir**: `runs`
- **maxvars**: `10,20,30,40,50`
- **lens**: `3,4,5`
- **case_limit**: `10`

Notes:
- Status is computed from **latest-per-id** rows in `results.jsonl` (append-only logs).
- `run.manifest.json` can be overwritten by later `--ids` reruns; this tool avoids relying on it for selection.

### Target: google/gemini-3-flash-preview/think_minimal

| subset | repr | prompt | suite | len=3 | len=4 | len=5 |
| --- | --- | --- | --- | --- | --- | --- |
| hornonly | cnf_compact | examples_only | `sat__repr-cnf_compact__subset-hornonly__prompt-examples_only__google_gemini-3-flash-preview__think-minimal` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.98 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.88 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.76 |
| hornonly | cnf_compact | horn_alg_from | `sat__repr-cnf_compact__subset-hornonly__prompt-horn_alg_from__google_gemini-3-flash-preview__think-minimal` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.96 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=1.00 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.92 |
| hornonly | cnf_compact | horn_alg_linear | `sat__repr-cnf_compact__subset-hornonly__prompt-horn_alg_linear__google_gemini-3-flash-preview__think-minimal` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=1.00 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.98 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.96 |
| hornonly | cnf_nl | examples_only | `sat__repr-cnf_nl__subset-hornonly__prompt-examples_only__google_gemini-3-flash-preview__think-minimal` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.96 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.86 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.72 |
| hornonly | cnf_nl | horn_alg_from | `sat__repr-cnf_nl__subset-hornonly__prompt-horn_alg_from__google_gemini-3-flash-preview__think-minimal` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.94 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.96 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.88 |
| hornonly | cnf_nl | horn_alg_linear | `sat__repr-cnf_nl__subset-hornonly__prompt-horn_alg_linear__google_gemini-3-flash-preview__think-minimal` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=1.00 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.98 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.90 |
| hornonly | horn_if_then | examples_only | `sat__repr-horn_if_then__subset-hornonly__prompt-examples_only__google_gemini-3-flash-preview__think-minimal` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=1.00 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.98 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.90 |
| hornonly | horn_if_then | horn_alg_from | `sat__repr-horn_if_then__subset-hornonly__prompt-horn_alg_from__google_gemini-3-flash-preview__think-minimal` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.96 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.98 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.94 |
| hornonly | horn_if_then | horn_alg_linear | `sat__repr-horn_if_then__subset-hornonly__prompt-horn_alg_linear__google_gemini-3-flash-preview__think-minimal` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.96 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=1.00 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.94 |
| nonhornonly | cnf_compact | dpll_alg_from | `sat__repr-cnf_compact__subset-nonhornonly__prompt-dpll_alg_from__google_gemini-3-flash-preview__think-minimal` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.52 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 |
| nonhornonly | cnf_compact | dpll_alg_linear | `sat__repr-cnf_compact__subset-nonhornonly__prompt-dpll_alg_linear__google_gemini-3-flash-preview__think-minimal` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.54 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 |
| nonhornonly | cnf_compact | examples_only | `sat__repr-cnf_compact__subset-nonhornonly__prompt-examples_only__google_gemini-3-flash-preview__think-minimal` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.52 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 |
| nonhornonly | cnf_nl | dpll_alg_from | `sat__repr-cnf_nl__subset-nonhornonly__prompt-dpll_alg_from__google_gemini-3-flash-preview__think-minimal` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.54 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 |
| nonhornonly | cnf_nl | dpll_alg_linear | `sat__repr-cnf_nl__subset-nonhornonly__prompt-dpll_alg_linear__google_gemini-3-flash-preview__think-minimal` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.54 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 |
| nonhornonly | cnf_nl | examples_only | `sat__repr-cnf_nl__subset-nonhornonly__prompt-examples_only__google_gemini-3-flash-preview__think-minimal` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 |
| nonhornonly | horn_if_then | examples_only | `sat__repr-horn_if_then__subset-nonhornonly__prompt-examples_only__google_gemini-3-flash-preview__think-minimal` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.54 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.48 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.52 |
| nonhornonly | horn_if_then | horn_alg_from | `sat__repr-horn_if_then__subset-nonhornonly__prompt-horn_alg_from__google_gemini-3-flash-preview__think-minimal` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.52 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 |
| nonhornonly | horn_if_then | horn_alg_linear | `sat__repr-horn_if_then__subset-nonhornonly__prompt-horn_alg_linear__google_gemini-3-flash-preview__think-minimal` | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.52 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 | DONE baseline_case10_len3_5_vars10_50 50/50 acc=0.50 |

