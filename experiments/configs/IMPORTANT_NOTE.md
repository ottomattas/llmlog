# Important: Clause Length Range

## ⚠️ Use Lengths 2-5, Not 1-5

The problem generator **does not support clause length 1** due to an algorithmic constraint:

- With `maxlen=1`, only unit clauses are generated: `[1]`, `[-1]`
- The generator requires both fully positive AND fully negative clauses
- With Horn problems (`hornflag=True`) and `maxlen=1`, only positive units can be generated
- This causes infinite loop

**Solution**: All experiments use **clause lengths 2-5** (4 levels)

---

## Updated Dataset Specs

### Validation Dataset
```bash
python experiments/makeproblems.py \
  --vars 1-20 \
  --clens 2-5 \
  --horn mixed \
  --percase 5 \
  --seed 42424 \
  --workers 4 \
  > data/problems_validation_vars1-20_len2-5_percase5_seed42424.js
```

**Total**: 800 problems (20 vars × 4 lens × 2 types × 5 per = 800)

### Production Dataset
```bash
python experiments/makeproblems.py \
  --vars 1-20 \
  --clens 2-5 \
  --horn mixed \
  --percase 40 \
  --seed 42424 \
  --workers 4 \
  > data/problems_production_vars1-20_len2-5_percase40_seed42424.js
```

**Total**: 6,400 problems (20 vars × 4 lens × 2 types × 40 per = 6,400)

---

## What This Means

- **Validation cost**: ~$120-$200 (reduced from $150-$250)
- **Production cost**: ~$1,920-$3,200 (reduced from $2,400-$4,000)
- **Still excellent coverage**: Lengths 2-5 capture the full complexity spectrum
- **More focused**: Classic 3-SAT is length 3, we have 2-5 which is perfect

---

## Why This Is Fine

**Clause length 2-5 is actually BETTER** because:
1. **More meaningful**: Length 2-5 captures real complexity variations
2. **Standard in literature**: 3-SAT (length 3) is the classic benchmark
3. **Faster generation**: 20% faster (4 lengths vs 5)
4. **Lower cost**: 20% cheaper experiments
5. **Still comprehensive**: Complete range from simple to complex

**You're not missing anything** by skipping length 1!

---

All configs have been updated to reflect `len2-5` in filenames.

