# Experiment Setup and Execution Guide

> Complete guide for generating datasets and running validation/production experiments

---

## Quick Start

### 1. Generate Validation Dataset (Already Done! ✅)

```bash
python experiments/makeproblems.py \
  --vars 4-20 \
  --clens 2-5 \
  --horn mixed \
  --percase 4 \
  --seed 42424 \
  --workers 4 \
  > data/problems_validation_vars4-20_len2-5_percase4_seed42424.js
```

**Result**: 544 problems (272 Horn, 272 non-Horn, balanced sat/unsat)

### 2. Test One Config

```bash
# Dry-run (no API calls)
python -m experiments.runner \
  --config experiments/configs/horn_yn_hornonly.yaml \
  --limit 5 \
  --dry-run

# Small real test (1 model, ~$1-2)
python -m experiments.runner \
  --config experiments/configs/horn_yn_hornonly.yaml \
  --limit 10 \
  --only anthropic \
  --resume \
  --run test_001
```

### 3. Run Full Validation Suite

```bash
RUN_ID="validation_$(date +%Y%m%d)"

for config in experiments/configs/horn_*.yaml experiments/configs/cnf*.yaml; do
  echo "Running: $(basename $config)"
  python -m experiments.runner \
    --config "$config" \
    --resume \
    --run "$RUN_ID"
done
```

**Cost**: ~$100-$160, **Time**: ~5-8 hours

---

## Dataset Specifications

### Validation Dataset (Current)

**File**: `data/problems_validation_vars4-20_len2-5_percase4_seed42424.js`

| Aspect | Value |
|--------|-------|
| Variables | 4-20 (17 levels) |
| Clause lengths | 2-5 (4 levels) |
| Per case | 4 (2 sat + 2 unsat) |
| **Total** | **544 problems** |
| Horn / Non-Horn | 272 / 272 |
| Sat / Unsat | 272 / 272 |
| Per var level | 32 problems |

### Production Dataset (After Validation)

**Command**:
```bash
python experiments/makeproblems.py \
  --vars 4-20 \
  --clens 2-5 \
  --horn mixed \
  --percase 40 \
  --seed 42424 \
  --workers 4 \
  > data/problems_production_vars4-20_len2-5_percase40_seed42424.js
```

| Aspect | Value |
|--------|-------|
| Variables | 4-20 (17 levels) |
| Clause lengths | 2-5 (4 levels) |
| Per case | 40 (20 sat + 20 unsat) |
| **Total** | **5,440 problems** |
| Horn / Non-Horn | 2,720 / 2,720 |
| Per var level | 320 problems |
| Generation time | ~60-90 minutes |

**Why vars 4-20 (not 1-20)**:
- Generator constraints: vars 1-3 cause issues with certain length/type combinations
- Vars 4: Still simple enough for baseline
- Vars 20: Maximum supported by truth table solver
- 17 levels: Excellent granularity for degradation curves

**Why lengths 2-5 (not 1-5)**:
- Length 1 (unit clauses) causes infinite loops in generation
- Lengths 2-5 capture full complexity spectrum
- Classic 3-SAT uses length 3 (we have 2-5)
- More meaningful than including trivial length-1

---

## 6 Experiment Configurations

All configs are ready and point to validation dataset:

| # | Name | Representation | Task | Filter | Problems |
|---|------|----------------|------|--------|----------|
| 1 | horn_yn_hornonly | horn_if_then | yes_no | horn_only | 272 |
| 2 | horn_yn_mixed | horn_if_then | yes_no | all | 544 |
| 3 | cnf1_con_mixed | cnf_v1 (verbose) | contradiction | all | 544 |
| 4 | cnf2_con_mixed | cnf_v2 (compact) | contradiction | all | 544 |
| 5 | cnf1_con_hornonly | cnf_v1 (verbose) | contradiction | horn_only | 272 |
| 6 | cnf2_con_hornonly | cnf_v2 (compact) | contradiction | horn_only | 272 |

**All configs include identical 12 models** for fair comparison.

---

## 12 Models (Identical Across All Experiments)

| Tier | Provider | Model | Thinking | Purpose |
|------|----------|-------|----------|---------|
| **Tier 1: Flagship** | | | | |
| T1 | Anthropic | claude-sonnet-4-5-20250929 | High (24576) | Best performance |
| T1 | Google | gemini-2.5-pro | High (24576) | Best performance |
| T1 | OpenAI | gpt-5-pro-2025-10-06 | High | Best performance |
| **Tier 2: Medium** | | | | |
| T2 | Anthropic | claude-opus-4-1-20250805 | Med (8192) | Balanced |
| T2 | Google | gemini-2.5-flash | Med (8192) | Balanced |
| T2 | OpenAI | gpt-5-2025-08-07 | Medium | Balanced |
| **Tier 3: Budget + Thinking** | | | | |
| T3 | Anthropic | claude-haiku-4-5-20251001 | Low (1024) | Budget w/ boost |
| T3 | Google | gemini-2.5-flash-lite | Low (1024) | Budget w/ boost |
| T3 | OpenAI | gpt-5-mini-2025-08-07 | Low | Budget w/ boost |
| **Tier 3: Budget No Thinking** | | | | |
| T3 | Anthropic | claude-haiku-4-5-20251001 | None | Baseline budget |
| T3 | Google | gemini-2.5-flash | None | Baseline budget |
| T3 | OpenAI | gpt-5-nano-2025-08-07 | None | Baseline budget |

---

## Validation Workflow

### Phase 1: Quick Test (5-10 problems)

```bash
# Test one config with dry-run
python -m experiments.runner \
  --config experiments/configs/horn_yn_hornonly.yaml \
  --limit 10 \
  --dry-run

# If prompts look good, run real test with 1 model
python -m experiments.runner \
  --config experiments/configs/horn_yn_hornonly.yaml \
  --limit 10 \
  --only anthropic \
  --resume \
  --run quicktest
```

**Verify**:
- Prompts render correctly
- Models run successfully
- Results are written to expected paths
- No parsing errors

### Phase 2: Full Validation (All 6 Experiments)

```bash
RUN_ID="validation_$(date +%Y%m%d)"

# Run all experiments
for config in experiments/configs/horn_*.yaml experiments/configs/cnf*.yaml; do
  echo "Running: $(basename $config)"
  python -m experiments.runner \
    --config "$config" \
    --resume \
    --run "$RUN_ID"
done
```

**Expected**:
- 72 result files (6 experiments × 12 models)
- Cost: ~$100-$160
- Time: ~5-8 hours

**Monitor**:
```bash
# Check progress
find experiments/runs -name "results.summary.json" | wc -l

# Watch a specific experiment
tail -f experiments/runs/horn_yn_hornonly/$RUN_ID/anthropic/claude-sonnet*/results.summary.json

# Check for errors
grep -r "error" experiments/runs/*/$RUN_ID/ | head -20
```

### Phase 3: Analyze Validation Results

```bash
# Analyze one model from each experiment
python -m experiments.analyze_generic \
  experiments/runs/horn_yn_hornonly/$RUN_ID/anthropic/claude-sonnet*/results.jsonl

python -m experiments.analyze_generic \
  experiments/runs/cnf1_con_mixed/$RUN_ID/anthropic/claude-sonnet*/results.jsonl
```

**Discuss with supervisors**:
- Do results make sense?
- Are experiment configs correct?
- Ready for production run?

### Phase 4: Production Run (After Validation Success)

```bash
# 1. Generate production dataset (~60-90 min)
python experiments/makeproblems.py \
  --vars 4-20 \
  --clens 2-5 \
  --horn mixed \
  --percase 40 \
  --seed 42424 \
  --workers 4 \
  > data/problems_production_vars4-20_len2-5_percase40_seed42424.js

# 2. Update all 6 configs to point to production dataset
sed -i.bak 's|problems_validation_vars4-20_len2-5_percase4_|problems_production_vars4-20_len2-5_percase40_|g' \
  experiments/configs/horn_*.yaml experiments/configs/cnf*.yaml
rm experiments/configs/*.bak

# 3. Run all experiments on production
RUN_ID="production_$(date +%Y%m%d)"

for config in experiments/configs/horn_*.yaml experiments/configs/cnf*.yaml; do
  python -m experiments.runner \
    --config "$config" \
    --resume \
    --run "$RUN_ID"
done
```

**Expected**:
- 72 result files
- Cost: ~$1,600-$2,720
- Time: ~45-68 hours (2-3 days) - run over weekend!

---

## Cost Summary

| Phase | Problems | Models | Experiments | API Calls | Cost | Time |
|-------|----------|--------|-------------|-----------|------|------|
| Quick test | 10 | 1 | 1 | 10 | ~$1-2 | <1 min |
| Validation | 544 | 12 | 6 | 39,168 | $100-$160 | 5-8 hours |
| Production | 5,440 | 12 | 6 | 391,680 | $1,600-$2,720 | 45-68 hours |

---

## Troubleshooting

### Generator Issues

**Problem**: Generation hangs with certain var/length combinations

**Problematic combinations**:
- Vars 1-3 with any configuration
- Vars 18-20 with length 5 + mixed (non-Horn)

**Solution**: Use **vars 4-20, lengths 2-5** (current setup)

### Rate Limits

**Problem**: HTTP 429 errors during experiments

**Solutions**:
- Reduce `concurrency.workers` in config (try 6 instead of 12)
- Use `--resume` to continue after cooling down
- Increase `retry.backoff_seconds` to `[5, 10, 30, 60]`

### Parsing Errors

**Problem**: High "unclear" count (>10%)

**Check**:
- Review provenance files for actual model outputs
- Verify parser type matches task (yes_no vs contradiction)
- Check if models are following instructions

---

## Quick Reference Commands

### Generate Datasets
```bash
# Validation (already done!)
python experiments/makeproblems.py --vars 4-20 --clens 2-5 --horn mixed --percase 4 --seed 42424 --workers 4 > data/problems_validation_vars4-20_len2-5_percase4_seed42424.js

# Production (after validation)
python experiments/makeproblems.py --vars 4-20 --clens 2-5 --horn mixed --percase 40 --seed 42424 --workers 4 > data/problems_production_vars4-20_len2-5_percase40_seed42424.js
```

### Run Experiments
```bash
# Single experiment
python -m experiments.runner --config experiments/configs/horn_yn_hornonly.yaml --resume --run validation_001

# All 6 experiments
for config in experiments/configs/horn_*.yaml experiments/configs/cnf*.yaml; do
  python -m experiments.runner --config "$config" --resume --run validation_001
done
```

### Monitor Progress
```bash
# Count completed results
find experiments/runs -name "results.summary.json" | wc -l

# Average accuracy so far
jq -s 'map(.accuracy) | add/length' experiments/runs/*/*/*/*/results.summary.json

# Check for errors
grep -c "\"error\":" experiments/runs/*/*/*/*/results.jsonl
```

### Analyze Results
```bash
# Single model analysis
python -m experiments.analyze_generic experiments/runs/horn_yn_hornonly/validation_001/anthropic/claude-sonnet*/results.jsonl

# Compare two experiments
python -m experiments.compare_runs --name1 horn_yn_hornonly --name2 cnf1_con_mixed
```

---

## After Results: Dashboard Generation

See **DASHBOARD_DESIGN.md** for:
- 6 research questions to answer
- Dashboard structure and implementation plan
- Analysis tools to build
- Export options for publication

---

## Success Checklist

**Validation Complete** when:
- [x] All 72 result files exist (6 × 12)
- [ ] Average accuracy 70-100% (reasonable)
- [ ] Parsing errors <5%
- [ ] Results discussed with supervisors
- [ ] Decision made: proceed to production or adjust

**Production Complete** when:
- [ ] All 72 result files exist
- [ ] Dashboard tools implemented
- [ ] All 6 research questions answered
- [ ] Results ready for publication

---

**Next**: Run quick test with `--limit 10 --only anthropic` to validate pipeline!

