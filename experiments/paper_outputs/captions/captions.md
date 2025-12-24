## Figure descriptions (auto-generated)

This file contains **neutral descriptions** of the generated per-model figures under `experiments/paper_outputs/figures/`.

### Global notes (applies to all figures)

- Each figure page is a **grid of heatmaps**.
- **x-axis**: `maxlen` (clause length bucket)
- **y-axis**: `maxvars` (variable count bucket)
- **row facet**: `horn` flag (1 = Horn, 0 = non-Horn) when both appear for that prompt/model
- **column facet**: `thinking_mode` (e.g. `nothink`, `think-low`, `think-med`, `think-high`)
- **color** encodes the metric named in the page title/colorbar.
- **blank cells** indicate no data was available for that `(maxvars, maxlen)` bucket.
- Ground truth is derived from `meta.satflag` in `results.jsonl` (1 = satisfiable, 0 = unsatisfiable/contradiction).
- Model outputs are **re-parsed** from `results.provenance.jsonl` `full_text` where available; unparseable outputs are counted as `unclear` and treated as incorrect in accuracy metrics.

Exact prompt instructions + representative example statement blocks are listed in `experiments/paper_outputs/prompts/prompt_catalog.md` (indexed by `prompt_id`).

---

### anthropic/claude-3-5-haiku-20241022

- Report PDF: `experiments/paper_outputs/figures/model_reports/anthropic__claude-3-5-haiku-20241022.pdf`
- PNG directory: `experiments/paper_outputs/figures/png/anthropic__claude-3-5-haiku-20241022/`

#### prompt_83b02d3a05

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/exp1_cnf_v1_contradiction.j2`
- total examples aggregated (all thinking×horn): 5
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-3-5-haiku-20241022/prompt_83b02d3a05__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-3-5-haiku-20241022/prompt_83b02d3a05__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-3-5-haiku-20241022/prompt_83b02d3a05__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-3-5-haiku-20241022/prompt_83b02d3a05__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-3-5-haiku-20241022 under prompt condition prompt_83b02d3a05 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-3-5-haiku-20241022/prompt_83b02d3a05__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-3-5-haiku-20241022/prompt_83b02d3a05__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_83b02d3a05` for the exact instructions and example statements.

#### prompt_c6875730a1

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/exp6_horn_yesno.j2`
- total examples aggregated (all thinking×horn): 520
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-3-5-haiku-20241022/prompt_c6875730a1__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-3-5-haiku-20241022/prompt_c6875730a1__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-3-5-haiku-20241022/prompt_c6875730a1__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-3-5-haiku-20241022/prompt_c6875730a1__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-3-5-haiku-20241022 under prompt condition prompt_c6875730a1 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-3-5-haiku-20241022/prompt_c6875730a1__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-3-5-haiku-20241022/prompt_c6875730a1__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c6875730a1` for the exact instructions and example statements.

---

### anthropic/claude-haiku-4-5-20251001

- Report PDF: `experiments/paper_outputs/figures/model_reports/anthropic__claude-haiku-4-5-20251001.pdf`
- PNG directory: `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/`

#### prompt_0b276d34e8

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 1950
- thinking modes present: nothink, think-low, think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_0b276d34e8__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_0b276d34e8__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_0b276d34e8__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_0b276d34e8__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-haiku-4-5-20251001 under prompt condition prompt_0b276d34e8 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_0b276d34e8__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_0b276d34e8__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_0b276d34e8` for the exact instructions and example statements.

#### prompt_21889a86a3

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 66
- thinking modes present: nothink, think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_21889a86a3__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_21889a86a3__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_21889a86a3__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_21889a86a3__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-haiku-4-5-20251001 under prompt condition prompt_21889a86a3 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_21889a86a3__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_21889a86a3__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_21889a86a3` for the exact instructions and example statements.

#### prompt_2376d1fca7

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 16
- thinking modes present: nothink, think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_2376d1fca7__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_2376d1fca7__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_2376d1fca7__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_2376d1fca7__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-haiku-4-5-20251001 under prompt condition prompt_2376d1fca7 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_2376d1fca7__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_2376d1fca7__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2376d1fca7` for the exact instructions and example statements.

#### prompt_2e9c5ccddf

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 56
- thinking modes present: nothink, think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_2e9c5ccddf__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_2e9c5ccddf__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_2e9c5ccddf__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_2e9c5ccddf__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-haiku-4-5-20251001 under prompt condition prompt_2e9c5ccddf (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_2e9c5ccddf__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_2e9c5ccddf__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2e9c5ccddf` for the exact instructions and example statements.

#### prompt_62ba908560

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 1399
- thinking modes present: nothink, think-high, think-low, think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_62ba908560__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_62ba908560__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_62ba908560__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_62ba908560__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-haiku-4-5-20251001 under prompt condition prompt_62ba908560 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_62ba908560__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_62ba908560__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_62ba908560` for the exact instructions and example statements.

#### prompt_73ecab0579

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- total examples aggregated (all thinking×horn): 6
- thinking modes present: nothink, think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_73ecab0579__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_73ecab0579__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_73ecab0579__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_73ecab0579__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-haiku-4-5-20251001 under prompt condition prompt_73ecab0579 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_73ecab0579__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_73ecab0579__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_73ecab0579` for the exact instructions and example statements.

#### prompt_7b28aa32dc

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 1266
- thinking modes present: nothink, think-high, think-low, think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_7b28aa32dc__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_7b28aa32dc__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_7b28aa32dc__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_7b28aa32dc__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-haiku-4-5-20251001 under prompt condition prompt_7b28aa32dc (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_7b28aa32dc__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_7b28aa32dc__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_7b28aa32dc` for the exact instructions and example statements.

#### prompt_c012d6f2e6

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 2728
- thinking modes present: nothink, think-high, think-low, think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_c012d6f2e6__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_c012d6f2e6__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_c012d6f2e6__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_c012d6f2e6__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-haiku-4-5-20251001 under prompt condition prompt_c012d6f2e6 (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_c012d6f2e6__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_c012d6f2e6__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c012d6f2e6` for the exact instructions and example statements.

#### prompt_c1b2be97aa

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 616
- thinking modes present: nothink, think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_c1b2be97aa__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_c1b2be97aa__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_c1b2be97aa__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_c1b2be97aa__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-haiku-4-5-20251001 under prompt condition prompt_c1b2be97aa (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_c1b2be97aa__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-haiku-4-5-20251001/prompt_c1b2be97aa__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c1b2be97aa` for the exact instructions and example statements.

---

### anthropic/claude-opus-4-1-20250805

- Report PDF: `experiments/paper_outputs/figures/model_reports/anthropic__claude-opus-4-1-20250805.pdf`
- PNG directory: `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/`

#### prompt_21889a86a3

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 32
- thinking modes present: think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_21889a86a3__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_21889a86a3__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_21889a86a3__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_21889a86a3__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-opus-4-1-20250805 under prompt condition prompt_21889a86a3 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_21889a86a3__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_21889a86a3__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_21889a86a3` for the exact instructions and example statements.

#### prompt_2376d1fca7

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 8
- thinking modes present: think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_2376d1fca7__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_2376d1fca7__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_2376d1fca7__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_2376d1fca7__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-opus-4-1-20250805 under prompt condition prompt_2376d1fca7 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_2376d1fca7__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_2376d1fca7__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2376d1fca7` for the exact instructions and example statements.

#### prompt_2e9c5ccddf

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 28
- thinking modes present: think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_2e9c5ccddf__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_2e9c5ccddf__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_2e9c5ccddf__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_2e9c5ccddf__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-opus-4-1-20250805 under prompt condition prompt_2e9c5ccddf (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_2e9c5ccddf__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_2e9c5ccddf__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2e9c5ccddf` for the exact instructions and example statements.

#### prompt_73ecab0579

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- total examples aggregated (all thinking×horn): 3
- thinking modes present: think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_73ecab0579__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_73ecab0579__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_73ecab0579__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_73ecab0579__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-opus-4-1-20250805 under prompt condition prompt_73ecab0579 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_73ecab0579__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_73ecab0579__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_73ecab0579` for the exact instructions and example statements.

#### prompt_83b02d3a05

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/exp1_cnf_v1_contradiction.j2`
- total examples aggregated (all thinking×horn): 5
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_83b02d3a05__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_83b02d3a05__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_83b02d3a05__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_83b02d3a05__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-opus-4-1-20250805 under prompt condition prompt_83b02d3a05 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_83b02d3a05__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_83b02d3a05__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_83b02d3a05` for the exact instructions and example statements.

#### prompt_c1b2be97aa

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 308
- thinking modes present: think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_c1b2be97aa__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_c1b2be97aa__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_c1b2be97aa__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_c1b2be97aa__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-opus-4-1-20250805 under prompt condition prompt_c1b2be97aa (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_c1b2be97aa__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_c1b2be97aa__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c1b2be97aa` for the exact instructions and example statements.

#### prompt_c6875730a1

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/exp6_horn_yesno.j2`
- total examples aggregated (all thinking×horn): 520
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_c6875730a1__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_c6875730a1__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_c6875730a1__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_c6875730a1__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-opus-4-1-20250805 under prompt condition prompt_c6875730a1 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_c6875730a1__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-opus-4-1-20250805/prompt_c6875730a1__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c6875730a1` for the exact instructions and example statements.

---

### anthropic/claude-sonnet-4-20250514

- Report PDF: `experiments/paper_outputs/figures/model_reports/anthropic__claude-sonnet-4-20250514.pdf`
- PNG directory: `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-20250514/`

#### prompt_c6875730a1

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/exp6_horn_yesno.j2`
- total examples aggregated (all thinking×horn): 520
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-20250514/prompt_c6875730a1__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-20250514/prompt_c6875730a1__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-20250514/prompt_c6875730a1__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-20250514/prompt_c6875730a1__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-sonnet-4-20250514 under prompt condition prompt_c6875730a1 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-20250514/prompt_c6875730a1__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-20250514/prompt_c6875730a1__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c6875730a1` for the exact instructions and example statements.

---

### anthropic/claude-sonnet-4-5-20250929

- Report PDF: `experiments/paper_outputs/figures/model_reports/anthropic__claude-sonnet-4-5-20250929.pdf`
- PNG directory: `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/`

#### prompt_0b276d34e8

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 650
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_0b276d34e8__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_0b276d34e8__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_0b276d34e8__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_0b276d34e8__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-sonnet-4-5-20250929 under prompt condition prompt_0b276d34e8 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_0b276d34e8__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_0b276d34e8__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_0b276d34e8` for the exact instructions and example statements.

#### prompt_21889a86a3

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 33
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_21889a86a3__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_21889a86a3__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_21889a86a3__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_21889a86a3__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-sonnet-4-5-20250929 under prompt condition prompt_21889a86a3 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_21889a86a3__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_21889a86a3__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_21889a86a3` for the exact instructions and example statements.

#### prompt_2376d1fca7

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 8
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_2376d1fca7__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_2376d1fca7__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_2376d1fca7__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_2376d1fca7__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-sonnet-4-5-20250929 under prompt condition prompt_2376d1fca7 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_2376d1fca7__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_2376d1fca7__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2376d1fca7` for the exact instructions and example statements.

#### prompt_2e9c5ccddf

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 28
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_2e9c5ccddf__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_2e9c5ccddf__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_2e9c5ccddf__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_2e9c5ccddf__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-sonnet-4-5-20250929 under prompt condition prompt_2e9c5ccddf (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_2e9c5ccddf__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_2e9c5ccddf__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2e9c5ccddf` for the exact instructions and example statements.

#### prompt_62ba908560

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 383
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_62ba908560__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_62ba908560__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_62ba908560__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_62ba908560__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-sonnet-4-5-20250929 under prompt condition prompt_62ba908560 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_62ba908560__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_62ba908560__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_62ba908560` for the exact instructions and example statements.

#### prompt_73ecab0579

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- total examples aggregated (all thinking×horn): 3
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_73ecab0579__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_73ecab0579__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_73ecab0579__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_73ecab0579__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-sonnet-4-5-20250929 under prompt condition prompt_73ecab0579 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_73ecab0579__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_73ecab0579__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_73ecab0579` for the exact instructions and example statements.

#### prompt_7b28aa32dc

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 277
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_7b28aa32dc__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_7b28aa32dc__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_7b28aa32dc__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_7b28aa32dc__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-sonnet-4-5-20250929 under prompt condition prompt_7b28aa32dc (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_7b28aa32dc__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_7b28aa32dc__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_7b28aa32dc` for the exact instructions and example statements.

#### prompt_83b02d3a05

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/exp1_cnf_v1_contradiction.j2`
- total examples aggregated (all thinking×horn): 5
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_83b02d3a05__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_83b02d3a05__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_83b02d3a05__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_83b02d3a05__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-sonnet-4-5-20250929 under prompt condition prompt_83b02d3a05 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_83b02d3a05__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_83b02d3a05__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_83b02d3a05` for the exact instructions and example statements.

#### prompt_c012d6f2e6

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 666
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_c012d6f2e6__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_c012d6f2e6__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_c012d6f2e6__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_c012d6f2e6__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-sonnet-4-5-20250929 under prompt condition prompt_c012d6f2e6 (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_c012d6f2e6__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_c012d6f2e6__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c012d6f2e6` for the exact instructions and example statements.

#### prompt_c1b2be97aa

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 308
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_c1b2be97aa__accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_c1b2be97aa__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_c1b2be97aa__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_c1b2be97aa__accuracy.png`): Heatmaps of overall accuracy (correct/total) for anthropic/claude-sonnet-4-5-20250929 under prompt condition prompt_c1b2be97aa (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_c1b2be97aa__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/anthropic__claude-sonnet-4-5-20250929/prompt_c1b2be97aa__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c1b2be97aa` for the exact instructions and example statements.

---

### google/gemini-2.5-flash

- Report PDF: `experiments/paper_outputs/figures/model_reports/google__gemini-2.5-flash.pdf`
- PNG directory: `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/`

#### prompt_0b276d34e8

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 649
- thinking modes present: think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_0b276d34e8__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_0b276d34e8__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_0b276d34e8__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_0b276d34e8__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash under prompt condition prompt_0b276d34e8 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_0b276d34e8__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_0b276d34e8__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_0b276d34e8` for the exact instructions and example statements.

#### prompt_21889a86a3

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 33
- thinking modes present: think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_21889a86a3__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_21889a86a3__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_21889a86a3__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_21889a86a3__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash under prompt condition prompt_21889a86a3 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_21889a86a3__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_21889a86a3__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_21889a86a3` for the exact instructions and example statements.

#### prompt_2376d1fca7

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 8
- thinking modes present: think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_2376d1fca7__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_2376d1fca7__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_2376d1fca7__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_2376d1fca7__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash under prompt condition prompt_2376d1fca7 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_2376d1fca7__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_2376d1fca7__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2376d1fca7` for the exact instructions and example statements.

#### prompt_2e9c5ccddf

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 28
- thinking modes present: think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_2e9c5ccddf__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_2e9c5ccddf__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_2e9c5ccddf__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_2e9c5ccddf__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash under prompt condition prompt_2e9c5ccddf (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_2e9c5ccddf__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_2e9c5ccddf__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2e9c5ccddf` for the exact instructions and example statements.

#### prompt_62ba908560

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 382
- thinking modes present: think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_62ba908560__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_62ba908560__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_62ba908560__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_62ba908560__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash under prompt condition prompt_62ba908560 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_62ba908560__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_62ba908560__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_62ba908560` for the exact instructions and example statements.

#### prompt_73ecab0579

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- total examples aggregated (all thinking×horn): 3
- thinking modes present: think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_73ecab0579__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_73ecab0579__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_73ecab0579__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_73ecab0579__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash under prompt condition prompt_73ecab0579 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_73ecab0579__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_73ecab0579__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_73ecab0579` for the exact instructions and example statements.

#### prompt_7b28aa32dc

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 277
- thinking modes present: think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_7b28aa32dc__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_7b28aa32dc__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_7b28aa32dc__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_7b28aa32dc__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash under prompt condition prompt_7b28aa32dc (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_7b28aa32dc__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_7b28aa32dc__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_7b28aa32dc` for the exact instructions and example statements.

#### prompt_83b02d3a05

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/exp1_cnf_v1_contradiction.j2`
- total examples aggregated (all thinking×horn): 5
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_83b02d3a05__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_83b02d3a05__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_83b02d3a05__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_83b02d3a05__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash under prompt condition prompt_83b02d3a05 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_83b02d3a05__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_83b02d3a05__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_83b02d3a05` for the exact instructions and example statements.

#### prompt_c012d6f2e6

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 666
- thinking modes present: think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_c012d6f2e6__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_c012d6f2e6__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_c012d6f2e6__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_c012d6f2e6__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash under prompt condition prompt_c012d6f2e6 (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_c012d6f2e6__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_c012d6f2e6__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c012d6f2e6` for the exact instructions and example statements.

#### prompt_c1b2be97aa

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 308
- thinking modes present: think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_c1b2be97aa__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_c1b2be97aa__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_c1b2be97aa__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_c1b2be97aa__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash under prompt condition prompt_c1b2be97aa (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_c1b2be97aa__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_c1b2be97aa__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c1b2be97aa` for the exact instructions and example statements.

#### prompt_c6875730a1

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/exp6_horn_yesno.j2`
- total examples aggregated (all thinking×horn): 520
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_c6875730a1__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_c6875730a1__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_c6875730a1__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_c6875730a1__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash under prompt condition prompt_c6875730a1 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_c6875730a1__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash/prompt_c6875730a1__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c6875730a1` for the exact instructions and example statements.

---

### google/gemini-2.5-flash-lite

- Report PDF: `experiments/paper_outputs/figures/model_reports/google__gemini-2.5-flash-lite.pdf`
- PNG directory: `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/`

#### prompt_0b276d34e8

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 1300
- thinking modes present: nothink, think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_0b276d34e8__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_0b276d34e8__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_0b276d34e8__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_0b276d34e8__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash-lite under prompt condition prompt_0b276d34e8 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_0b276d34e8__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_0b276d34e8__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_0b276d34e8` for the exact instructions and example statements.

#### prompt_21889a86a3

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 66
- thinking modes present: nothink, think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_21889a86a3__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_21889a86a3__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_21889a86a3__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_21889a86a3__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash-lite under prompt condition prompt_21889a86a3 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_21889a86a3__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_21889a86a3__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_21889a86a3` for the exact instructions and example statements.

#### prompt_2376d1fca7

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 16
- thinking modes present: nothink, think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_2376d1fca7__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_2376d1fca7__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_2376d1fca7__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_2376d1fca7__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash-lite under prompt condition prompt_2376d1fca7 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_2376d1fca7__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_2376d1fca7__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2376d1fca7` for the exact instructions and example statements.

#### prompt_2e9c5ccddf

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 56
- thinking modes present: nothink, think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_2e9c5ccddf__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_2e9c5ccddf__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_2e9c5ccddf__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_2e9c5ccddf__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash-lite under prompt condition prompt_2e9c5ccddf (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_2e9c5ccddf__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_2e9c5ccddf__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2e9c5ccddf` for the exact instructions and example statements.

#### prompt_62ba908560

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 1147
- thinking modes present: nothink, think-high, think-low, think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_62ba908560__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_62ba908560__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_62ba908560__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_62ba908560__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash-lite under prompt condition prompt_62ba908560 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_62ba908560__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_62ba908560__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_62ba908560` for the exact instructions and example statements.

#### prompt_73ecab0579

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- total examples aggregated (all thinking×horn): 6
- thinking modes present: nothink, think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_73ecab0579__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_73ecab0579__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_73ecab0579__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_73ecab0579__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash-lite under prompt condition prompt_73ecab0579 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_73ecab0579__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_73ecab0579__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_73ecab0579` for the exact instructions and example statements.

#### prompt_7b28aa32dc

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 1148
- thinking modes present: nothink, think-high, think-low, think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_7b28aa32dc__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_7b28aa32dc__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_7b28aa32dc__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_7b28aa32dc__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash-lite under prompt condition prompt_7b28aa32dc (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_7b28aa32dc__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_7b28aa32dc__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_7b28aa32dc` for the exact instructions and example statements.

#### prompt_83b02d3a05

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/exp1_cnf_v1_contradiction.j2`
- total examples aggregated (all thinking×horn): 5
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_83b02d3a05__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_83b02d3a05__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_83b02d3a05__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_83b02d3a05__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash-lite under prompt condition prompt_83b02d3a05 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_83b02d3a05__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_83b02d3a05__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_83b02d3a05` for the exact instructions and example statements.

#### prompt_c012d6f2e6

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 2109
- thinking modes present: nothink, think-high, think-low, think-med
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_c012d6f2e6__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_c012d6f2e6__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_c012d6f2e6__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_c012d6f2e6__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash-lite under prompt condition prompt_c012d6f2e6 (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_c012d6f2e6__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_c012d6f2e6__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c012d6f2e6` for the exact instructions and example statements.

#### prompt_c1b2be97aa

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 616
- thinking modes present: nothink, think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_c1b2be97aa__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_c1b2be97aa__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_c1b2be97aa__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_c1b2be97aa__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash-lite under prompt condition prompt_c1b2be97aa (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_c1b2be97aa__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_c1b2be97aa__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c1b2be97aa` for the exact instructions and example statements.

#### prompt_c6875730a1

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/exp6_horn_yesno.j2`
- total examples aggregated (all thinking×horn): 520
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_c6875730a1__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_c6875730a1__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_c6875730a1__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_c6875730a1__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-flash-lite under prompt condition prompt_c6875730a1 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_c6875730a1__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-flash-lite/prompt_c6875730a1__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c6875730a1` for the exact instructions and example statements.

---

### google/gemini-2.5-pro

- Report PDF: `experiments/paper_outputs/figures/model_reports/google__gemini-2.5-pro.pdf`
- PNG directory: `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/`

#### prompt_0b276d34e8

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 649
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_0b276d34e8__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_0b276d34e8__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_0b276d34e8__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_0b276d34e8__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-pro under prompt condition prompt_0b276d34e8 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_0b276d34e8__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_0b276d34e8__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_0b276d34e8` for the exact instructions and example statements.

#### prompt_21889a86a3

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 33
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_21889a86a3__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_21889a86a3__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_21889a86a3__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_21889a86a3__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-pro under prompt condition prompt_21889a86a3 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_21889a86a3__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_21889a86a3__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_21889a86a3` for the exact instructions and example statements.

#### prompt_2376d1fca7

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 8
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_2376d1fca7__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_2376d1fca7__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_2376d1fca7__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_2376d1fca7__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-pro under prompt condition prompt_2376d1fca7 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_2376d1fca7__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_2376d1fca7__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2376d1fca7` for the exact instructions and example statements.

#### prompt_2e9c5ccddf

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 28
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_2e9c5ccddf__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_2e9c5ccddf__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_2e9c5ccddf__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_2e9c5ccddf__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-pro under prompt condition prompt_2e9c5ccddf (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_2e9c5ccddf__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_2e9c5ccddf__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2e9c5ccddf` for the exact instructions and example statements.

#### prompt_62ba908560

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 381
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_62ba908560__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_62ba908560__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_62ba908560__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_62ba908560__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-pro under prompt condition prompt_62ba908560 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_62ba908560__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_62ba908560__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_62ba908560` for the exact instructions and example statements.

#### prompt_73ecab0579

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- total examples aggregated (all thinking×horn): 3
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_73ecab0579__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_73ecab0579__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_73ecab0579__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_73ecab0579__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-pro under prompt condition prompt_73ecab0579 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_73ecab0579__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_73ecab0579__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_73ecab0579` for the exact instructions and example statements.

#### prompt_7b28aa32dc

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 277
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_7b28aa32dc__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_7b28aa32dc__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_7b28aa32dc__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_7b28aa32dc__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-pro under prompt condition prompt_7b28aa32dc (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_7b28aa32dc__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_7b28aa32dc__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_7b28aa32dc` for the exact instructions and example statements.

#### prompt_83b02d3a05

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/exp1_cnf_v1_contradiction.j2`
- total examples aggregated (all thinking×horn): 5
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_83b02d3a05__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_83b02d3a05__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_83b02d3a05__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_83b02d3a05__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-pro under prompt condition prompt_83b02d3a05 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_83b02d3a05__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_83b02d3a05__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_83b02d3a05` for the exact instructions and example statements.

#### prompt_c012d6f2e6

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 665
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_c012d6f2e6__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_c012d6f2e6__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_c012d6f2e6__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_c012d6f2e6__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-pro under prompt condition prompt_c012d6f2e6 (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_c012d6f2e6__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_c012d6f2e6__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c012d6f2e6` for the exact instructions and example statements.

#### prompt_c1b2be97aa

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 308
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_c1b2be97aa__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_c1b2be97aa__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_c1b2be97aa__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_c1b2be97aa__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-pro under prompt condition prompt_c1b2be97aa (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_c1b2be97aa__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_c1b2be97aa__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c1b2be97aa` for the exact instructions and example statements.

#### prompt_c6875730a1

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/exp6_horn_yesno.j2`
- total examples aggregated (all thinking×horn): 520
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_c6875730a1__accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_c6875730a1__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_c6875730a1__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_c6875730a1__accuracy.png`): Heatmaps of overall accuracy (correct/total) for google/gemini-2.5-pro under prompt condition prompt_c6875730a1 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_c6875730a1__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/google__gemini-2.5-pro/prompt_c6875730a1__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c6875730a1` for the exact instructions and example statements.

---

### openai/gpt-5-2025-08-07

- Report PDF: `experiments/paper_outputs/figures/model_reports/openai__gpt-5-2025-08-07.pdf`
- PNG directory: `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/`

#### prompt_0b276d34e8

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 1300
- thinking modes present: think-high, think-medium
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_0b276d34e8__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_0b276d34e8__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_0b276d34e8__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_0b276d34e8__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-2025-08-07 under prompt condition prompt_0b276d34e8 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_0b276d34e8__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_0b276d34e8__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_0b276d34e8` for the exact instructions and example statements.

#### prompt_21889a86a3

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 33
- thinking modes present: think-medium
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_21889a86a3__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_21889a86a3__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_21889a86a3__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_21889a86a3__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-2025-08-07 under prompt condition prompt_21889a86a3 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_21889a86a3__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_21889a86a3__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_21889a86a3` for the exact instructions and example statements.

#### prompt_2376d1fca7

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 8
- thinking modes present: think-medium
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_2376d1fca7__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_2376d1fca7__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_2376d1fca7__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_2376d1fca7__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-2025-08-07 under prompt condition prompt_2376d1fca7 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_2376d1fca7__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_2376d1fca7__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2376d1fca7` for the exact instructions and example statements.

#### prompt_2e9c5ccddf

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 28
- thinking modes present: think-medium
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_2e9c5ccddf__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_2e9c5ccddf__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_2e9c5ccddf__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_2e9c5ccddf__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-2025-08-07 under prompt condition prompt_2e9c5ccddf (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_2e9c5ccddf__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_2e9c5ccddf__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2e9c5ccddf` for the exact instructions and example statements.

#### prompt_62ba908560

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 764
- thinking modes present: think-high, think-medium
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_62ba908560__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_62ba908560__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_62ba908560__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_62ba908560__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-2025-08-07 under prompt condition prompt_62ba908560 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_62ba908560__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_62ba908560__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_62ba908560` for the exact instructions and example statements.

#### prompt_73ecab0579

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- total examples aggregated (all thinking×horn): 3
- thinking modes present: think-medium
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_73ecab0579__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_73ecab0579__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_73ecab0579__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_73ecab0579__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-2025-08-07 under prompt condition prompt_73ecab0579 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_73ecab0579__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_73ecab0579__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_73ecab0579` for the exact instructions and example statements.

#### prompt_7b28aa32dc

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 554
- thinking modes present: think-high, think-medium
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_7b28aa32dc__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_7b28aa32dc__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_7b28aa32dc__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_7b28aa32dc__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-2025-08-07 under prompt condition prompt_7b28aa32dc (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_7b28aa32dc__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_7b28aa32dc__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_7b28aa32dc` for the exact instructions and example statements.

#### prompt_83b02d3a05

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/exp1_cnf_v1_contradiction.j2`
- total examples aggregated (all thinking×horn): 5
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_83b02d3a05__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_83b02d3a05__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_83b02d3a05__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_83b02d3a05__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-2025-08-07 under prompt condition prompt_83b02d3a05 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_83b02d3a05__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_83b02d3a05__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_83b02d3a05` for the exact instructions and example statements.

#### prompt_c012d6f2e6

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 1332
- thinking modes present: think-high, think-medium
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_c012d6f2e6__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_c012d6f2e6__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_c012d6f2e6__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_c012d6f2e6__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-2025-08-07 under prompt condition prompt_c012d6f2e6 (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_c012d6f2e6__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_c012d6f2e6__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c012d6f2e6` for the exact instructions and example statements.

#### prompt_c1b2be97aa

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 308
- thinking modes present: think-medium
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_c1b2be97aa__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_c1b2be97aa__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_c1b2be97aa__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_c1b2be97aa__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-2025-08-07 under prompt condition prompt_c1b2be97aa (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_c1b2be97aa__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_c1b2be97aa__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c1b2be97aa` for the exact instructions and example statements.

#### prompt_c6875730a1

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/exp6_horn_yesno.j2`
- total examples aggregated (all thinking×horn): 520
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_c6875730a1__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_c6875730a1__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_c6875730a1__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_c6875730a1__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-2025-08-07 under prompt condition prompt_c6875730a1 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_c6875730a1__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-2025-08-07/prompt_c6875730a1__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c6875730a1` for the exact instructions and example statements.

---

### openai/gpt-5-mini-2025-08-07

- Report PDF: `experiments/paper_outputs/figures/model_reports/openai__gpt-5-mini-2025-08-07.pdf`
- PNG directory: `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/`

#### prompt_0b276d34e8

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 650
- thinking modes present: think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_0b276d34e8__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_0b276d34e8__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_0b276d34e8__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_0b276d34e8__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-mini-2025-08-07 under prompt condition prompt_0b276d34e8 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_0b276d34e8__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_0b276d34e8__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_0b276d34e8` for the exact instructions and example statements.

#### prompt_21889a86a3

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 33
- thinking modes present: think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_21889a86a3__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_21889a86a3__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_21889a86a3__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_21889a86a3__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-mini-2025-08-07 under prompt condition prompt_21889a86a3 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_21889a86a3__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_21889a86a3__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_21889a86a3` for the exact instructions and example statements.

#### prompt_2376d1fca7

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 8
- thinking modes present: think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_2376d1fca7__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_2376d1fca7__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_2376d1fca7__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_2376d1fca7__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-mini-2025-08-07 under prompt condition prompt_2376d1fca7 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_2376d1fca7__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_2376d1fca7__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2376d1fca7` for the exact instructions and example statements.

#### prompt_2e9c5ccddf

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 28
- thinking modes present: think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_2e9c5ccddf__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_2e9c5ccddf__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_2e9c5ccddf__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_2e9c5ccddf__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-mini-2025-08-07 under prompt condition prompt_2e9c5ccddf (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_2e9c5ccddf__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_2e9c5ccddf__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2e9c5ccddf` for the exact instructions and example statements.

#### prompt_62ba908560

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 382
- thinking modes present: think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_62ba908560__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_62ba908560__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_62ba908560__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_62ba908560__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-mini-2025-08-07 under prompt condition prompt_62ba908560 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_62ba908560__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_62ba908560__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_62ba908560` for the exact instructions and example statements.

#### prompt_73ecab0579

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- total examples aggregated (all thinking×horn): 3
- thinking modes present: think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_73ecab0579__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_73ecab0579__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_73ecab0579__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_73ecab0579__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-mini-2025-08-07 under prompt condition prompt_73ecab0579 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_73ecab0579__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_73ecab0579__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_73ecab0579` for the exact instructions and example statements.

#### prompt_7b28aa32dc

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 277
- thinking modes present: think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_7b28aa32dc__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_7b28aa32dc__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_7b28aa32dc__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_7b28aa32dc__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-mini-2025-08-07 under prompt condition prompt_7b28aa32dc (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_7b28aa32dc__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_7b28aa32dc__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_7b28aa32dc` for the exact instructions and example statements.

#### prompt_83b02d3a05

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/exp1_cnf_v1_contradiction.j2`
- total examples aggregated (all thinking×horn): 5
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_83b02d3a05__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_83b02d3a05__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_83b02d3a05__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_83b02d3a05__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-mini-2025-08-07 under prompt condition prompt_83b02d3a05 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_83b02d3a05__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_83b02d3a05__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_83b02d3a05` for the exact instructions and example statements.

#### prompt_c012d6f2e6

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 666
- thinking modes present: think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_c012d6f2e6__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_c012d6f2e6__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_c012d6f2e6__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_c012d6f2e6__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-mini-2025-08-07 under prompt condition prompt_c012d6f2e6 (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_c012d6f2e6__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_c012d6f2e6__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c012d6f2e6` for the exact instructions and example statements.

#### prompt_c1b2be97aa

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 308
- thinking modes present: think-low
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_c1b2be97aa__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_c1b2be97aa__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_c1b2be97aa__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_c1b2be97aa__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-mini-2025-08-07 under prompt condition prompt_c1b2be97aa (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_c1b2be97aa__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_c1b2be97aa__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c1b2be97aa` for the exact instructions and example statements.

#### prompt_c6875730a1

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/exp6_horn_yesno.j2`
- total examples aggregated (all thinking×horn): 520
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_c6875730a1__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_c6875730a1__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_c6875730a1__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_c6875730a1__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-mini-2025-08-07 under prompt condition prompt_c6875730a1 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_c6875730a1__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-mini-2025-08-07/prompt_c6875730a1__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c6875730a1` for the exact instructions and example statements.

---

### openai/gpt-5-nano-2025-08-07

- Report PDF: `experiments/paper_outputs/figures/model_reports/openai__gpt-5-nano-2025-08-07.pdf`
- PNG directory: `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/`

#### prompt_0b276d34e8

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 650
- thinking modes present: nothink
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_0b276d34e8__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_0b276d34e8__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_0b276d34e8__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_0b276d34e8__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-nano-2025-08-07 under prompt condition prompt_0b276d34e8 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_0b276d34e8__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_0b276d34e8__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_0b276d34e8` for the exact instructions and example statements.

#### prompt_154dcb992a

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- total examples aggregated (all thinking×horn): 1
- thinking modes present: nothink
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_154dcb992a__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_154dcb992a__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_154dcb992a__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_154dcb992a__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-nano-2025-08-07 under prompt condition prompt_154dcb992a (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_154dcb992a__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_154dcb992a__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_154dcb992a` for the exact instructions and example statements.

#### prompt_21889a86a3

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 33
- thinking modes present: nothink
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_21889a86a3__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_21889a86a3__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_21889a86a3__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_21889a86a3__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-nano-2025-08-07 under prompt condition prompt_21889a86a3 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_21889a86a3__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_21889a86a3__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_21889a86a3` for the exact instructions and example statements.

#### prompt_2376d1fca7

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 8
- thinking modes present: nothink
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_2376d1fca7__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_2376d1fca7__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_2376d1fca7__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_2376d1fca7__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-nano-2025-08-07 under prompt condition prompt_2376d1fca7 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_2376d1fca7__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_2376d1fca7__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2376d1fca7` for the exact instructions and example statements.

#### prompt_2e9c5ccddf

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 28
- thinking modes present: nothink
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_2e9c5ccddf__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_2e9c5ccddf__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_2e9c5ccddf__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_2e9c5ccddf__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-nano-2025-08-07 under prompt condition prompt_2e9c5ccddf (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_2e9c5ccddf__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_2e9c5ccddf__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2e9c5ccddf` for the exact instructions and example statements.

#### prompt_62ba908560

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 527
- thinking modes present: nothink, think-high, think-low, think-medium
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_62ba908560__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_62ba908560__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_62ba908560__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_62ba908560__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-nano-2025-08-07 under prompt condition prompt_62ba908560 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_62ba908560__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_62ba908560__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_62ba908560` for the exact instructions and example statements.

#### prompt_73ecab0579

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- total examples aggregated (all thinking×horn): 3
- thinking modes present: nothink
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_73ecab0579__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_73ecab0579__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_73ecab0579__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_73ecab0579__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-nano-2025-08-07 under prompt condition prompt_73ecab0579 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_73ecab0579__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_73ecab0579__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_73ecab0579` for the exact instructions and example statements.

#### prompt_7b28aa32dc

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 761
- thinking modes present: nothink, think-high, think-low, think-medium
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_7b28aa32dc__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_7b28aa32dc__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_7b28aa32dc__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_7b28aa32dc__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-nano-2025-08-07 under prompt condition prompt_7b28aa32dc (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_7b28aa32dc__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_7b28aa32dc__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_7b28aa32dc` for the exact instructions and example statements.

#### prompt_c012d6f2e6

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 1010
- thinking modes present: nothink, think-high, think-low, think-medium
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_c012d6f2e6__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_c012d6f2e6__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_c012d6f2e6__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_c012d6f2e6__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-nano-2025-08-07 under prompt condition prompt_c012d6f2e6 (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_c012d6f2e6__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_c012d6f2e6__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c012d6f2e6` for the exact instructions and example statements.

#### prompt_c1b2be97aa

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 308
- thinking modes present: nothink
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_c1b2be97aa__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_c1b2be97aa__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_c1b2be97aa__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_c1b2be97aa__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-nano-2025-08-07 under prompt condition prompt_c1b2be97aa (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_c1b2be97aa__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_c1b2be97aa__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c1b2be97aa` for the exact instructions and example statements.

#### prompt_c6875730a1

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/exp6_horn_yesno.j2`
- total examples aggregated (all thinking×horn): 520
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_c6875730a1__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_c6875730a1__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_c6875730a1__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_c6875730a1__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-nano-2025-08-07 under prompt condition prompt_c6875730a1 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_c6875730a1__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-nano-2025-08-07/prompt_c6875730a1__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c6875730a1` for the exact instructions and example statements.

---

### openai/gpt-5-pro-2025-10-06

- Report PDF: `experiments/paper_outputs/figures/model_reports/openai__gpt-5-pro-2025-10-06.pdf`
- PNG directory: `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/`

#### prompt_21889a86a3

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 32
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_21889a86a3__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_21889a86a3__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_21889a86a3__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_21889a86a3__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-pro-2025-10-06 under prompt condition prompt_21889a86a3 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_21889a86a3__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_21889a86a3__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_21889a86a3` for the exact instructions and example statements.

#### prompt_2376d1fca7

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 8
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_2376d1fca7__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_2376d1fca7__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_2376d1fca7__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_2376d1fca7__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-pro-2025-10-06 under prompt condition prompt_2376d1fca7 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_2376d1fca7__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_2376d1fca7__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2376d1fca7` for the exact instructions and example statements.

#### prompt_2e9c5ccddf

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 28
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_2e9c5ccddf__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_2e9c5ccddf__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_2e9c5ccddf__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_2e9c5ccddf__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-pro-2025-10-06 under prompt condition prompt_2e9c5ccddf (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_2e9c5ccddf__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_2e9c5ccddf__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_2e9c5ccddf` for the exact instructions and example statements.

#### prompt_73ecab0579

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- total examples aggregated (all thinking×horn): 3
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_73ecab0579__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_73ecab0579__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_73ecab0579__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_73ecab0579__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-pro-2025-10-06 under prompt condition prompt_73ecab0579 (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_73ecab0579__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_73ecab0579__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_73ecab0579` for the exact instructions and example statements.

#### prompt_83b02d3a05

- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- prompt_template: `prompts/exp1_cnf_v1_contradiction.j2`
- total examples aggregated (all thinking×horn): 5
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_83b02d3a05__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_83b02d3a05__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_83b02d3a05__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_83b02d3a05__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-pro-2025-10-06 under prompt condition prompt_83b02d3a05 (prompt_style=cnf_v1). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_83b02d3a05__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_83b02d3a05__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_83b02d3a05` for the exact instructions and example statements.

#### prompt_c1b2be97aa

- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 307
- thinking modes present: think-high
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_c1b2be97aa__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_c1b2be97aa__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_c1b2be97aa__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_c1b2be97aa__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5-pro-2025-10-06 under prompt condition prompt_c1b2be97aa (prompt_style=horn_if_then). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_c1b2be97aa__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5-pro-2025-10-06/prompt_c1b2be97aa__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c1b2be97aa` for the exact instructions and example statements.

---

### openai/gpt-5.2

- Report PDF: `experiments/paper_outputs/figures/model_reports/openai__gpt-5.2.pdf`
- PNG directory: `experiments/paper_outputs/figures/png/openai__gpt-5.2/`

#### prompt_c012d6f2e6

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 2
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5.2/prompt_c012d6f2e6__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5.2/prompt_c012d6f2e6__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5.2/prompt_c012d6f2e6__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5.2/prompt_c012d6f2e6__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5.2 under prompt condition prompt_c012d6f2e6 (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5.2/prompt_c012d6f2e6__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5.2/prompt_c012d6f2e6__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c012d6f2e6` for the exact instructions and example statements.

---

### openai/gpt-5.2-pro-2025-12-11

- Report PDF: `experiments/paper_outputs/figures/model_reports/openai__gpt-5.2-pro-2025-12-11.pdf`
- PNG directory: `experiments/paper_outputs/figures/png/openai__gpt-5.2-pro-2025-12-11/`

#### prompt_c012d6f2e6

- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- prompt_template: `prompts/_template_unified.j2`
- total examples aggregated (all thinking×horn): 151
- thinking modes present: n/a
- horn flags present: n/a

Figure pages (PNG):

- `experiments/paper_outputs/figures/png/openai__gpt-5.2-pro-2025-12-11/prompt_c012d6f2e6__accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5.2-pro-2025-12-11/prompt_c012d6f2e6__sat_accuracy.png`
- `experiments/paper_outputs/figures/png/openai__gpt-5.2-pro-2025-12-11/prompt_c012d6f2e6__unsat_accuracy.png`

Captions (copy/paste starting points):

- **Overall accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5.2-pro-2025-12-11/prompt_c012d6f2e6__accuracy.png`): Heatmaps of overall accuracy (correct/total) for openai/gpt-5.2-pro-2025-12-11 under prompt condition prompt_c012d6f2e6 (prompt_style=cnf_v2). Each column corresponds to a thinking_mode and each row corresponds to the horn flag. Axes are maxvars (y) and maxlen (x).
- **Satisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5.2-pro-2025-12-11/prompt_c012d6f2e6__sat_accuracy.png`): Heatmaps of accuracy restricted to satisfiable ground-truth instances (satflag=1), for the same model/prompt condition and faceting as above.
- **Unsatisfiable accuracy** (`experiments/paper_outputs/figures/png/openai__gpt-5.2-pro-2025-12-11/prompt_c012d6f2e6__unsat_accuracy.png`): Heatmaps of accuracy restricted to unsatisfiable/contradiction ground-truth instances (satflag=0), for the same model/prompt condition and faceting as above.

Prompt reference: see `experiments/paper_outputs/prompts/prompt_catalog.md` section `prompt_c012d6f2e6` for the exact instructions and example statements.

---

