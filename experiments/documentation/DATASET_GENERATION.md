# Dataset Generation Guide

## Recommended Dataset for Full Experimental Suite

Based on DASHBOARD_DESIGN.md requirements, here's the dataset specification:

### Target Specifications

**Production Dataset** (for publication):
- **Variables**: 1-20 (20 levels) — complete range from trivial to very complex
- **Clause lengths**: 1-5 (5 levels) — from simple to complex clauses
- **Horn vs Non-Horn**: Mixed (both types)
- **Problems per case**: **40** (20 sat + 20 unsat, balanced)
- **Total problems**: 20 vars × 5 lens × 2 types × 40 per = **6,400 problems**
- **Seed**: 42424 (for reproducibility)
- **Statistical rigor**: 400 samples per variable level for robust analysis

**Validation Dataset** (for initial testing):
- **Problems per case**: **5** (quick validation)
- **Total problems**: 20 vars × 5 lens × 2 types × 5 per = **800 problems**
- Same seed for consistency

### Why These Parameters?

1. **Variables 1-20**: 
   - Starts at 1 (trivial, baseline)
   - Goes to 20 (maximum supported by truth table solver)
   - Complete range from trivial to very challenging
   - 20 levels gives fine-grained degradation curves
   - Will clearly show where each model breaks down

2. **Clause lengths 2-5**:
   - Length 2-3: Binary and ternary clauses
   - Length 2-3: Binary and ternary clauses
   - Length 3: Classic 3-SAT complexity
   - Length 4: Higher complexity
   - Length 5: Maximum interesting complexity
   - Complete range from simple to complex

3. **Mixed Horn/Non-Horn**:
   - Essential for RQ2 (representation mismatch)
   - Production: 4,000 Horn + 4,000 non-Horn
   - Validation: 400 Horn + 500 non-Horn
   - Perfectly balanced for fair comparison

4. **40 problems per case (production)**:
   - 20 satisfiable + 20 unsatisfiable (balanced)
   - **Strong statistical significance** at each complexity level
   - 400 samples per variable level = robust confidence intervals
   - Publication-quality rigor for research papers
   - Smooth degradation curves with minimal noise

5. **5 problems per case (validation)**:
   - Quick sanity check before full run
   - Test all configurations work correctly
   - Discuss initial results with supervisors
   - ~$150-$250 cost vs $2,400-$4,000 for full

### Generation Commands

#### Step 1: Validation Dataset (Start Here!)

```bash
cd /Users/ottomattas/Downloads/repos/llmlog
source venv/bin/activate

# Generate VALIDATION dataset first (takes ~8-15 minutes)
python experiments/makeproblems.py \
  --vars 1-20 \
  --clens 2-5 \
  --horn mixed \
  --percase 5 \
  --seed 42424 \
  --workers 4 \
  > data/problems_validation_vars1-20_len2-5_percase5_seed42424.js

# Quick stats check
wc -l data/problems_validation_vars1-20_len2-5_percase5_seed42424.js
# Expected: 1001 lines (1000 problems + 1 header)
```

**Use validation dataset to**:
- Test all 6 experiment configs work
- Validate parsing and prompts are correct
- Get initial accuracy estimates per model
- Discuss preliminary results with supervisors
- Estimate full run cost and time

#### Step 2: Production Dataset (After Validation Success)

```bash
# Generate PRODUCTION dataset (takes ~60-120 minutes)
python experiments/makeproblems.py \
  --vars 1-20 \
  --clens 2-5 \
  --horn mixed \
  --percase 40 \
  --seed 42424 \
  --workers 4 \
  > data/problems_production_vars1-20_len2-5_percase40_seed42424.js

# Quick stats check
wc -l data/problems_production_vars1-20_len2-5_percase40_seed42424.js
# Expected: 8001 lines (8000 problems + 1 header)
```

### Alternative: Quick Test (Even Smaller)

For super-quick sanity check (not recommended for real validation):

```bash
# Tiny test: vars 1-8, len 1-3, 2 per case
# Total: 8 × 3 × 2 × 2 = 96 problems
python experiments/makeproblems.py \
  --vars 1-8 \
  --clens 1-3 \
  --horn mixed \
  --percase 2 \
  --seed 42424 \
  --workers 4 \
  > data/problems_quicktest_vars1-8_len1-3_percase2_seed42424.js
```

**Use only for**: Testing prompts render correctly, configs work, no crashes.

---

## Using Runner with Validation Dataset

The runner has a `--limit` option to process only N problems from any dataset:

```bash
# Test with validation dataset (1000 problems)
python -m experiments.runner \
  --config experiments/configs/horn_yn_hornonly.yaml \
  --resume \
  --run validation_001

# Or test just first 100 problems from validation dataset
python -m experiments.runner \
  --config experiments/configs/horn_yn_hornonly.yaml \
  --limit 100 \
  --resume \
  --run quicktest_001
```

**Recommended validation workflow**:
1. Generate validation dataset (5 per case, 1000 total)
2. Run all 6 experiments on validation dataset
3. Analyze results, discuss with supervisors
4. If good → Generate production dataset (40 per case, 8000 total)
5. Run full suite on production dataset

---

## Verification Steps

After generation, verify the dataset:

```bash
# Verify VALIDATION dataset
python3 -c "
import json

# Change filename to match your dataset
DATASET='data/problems_validation_vars1-20_len2-5_percase5_seed42424.js'

with open(DATASET) as f:
    lines = [l.strip() for l in f if l.strip()]

# Skip header
problems = []
for line in lines[1:]:
    p = json.loads(line)
    problems.append({
        'id': p[0],
        'maxvars': p[1],
        'maxlen': p[2],
        'horn': p[3],
        'sat': p[4],
    })

print(f'Total: {len(problems)} problems')
print(f'Horn: {sum(1 for p in problems if p[\"horn\"]==1)}')
print(f'Non-Horn: {sum(1 for p in problems if p[\"horn\"]==0)}')
print(f'Sat: {sum(1 for p in problems if p[\"sat\"]==1)}')
print(f'Unsat: {sum(1 for p in problems if p[\"sat\"]==0)}')

from collections import Counter
var_dist = Counter(p['maxvars'] for p in problems)
len_dist = Counter(p['maxlen'] for p in problems)

print(f'\\nVars distribution:')
for k in sorted(var_dist.keys()):
    print(f'  {k}: {var_dist[k]}')

print(f'\\nLengths distribution:')
for k in sorted(len_dist.keys()):
    print(f'  {k}: {len_dist[k]}')
"

# For PRODUCTION dataset, change DATASET variable above to:
# DATASET='data/problems_production_vars1-20_len2-5_percase40_seed42424.js'
```

Or use this shorter verification:

```bash
# Count lines
wc -l data/problems_validation_vars1-20_len2-5_percase5_seed42424.js
# Expected: 1001 (validation) or 8001 (production)

# Quick check of first few problems
head -5 data/problems_validation_vars1-20_len2-5_percase5_seed42424.js
```

```
Total: 1000 problems
Horn: 500
Non-Horn: 500
Sat: 500
Unsat: 500

Vars distribution:
  1: 40
  2: 50
  ... (should be 50 per vars level)
  20: 40

Lengths distribution:
  1: 160
  2: 200
  3: 200
  4: 200
  5: 160
```

**Expected output for production dataset** (40 per case):
```
Total: 8000 problems
Horn: 4000
Non-Horn: 4000
Sat: 4000
Unsat: 4000

Vars distribution:
  1: 320
  2: 400
  3: 400
  ... (should be 400 per vars level)
  20: 320

Lengths distribution:
  1: 1280
  2: 1600
  3: 1600
  4: 1600
  5: 1280
```

---

## Dataset Naming Convention

Use descriptive names:

```
problems_<purpose>_vars<range>_len<range>_seed<seed>.js

Examples:
- problems_production_vars3-18_len3-5_seed42424.js
- problems_test_vars3-10_len3-4_seed42424.js
- problems_extended_vars3-20_len3-5_seed42424.js
```

---

## Performance Notes

### Generation Time

With `--workers 4`:
- 96 problems (quick test): ~2-3 minutes
- 800 problems (validation): ~8-15 minutes
- 6,400 problems (production): ~60-120 minutes (1-2 hours)

**Bottleneck**: Truth table solving for larger variable counts (17-20 vars)

**Note**: Variables 1-2 are very fast. Variables 15-20 are significantly slower due to exponential truth table complexity.

**Generation strategy**: Start with validation (5 per case) to test everything, then run production (40 per case) overnight.

### Optimization Options

1. **Use `--no-proof` flag** if you don't need full resolution proofs:
   ```bash
   python experiments/makeproblems.py \
     --vars 1-20 \
     --clens 2-5 \
     --horn mixed \
     --percase 20 \
     --seed 42424 \
     --workers 4 \
     --no-proof \
     > data/problems_production_vars1-20_len2-5_seed42424_noproof.js
   ```
   This is **much faster** (2-3× speedup) but proofs won't be available for depth analysis.
   
   **Recommendation**: Use `--no-proof` for test datasets, include proofs for production.

2. **Increase workers** if you have more CPU cores:
   ```bash
   --workers 8  # or more
   ```

3. **Generate in stages** for very large datasets:
   ```bash
   # Generate separate datasets and concatenate
   python experiments/makeproblems.py --vars 1-10 ... > data/part1.js
   python experiments/makeproblems.py --vars 11-20 ... > data/part2.js
   
   # Then merge (skip header from part2)
   head -1 data/part1.js > data/merged.js
   tail -n +2 data/part1.js >> data/merged.js
   tail -n +2 data/part2.js >> data/merged.js
   ```

---

## Next Steps

After generating the dataset:

1. ✅ **Verify** the dataset (see Verification Steps above)
2. ✅ **Update experiment configs** to point to new dataset:
   ```yaml
   input_file: data/problems_production_vars3-18_len3-5_seed42424.js
   ```
3. ✅ **Test run** with `--limit 10` to validate
4. ✅ **Full run** all 6 experiments with the dataset

---

## Comparison with Existing Datasets

| Dataset | Vars | Lens | Per Case | Total | Purpose | Cost (6 exp × 12 models) |
|---------|------|------|----------|-------|---------|--------------------------|
| `problems_dist20_v1.js` | 3-15 | 3-4 | 20 | 1,040 | Legacy reference | ~$500-$800 |
| Quick test | 1-8 | 1-3 | 2 | 96 | Config sanity check | ~$25-$50 |
| **Validation** | 1-20 | 1-5 | **5** | **1,000** | **Initial validation** | **~$150-$250** |
| **Production** | 1-20 | 1-5 | **40** | **8,000** | **Publication quality** | **~$2,400-$4,000** |

**Recommended workflow**:
1. ✅ **Start with validation dataset** (5 per case, 800 problems)
   - Test all configs work correctly
   - Get initial accuracy estimates
   - Discuss results with supervisors
   - Cost: ~$150-$250, Time: ~8-12 hours
   
2. ✅ **Move to production dataset** (40 per case, 6,400 problems)
   - Publication-quality statistics
   - 400 samples per variable level
   - Robust degradation curves
   - Cost: ~$2,400-$4,000, Time: ~66-96 hours (3-4 days)

---

## Troubleshooting

### Generation hangs or is very slow

**Problem**: Generation stuck on high-variable cases (17-20 vars)

**Solution**: 
- Reduce max vars to 15-16
- Use `--no-proof` for faster generation
- Increase `--workers`

### "too many variables for truth table solver"

**Problem**: Trying to generate >20 variables

**Solution**: The truth table solver only supports up to 20 variables. Use `--vars 1-20` maximum.

### Unbalanced distribution

**Problem**: Not getting 50/50 sat/unsat split

**Solution**: This is normal randomness. The script tries to balance but may be slightly off. Should be close to 50/50 overall.

### Memory errors with many workers

**Problem**: Out of memory with `--workers 8`

**Solution**: Reduce workers to 2-4. Problem generation is CPU-bound, not memory-bound, so more workers beyond CPU count doesn't help much.

---

**Ready to generate?** Run the production command above and proceed with EXPERIMENT_CHECKLIST.md Phase 1.2!

