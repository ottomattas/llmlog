# Validation-to-Production Workflow

## Two-Phase Approach

This document explains the recommended two-phase experimental workflow: **validation first, then production**.

---

## Phase 1: Validation (Start Here!) 

### Goal
- Verify all configurations work correctly
- Get initial accuracy estimates for all models
- Identify any issues before committing to full production run
- Discuss preliminary results with supervisors
- **Cost: ~$150-$250, Time: ~8-12 hours**

### Dataset: Validation (5 per case)
```bash
python experiments/makeproblems.py \
  --vars 1-20 \
  --clens 2-5 \
  --horn mixed \
  --percase 5 \
  --seed 42424 \
  --workers 4 \
  > data/problems_validation_vars1-20_len2-5_percase5_seed42424.js

# Result: 800 problems (50 per variable level)
```

### Run All Experiments on Validation
```bash
# Update all 6 configs to use validation dataset
# input_file: data/problems_validation_vars1-20_len2-5_percase5_seed42424.js

# Run
for config in experiments/configs/*.yaml; do
  python -m experiments.runner \
    --config "$config" \
    --resume \
    --run validation_001
done
```

### What to Check
- [ ] All 12 models × 6 experiments = 72 result files generated
- [ ] No major parsing errors (<5% unclear answers)
- [ ] Accuracy trends make sense:
  - Flagship models: 85-100%
  - Budget models: 70-95%
  - Degradation visible as vars increase
- [ ] All prompts render correctly (check provenance files)

### Analyze Validation Results
```bash
# Check one model from each experiment
python -m experiments.analyze_generic \
  experiments/runs/horn_yn_hornonly/validation_001/anthropic/claude-sonnet*/results.jsonl

python -m experiments.analyze_generic \
  experiments/runs/cnf1_con_mixed/validation_001/anthropic/claude-sonnet*/results.jsonl

# Look for:
# - Overall accuracy seems reasonable?
# - Degradation pattern visible by maxvars?
# - Any unexpected errors or patterns?
```

### Discussion with Supervisors
**Share**:
- Overall accuracy per model per experiment (summary.json files)
- Initial degradation trends
- Any surprises or issues

**Decide**:
- Are experiment configurations correct?
- Do we need to adjust prompts?
- Should we modify the experimental design?
- Are we ready for production run?

**If validation looks good → Proceed to Phase 2**

---

## Phase 2: Production (After Validation Success)

### Goal
- Publication-quality dataset with statistical rigor
- 400 samples per variable level (8× more than validation)
- Smooth degradation curves for analysis
- Robust results for all 6 research questions
- **Cost: ~$2,400-$4,000, Time: ~66-96 hours (3-4 days)**

### Dataset: Production (40 per case)
```bash
# Generate overnight (1-2 hours)
python experiments/makeproblems.py \
  --vars 1-20 \
  --clens 2-5 \
  --horn mixed \
  --percase 40 \
  --seed 42424 \
  --workers 4 \
  > data/problems_production_vars1-20_len2-5_percase40_seed42424.js

# Result: 6,400 problems (400 per variable level)
```

### Run All Experiments on Production
```bash
# Update all 6 configs to use production dataset
# input_file: data/problems_production_vars1-20_len2-5_percase40_seed42424.js

# Run (will take 3-4 days)
RUN_ID="production_$(date +%Y%m%d)"

for config in experiments/configs/*.yaml; do
  python -m experiments.runner \
    --config "$config" \
    --resume \
    --run "$RUN_ID"
done
```

**Tip**: Run over weekend or when you can monitor occasionally for rate limit issues.

### Monitor Production Run
```bash
# Watch progress
watch -n 60 'find experiments/runs -name "results.summary.json" | grep production | wc -l'

# Check for errors
grep -r "error" experiments/runs/*/production_*/anthropic/*/results.jsonl | wc -l

# Estimate completion
tail -1 experiments/runs/*/production_*/*/*/results.summary.json
```

### After Production Complete
- [ ] All 72 result files exist (6 × 12)
- [ ] Generate dashboard (see DASHBOARD_DESIGN.md)
- [ ] Analyze all research questions
- [ ] Export for paper

---

## Why This Two-Phase Approach?

### ✅ Benefits

1. **Risk Mitigation**
   - Catch config errors early (~$50 vs $2,500)
   - Verify prompts work before full run
   - Test all 12 models work correctly

2. **Early Insights**
   - Get rough accuracy estimates
   - See initial degradation patterns
   - Identify potential issues

3. **Supervisor Feedback**
   - Show preliminary results
   - Adjust experimental design if needed
   - Get buy-in before large expense

4. **Confidence**
   - Know production run will succeed
   - Already validated parsing works
   - Estimated final accuracy ranges

5. **Cost Control**
   - Only spend $150-250 initially
   - Commit to $2,400-4,000 only after validation success

### Alternative: Direct to Production

**Skip validation if**:
- You've already tested configs on legacy datasets
- Supervisors approve $2,500-4,000 upfront
- You're confident everything will work

**Risk**: If configs are wrong, you waste $2,500+ and 3-4 days.

---

## Runner's --limit Option

The runner supports `--limit N` to process only first N problems:

```bash
# Test with just 10 problems from ANY dataset
python -m experiments.runner \
  --config experiments/configs/horn_yn_hornonly.yaml \
  --limit 10 \
  --run quicktest

# Test with 100 problems from validation dataset
python -m experiments.runner \
  --config experiments/configs/horn_yn_hornonly.yaml \
  --limit 100 \
  --run partialtest

# Full validation dataset (no limit needed, dataset already small)
python -m experiments.runner \
  --config experiments/configs/horn_yn_hornonly.yaml \
  --run validation_001

# Full production dataset (all 8000 problems)
python -m experiments.runner \
  --config experiments/configs/horn_yn_hornonly.yaml \
  --run production_001
```

**How --limit works**:
- Processes first N problems from the dataset
- Useful for quick tests without generating new dataset
- Can use production dataset with `--limit 1000` to simulate validation

**However**: Better to use proper validation dataset (5 per case) because:
- Balanced across all complexity levels
- Faster to generate (8-15 min vs 60-120 min)
- Can keep both datasets for comparison

---

## Recommended Timeline

### Week 1: Validation
- **Day 1**: Generate validation dataset, create 6 configs
- **Day 2**: Test with `--limit 10`, fix any issues
- **Day 3**: Run full validation (all 6 experiments)
- **Day 4**: Analyze results, meet with supervisors
- **Day 5**: Decide: proceed to production?

### Week 2: Production (if validated)
- **Day 1**: Generate production dataset (1-2 hours)
- **Day 2-5**: Run production experiments (3-4 days)
  - Monitor for rate limits
  - Resume if interrupted

### Week 3: Analysis
- **Day 1-2**: Implement analysis tools (if not done)
- **Day 3**: Generate dashboard
- **Day 4-5**: Answer all 6 research questions

### Week 4: Publication
- **Day 1-2**: Export tables and figures
- **Day 3-5**: Write paper draft

**Total**: ~4 weeks from start to draft paper.

---

## Cost Breakdown

| Phase | Dataset | Problems | Models | Experiments | Total Calls | Cost | Time |
|-------|---------|----------|--------|-------------|-------------|------|------|
| Validation | 5 per case | 1,000 | 12 | 6 | 72,000 | $150-$250 | 8-12h |
| Production | 40 per case | 8,000 | 12 | 6 | 576,000 | $2,400-$4,000 | 66-96h |
| **Total** | Both | 9,000 | 12 | 6 | 648,000 | **$2,550-$4,250** | **74-108h** |

**Phased spending**: Validate first ($150-250), then commit to production ($2,400-4,000) only after success.

---

## Quick Reference Commands

### Generate Datasets
```bash
# Validation (do this first!)
python experiments/makeproblems.py --vars 1-20 --clens 2-5 --horn mixed --percase 5 --seed 42424 --workers 4 > data/problems_validation_vars1-20_len2-5_percase5_seed42424.js

# Production (after validation succeeds)
python experiments/makeproblems.py --vars 1-20 --clens 2-5 --horn mixed --percase 40 --seed 42424 --workers 4 > data/problems_production_vars1-20_len2-5_percase40_seed42424.js
```

### Run Experiments
```bash
# Validation
for config in experiments/configs/*.yaml; do
  python -m experiments.runner --config "$config" --resume --run validation_001
done

# Production
for config in experiments/configs/*.yaml; do
  python -m experiments.runner --config "$config" --resume --run production_001
done
```

### Check Progress
```bash
# Count completed result files
find experiments/runs -name "results.summary.json" | wc -l
# Should be: 72 (validation) or 72 (production) or 144 (both)

# Average accuracy so far
jq -s 'map(.accuracy) | add/length' experiments/runs/*/*/*/*/results.summary.json
```

---

**Next**: Follow EXPERIMENT_CHECKLIST.md Phase 1 to begin!

