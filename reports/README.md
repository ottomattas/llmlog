## Reports (committed artifacts)

This directory contains **committed** analysis artifacts that are useful for paper traceability and review.

### Paper figures

`reports/paper_figures/` contains:
- PDF figures used by the paper draft
- PNG thumbnails (`_thumbs/`) for quick review
- A **source report** showing exactly which run(s) were used per model:
  - `paper_figures.selection.md`
  - `paper_figures.selection.json`

To regenerate from the latest `_refactor/runs/**/results.jsonl`:

```bash
/Users/ottomattas/Downloads/repos/llmlog/venv/bin/python _refactor/scripts/generate_paper_figures.py \
  --runs-dir _refactor/runs \
  --output-dir reports/paper_figures \
  --run-selection reports/paper_figures/run_selection.yaml
```

