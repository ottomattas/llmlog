# Dashboard Design — Unified LLM Logic Reasoning Analysis

> **Status**: Planning document. Use this after experiments are complete.

## Overview

This document describes the design for a unified analysis dashboard that will compare ~12 LLM models across multiple logic reasoning experiments. The dashboard will answer 6 core research questions and provide interactive visualizations of model performance and degradation patterns.

---

## Experimental Setup

### Dataset Specifications

**Datasets**:

1. **Validation Dataset** (for initial testing):
   - Variables: 1-20, Clause length: 1-5
   - **5 per case** → **1,000 problems** total
   - Purpose: Validate configs, get initial results, discuss with supervisors
   - Cost: ~$150-$250, Time: ~8-12 hours

2. **Production Dataset** (for publication):
   - Variables: 1-20, Clause length: 1-5
   - **40 per case** → **8,000 problems** total
   - Purpose: Publication-quality statistics, robust analysis
   - Balance: 4,000 Horn + 4,000 non-Horn, 4,000 Sat + 4,000 Unsat
   - Granularity: 400 problems per variable level
   - Cost: ~$2,400-$4,000, Time: ~66-96 hours (3-4 days)

**Reference** (existing `dist20` dataset):
- 1040 problems
- 520 Horn + 520 Non-Horn
- 520 Sat + 520 Unsat
- Variables: 3-15 (80 problems each)
- Clause length: 3-4

### Model Configuration

**12 Fixed Models** (same across all experiments):

| Tier | Provider | Model | Thinking Config |
|------|----------|-------|----------------|
| **Tier 1: Flagship (High Thinking)** | | | |
| 1 | Anthropic | claude-sonnet-4-5-20250929 | enabled, budget=24576 |
| 2 | Google | gemini-2.5-pro | enabled, budget=24576 |
| 3 | OpenAI | gpt-5-pro-2025-10-06 | enabled, effort=high |
| **Tier 2: Medium (Medium Thinking)** | | | |
| 4 | Anthropic | claude-opus-4-1-20250805 | enabled, budget=8192 |
| 5 | Google | gemini-2.5-flash | enabled, budget=8192 |
| 6 | OpenAI | gpt-5-2025-08-07 | enabled, effort=medium |
| **Tier 3: Budget (Low Thinking)** | | | |
| 7 | Anthropic | claude-haiku-4-5-20251001 | enabled, budget=1024 |
| 8 | Google | gemini-2.5-flash-lite | enabled, budget=1024 |
| 9 | OpenAI | gpt-5-mini-2025-08-07 | enabled, effort=low |
| **Tier 3: Budget (No Thinking)** | | | |
| 10 | Anthropic | claude-haiku-4-5-20251001 | disabled |
| 11 | Google | gemini-2.5-flash | disabled |
| 12 | OpenAI | gpt-5-nano-2025-08-07 | disabled |

### Experimental Dimensions

**Representation Styles**:
- `horn_if_then`: Facts (`p1.`) and rules (`if p2 and p3 then p4.`)
- `cnf_v1`: Verbose CNF (`p1 is true or p2 is false.`)
- `cnf_v2`: Compact CNF (`p1 or not(p2).`)

**Tasks**:
- `yes_no`: For Horn problems (Is p0 derivable?)
- `contradiction`: For CNF problems (Is the set contradictory?)

**Filters**:
- `horn_only: true` — Only Horn problems (520 problems)
- `horn_only: false` — Mixed (all 1040 problems)

### Experiment Matrix

**Recommended Experiments** (6-8 total):

| # | Name | Representation | Task | Filter | Purpose |
|---|------|----------------|------|--------|---------|
| 1 | `horn_yn_hornonly` | `horn_if_then` | `yes_no` | `horn_only: true` | Baseline: Horn on Horn problems |
| 2 | `horn_yn_mixed` | `horn_if_then` | `yes_no` | `horn_only: false` | Mismatch: Horn repr on non-Horn problems |
| 3 | `cnf1_con_mixed` | `cnf_v1` | `contradiction` | `horn_only: false` | Verbose CNF on all problems |
| 4 | `cnf2_con_mixed` | `cnf_v2` | `contradiction` | `horn_only: false` | Compact CNF on all problems |
| 5 | `cnf1_con_hornonly` | `cnf_v1` | `contradiction` | `horn_only: true` | Verbose CNF on Horn subset |
| 6 | `cnf2_con_hornonly` | `cnf_v2` | `contradiction` | `horn_only: true` | Compact CNF on Horn subset |

**Optional Additional**:
- Different datasets (vary complexity ranges)
- Temperature variations
- Prompt variations (with/without examples)

---

## Research Questions

### RQ1: Does Representation Matter?

**Question**: How does the choice of representation (horn_if_then vs cnf_v1 vs cnf_v2) affect model accuracy?

**Hypothesis**: 
- `horn_if_then` should work best for Horn problems
- CNF representations (`cnf_v1`, `cnf_v2`) should be more general
- `cnf_v1` (verbose) might be easier than `cnf_v2` (compact)

**Analysis**:
```
Compare experiments on same problem subset:
- exp1 (horn+yn+hornonly) vs exp5 (cnf1+con+hornonly) vs exp6 (cnf2+con+hornonly)
- All on same 520 Horn problems
- Group by model tier

Metrics:
- Overall accuracy per representation
- Accuracy by complexity level (vars)
- Statistical significance tests
```

**Expected Finding**: Representation choice affects accuracy by 5-10%, with task-appropriate representations performing best.

---

### RQ2: Can Models Handle Representation Mismatch?

**Question**: What happens when we use Horn representation on non-Horn problems?

**Hypothesis**: 
- Models will show significant accuracy penalty (10-15%)
- Some problems will be unparseable (error rate increases)
- Flagship models may handle mismatch better than budget models

**Analysis**:
```
Compare:
- exp1 (horn+yn+hornonly): Horn repr on Horn problems only
- exp2 (horn+yn+mixed): Horn repr on ALL problems (including non-Horn)

For each model, compute:
- Accuracy on Horn subset (should be similar)
- Accuracy on non-Horn subset (expect failure)
- Overall penalty from mismatch

Cross-reference with:
- exp3 (cnf1+con+mixed): Proper handling of non-Horn
```

**Expected Finding**: All models show ~10-15% penalty when representation doesn't match problem structure. Non-Horn problems may cause parsing errors or random guessing.

---

### RQ3: When Do Models Break Down?

**Question**: At what complexity threshold (variables, clause length) does accuracy drop below usable levels (90%, 75%, 50%)?

**Hypothesis**:
- All models degrade as complexity increases
- Flagship models maintain accuracy longer
- Budget models hit 50% threshold at ~7-9 variables
- Extended thinking extends the threshold by 1-2 variables

**Analysis**:
```
For each experiment and model:
1. Group results by maxvars (3, 4, 5, ..., 15)
2. Compute accuracy per group
3. Identify threshold variables:
   - Where accuracy drops below 90%
   - Where accuracy drops below 75%
   - Where accuracy drops below 50%

Generate degradation curves:
- X-axis: maxvars
- Y-axis: accuracy
- One line per model
- Horizontal threshold lines at 90%, 75%, 50%

Also analyze by:
- Clause length (maxlen)
- Proof depth (for provable problems)
```

**Expected Finding**: 
- Flagship: >90% up to 10-11 vars, >75% up to 13-14 vars
- Medium: >90% up to 8-9 vars, >75% up to 11-12 vars
- Budget+thinking: >90% up to 6-7 vars, >75% up to 9-10 vars
- Budget no-thinking: >90% up to 5-6 vars, >75% up to 7-8 vars

---

### RQ4: Is Extended Thinking Worth It?

**Question**: Does enabling extended thinking justify the cost (2-3× inference cost)?

**Hypothesis**:
- Thinking provides minimal benefit on simple problems (≤6 vars)
- Thinking provides 3-5% boost on medium complexity (7-10 vars)
- Thinking provides 5-8% boost on high complexity (>10 vars)
- Cost-benefit depends on accuracy requirements

**Analysis**:
```
Compare same models with/without thinking:
- Model 10 (Haiku no-think) vs Model 7 (Haiku low-think)
- Model 11 (Flash no-think) vs Model 8 (Flash-Lite low-think)
- Model 12 (Nano no-think) vs Model 9 (Mini low-think)

For each complexity bucket (vars 3-6, 7-10, 11-15):
- Compute accuracy delta (thinking - no-thinking)
- Compute cost per correct answer
- Determine break-even threshold

Also compare across thinking levels:
- Low vs Medium vs High thinking (within same provider)
```

**Expected Finding**: 
- Simple problems (≤6 vars): +1-2% (not worth it)
- Medium problems (7-10 vars): +3-5% (worth it if accuracy critical)
- Complex problems (>10 vars): +5-8% (definitely worth it)
- Thinking extends usable complexity range by ~2 variables

---

### RQ5: Which Tier Should I Use?

**Question**: What's the accuracy-cost trade-off across model tiers?

**Hypothesis**:
- Flagship models: Highest accuracy, highest cost, best for critical tasks
- Medium models: Best cost/accuracy ratio for most use cases
- Budget models: Acceptable for simple problems only

**Analysis**:
```
For each tier, aggregate across all experiments:
- Average overall accuracy
- Accuracy by complexity level
- Degradation threshold (vars at 75%, 50%)
- Cost per 1K inferences (based on provider pricing)
- Cost per correct answer = cost / (accuracy × problems)

Tier comparison table:
Tier      Avg Acc   <75% at   Cost/1K   Cost/Correct   Use Case
────────  ────────  ────────  ────────  ─────────────  ──────────
Flagship   97-99%   13+ vars   $3.00       $3.07       Critical
Medium     94-96%   11-12 v    $1.50       $1.59       General
Low+think  89-92%    9-10 v    $0.60       $0.67       Budget
No-think   85-88%    7-8 v     $0.30       $0.35       Simple only
```

**Expected Finding**: Medium tier offers best cost/accuracy trade-off. Flagship only needed for vars >12. Budget adequate for vars ≤6.

---

### RQ6: Which Model Is Best for What?

**Question**: Are there task-specific model strengths? Do different models excel at different representations or problem types?

**Hypothesis**:
- Different providers have different strengths
- Some models better at symbolic reasoning (CNF)
- Some models better at goal-directed reasoning (Horn)

**Analysis**:
```
For each experiment, rank all 12 models by accuracy:
1. Overall ranking
2. Ranking by problem type (Horn vs non-Horn)
3. Ranking by complexity level

Cross-tabulate:
Experiment          Best Model    2nd Best       3rd Best
──────────────────  ────────────  ─────────────  ─────────
horn_yn_hornonly    GPT-5-Pro     Sonnet-4.5     Gemini-Pro
horn_yn_mixed       GPT-5-Pro     Sonnet-4.5     Opus-4
cnf1_con_mixed      Gemini-Pro    GPT-5-Pro      Sonnet-4.5
cnf2_con_mixed      GPT-5-Pro     Sonnet-4.5     Gemini-Pro
...

Compute "win rate" per model:
- How often does each model rank in top 3?
- How often is each model THE best?

Identify specializations:
- Which model is best for Horn problems?
- Which model is best for CNF problems?
- Which model is most versatile (consistent across all)?
```

**Expected Finding**: 
- GPT-5-Pro: Most versatile, strong across all tasks
- Sonnet-4.5: Best on complex Horn problems
- Gemini-Pro: Best on verbose CNF (cnf_v1)
- Each provider has specific strengths

---

## Dashboard Structure

### Single-Page Interactive HTML

**Layout Overview**:
```
┌─────────────────────────────────────────────────────┐
│  Header: Title, Filters, Export                     │
├─────────────────────────────────────────────────────┤
│  Section 1: Overview Heatmap                        │
│  (Experiment × Model grid, color-coded accuracy)    │
├─────────────────────────────────────────────────────┤
│  Section 2: Degradation Curves                      │
│  (Interactive plot, toggle models, select metric)   │
├─────────────────────────────────────────────────────┤
│  Section 3: Research Questions Analysis             │
│  (6 sub-sections, one per RQ, with tables/charts)   │
├─────────────────────────────────────────────────────┤
│  Section 4: Detailed Breakdowns                     │
│  (Tabs: By Experiment, By Model, By Complexity)     │
└─────────────────────────────────────────────────────┘
```

### Section 1: Overview Heatmap

**Purpose**: Provide at-a-glance comparison of all models across all experiments.

**Design**:
- Rows: Experiments (6-8 rows)
- Columns: Models (12 columns)
- Cells: Color-coded by accuracy
  - 🟩 Green (>90%): Excellent
  - 🟨 Yellow (75-90%): Good
  - 🟧 Orange (50-75%): Struggling
  - 🟥 Red (<50%): Failed
- Click cell → jump to degradation curve for that model+experiment

**Interactivity**:
- Sort by: experiment name, avg accuracy, etc.
- Filter by: tier, provider, thinking enabled/disabled
- Highlight: best model per row, best experiment per column

### Section 2: Degradation Curves

**Purpose**: Visualize how accuracy degrades as problem complexity increases.

**Design**:
- Dropdown: Select experiment
- Plot: All 12 models overlaid
  - X-axis: Complexity metric (maxvars, maxlen, or depth)
  - Y-axis: Accuracy (0-100%)
  - Lines: One per model, color by provider, style by tier
  - Thresholds: Horizontal lines at 90%, 75%, 50%

**Interactivity**:
- Toggle models on/off (checkboxes)
- Switch metric: maxvars, maxlen, depth (radio buttons)
- Hover: Show exact values
- Zoom: Drag to zoom into complexity range

**Color Scheme**:
- Anthropic: Pink/Red
- Google: Blue
- OpenAI: Green

**Line Styles**:
- Solid: Tier 1 (flagship)
- Dashed: Tier 2 (medium)
- Dotted: Tier 3 (budget)
- Thin: No thinking

### Section 3: Research Questions Analysis

**Sub-section per RQ**:

Each RQ gets a collapsible section with:
- **Question statement** (bold)
- **Summary finding** (1-2 sentences)
- **Data table** (key metrics)
- **Mini-chart** (if applicable)
- **Interpretation** (bullet points)

**RQ1**: Representation comparison table
**RQ2**: Mismatch penalty table
**RQ3**: Threshold analysis table + mini degradation curve
**RQ4**: Thinking benefit table by complexity
**RQ5**: Tier comparison table with cost analysis
**RQ6**: Model rankings and win-rate matrix

### Section 4: Detailed Breakdowns

**Tabs**:

**Tab 1: By Experiment**
- Select experiment from dropdown
- Show detailed breakdown:
  - Model ranking table
  - Accuracy by complexity level
  - Sat vs Unsat accuracy
  - Horn vs non-Horn accuracy (if mixed)
  - Error analysis (unclear answers, parse failures)

**Tab 2: By Model**
- Select model from dropdown
- Show across all experiments:
  - Performance summary table
  - Best/worst experiments
  - Degradation curve (overlay all experiments)
  - Strengths/weaknesses

**Tab 3: By Complexity**
- Select complexity level (vars 3-15)
- Show accuracy of all models at that level
- Compare across experiments
- Identify which models remain reliable

**Tab 4: Export**
- Export heatmap as PNG/SVG
- Export degradation curves as PNG/SVG
- Export all tables as CSV
- Generate LaTeX tables for paper
- Download summary report as Markdown/PDF

---

## Data Requirements

### Input Files

After experiments are complete, the dashboard expects:

```
experiments/runs/
├── horn_yn_hornonly/
│   └── <run_id>/
│       ├── anthropic/
│       │   ├── claude-sonnet-4-5-20250929/
│       │   │   ├── results.jsonl
│       │   │   └── results.summary.json
│       │   ├── claude-opus-4-1-20250805/
│       │   │   └── ...
│       │   └── ... (all Anthropic models)
│       ├── google/
│       │   └── ... (all Google models)
│       └── openai/
│           └── ... (all OpenAI models)
│
├── horn_yn_mixed/
│   └── ... (same structure)
│
├── cnf1_con_mixed/
│   └── ... (same structure)
│
└── ... (all experiments)
```

### Required Data Schema

**results.jsonl** (one JSON object per line):
```json
{
  "id": 1,
  "meta": {
    "maxvars": 3,
    "maxlen": 3,
    "horn": 1,
    "satflag": 0,
    "proof": [...]
  },
  "parsed_answer": 0,
  "correct": true,
  "provider": "anthropic",
  "model": "claude-sonnet-4-5-20250929",
  "timing_ms": 1234,
  "usage": {
    "input_tokens": 100,
    "output_tokens": 50,
    "reasoning_tokens": 200
  }
}
```

**results.summary.json**:
```json
{
  "total": 520,
  "correct": 486,
  "accuracy": 0.9346,
  "unclear": 5,
  "avg_timing_ms": 2145
}
```

---

## Implementation Tools

### Tool 1: `experiments/analyze_matrix.py`

**Purpose**: Aggregate results from all experiments and compute metrics.

**Usage**:
```bash
python -m experiments.analyze_matrix \
  --runs-dir experiments/runs \
  --output experiments/aggregated_results.json
```

**Functionality**:
- Scan all result files
- Load and validate data
- Compute aggregated metrics:
  - Overall accuracy per model per experiment
  - Accuracy by complexity level (vars, length, depth)
  - Threshold analysis (where accuracy drops below 90%, 75%, 50%)
  - Error rates (unclear, incorrect)
- Answer each RQ with specific computations
- Output comprehensive JSON for dashboard

**Output Schema**:
```json
{
  "metadata": {
    "generated": "2025-10-15T12:00:00",
    "total_experiments": 6,
    "total_models": 12,
    "total_problems": 1040
  },
  "experiments": {
    "horn_yn_hornonly": {
      "models": {
        "anthropic/claude-sonnet-4-5-20250929": {
          "overall_accuracy": 0.98,
          "accuracy_by_vars": {3: 1.0, 4: 1.0, ...},
          "thresholds": {90: 10, 75: 13, 50: null},
          ...
        },
        ...
      }
    },
    ...
  },
  "research_questions": {
    "rq1": {...},
    "rq2": {...},
    ...
  }
}
```

### Tool 2: `experiments/generate_dashboard.py`

**Purpose**: Generate interactive HTML dashboard from aggregated results.

**Usage**:
```bash
python -m experiments.generate_dashboard \
  --input experiments/aggregated_results.json \
  --output experiments/dashboard.html
```

**Functionality**:
- Load aggregated JSON
- Generate HTML with embedded CSS and JavaScript
- Create interactive components:
  - Heatmap (D3.js or Plotly)
  - Degradation curves (Plotly)
  - Tables (DataTables.js)
  - Filters and toggles
- Embed all data inline (single file)
- Responsive design

**Libraries**:
- Plotly.js for plots
- DataTables.js for tables
- Bootstrap for layout
- Custom CSS for styling

### Tool 3: `experiments/export_results.py`

**Purpose**: Export dashboard components for papers/presentations.

**Usage**:
```bash
python -m experiments.export_results \
  --input experiments/aggregated_results.json \
  --format latex \
  --output results_tables.tex

python -m experiments.export_results \
  --input experiments/aggregated_results.json \
  --format csv \
  --output results_tables.csv

python -m experiments.export_results \
  --input experiments/aggregated_results.json \
  --format markdown \
  --output RESULTS_SUMMARY.md
```

**Functionality**:
- Generate publication-ready tables
- Export plots as high-res PNG/SVG
- Create summary report
- Format for specific venues (ACL, NeurIPS, etc.)

---

## Workflow

### 1. Setup Phase (Before Running Experiments)

```bash
# 1. Generate new problem dataset
python -m experiments.makeproblems \
  --vars 1-20 \
  --len 1-5 \
  --count 2000 \
  --seed 4242 \
  --output data/problems_complex_v2.js

# 2. Create experiment configs (copy template for each)
cp experiments/configs/_template_unified.yaml \
   experiments/configs/horn_yn_hornonly.yaml

# Edit each config:
# - Set name
# - Set input_file
# - Set prompt style and task
# - Set filters
# - Keep all 12 targets identical across all configs

# 3. Review prompts
# Ensure prompts/_template_unified.j2 is appropriate
# Or create experiment-specific prompts if needed
```

### 2. Execution Phase

```bash
# Run all experiments
for config in experiments/configs/horn_*.yaml experiments/configs/cnf*.yaml; do
  python -m experiments.runner \
    --config "$config" \
    --resume \
    --run production_001
done

# Monitor progress
tail -f experiments/runs/*/production_001/*/*/results.summary.json
```

### 3. Analysis Phase (Use This Dashboard Design)

```bash
# 1. Aggregate all results
python -m experiments.analyze_matrix \
  --runs-dir experiments/runs \
  --run-id production_001 \
  --output experiments/aggregated_results.json

# 2. Generate dashboard
python -m experiments.generate_dashboard \
  --input experiments/aggregated_results.json \
  --output experiments/dashboard.html

# 3. Open and explore
open experiments/dashboard.html

# 4. Export for paper
python -m experiments.export_results \
  --input experiments/aggregated_results.json \
  --format latex \
  --output paper_tables.tex
```

---

## Expected Outcomes

### Quantitative Results

**Accuracy Ranges** (predicted):
- Flagship models: 95-100% (simple), 85-95% (complex)
- Medium models: 90-98% (simple), 80-90% (complex)
- Budget+think: 85-95% (simple), 70-85% (complex)
- Budget no-think: 80-92% (simple), 65-80% (complex)

**Degradation Thresholds** (predicted):
- All models maintain >90% accuracy up to 6-8 variables
- Flagship models maintain >75% up to 12-14 variables
- Budget models drop below 75% at 8-10 variables
- Non-Horn problems ~10% harder than Horn problems

### Qualitative Insights

**Representation Effects**:
- Horn representation fails on non-Horn problems (expected)
- CNF representations work on all problems but may be less efficient
- Compact CNF (v2) potentially harder than verbose (v1)

**Thinking Value**:
- Minimal benefit on simple problems (<6 vars)
- Significant benefit on complex problems (>10 vars)
- Cost justified only for accuracy-critical applications

**Model Specializations**:
- Provider-specific strengths (e.g., Gemini for CNF, GPT for Horn)
- Some models more robust to representation mismatch
- Flagship models more versatile than budget models

---

## Publication Plan

### Conference Paper Structure

**Title**: "Systematic Evaluation of LLM Logical Reasoning: Representation, Complexity, and Extended Thinking"

**Sections**:
1. Introduction
2. Related Work
3. Experimental Design
   - Problem dataset
   - Model configurations
   - Experimental dimensions
4. Results
   - RQ1: Representation matters
   - RQ2: Mismatch handling
   - RQ3: Degradation thresholds
   - RQ4: Thinking cost-benefit
   - RQ5: Tier comparison
   - RQ6: Model specializations
5. Discussion
6. Conclusion

**Figures** (from dashboard):
- Figure 1: Overview heatmap
- Figure 2: Degradation curves (4-panel, by experiment type)
- Figure 3: Thinking benefit by complexity
- Table 1: Model configurations
- Table 2: Threshold analysis
- Table 3: Cost-benefit analysis
- Table 4: Model rankings

**Contributions**:
- Largest systematic study of LLM logical reasoning (12 models × 6-8 experiments)
- First comparison of extended thinking across providers
- Novel analysis of representation mismatch effects
- Practical guidance for model selection

---

## Next Steps

### Before Running Experiments

- [ ] Generate new problem dataset with desired parameters
- [ ] Create 6-8 experiment configs (one per combination)
- [ ] Review and finalize prompt templates
- [ ] Validate runner setup with small test (--limit 10)
- [ ] Estimate cost and time (12 models × 6 experiments × 1000 problems)

### After Experiments Complete

- [ ] Implement `analyze_matrix.py`
- [ ] Implement `generate_dashboard.py`
- [ ] Implement `export_results.py`
- [ ] Generate dashboard and explore results
- [ ] Answer each RQ systematically
- [ ] Write paper draft
- [ ] Create presentation slides

### Optional Enhancements

- [ ] Add statistical significance tests (t-tests, bootstrap)
- [ ] Include confidence intervals on all metrics
- [ ] Add cost tracking and ROI analysis
- [ ] Create interactive drill-down for specific problems
- [ ] Generate problem-level heatmaps (which problems are hardest?)
- [ ] Add model agreement analysis (where do models disagree?)

---

## Questions to Resolve

Before running experiments, decide:

1. **Dataset size**: 1000 vs 2000 vs 5000 problems?
2. **Variable range**: Up to 15 vars (like dist20) or up to 20 vars (harder)?
3. **Experiments**: Run all 6 recommended, or add more variants?
4. **Cost**: Estimate total API cost (12 models × 6 exps × N problems)?
5. **Time**: How long will experiments take? (Concurrency settings)
6. **Validation**: Test on small subset first to validate setup?

---

## Appendix: Quick Reference

### Model Nicknames (for plots/tables)

| Full Name | Nickname | Tier |
|-----------|----------|------|
| claude-sonnet-4-5-20250929 | Sonnet-4.5 | T1 |
| gemini-2.5-pro | Gemini-Pro | T1 |
| gpt-5-pro-2025-10-06 | GPT-5-Pro | T1 |
| claude-opus-4-1-20250805 | Opus-4 | T2 |
| gemini-2.5-flash | Flash | T2 |
| gpt-5-2025-08-07 | GPT-5 | T2 |
| claude-haiku-4-5-20251001 (think) | Haiku+ | T3 |
| gemini-2.5-flash-lite (think) | Flash-Lite+ | T3 |
| gpt-5-mini-2025-08-07 | GPT-5-Mini | T3 |
| claude-haiku-4-5-20251001 (no-think) | Haiku | T3 |
| gemini-2.5-flash (no-think) | Flash- | T3 |
| gpt-5-nano-2025-08-07 | Nano | T3 |

### Experiment Nicknames

| Config Name | Nickname | Description |
|-------------|----------|-------------|
| horn_yn_hornonly | H-YN-HO | Horn repr, yes/no, Horn problems only |
| horn_yn_mixed | H-YN-MX | Horn repr, yes/no, all problems |
| cnf1_con_mixed | C1-CON-MX | Verbose CNF, contradiction, all |
| cnf2_con_mixed | C2-CON-MX | Compact CNF, contradiction, all |
| cnf1_con_hornonly | C1-CON-HO | Verbose CNF, contradiction, Horn only |
| cnf2_con_hornonly | C2-CON-HO | Compact CNF, contradiction, Horn only |

---

**Document Version**: 1.0  
**Last Updated**: 2025-10-15  
**Status**: Ready for use after experiments complete  

