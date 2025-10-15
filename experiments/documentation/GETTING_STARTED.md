# Getting Started: Quick Reference

## Complete Experimental Setup

We're running a systematic evaluation of **12 LLM models** across **6 experiments** to answer **6 research questions** about logical reasoning.

---

## 📊 The Numbers

| Aspect | Validation | Production |
|--------|------------|------------|
| **Problems** | 1,000 | 8,000 |
| **Per case** | 5 | 40 |
| **Models** | 12 | 12 |
| **Experiments** | 6 | 6 |
| **Total API calls** | 72,000 | 576,000 |
| **Est. Cost** | $150-$250 | $2,400-$4,000 |
| **Est. Time** | 8-12 hours | 66-96 hours (3-4 days) |

---

## 🎯 Three-Step Plan

### Step 1: Generate Validation Dataset

```bash
cd /Users/ottomattas/Downloads/repos/llmlog
source venv/bin/activate

python experiments/makeproblems.py \
  --vars 1-20 \
  --clens 1-5 \
  --horn mixed \
  --percase 5 \
  --seed 42424 \
  --workers 4 \
  > data/problems_validation_vars1-20_len1-5_percase5_seed42424.js
```

**Result**: 1,000 problems, takes ~8-15 minutes

### Step 2: Run Validation Experiments

```bash
# Create 6 configs (see EXPERIMENT_CHECKLIST.md)
# Point all to validation dataset

# Run all 6 experiments
for config in experiments/configs/horn_*.yaml experiments/configs/cnf*.yaml; do
  python -m experiments.runner \
    --config "$config" \
    --resume \
    --run validation_001
done
```

**Result**: 72 result files (6 experiments × 12 models)  
**Cost**: ~$150-$250, **Time**: ~8-12 hours

### Step 3: Decide on Production

After analyzing validation results:

```bash
# If good → Generate production dataset
python experiments/makeproblems.py \
  --vars 1-20 \
  --clens 1-5 \
  --horn mixed \
  --percase 40 \
  --seed 42424 \
  --workers 4 \
  > data/problems_production_vars1-20_len1-5_percase40_seed42424.js

# Run all experiments on production
# (Update configs to point to production dataset first)
for config in experiments/configs/*.yaml; do
  python -m experiments.runner \
    --config "$config" \
    --resume \
    --run production_001
done
```

**Result**: 8,000 problems, 72 result files  
**Cost**: ~$2,400-$4,000, **Time**: ~3-4 days

---

## 📚 Documentation Map

| Document | When to Use | Time |
|----------|-------------|------|
| **This file** | First read (overview) | 5 min |
| **[VALIDATION_WORKFLOW.md](VALIDATION_WORKFLOW.md)** | Understand two-phase approach | 10 min |
| **[DATASET_GENERATION.md](DATASET_GENERATION.md)** | Generate datasets | 15 min |
| **[EXPERIMENT_CHECKLIST.md](EXPERIMENT_CHECKLIST.md)** | Execute experiments | Reference |
| **[DASHBOARD_DESIGN.md](DASHBOARD_DESIGN.md)** | After results (analysis plan) | 20 min |

---

## 🔬 What We're Testing

### 6 Experiments × 12 Models = 72 Configurations

**Experiments** (vary representation and filter):
1. `horn_yn_hornonly` — Horn repr on Horn problems only
2. `horn_yn_mixed` — Horn repr on all problems (mismatch test)
3. `cnf1_con_mixed` — Verbose CNF on all problems
4. `cnf2_con_mixed` — Compact CNF on all problems
5. `cnf1_con_hornonly` — Verbose CNF on Horn only
6. `cnf2_con_hornonly` — Compact CNF on Horn only

**12 Models** (same across all experiments):
- **Tier 1**: Sonnet-4.5, Gemini-Pro, GPT-5-Pro (high thinking)
- **Tier 2**: Opus-4, Flash, GPT-5 (medium thinking)
- **Tier 3**: Haiku+, Flash-Lite+, GPT-5-Mini (low thinking)
- **Tier 3**: Haiku, Flash-, Nano (no thinking)

---

## ❓ 6 Research Questions We'll Answer

1. **Does representation matter?** — horn vs cnf_v1 vs cnf_v2
2. **Can models handle mismatch?** — Horn repr on non-Horn problems
3. **When do models break down?** — Complexity thresholds (90%, 75%, 50%)
4. **Is extended thinking worth it?** — Cost-benefit analysis
5. **Which tier should I use?** — Accuracy vs cost trade-off
6. **Which model is best for what?** — Task-specific strengths

---

## ⚡ Quick Commands

### Generate Validation Dataset
```bash
python experiments/makeproblems.py --vars 1-20 --clens 1-5 --horn mixed --percase 5 --seed 42424 --workers 4 > data/problems_validation_vars1-20_len1-5_percase5_seed42424.js
```

### Test Single Config (10 problems)
```bash
python -m experiments.runner --config experiments/configs/horn_yn_hornonly.yaml --limit 10 --dry-run
```

### Run Validation
```bash
for config in experiments/configs/*.yaml; do python -m experiments.runner --config "$config" --resume --run validation_001; done
```

### Check Progress
```bash
find experiments/runs -name "results.summary.json" | wc -l
```

### Quick Analysis
```bash
python -m experiments.analyze_generic experiments/runs/horn_yn_hornonly/validation_001/anthropic/claude-sonnet*/results.jsonl
```

---

##  ✅ Success Criteria

**Validation phase complete** when:
- [x] All 72 result files exist (6 × 12)
- [x] Average accuracy 70-100% (reasonable range)
- [x] Parsing errors <5%
- [x] Discussed with supervisors
- [x] Decision: proceed to production or adjust

**Production phase complete** when:
- [x] All 72 result files exist
- [x] Ready to generate dashboard
- [x] Can answer all 6 research questions

---

## 🚦 Current Status

- [ ] Read all documentation
- [ ] Generate validation dataset
- [ ] Create 6 experiment configs
- [ ] Test with `--limit 10`
- [ ] Run full validation
- [ ] Analyze validation results
- [ ] Discuss with supervisors
- [ ] Generate production dataset
- [ ] Run production experiments
- [ ] Implement dashboard tools
- [ ] Generate dashboard
- [ ] Answer research questions
- [ ] Write paper

---

## 💡 Key Insights from Design

**Representation matters**: Different ways to encode same problem affect accuracy

**Mismatch is costly**: Using wrong representation → ~10-15% accuracy penalty

**Models degrade**: All models struggle as complexity increases, but at different thresholds

**Thinking helps on hard problems**: Minimal benefit on simple, critical on complex

**Tier vs cost**: Medium tier likely best cost/accuracy ratio

**Model specialization**: Different models excel at different task types

---

## 🎓 Next Steps

1. **Right now**: Read [VALIDATION_WORKFLOW.md](VALIDATION_WORKFLOW.md)
2. **Then**: Follow [DATASET_GENERATION.md](DATASET_GENERATION.md) Step 1
3. **Then**: Follow [EXPERIMENT_CHECKLIST.md](EXPERIMENT_CHECKLIST.md) Phase 1
4. **After validation**: Decide on production
5. **After production**: Implement dashboard (see [DASHBOARD_DESIGN.md](DASHBOARD_DESIGN.md))

---


