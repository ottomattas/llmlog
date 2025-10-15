# Experiments — Planning and Execution Guide

This directory contains the experimental framework for systematic LLM logic reasoning evaluation.

---

## Quick Links

### 🚀 Start Here
- **[GETTING_STARTED.md](GETTING_STARTED.md)** — Quick overview and 3-step plan (START HERE!)

### Planning Documents
- **[VALIDATION_WORKFLOW.md](VALIDATION_WORKFLOW.md)** — Two-phase approach: validation → production (RECOMMENDED)
- **[DATASET_GENERATION.md](DATASET_GENERATION.md)** — How to generate validation and production datasets
- **[EXPERIMENT_CHECKLIST.md](EXPERIMENT_CHECKLIST.md)** — Step-by-step execution checklist
- **[DASHBOARD_DESIGN.md](DASHBOARD_DESIGN.md)** — Complete dashboard design and 6 research questions

### Implementation Tools
- `runner.py` — Generic experiment executor (config-driven)
- `analyze_generic.py` — Basic result analysis
- `schema.py` — Data schema definitions

### To Be Implemented (After Results)
- `analyze_matrix.py` — Aggregate analysis across all experiments (see DASHBOARD_DESIGN.md)
- `generate_dashboard.py` — Interactive HTML dashboard generator (see DASHBOARD_DESIGN.md)
- `export_results.py` — Export tables/figures for publication (see DASHBOARD_DESIGN.md)

---

## Workflow Overview

### Phase 1: Planning (Current Phase)

1. ✅ Review **DASHBOARD_DESIGN.md** to understand:
   - 6 core research questions
   - Experimental design (6 experiments × 12 models)
   - Expected dashboard structure
   - Analysis approach

2. ✅ Read **VALIDATION_WORKFLOW.md** for the two-phase strategy:
   - Phase 1: Validation dataset (1,000 problems, ~$150-250)
   - Phase 2: Production dataset (8,000 problems, ~$2,400-4,000)
   - Why this approach saves money and reduces risk

3. ✅ Follow **DATASET_GENERATION.md** to:
   - Generate validation dataset (5 per case)
   - Understand dataset structure and verification

4. ✅ Follow **EXPERIMENT_CHECKLIST.md** to:
   - Create 6 experiment configs
   - Set up and validate with small test

### Phase 2: Execution

3. Run experiments:
   ```bash
   python -m experiments.runner \
     --config experiments/configs/<config>.yaml \
     --resume --run production_001
   ```

4. Monitor and validate results

### Phase 3: Analysis (After Results)

5. Implement analysis tools (see DASHBOARD_DESIGN.md Section "Implementation Tools")

6. Generate dashboard:
   ```bash
   python -m experiments.analyze_matrix --runs-dir experiments/runs --output aggregated_results.json
   python -m experiments.generate_dashboard --input aggregated_results.json --output dashboard.html
   ```

7. Explore results and answer research questions

### Phase 4: Publication

8. Export results:
   ```bash
   python -m experiments.export_results --format latex --output paper_tables.tex
   ```

9. Write paper using exported tables and figures

---

## Directory Structure

```
experiments/
├── DASHBOARD_DESIGN.md          ← 📘 Complete design and RQ definitions
├── EXPERIMENT_CHECKLIST.md      ← ✅ Step-by-step execution guide
├── README.md                     ← 📄 This file
│
├── configs/                      ← Experiment configurations
│   ├── _template_unified.yaml   ← Template for new experiments
│   ├── horn_yn_hornonly.yaml    ← To be created
│   ├── horn_yn_mixed.yaml        ← To be created
│   └── ... (6 configs total)
│
├── runs/                         ← Experiment results (gitignored)
│   └── <experiment>/
│       └── <run_id>/
│           └── <provider>/<model>/
│               ├── results.jsonl
│               └── results.summary.json
│
├── runner.py                     ← ✅ Implemented
├── analyze_generic.py            ← ✅ Implemented
├── schema.py                     ← ✅ Implemented
│
├── analyze_matrix.py             ← ⏳ To implement (see DASHBOARD_DESIGN.md)
├── generate_dashboard.py         ← ⏳ To implement (see DASHBOARD_DESIGN.md)
└── export_results.py             ← ⏳ To implement (see DASHBOARD_DESIGN.md)
```

---

## Experimental Design Summary

(See DASHBOARD_DESIGN.md for full details)

### 12 Fixed Models (Same Across All Experiments)

| Tier | Models | Thinking |
|------|--------|----------|
| T1 Flagship | Sonnet-4.5, Gemini-Pro, GPT-5-Pro | High |
| T2 Medium | Opus-4, Flash, GPT-5 | Medium |
| T3 Budget | Haiku+, Flash-Lite+, GPT-5-Mini | Low |
| T3 No-Think | Haiku, Flash-, Nano | None |

### 6 Recommended Experiments

| # | Name | Representation | Task | Filter | Purpose |
|---|------|----------------|------|--------|---------|
| 1 | horn_yn_hornonly | horn_if_then | yes_no | horn_only | Baseline |
| 2 | horn_yn_mixed | horn_if_then | yes_no | mixed | Mismatch test |
| 3 | cnf1_con_mixed | cnf_v1 | contradiction | mixed | Verbose CNF |
| 4 | cnf2_con_mixed | cnf_v2 | contradiction | mixed | Compact CNF |
| 5 | cnf1_con_hornonly | cnf_v1 | contradiction | horn_only | CNF on Horn |
| 6 | cnf2_con_hornonly | cnf_v2 | contradiction | horn_only | CNF on Horn |

### 6 Research Questions

1. **Does representation matter?** — How does horn_if_then vs cnf_v1 vs cnf_v2 affect accuracy?
2. **Can models handle mismatch?** — What happens when representation doesn't match problem type?
3. **When do models break down?** — At what complexity (vars) does accuracy drop below 90%/75%/50%?
4. **Is extended thinking worth it?** — Does 2-3× cost justify accuracy gains?
5. **Which tier should I use?** — What's the cost/accuracy trade-off?
6. **Which model is best for what?** — Are there task-specific model strengths?

---

## Key Concepts

### Representation (Prompt Style)

How problems are rendered in text:

- **`horn_if_then`**: Facts and rules
  ```
  p1.
  if p2 and p3 then p4.
  ```

- **`cnf_v1`**: Verbose CNF
  ```
  p1 is true or p2 is false.
  ```

- **`cnf_v2`**: Compact CNF
  ```
  p1 or not(p2).
  ```

### Task (What We Ask)

- **`yes_no`**: Is p0 derivable? (for Horn problems)
- **`contradiction`**: Is the set contradictory? (for CNF problems)

### Filters

- **`horn_only: true`**: Only use Horn problems from dataset
- **`horn_only: false`**: Use all problems (Horn + non-Horn)

---

## Running Experiments

### Single Experiment

```bash
python -m experiments.runner \
  --config experiments/configs/horn_yn_hornonly.yaml \
  --resume \
  --run production_001
```

### Options

- `--limit N` — Only process first N problems (for testing)
- `--dry-run` — Print prompts without calling APIs
- `--resume` — Skip already-processed problems
- `--only anthropic,openai` — Only run specific providers
- `--run <id>` — Set run ID (default: timestamp)

### Monitoring

```bash
# Watch progress
tail -f experiments/runs/*/production_001/*/*/results.summary.json

# Count completed models
find experiments/runs -name "results.summary.json" | wc -l

# Check average accuracy
jq -s 'map(.accuracy) | add/length' experiments/runs/*/*/*/*/results.summary.json
```

---

## After Experiments Complete

### 1. Implement Analysis Tools

See DASHBOARD_DESIGN.md Section "Implementation Tools" for specifications:

**`analyze_matrix.py`**:
- Load all result files
- Compute aggregated metrics
- Answer each research question
- Output JSON for dashboard

**`generate_dashboard.py`**:
- Load aggregated JSON
- Generate interactive HTML
- Include heatmap, degradation curves, RQ analysis

**`export_results.py`**:
- Export tables as LaTeX/CSV/Markdown
- Export plots as PNG/SVG
- Generate summary report

### 2. Generate Dashboard

```bash
python -m experiments.analyze_matrix \
  --runs-dir experiments/runs \
  --run-id production_001 \
  --output aggregated_results.json

python -m experiments.generate_dashboard \
  --input aggregated_results.json \
  --output dashboard.html

open dashboard.html
```

### 3. Explore Results

Dashboard sections:
1. Overview heatmap (all models × all experiments)
2. Degradation curves (interactive, toggle models)
3. Research questions analysis (6 sections)
4. Detailed breakdowns (by experiment, by model, by complexity)

### 4. Export for Publication

```bash
python -m experiments.export_results \
  --input aggregated_results.json \
  --format latex \
  --output paper_tables.tex
```

---

## Cost Estimation

**Per API Call** (approximate):
- Tier 1 (flagship): $0.010 - $0.020
- Tier 2 (medium): $0.005 - $0.010
- Tier 3 (budget): $0.001 - $0.005

**Validation** (6 experiments × 12 models × 1000 problems):
- ~72,000 API calls
- Cost: $150 - $250
- Time: ~8-12 hours total

**Production** (6 experiments × 12 models × 8000 problems):
- ~576,000 API calls
- Cost: $2,400 - $4,000
- Time: ~66-96 hours (3-4 days)
- Run overnight/over weekend

---

## Troubleshooting

### High Error Rates
- Verify prompt formatting in template
- Check parser matches task type
- Inspect failed cases manually

### Rate Limits
- Reduce `concurrency.workers` in config
- Increase `retry.backoff_seconds`
- Use `--resume` to continue

### Inconsistent Results
- Ensure `seed` is set in all configs
- Verify `temperature` settings
- Use `lockstep: true` for fair comparison

---

## Next Steps

1. ✅ Read **DASHBOARD_DESIGN.md** completely
2. ✅ Follow **EXPERIMENT_CHECKLIST.md** Phase 1 (Setup)
3. ☐ Generate problem dataset
4. ☐ Create 6 experiment configs
5. ☐ Run test with `--limit 10`
6. ☐ Execute full experiments
7. ☐ Implement analysis tools (after results)
8. ☐ Generate dashboard
9. ☐ Write paper

---

## Questions?

Refer to:
- **DASHBOARD_DESIGN.md** for research questions and dashboard structure
- **EXPERIMENT_CHECKLIST.md** for step-by-step execution guide
- Main repo **README.md** for general framework documentation
- `configs/README.md` for configuration details
- `prompts/README.md` for prompt engineering guidance

---

**Status**: Planning phase — experiments not yet run  
**Next**: Follow EXPERIMENT_CHECKLIST.md Phase 1  

