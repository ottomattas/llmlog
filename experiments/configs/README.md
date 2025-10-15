# Experiment Configurations

This folder contains 6 YAML configuration files for the experimental suite.

---

## All 6 Experiments

| # | Config File | Representation | Task | Filter | Problems | Purpose |
|---|-------------|----------------|------|--------|----------|---------|
| 1 | `horn_yn_hornonly.yaml` | horn_if_then | yes_no | horn_only | 272 | Baseline: Horn on Horn |
| 2 | `horn_yn_mixed.yaml` | horn_if_then | yes_no | all | 544 | Mismatch: Horn on all |
| 3 | `cnf1_con_mixed.yaml` | cnf_v1 | contradiction | all | 544 | Verbose CNF on all |
| 4 | `cnf2_con_mixed.yaml` | cnf_v2 | contradiction | all | 544 | Compact CNF on all |
| 5 | `cnf1_con_hornonly.yaml` | cnf_v1 | contradiction | horn_only | 272 | Verbose CNF on Horn |
| 6 | `cnf2_con_hornonly.yaml` | cnf_v2 | contradiction | horn_only | 272 | Compact CNF on Horn |

---

## Key Features

### Same 12 Models Across All Experiments

All configs include identical model configurations for fair comparison:
- **Tier 1**: Sonnet-4.5, Gemini-Pro, GPT-5-Pro (high thinking)
- **Tier 2**: Opus-4, Flash, GPT-5 (medium thinking)
- **Tier 3**: Haiku+, Flash-Lite+, Mini (low thinking)
- **Tier 3**: Haiku, Flash-, Nano (no thinking)

### Current Dataset

All configs point to validation dataset:
```yaml
input_file: data/problems_validation_vars4-20_len2-5_percase4_seed42424.js
```

After validation, update to production:
```yaml
input_file: data/problems_production_vars4-20_len2-5_percase40_seed42424.js
```

---

## Representations

### horn_if_then
Renders as facts and if-then rules:
```
p1.
if p2 and p3 then p4.
```
- Used in: Experiments 1-2
- Task: yes_no (is p0 derivable?)

### cnf_v1 (Verbose)
Natural language CNF:
```
p1 is true or p2 is false.
```
- Used in: Experiments 3, 5
- Task: contradiction

### cnf_v2 (Compact)
Symbolic CNF:
```
p1 or not(p2).
```
- Used in: Experiments 4, 6
- Task: contradiction

---

## Important Notes

### ⚠️ Variable and Length Constraints

The problem generator has limitations:
- **Vars 1-3**: Cause generation issues (infinite loops)
- **Lengths 1**: Unit clauses cause infinite loops
- **High complexity**: Vars 18-20 + length 5 + mixed hangs

**Solution**: Use **vars 4-20, lengths 2-5** (current setup)

### Anthropic Temperature Requirement

Anthropic models with `thinking.enabled=true` require `temperature: 1`:
- Sonnet-4.5, Opus-4, Haiku (with thinking): `temperature: 1`
- Haiku (without thinking): `temperature: 0`

All configs are already configured correctly.

---

## Testing Configs

### Quick Test (No API Calls)
```bash
python -m experiments.runner \
  --config experiments/configs/horn_yn_hornonly.yaml \
  --limit 5 \
  --dry-run
```

### Small Real Test
```bash
python -m experiments.runner \
  --config experiments/configs/horn_yn_hornonly.yaml \
  --limit 10 \
  --only anthropic \
  --resume \
  --run test_001
```

### Run All 6 Experiments
```bash
for config in experiments/configs/horn_*.yaml experiments/configs/cnf*.yaml; do
  python -m experiments.runner --config "$config" --resume --run validation_001
done
```

---

## Switching to Production Dataset

When ready for production run:

```bash
# Update all 6 configs at once
sed -i.bak 's|problems_validation_vars4-20_len2-5_percase4_|problems_production_vars4-20_len2-5_percase40_|g' \
  experiments/configs/horn_*.yaml experiments/configs/cnf*.yaml

# Remove backups
rm experiments/configs/*.bak

# Verify changes
grep "^input_file:" experiments/configs/horn_*.yaml experiments/configs/cnf*.yaml
```

---

**See parent README.md for full documentation links and workflow overview.**
