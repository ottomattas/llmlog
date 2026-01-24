## Experiment matrix: openai_gpt-5.2-pro__think-high__hornonly_extvars60_80_100

- **Matrix config**: `/Users/ottomattas/Downloads/repos/llmlog/_refactor/configs/matrices/openai_gpt-5.2-pro__think-high__hornonly_extvars60_80_100.yaml`
- **Runs dir**: `/Users/ottomattas/Downloads/repos/llmlog/_refactor/runs`
- **maxvars**: `60,80,100`
- **lens**: `3,4,5`
- **case_limit**: `10`

Notes:
- Status is computed from **latest-per-id** rows in `results.jsonl` (append-only logs).
- `run.manifest.json` can be overwritten by later `--ids` reruns; this tool avoids relying on it for selection.

### Target: openai/gpt-5.2-pro/think_high

| subset | repr | prompt | suite | len=3 | len=4 | len=5 |
| --- | --- | --- | --- | --- | --- | --- |
| hornonly | cnf_compact | examples_only | `sat__repr-cnf_compact__subset-hornonly__prompt-examples_only__openai_gpt-5.2-pro__think-high__extvars60_80_100` | DONE horn_ex_only_len3_vars60_80_100_case10 30/30 acc=1.00 | DONE horn_ex_only_len4_vars60_80_100_case10 30/30 acc=1.00 | DONE horn_ex_only_len5_vars60_80_100_case10 30/30 acc=1.00 |
| hornonly | cnf_compact | horn_alg_linear | `sat__repr-cnf_compact__subset-hornonly__prompt-horn_alg_linear__openai_gpt-5.2-pro__think-high__extvars60_80_100` | DONE horn_alg_linear_cnf_compact_len3_vars60_80_100_case10 30/30 acc=1.00 | DONE horn_alg_linear_cnf_compact_len4_vars60_80_100_case10 30/30 acc=1.00 | DONE horn_alg_linear_cnf_compact_len5_vars60_80_100_case10 30/30 acc=1.00 |

