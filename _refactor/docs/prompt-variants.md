## Prompt variants (examples-only vs algorithmic)

This document describes the prompt variants introduced for controlled experiments where we **keep parsing stable** (single answer token on the last line) while allowing **long reasoning traces** to be captured in provenance.

### Shared parsing contract
- **Final answer token**: every template instructs the model to output exactly **one** final word on the **last line**:
  - `contradiction` (UNSAT)
  - `satisfiable` (SAT)
  - `unknown` (only if genuinely undecidable)
- **Reasoning trace**: templates explicitly allow printing any amount of reasoning above the final answer.
- **Why this works**: the `_refactor` parser prefers the **last decisive token**, so intermediate uses of words like “contradiction” in the trace won’t break parsing.

Where the trace is saved:
- `runs/<suite>/<run>/<provider>/<model>/<thinking_mode>/results.provenance.jsonl`
  - `completion_text`: full model output (this is where the trace lives)
  - `raw_response`: provider response (best-effort)
  - `thinking_text`: provider-returned reasoning summaries when available (often partial; OpenAI usually does not return full hidden reasoning)

### Representation variants (“compact” vs “normal”)
These correspond to the suite `representation` and the template name:
- **compact CNF** (`representation: cnf_compact`)
  - Literals are `pN` / `not(pN)`
  - Template prefix: `sat_decision__cnf_compact__...`
- **natural-language CNF** (`representation: cnf_nl`)
  - Literals are `pN is true` / `pN is false`
  - Template prefix: `sat_decision__cnf_nl__...`

### Prompt styles

#### 1) Examples-only (no explicit algorithm)
Goal: a “few-shot” baseline that gives **examples** but does not prescribe a method.

Templates:
- `prompts/sat_decision__cnf_compact__examples_only.j2`
- `prompts/sat_decision__cnf_nl__examples_only.j2`

Suites (run on either subset):
- `...__prompt-examples_only__...`

#### 2) Horn algorithm (linear trace)
Goal: prescribe the standard **Horn-SAT forward chaining** procedure. The trace is primarily the **ordered list of derived true variables**.

Templates:
- `prompts/sat_decision__cnf_compact__horn_alg_linear.j2`
- `prompts/sat_decision__cnf_nl__horn_alg_linear.j2`

Suites:
- `subset: hornonly` and `...__prompt-horn_alg_linear__...`

#### 3) Horn algorithm (“from” / provenance)
Goal: same Horn-SAT forward chaining, but also request **why** each variable was derived:
- `pX from Sk using pA pB ...`

Templates:
- `prompts/sat_decision__cnf_compact__horn_alg_from.j2`
- `prompts/sat_decision__cnf_nl__horn_alg_from.j2`

Suites:
- `subset: hornonly` and `...__prompt-horn_alg_from__...`

When to use:
- You want a more auditable trace (“parents/from” style), at the cost of longer outputs.

#### 4) Non-Horn algorithm (DPLL trace)
Goal: prescribe a general SAT solver method suitable for **non-Horn** CNF:
- unit propagation
- (optional) pure literals
- branching/backtracking

Templates:
- `prompts/sat_decision__cnf_compact__dpll_alg_linear.j2`
- `prompts/sat_decision__cnf_nl__dpll_alg_linear.j2`

Suites:
- `subset: nonhornonly` and `...__prompt-dpll_alg_linear__...`

#### 5) Non-Horn algorithm (“from” / clause provenance)
Goal: DPLL trace, but also request the forcing clause for unit propagations:
- `assign p7 from Ci`
- `conflict at Ci`

Templates:
- `prompts/sat_decision__cnf_compact__dpll_alg_from.j2`
- `prompts/sat_decision__cnf_nl__dpll_alg_from.j2`

Suites:
- `subset: nonhornonly` and `...__prompt-dpll_alg_from__...`


