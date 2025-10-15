# Experiment Execution Checklist

> Quick reference for running the complete experimental suite

## Phase 1: Setup ☐

### 1.1 Generate Problem Dataset
```bash
# TODO: Implement or use existing makeproblems.py
python -m experiments.makeproblems \
  --vars 1-20 \
  --len 1-5 \
  --count 2000 \
  --seed 4242 \
  --output data/problems_complex_v2.js
```

**Verify**:
- [ ] Dataset has ~2000 problems
- [ ] Balanced Horn vs non-Horn
- [ ] Balanced Sat vs Unsat
- [ ] Variables range from 1-20
- [ ] Clause length ranges from 1-5

### 1.2 Create Experiment Configs

**6 Required Experiments**:

```bash
# Create from template
cd experiments/configs

# 1. Horn representation on Horn problems (baseline)
cp _template_unified.yaml horn_yn_hornonly.yaml

# 2. Horn representation on mixed problems (mismatch test)
cp _template_unified.yaml horn_yn_mixed.yaml

# 3. Verbose CNF on mixed problems
cp _template_unified.yaml cnf1_con_mixed.yaml

# 4. Compact CNF on mixed problems
cp _template_unified.yaml cnf2_con_mixed.yaml

# 5. Verbose CNF on Horn problems only
cp _template_unified.yaml cnf1_con_hornonly.yaml

# 6. Compact CNF on Horn problems only
cp _template_unified.yaml cnf2_con_hornonly.yaml
```

**For each config, edit**:
- [ ] Set `name:` to match filename (e.g., `horn_yn_hornonly`)
- [ ] Set `input_file:` to new dataset path
- [ ] Set `prompt.style:` (`horn_if_then`, `cnf_v1`, or `cnf_v2`)
- [ ] Set `parse.type:` (`yes_no` or `contradiction`)
- [ ] Set `filters.horn_only:` (`true` or `false`)
- [ ] Keep all 12 `targets:` identical across ALL configs
- [ ] Verify `output_pattern:` includes `${name}` and `${run}`

### 1.3 Verify Prompts

- [ ] Check `prompts/_template_unified.j2` is appropriate
- [ ] Template handles both Horn and CNF styles
- [ ] Instructions are clear for yes/no and contradiction tasks

### 1.4 Test Run (Small Sample)

```bash
# Test one config with 10 problems
python -m experiments.runner \
  --config experiments/configs/horn_yn_hornonly.yaml \
  --limit 10 \
  --dry-run

# If dry-run looks good, run for real
python -m experiments.runner \
  --config experiments/configs/horn_yn_hornonly.yaml \
  --limit 10 \
  --resume \
  --run test_001
```

**Verify**:
- [ ] All 12 models run successfully
- [ ] Results written to expected paths
- [ ] Summary JSON shows reasonable accuracy
- [ ] No parsing errors

### 1.5 Estimate Cost and Time

**Cost Calculation**:
```
Models per experiment: 12
Experiments: 6
Problems: 2000
Total API calls: 12 × 6 × 2000 = 144,000

Estimated cost per call:
- Tier 1 (flagship): ~$0.015
- Tier 2 (medium): ~$0.008
- Tier 3 (budget): ~$0.003

Total cost estimate: $600-$1200 (varies by provider)
```

**Time Estimation**:
```
With concurrency=12, lockstep=true:
- ~5 seconds per problem (average)
- 2000 problems × 5 sec = ~2.8 hours per experiment
- 6 experiments × 2.8 hours = ~17 hours total

With retry delays and rate limits: 20-24 hours total
```

- [ ] Budget approved for API costs
- [ ] Time window available for execution
- [ ] Plan for handling rate limits

---

## Phase 2: Execution ☐

### 2.1 Run All Experiments

```bash
# Set run ID for this batch
RUN_ID="production_$(date +%Y%m%d)"

# Run all experiments sequentially (or in parallel if providers allow)
for config in experiments/configs/horn_*.yaml experiments/configs/cnf*.yaml; do
  echo "Running $(basename $config)..."
  python -m experiments.runner \
    --config "$config" \
    --resume \
    --run "$RUN_ID"
done
```

**Or run individually** (recommended for better control):

```bash
RUN_ID="production_20251015"

# Experiment 1
python -m experiments.runner \
  --config experiments/configs/horn_yn_hornonly.yaml \
  --resume --run "$RUN_ID"

# Experiment 2
python -m experiments.runner \
  --config experiments/configs/horn_yn_mixed.yaml \
  --resume --run "$RUN_ID"

# Experiment 3
python -m experiments.runner \
  --config experiments/configs/cnf1_con_mixed.yaml \
  --resume --run "$RUN_ID"

# Experiment 4
python -m experiments.runner \
  --config experiments/configs/cnf2_con_mixed.yaml \
  --resume --run "$RUN_ID"

# Experiment 5
python -m experiments.runner \
  --config experiments/configs/cnf1_con_hornonly.yaml \
  --resume --run "$RUN_ID"

# Experiment 6
python -m experiments.runner \
  --config experiments/configs/cnf2_con_hornonly.yaml \
  --resume --run "$RUN_ID"
```

### 2.2 Monitor Progress

```bash
# Watch summary files being created
watch -n 10 'find experiments/runs -name "results.summary.json" -newer /tmp/start_time | wc -l'

# Check specific experiment progress
tail -f experiments/runs/horn_yn_hornonly/$RUN_ID/*/claude-sonnet*/results.summary.json

# Check for errors
grep -r "error" experiments/runs/*/$ RUN_ID/ | head -20
```

### 2.3 Validate Results

After each experiment completes:

```bash
# Quick analysis
python -m experiments.analyze_generic \
  experiments/runs/horn_yn_hornonly/$RUN_ID/anthropic/claude-sonnet*/results.jsonl

# Check all models completed
ls experiments/runs/horn_yn_hornonly/$RUN_ID/*/*/results.jsonl | wc -l
# Should be: 12 (one per model)
```

**For each experiment**:
- [ ] All 12 models completed
- [ ] Results files exist and are non-empty
- [ ] Summary accuracy seems reasonable
- [ ] No unexpected high error rates

---

## Phase 3: Analysis ☐

### 3.1 Implement Analysis Tools

(Following DASHBOARD_DESIGN.md)

```bash
# Create the analysis tool
# TODO: Implement experiments/analyze_matrix.py based on design doc
```

**Features to implement**:
- [ ] Load all result files from all experiments
- [ ] Compute overall accuracy per model per experiment
- [ ] Compute accuracy by complexity (maxvars, maxlen, depth)
- [ ] Identify degradation thresholds (90%, 75%, 50%)
- [ ] Answer each of 6 research questions
- [ ] Export comprehensive JSON

### 3.2 Run Analysis

```bash
python -m experiments.analyze_matrix \
  --runs-dir experiments/runs \
  --run-id "$RUN_ID" \
  --output experiments/aggregated_results.json
```

**Verify**:
- [ ] JSON file created successfully
- [ ] Contains all experiments and models
- [ ] Research questions sections populated
- [ ] Thresholds calculated for all models

### 3.3 Generate Dashboard

```bash
# TODO: Implement experiments/generate_dashboard.py based on design doc

python -m experiments.generate_dashboard \
  --input experiments/aggregated_results.json \
  --output experiments/dashboard.html
```

**Verify**:
- [ ] Single HTML file created
- [ ] Opens in browser successfully
- [ ] Heatmap displays correctly
- [ ] Degradation curves are interactive
- [ ] All 6 RQ sections populated
- [ ] Filters and toggles work

### 3.4 Explore Results

Open dashboard and answer each RQ:

- [ ] **RQ1**: Which representation is most accurate?
- [ ] **RQ2**: What's the penalty for representation mismatch?
- [ ] **RQ3**: Where do models break down? (threshold variables)
- [ ] **RQ4**: Is extended thinking worth the cost?
- [ ] **RQ5**: Which tier has best cost/accuracy ratio?
- [ ] **RQ6**: Which models are best for which tasks?

---

## Phase 4: Publication ☐

### 4.1 Export Results

```bash
# TODO: Implement experiments/export_results.py

# LaTeX tables for paper
python -m experiments.export_results \
  --input experiments/aggregated_results.json \
  --format latex \
  --output paper_tables.tex

# CSV for analysis in R/Excel
python -m experiments.export_results \
  --input experiments/aggregated_results.json \
  --format csv \
  --output results_tables.csv

# Markdown summary
python -m experiments.export_results \
  --input experiments/aggregated_results.json \
  --format markdown \
  --output RESULTS_SUMMARY.md
```

### 4.2 Create Figures

```bash
# Export high-res plots from dashboard
# (Implement screenshot/export functionality in dashboard)

# Or generate standalone plots:
python -m experiments.plot_degradation \
  --input experiments/aggregated_results.json \
  --output figures/degradation_all.png \
  --dpi 300
```

**Figures needed**:
- [ ] Figure 1: Overview heatmap
- [ ] Figure 2: Degradation curves (4-panel)
- [ ] Figure 3: Thinking benefit by complexity
- [ ] Figure 4: Cost-benefit analysis

### 4.3 Write Paper

**Sections** (see DASHBOARD_DESIGN.md for structure):
- [ ] Abstract
- [ ] Introduction
- [ ] Related Work
- [ ] Experimental Design
- [ ] Results (one subsection per RQ)
- [ ] Discussion
- [ ] Conclusion

**Tables needed**:
- [ ] Table 1: Model configurations (12 models)
- [ ] Table 2: Experiment configurations (6 experiments)
- [ ] Table 3: Degradation thresholds
- [ ] Table 4: Cost-benefit analysis
- [ ] Table 5: Model rankings

---

## Troubleshooting

### Common Issues

**High error rates**:
- Check prompt formatting
- Verify parser is appropriate for task
- Inspect a few failed cases manually

**Rate limit errors**:
- Reduce `concurrency.workers`
- Increase `retry.backoff_seconds`
- Use `--resume` to continue after cooling down

**Inconsistent results**:
- Verify `seed` is set in configs
- Check `temperature` settings
- Ensure `lockstep: true` for fair comparison

**Missing results**:
- Check logs for errors
- Verify API keys are valid
- Ensure sufficient API quota

---

## Quick Commands

```bash
# Check progress
find experiments/runs -name "results.summary.json" | wc -l

# Total problems processed
jq -s 'map(.total) | add' experiments/runs/*/*/*/*/results.summary.json

# Average accuracy across all
jq -s 'map(.accuracy) | add / length' experiments/runs/*/*/*/*/results.summary.json

# Find best model
jq -r '"\(.accuracy) \(.model)"' experiments/runs/*/*/*/*/results.summary.json | sort -rn | head -1

# Disk usage
du -sh experiments/runs
```

---

## Timeline Example

**Week 1**: Setup
- Day 1-2: Generate dataset, create configs
- Day 3: Test runs and validation
- Day 4-5: Full experiment execution

**Week 2**: Analysis
- Day 1-2: Implement analysis tools
- Day 3: Generate dashboard
- Day 4-5: Explore results, answer RQs

**Week 3**: Publication
- Day 1-2: Export results, create figures
- Day 3-5: Write paper draft

---

## Success Criteria

**Experiments Complete** when:
- [ ] All 6 experiments have results for all 12 models
- [ ] Total of 72 result files (6 × 12)
- [ ] No major parsing errors (<5% unclear rate)
- [ ] Results seem reasonable (accuracy not all 0% or 100%)

**Analysis Complete** when:
- [ ] Dashboard loads and displays all data
- [ ] All 6 RQs have clear answers
- [ ] Degradation thresholds identified for all models
- [ ] Key findings documented

**Publication Ready** when:
- [ ] All tables and figures exported
- [ ] Paper draft complete
- [ ] Results peer-reviewed internally
- [ ] Ready for submission

---

**Document Version**: 1.0  
**Paired With**: DASHBOARD_DESIGN.md  
**Last Updated**: 2025-10-15  

