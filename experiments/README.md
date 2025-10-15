# Experiments Directory

Systematic LLM logic reasoning evaluation framework.

---

## 📚 Documentation

### Start Here
1. **[SETUP_GUIDE.md](SETUP_GUIDE.md)** — Complete setup and execution guide (START HERE!)
2. **[DASHBOARD_DESIGN.md](DASHBOARD_DESIGN.md)** — Analysis plan and 6 research questions (for after results)

### Configuration Files
- **[configs/README.md](configs/README.md)** — Overview of 6 experiment configs

---

## 🎯 Current Status

✅ **Ready for validation run!**

- [x] Validation dataset generated (544 problems)
- [x] 6 experiment configs created
- [x] All 12 models configured
- [x] Prompts tested and working
- [ ] Run validation suite (~$100-160, 5-8 hours)
- [ ] Analyze and discuss results
- [ ] Generate production dataset
- [ ] Run production suite
- [ ] Build dashboard

---

## ⚡ Quick Commands

### Test
```bash
# Dry-run (no API calls)
python -m experiments.runner \
  --config experiments/configs/horn_yn_hornonly.yaml \
  --limit 5 --dry-run
```

### Run Validation
```bash
for config in experiments/configs/horn_*.yaml experiments/configs/cnf*.yaml; do
  python -m experiments.runner --config "$config" --resume --run validation_001
done
```

### Analyze
```bash
python -m experiments.analyze_generic \
  experiments/runs/horn_yn_hornonly/validation_001/anthropic/claude-sonnet*/results.jsonl
```

---

## 📊 What You Have

**Validation Dataset**:
- 544 problems (vars 4-20, lengths 2-5)
- 272 Horn + 272 Non-Horn
- Perfectly balanced

**6 Experiments**:
- Test different representations (horn, cnf_v1, cnf_v2)
- Test different filters (horn_only vs mixed)
- Test different tasks (yes_no vs contradiction)

**12 Models**:
- 3 tiers × 3 providers
- With and without extended thinking
- Identical across all experiments

**Expected validation cost**: ~$100-$160  
**Expected validation time**: ~5-8 hours

---

## 🔬 Research Questions

1. Does representation matter?
2. Can models handle representation mismatch?
3. When do models break down?
4. Is extended thinking worth it?
5. Which tier should I use?
6. Which model is best for what?

See **DASHBOARD_DESIGN.md** for detailed analysis plan.

---

## 🚀 Next Steps

1. **Test one config** with `--limit 10`
2. **Run validation suite** (all 6 experiments)
3. **Analyze results** and discuss with supervisors
4. **Generate production dataset** (5,440 problems)
5. **Run production suite** (~2-3 days)
6. **Build dashboard** and answer research questions

**Start with**: [SETUP_GUIDE.md](SETUP_GUIDE.md)

