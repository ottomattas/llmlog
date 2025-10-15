# Experiment Configs Summary

## All 6 Experiment Configurations Created

| # | Config File | Representation | Task | Filter | Purpose |
|---|-------------|----------------|------|--------|---------|
| 1 | `horn_yn_hornonly.yaml` | `horn_if_then` | `yes_no` | `horn_only: true` | Baseline: Horn on Horn |
| 2 | `horn_yn_mixed.yaml` | `horn_if_then` | `yes_no` | `horn_only: false` | Mismatch test: Horn on all |
| 3 | `cnf1_con_mixed.yaml` | `cnf_v1` | `contradiction` | `horn_only: false` | Verbose CNF on all |
| 4 | `cnf2_con_mixed.yaml` | `cnf_v2` | `contradiction` | `horn_only: false` | Compact CNF on all |
| 5 | `cnf1_con_hornonly.yaml` | `cnf_v1` | `contradiction` | `horn_only: true` | Verbose CNF on Horn |
| 6 | `cnf2_con_hornonly.yaml` | `cnf_v2` | `contradiction` | `horn_only: true` | Compact CNF on Horn |

---

## Key Features (Same Across All Configs)

### 12 Models
All configs include the same 12 models for fair comparison:
- **Tier 1 (High)**: Sonnet-4.5, Gemini-Pro, GPT-5-Pro
- **Tier 2 (Medium)**: Opus-4, Flash, GPT-5
- **Tier 3 (Low+think)**: Haiku+, Flash-Lite+, GPT-5-Mini
- **Tier 3 (No-think)**: Haiku, Flash-, Nano

### Dataset
All configs currently point to:
```yaml
input_file: data/problems_validation_vars1-20_len1-5_percase5_seed42424.js
```

**After validation**, update to production:
```yaml
input_file: data/problems_production_vars1-20_len1-5_percase40_seed42424.js
```

### Output Pattern
```yaml
output_pattern: experiments/runs/${name}/${run}/${provider}/${model}/results.jsonl
```

Results will be organized by experiment, run ID, provider, and model.

---

## Representations Explained

### `horn_if_then`
Renders Horn clauses as facts and rules:
```
p1.
if p2 and p3 then p4.
```

**Used in**: Experiments 1-2

### `cnf_v1` (Verbose)
Renders CNF with natural language:
```
p1 is true or p2 is false.
```

**Used in**: Experiments 3, 5

### `cnf_v2` (Compact)
Renders CNF with compact notation:
```
p1 or not(p2).
```

**Used in**: Experiments 4, 6

---

## Tasks Explained

### `yes_no`
For Horn problems: "Is p0 derivable?"
- Parser scans for "yes" or "no" tokens
- Used with `horn_if_then` representation

**Used in**: Experiments 1-2

### `contradiction`
For CNF problems: "Is the set contradictory?"
- Parser expects last token: "contradiction" or "satisfiable"
- Used with `cnf_v1` and `cnf_v2` representations

**Used in**: Experiments 3-6

---

## Research Questions Mapped to Experiments

### RQ1: Does representation matter?
Compare experiments 1, 5, 6 (same problem subset, different representations)

### RQ2: Can models handle mismatch?
Compare experiments 1 vs 2 (horn_only vs mixed with horn_if_then)

### RQ3: When do models break down?
Analyze degradation curves from all experiments

### RQ4: Is extended thinking worth it?
Compare thinking vs no-thinking models across all experiments

### RQ5: Which tier should I use?
Compare tier 1 vs 2 vs 3 across all experiments

### RQ6: Which model is best for what?
Cross-compare all models across all 6 experiments

---

## Quick Test Commands

Test each config with 10 problems:

```bash
# Experiment 1
python -m experiments.runner --config experiments/configs/horn_yn_hornonly.yaml --limit 10 --dry-run

# Experiment 2  
python -m experiments.runner --config experiments/configs/horn_yn_mixed.yaml --limit 10 --dry-run

# Experiment 3
python -m experiments.runner --config experiments/configs/cnf1_con_mixed.yaml --limit 10 --dry-run

# Experiment 4
python -m experiments.runner --config experiments/configs/cnf2_con_mixed.yaml --limit 10 --dry-run

# Experiment 5
python -m experiments.runner --config experiments/configs/cnf1_con_hornonly.yaml --limit 10 --dry-run

# Experiment 6
python -m experiments.runner --config experiments/configs/cnf2_con_hornonly.yaml --limit 10 --dry-run
```

---

## Run All Validation Experiments

After validation dataset is generated:

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

**Expected**: 72 result files (6 experiments × 12 models)

---

## Switch to Production Dataset

When ready for production run, update all 6 configs:

```bash
# Use sed to update all configs at once
sed -i.bak 's|problems_validation_vars1-20_len1-5_percase5_seed42424.js|problems_production_vars1-20_len1-5_percase40_seed42424.js|g' experiments/configs/horn_*.yaml experiments/configs/cnf*.yaml

# Verify changes
grep "input_file:" experiments/configs/horn_*.yaml experiments/configs/cnf*.yaml
```

Or manually edit each file to change the `input_file:` line.

---

## Validation Checklist

Before running full validation:

- [x] All 6 config files created
- [ ] Validation dataset generated
- [ ] Prompt template exists (`prompts/_template_unified.j2`)
- [ ] Test one config with `--limit 10`
- [ ] All 12 models configured correctly
- [ ] API keys set up
- [ ] Ready to run!

---

**Next**: Generate validation dataset and test with `--limit 10`!

