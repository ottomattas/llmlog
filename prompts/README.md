# Prompts: Logic Representations and Authoring Guidance

This folder contains Jinja templates used by `experiments/runner.py` to render logic problems for models.

Mental model
- Representation (encoding): how problems are written for the LLM
  - `horn_if_then`: facts (`pN.`) and rules (`if pA and pB then pC.`). Used for goal-directed entailment (derive p0?).
  - `cnf_v1`: verbose CNF with natural-language form: `pN is true` / `pM is false`, joined by `or`.
  - `cnf_v2`: compact CNF with symbolic `pN` and `not(pM)`, joined by `or`.
- Task (label scheme): what output we expect and how it’s parsed
  - `yes_no`: final label `yes` or `no` (Horn entailment of p0)
  - `contradiction`: final last token `contradiction` or `satisfiable`/`unknown` (CNF SAT framing)

When to use which representation
- Use `horn_if_then` when you want goal entailment and concise outputs (pairs naturally with `yes_no`).
- Use `cnf_v1` when emphasizing readability and NL scaffolding; pairs with `contradiction`.
- Use `cnf_v2` when emphasizing token-efficiency and symbolic cues; pairs with `contradiction`.

Template contract
- Each template must contain a `{{ clauses }}` placeholder; the runner will inject the rendered clauses based on the chosen representation.
- Keep instructions minimal and unambiguous to stabilize parsing (especially for `yes_no` and last-token extraction).

Authoring tips
- Avoid extra concluding words after the final label; parsers rely on clean last tokens for `contradiction` and token scans for `yes_no`.
- Prefer examples that match the representation and task to nudge models toward the expected reasoning and output format.
- Keep variable names as `pN` consistently.

Files of interest
- `_template_unified.j2`: generic prompt compatible with both Horn and CNF clause injections.
- `exp*_*.j2`: historical/task-specific prompts with additional instructions or examples.
