## Prompt catalog
This catalog lists each distinct prompt *condition* (template + style + answer-family + injected rules), so figures can reference the exact instructions given to the model.

### prompt_0b276d34e8
- prompt_template: `prompts/_template_unified.j2`
- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- leaf_runs_count: 48

Instruction text (before `Statements:`):

```
Your task is to solve a propositional logic problem.

Choose the appropriate interpretation based on how the statements are rendered below.
- If you see facts like "p1." and rules like "if p2 and p3 then p4.", treat them as Horn facts and implications, and determine whether p0 can be derived.
- If you see disjunctions like "p1 is true or p2 is false." or compact forms like "p1 or not(p2).", treat them as CNF clauses, and determine whether the set is a contradiction (unsatisfiable) or satisfiable.

Conventions
- Propositional variables are written as pN, where N is a number.
- All statements are jointly assumed true (conjoined).

Answer format
- For Horn tasks (style: horn_if_then): Output exactly one final word on the last line, lowercase with no punctuation: "yes" if p0 is derivable from the given facts and rules; otherwise "no". Do not output any other words (do not output "contradiction"/"satisfiable"/"unknown").
- For CNF contradiction tasks (styles: cnf_v1 or cnf_v2): Output exactly one final word on the last line, lowercase with no punctuation: "contradiction" if the set is a contradiction (unsatisfiable); otherwise "satisfiable", or "unknown" if undecidable. Do not output any other words (do not output "yes"/"no").

Examples (Horn, yes/no)
- p1. if p1 then p0. → yes
- p1. if p1 then p9. → no
- p1. if p1 then p2. if p2 then p0. → yes

Examples (CNF, contradiction)
- p1 is true. not(p1) or p2. p2 is false. → contradiction.
- p1. not(p1) or p2. not(p2). → contradiction.
- p1. p1 or p2. not(p2). → satisfiable.
```

Examples (horn=0):

- low: maxvars=4, maxlen=2, satflag=1

```
p4 is true.
p4 is false or p1 is false.
p3 is false or p1 is false.
p3 is false or p4 is true.
p2 is false or p1 is false.
p1 is false or p4 is true.
p2 is true or p4 is true.
```

- mid: maxvars=10, maxlen=4, satflag=1

```
p9 is true or p10 is true.
p10 is false or p3 is true or p9 is true.
p9 is false or p8 is false or p4 is true.
p9 is false or p7 is false or p4 is false.
p9 is false or p3 is true or p4 is true.
p8 is false or p5 is false or p2 is true.
p8 is false or p4 is false or p1 is true.
p8 is false or p3 is false or p9 is true.
p8 is false or p2 is true or p3 is true.
p8 is false or p2 is true or p9 is true.
p6 is false or p1 is false or p2 is true.
p5 is false or p3 is false or p8 is true.
p5 is false or p1 is false or p6 is true.
p5 is false or p1 is false or p7 is true.
p5 is false or p3 is true or p4 is true.
p5 is false or p6 is true or p7 is true.
p4 is false or p3 is false or p1 is true.
p4 is false or p3 is false or p5 is true.
p4 is false or p3 is false or p10 is true.
p4 is false or p2 is false or p10 is true.
p3 is false or p2 is true or p9 is true.
p3 is false or p7 is true or p9 is true.
p2 is false or p1 is false or p7 is true.
p1 is true or p3 is true or p4 is true.
p1 is true or p4 is true or p5 is true.
p1 is true or p4 is true or p10 is true.
p2 is true or p4 is true or p5 is true.
p2 is true or p5 is true or p10 is true.
p2 is true or p9 is true or p10 is true.
p3 is true or p7 is true or p10 is true.
p7 is true or p8 is true or p9 is true.
p10 is false or p9 is false or p5 is false or p7 is true.
p10 is false or p8 is false or p1 is true or p3 is true.
p10 is false or p8 is false or p4 is true or p9 is true.
p10 is false or p7 is false or p3 is false or p2 is true.
p10 is false or p7 is false or p3 is false or p8 is true.
p10 is false or p6 is false or p1 is false or p9 is true.
p10 is false or p6 is false or p4 is true or p5 is true.
p10 is false or p5 is false or p1 is true or p9 is true.
p10 is false or p3 is false or p4 is true or p7 is true.
p10 is false or p2 is false or p3 is true or p9 is true.
p10 is false or p1 is false or p4 is true or p6 is true.
p9 is false or p7 is false or p1 is true or p5 is true.
p9 is false or p6 is false or p5 is false or p1 is false.
p8 is false or p7 is false or p6 is false or p5 is true.
p8 is false or p7 is false or p5 is false or p9 is true.
p8 is false or p7 is false or p3 is false or p2 is true.
p8 is false or p5 is false or p2 is false or p1 is true.
p8 is false or p5 is false or p2 is true or p6 is true.
p8 is false or p5 is false or p4 is true or p10 is true.
p8 is false or p3 is false or p2 is true or p4 is true.
p7 is false or p6 is false or p1 is true or p4 is true.
p7 is false or p5 is false or p2 is false or p10 is true.
p7 is false or p5 is false or p1 is false or p3 is true.
p7 is false or p5 is false or p1 is false or p10 is true.
p7 is false or p4 is false or p3 is false or p2 is true.
p7 is false or p4 is false or p2 is true or p8 is true.
p7 is false or p2 is false or p3 is true or p5 is true.
p7 is false or p2 is true or p5 is true or p6 is true.
p6 is false or p5 is false or p4 is false or p9 is true.
p6 is false or p4 is false or p2 is true or p9 is true.
p6 is false or p4 is false or p8 is true or p10 is true.
p6 is false or p3 is false or p2 is false or p4 is true.
p6 is false or p1 is true or p7 is true or p9 is true.
p6 is false or p2 is true or p5 is true or p10 is true.
p5 is false or p1 is false or p3 is true or p9 is true.
p5 is false or p1 is false or p8 is true or p9 is true.
p5 is false or p7 is true or p8 is true or p9 is true.
p4 is false or p2 is true or p3 is true or p10 is true.
p4 is false or p3 is true or p6 is true or p10 is true.
p3 is false or p2 is true or p4 is true or p7 is true.
p2 is false or p1 is true or p3 is true or p7 is true.
p2 is false or p4 is true or p6 is true or p7 is true.
p1 is false or p2 is true or p4 is true or p7 is true.
p3 is true or p6 is true or p7 is true or p8 is true.
p4 is true or p5 is true or p6 is true or p10 is true.
```

- high: maxvars=15, maxlen=3, satflag=0

```
p14 is false or p10 is true.
p12 is false or p10 is false.
p12 is false or p2 is true.
p11 is false or p2 is false.
p7 is false or p6 is true.
p5 is false or p2 is true.
p2 is true or p9 is true.
p6 is true or p10 is true.
p8 is true or p14 is true.
p15 is false or p11 is false or p10 is false.
p15 is false or p9 is false or p6 is false.
p15 is false or p9 is false or p10 is true.
p15 is false or p6 is false or p1 is false.
p15 is false or p4 is true or p14 is true.
p14 is false or p4 is false or p3 is false.
p14 is false or p3 is false or p9 is true.
p14 is false or p2 is true or p12 is true.
p13 is false or p12 is false or p7 is true.
p13 is false or p12 is false or p9 is true.
p13 is false or p10 is false or p14 is true.
p13 is false or p9 is false or p6 is false.
p13 is false or p8 is false or p6 is false.
p13 is false or p8 is false or p12 is true.
p13 is false or p3 is false or p8 is true.
p11 is false or p9 is false or p4 is true.
p11 is false or p4 is false or p1 is false.
p11 is false or p7 is true or p15 is true.
p10 is false or p4 is false or p1 is false.
p10 is false or p3 is false or p4 is true.
p10 is false or p1 is true or p6 is true.
p9 is false or p7 is false or p4 is true.
p9 is false or p2 is true or p7 is true.
p8 is false or p7 is false or p5 is false.
p8 is false or p5 is false or p10 is true.
p8 is false or p3 is false or p15 is true.
p8 is false or p2 is false or p1 is true.
p8 is false or p10 is true or p13 is true.
p7 is false or p4 is false or p15 is true.
p7 is false or p2 is false or p1 is false.
p7 is false or p2 is true or p10 is true.
p7 is false or p6 is true or p12 is true.
p6 is false or p3 is false or p1 is false.
p6 is false or p2 is false or p1 is false.
p6 is false or p1 is true or p10 is true.
p6 is false or p9 is true or p13 is true.
p4 is false or p7 is true or p13 is true.
p3 is false or p4 is true or p13 is true.
p3 is false or p8 is true or p14 is true.
p2 is false or p1 is false or p4 is true.
p2 is false or p7 is true or p8 is true.
p2 is false or p7 is true or p14 is true.
p2 is false or p8 is true or p11 is true.
p1 is false or p12 is true or p14 is true.
p1 is true or p8 is true or p9 is true.
p1 is true or p8 is true or p12 is true.
p1 is true or p12 is true or p15 is true.
p2 is true or p10 is true or p13 is true.
p3 is true or p7 is true or p14 is true.
p4 is true or p8 is true or p13 is true.
p4 is true or p13 is true or p15 is true.
```

Examples (horn=1):

- low: maxvars=4, maxlen=2, satflag=1

```
p4 is false.
p2 is true.
p3 is false or p1 is true.
p3 is false or p4 is true.
p2 is false or p1 is true.
```

- mid: maxvars=12, maxlen=4, satflag=1

```
p1 is true.
p3 is true.
p4 is true.
p5 is true.
p8 is true.
p12 is false or p1 is true.
p12 is false or p8 is true.
p9 is false or p5 is true.
p8 is false or p7 is true.
p8 is false or p11 is true.
p7 is false or p12 is true.
p4 is false or p2 is true.
p4 is false or p7 is true.
p3 is false or p2 is true.
p3 is false or p9 is true.
p2 is false or p6 is true.
p12 is false or p4 is false or p6 is true.
p11 is false or p10 is false or p6 is true.
p11 is false or p1 is false or p4 is true.
p10 is false or p9 is false or p4 is true.
p10 is false or p3 is false or p2 is true.
p9 is false or p6 is false or p1 is true.
p8 is false or p7 is false or p12 is true.
p7 is false or p3 is false or p1 is true.
p7 is false or p3 is false or p8 is true.
p7 is false or p1 is false or p5 is true.
p3 is false or p2 is false or p12 is true.
p12 is false or p9 is false or p5 is false or p6 is true.
p12 is false or p7 is false or p3 is false or p8 is true.
p12 is false or p7 is false or p1 is false or p9 is true.
p12 is false or p6 is false or p3 is false or p4 is true.
p11 is false or p9 is false or p5 is false or p12 is true.
p10 is false or p7 is false or p6 is false or p2 is false.
p10 is false or p7 is false or p2 is false or p11 is true.
p9 is false or p7 is false or p5 is false or p6 is true.
p7 is false or p6 is false or p4 is false or p8 is true.
p6 is false or p2 is false or p1 is false or p7 is true.
```

- high: maxvars=20, maxlen=5, satflag=0

```
p6 is true.
p11 is true.
p16 is true.
p17 is true.
p20 is false or p2 is true.
p20 is false or p10 is true.
p20 is false or p14 is true.
p19 is false or p9 is true.
p18 is false or p2 is true.
p16 is false or p11 is true.
p15 is false or p14 is true.
p15 is false or p17 is true.
p14 is false or p19 is true.
p12 is false or p8 is true.
p11 is false or p8 is true.
p9 is false or p1 is true.
p9 is false or p15 is true.
p8 is false or p4 is true.
p8 is false or p12 is true.
p7 is false or p1 is true.
p6 is false or p11 is true.
p3 is false or p2 is true.
p2 is false or p14 is true.
p2 is false or p18 is true.
p2 is false or p19 is true.
p20 is false or p10 is false or p7 is true.
p20 is false or p3 is false or p13 is true.
p19 is false or p8 is false or p18 is true.
p18 is false or p9 is false or p3 is true.
p17 is false or p11 is false or p10 is true.
p17 is false or p10 is false or p14 is true.
p16 is false or p14 is false or p3 is true.
p16 is false or p10 is false or p13 is true.
p15 is false or p11 is false or p19 is true.
p15 is false or p9 is false or p10 is true.
p15 is false or p6 is false or p4 is true.
p15 is false or p5 is false or p6 is true.
p14 is false or p12 is false or p4 is true.
p14 is false or p9 is false or p20 is true.
p14 is false or p6 is false or p9 is true.
p14 is false or p5 is false or p16 is true.
p14 is false or p4 is false or p11 is true.
p14 is false or p2 is false or p1 is true.
p12 is false or p9 is false or p17 is true.
p12 is false or p2 is false or p11 is true.
p11 is false or p7 is false or p8 is true.
p11 is false or p7 is false or p16 is true.
p11 is false or p5 is false or p7 is true.
p11 is false or p3 is false or p13 is true.
p10 is false or p5 is false or p4 is true.
p10 is false or p2 is false or p18 is true.
p10 is false or p1 is false or p16 is true.
p9 is false or p1 is false or p15 is true.
p8 is false or p4 is false or p3 is true.
p8 is false or p1 is false or p4 is true.
p6 is false or p4 is false or p18 is true.
p4 is false or p2 is false or p3 is true.
p20 is false or p16 is false or p14 is false or p10 is true.
p20 is false or p15 is false or p14 is false or p16 is true.
p20 is false or p12 is false or p8 is false or p4 is true.
p19 is false or p5 is false or p4 is false or p16 is true.
p18 is false or p16 is false or p15 is false or p13 is true.
p18 is false or p15 is false or p9 is false or p4 is false.
p18 is false or p15 is false or p7 is false or p13 is true.
p18 is false or p11 is false or p5 is false or p4 is true.
p17 is false or p16 is false or p9 is false or p13 is true.
p17 is false or p13 is false or p2 is false or p10 is true.
p17 is false or p13 is false or p1 is false or p4 is true.
p17 is false or p9 is false or p6 is false or p14 is true.
p16 is false or p14 is false or p3 is false or p18 is true.
p16 is false or p9 is false or p4 is false or p19 is true.
p16 is false or p2 is false or p1 is false or p17 is true.
p15 is false or p10 is false or p6 is false or p20 is true.
p15 is false or p9 is false or p3 is false or p10 is true.
p14 is false or p12 is false or p4 is false or p1 is true.
p14 is false or p10 is false or p8 is false or p1 is true.
p14 is false or p8 is false or p2 is false or p10 is true.
p13 is false or p11 is false or p1 is false or p17 is true.
p12 is false or p9 is false or p8 is false or p18 is true.
p12 is false or p7 is false or p3 is false or p2 is false.
p10 is false or p8 is false or p7 is false or p18 is true.
p6 is false or p4 is false or p3 is false or p20 is true.
p20 is false or p17 is false or p14 is false or p8 is false or p19 is true.
p19 is false or p17 is false or p12 is false or p2 is false or p10 is true.
p18 is false or p17 is false or p16 is false or p6 is false or p10 is true.
p17 is false or p12 is false or p10 is false or p6 is false or p19 is true.
p17 is false or p12 is false or p10 is false or p1 is false or p2 is true.
p16 is false or p15 is false or p10 is false or p1 is false or p9 is true.
p16 is false or p9 is false or p4 is false or p3 is false or p13 is true.
p14 is false or p12 is false or p7 is false or p5 is false or p20 is true.
p13 is false or p10 is false or p4 is false or p1 is false or p8 is true.
p8 is false or p7 is false or p3 is false or p1 is false or p17 is true.
```


---

### prompt_154dcb992a
- prompt_template: ``
- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- leaf_runs_count: 1

_No provenance prompt text was available for this prompt_id._

Examples (horn=1):

- low: maxvars=4, maxlen=2, satflag=1

_Example statements unavailable (missing prompt text)._\

- mid: maxvars=4, maxlen=2, satflag=1

_Example statements unavailable (missing prompt text)._\

- high: maxvars=4, maxlen=2, satflag=1

_Example statements unavailable (missing prompt text)._\


---

### prompt_21889a86a3
- prompt_template: `prompts/_template_unified.j2`
- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- leaf_runs_count: 96

Instruction text (before `Statements:`):

```
Your task is to solve a propositional logic problem.

Choose the appropriate interpretation based on how the statements are rendered below.
- If you see facts like "p1." and rules like "if p2 and p3 then p4.", treat them as Horn facts and implications, and determine whether p0 can be derived.
- If you see disjunctions like "p1 is true or p2 is false." or compact forms like "p1 or not(p2).", treat them as CNF clauses, and determine whether the set is a contradiction (unsatisfiable) or satisfiable.

Conventions
- Propositional variables are written as pN, where N is a number.
- All statements are jointly assumed true (conjoined).

Answer format
- For Horn tasks (style: horn_if_then): Output only a final single word "yes" if p0 is derivable from the given facts and rules, or "no" otherwise.
- For CNF contradiction tasks (styles: cnf_v1 or cnf_v2): Output a final single word as your last token: "contradiction" if the set is a contradiction (unsatisfiable), otherwise "satisfiable" or "unknown".

Examples (Horn, yes/no)
- p1. if p1 then p0. → yes
- p1. if p1 then p9. → no
- p1. if p1 then p2. if p2 then p0. → yes

Examples (CNF, contradiction)
- p1 is true. not(p1) or p2. p2 is false. → contradiction.
- p1. not(p1) or p2. not(p2). → contradiction.
- p1. p1 or p2. not(p2). → satisfiable.
```

Examples (horn=0):

- low: maxvars=4, maxlen=2, satflag=1

```
p4 is true.
p4 is false or p1 is false.
p3 is false or p1 is false.
p3 is false or p4 is true.
p2 is false or p1 is false.
p1 is false or p4 is true.
p2 is true or p4 is true.
```

- mid: maxvars=4, maxlen=2, satflag=1

```
p4 is true.
p4 is false or p1 is false.
p3 is false or p1 is false.
p3 is false or p4 is true.
p2 is false or p1 is false.
p1 is false or p4 is true.
p2 is true or p4 is true.
```

- high: maxvars=4, maxlen=2, satflag=0

```
p1 is false.
p4 is false or p2 is true.
p3 is false or p2 is false.
p2 is false or p4 is true.
p1 is false or p4 is true.
p1 is true or p2 is true.
p1 is true or p3 is true.
```

Examples (horn=1):

- low: maxvars=4, maxlen=2, satflag=1

```
p4 is false.
p2 is true.
p3 is false or p1 is true.
p3 is false or p4 is true.
p2 is false or p1 is true.
```

- mid: maxvars=4, maxlen=2, satflag=0

```
p2 is false.
p3 is true.
p3 is false or p1 is false.
p3 is false or p2 is true.
p1 is false or p4 is true.
```

- high: maxvars=4, maxlen=3, satflag=0

```
p3 is true.
p4 is false or p1 is false.
p4 is false or p1 is true.
p4 is false or p3 is true.
p3 is false or p1 is false.
p3 is false or p1 is true.
p3 is false or p4 is true.
p3 is false or p1 is false or p4 is true.
```


---

### prompt_2376d1fca7
- prompt_template: `prompts/_template_unified.j2`
- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- leaf_runs_count: 12

Instruction text (before `Statements:`):

```
Your task is to solve a propositional logic problem.

Choose the appropriate interpretation based on how the statements are rendered below.
- If you see facts like "p1." and rules like "if p2 and p3 then p4.", treat them as Horn facts and implications, and determine whether p0 can be derived.
- If you see disjunctions like "p1 is true or p2 is false." or compact forms like "p1 or not(p2).", treat them as CNF clauses, and determine whether the set is a contradiction (unsatisfiable) or satisfiable.
Unified answer rule (mixed cases)
- Regardless of how the statements are rendered, output only a final single word: "yes" if p0 is derivable OR the set is a contradiction; otherwise "no". Do not output any other words.

Conventions
- Propositional variables are written as pN, where N is a number.
- All statements are jointly assumed true (conjoined).

Answer format
- For Horn tasks (style: horn_if_then): Output only a final single word "yes" if p0 is derivable from the given facts and rules, or "no" otherwise.
- For CNF contradiction tasks (styles: cnf_v1 or cnf_v2): Output a final single word as your last token: "contradiction" if the set is a contradiction (unsatisfiable), otherwise "satisfiable" or "unknown".

Examples (Horn, yes/no)
- p1. if p1 then p0. → yes
- p1. if p1 then p9. → no
- p1. if p1 then p2. if p2 then p0. → yes

Examples (CNF, contradiction)
- p1 is true. not(p1) or p2. p2 is false. → contradiction.
- p1. not(p1) or p2. not(p2). → contradiction.
- p1. p1 or p2. not(p2). → satisfiable.
```

Examples (horn=0):

- low: maxvars=4, maxlen=2, satflag=1

```
p4.
if p4 and p1 then p0.
if p3 and p1 then p0.
if p3 then p4.
if p2 and p1 then p0.
if p1 then p4.
p2 or p4.
```

- mid: maxvars=4, maxlen=2, satflag=1

```
p4.
if p4 and p1 then p0.
if p3 and p1 then p0.
if p3 then p4.
if p2 and p1 then p0.
if p1 then p4.
p2 or p4.
```

- high: maxvars=4, maxlen=2, satflag=0

```
if p1 then p0.
if p4 then p2.
if p3 and p2 then p0.
if p2 then p4.
if p1 then p4.
p1 or p2.
p1 or p3.
```

Examples (horn=1):

- low: maxvars=4, maxlen=2, satflag=1

```
if p4 then p0.
p2.
if p3 then p1.
if p3 then p4.
if p2 then p1.
```

- mid: maxvars=4, maxlen=2, satflag=1

```
if p4 then p0.
p2.
if p3 then p1.
if p3 then p4.
if p2 then p1.
```

- high: maxvars=4, maxlen=2, satflag=0

```
p1.
p3.
if p4 and p1 then p0.
if p3 then p1.
if p1 then p4.
```


---

### prompt_2e9c5ccddf
- prompt_template: `prompts/_template_unified.j2`
- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- leaf_runs_count: 72

Instruction text (before `Statements:`):

```
Your task is to solve a propositional logic problem.

Choose the appropriate interpretation based on how the statements are rendered below.
- If you see facts like "p1." and rules like "if p2 and p3 then p4.", treat them as Horn facts and implications, and determine whether p0 can be derived.
- If you see disjunctions like "p1 is true or p2 is false." or compact forms like "p1 or not(p2).", treat them as CNF clauses, and determine whether the set is a contradiction (unsatisfiable) or satisfiable.

Conventions
- Propositional variables are written as pN, where N is a number.
- All statements are jointly assumed true (conjoined).

Answer format
- For Horn tasks (style: horn_if_then): Output only a final single word "yes" if p0 is derivable from the given facts and rules, or "no" otherwise.
- For CNF contradiction tasks (styles: cnf_v1 or cnf_v2): Output a final single word as your last token: "contradiction" if the set is a contradiction (unsatisfiable), otherwise "satisfiable" or "unknown".

Examples (Horn, yes/no)
- p1. if p1 then p0. → yes
- p1. if p1 then p9. → no
- p1. if p1 then p2. if p2 then p0. → yes

Examples (CNF, contradiction)
- p1 is true. not(p1) or p2. p2 is false. → contradiction.
- p1. not(p1) or p2. not(p2). → contradiction.
- p1. p1 or p2. not(p2). → satisfiable.
```

Examples (horn=0):

- low: maxvars=4, maxlen=2, satflag=1

```
p4.
not(p4) or not(p1).
not(p3) or not(p1).
not(p3) or p4.
not(p2) or not(p1).
not(p1) or p4.
p2 or p4.
```

- mid: maxvars=4, maxlen=2, satflag=1

```
p4.
not(p4) or not(p1).
not(p3) or not(p1).
not(p3) or p4.
not(p2) or not(p1).
not(p1) or p4.
p2 or p4.
```

- high: maxvars=4, maxlen=2, satflag=0

```
not(p1).
not(p4) or p2.
not(p3) or not(p2).
not(p2) or p4.
not(p1) or p4.
p1 or p2.
p1 or p3.
```

Examples (horn=1):

- low: maxvars=4, maxlen=2, satflag=1

```
not(p4).
p2.
not(p3) or p1.
not(p3) or p4.
not(p2) or p1.
```

- mid: maxvars=4, maxlen=2, satflag=1

```
not(p4).
p2.
not(p3) or p1.
not(p3) or p4.
not(p2) or p1.
```

- high: maxvars=4, maxlen=3, satflag=0

```
p3.
not(p4) or not(p1).
not(p4) or p1.
not(p4) or p3.
not(p3) or not(p1).
not(p3) or p1.
not(p3) or p4.
not(p3) or not(p1) or p4.
```


---

### prompt_62ba908560
- prompt_template: `prompts/_template_unified.j2`
- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- leaf_runs_count: 55

Instruction text (before `Statements:`):

```
Your task is to solve a propositional logic problem.

Choose the appropriate interpretation based on how the statements are rendered below.
- If you see facts like "p1." and rules like "if p2 and p3 then p4.", treat them as Horn facts and implications, and determine whether p0 can be derived.
- If you see disjunctions like "p1 is true or p2 is false." or compact forms like "p1 or not(p2).", treat them as CNF clauses, and determine whether the set is a contradiction (unsatisfiable) or satisfiable.
Unified answer rule (mixed cases)
- Regardless of how the statements are rendered, output only a final single word: "yes" if p0 is derivable OR the set is a contradiction; otherwise "no". Do not output any other words.

Conventions
- Propositional variables are written as pN, where N is a number.
- All statements are jointly assumed true (conjoined).

Answer format
- For Horn tasks (style: horn_if_then): Output exactly one final word on the last line, lowercase with no punctuation: "yes" if p0 is derivable from the given facts and rules; otherwise "no". Do not output any other words (do not output "contradiction"/"satisfiable"/"unknown").
- For CNF contradiction tasks (styles: cnf_v1 or cnf_v2): Output exactly one final word on the last line, lowercase with no punctuation: "contradiction" if the set is a contradiction (unsatisfiable); otherwise "satisfiable", or "unknown" if undecidable. Do not output any other words (do not output "yes"/"no").

Examples (Horn, yes/no)
- p1. if p1 then p0. → yes
- p1. if p1 then p9. → no
- p1. if p1 then p2. if p2 then p0. → yes

Examples (CNF, contradiction)
- p1 is true. not(p1) or p2. p2 is false. → contradiction.
- p1. not(p1) or p2. not(p2). → contradiction.
- p1. p1 or p2. not(p2). → satisfiable.
```

Examples (horn=0):

- low: maxvars=4, maxlen=2, satflag=1

```
p4.
if p4 and p1 then p0.
if p3 and p1 then p0.
if p3 then p4.
if p2 and p1 then p0.
if p1 then p4.
p2 or p4.
```

- mid: maxvars=10, maxlen=4, satflag=1

```
p9 or p10.
not(p10) or p3 or p9.
if p9 and p8 then p4.
if p9 and p7 and p4 then p0.
not(p9) or p3 or p4.
if p8 and p5 then p2.
if p8 and p4 then p1.
if p8 and p3 then p9.
not(p8) or p2 or p3.
not(p8) or p2 or p9.
if p6 and p1 then p2.
if p5 and p3 then p8.
if p5 and p1 then p6.
if p5 and p1 then p7.
not(p5) or p3 or p4.
not(p5) or p6 or p7.
if p4 and p3 then p1.
if p4 and p3 then p5.
if p4 and p3 then p10.
if p4 and p2 then p10.
not(p3) or p2 or p9.
not(p3) or p7 or p9.
if p2 and p1 then p7.
p1 or p3 or p4.
p1 or p4 or p5.
p1 or p4 or p10.
p2 or p4 or p5.
p2 or p5 or p10.
p2 or p9 or p10.
p3 or p7 or p10.
p7 or p8 or p9.
if p10 and p9 and p5 then p7.
not(p10) or not(p8) or p1 or p3.
not(p10) or not(p8) or p4 or p9.
if p10 and p7 and p3 then p2.
if p10 and p7 and p3 then p8.
if p10 and p6 and p1 then p9.
not(p10) or not(p6) or p4 or p5.
not(p10) or not(p5) or p1 or p9.
not(p10) or not(p3) or p4 or p7.
not(p10) or not(p2) or p3 or p9.
not(p10) or not(p1) or p4 or p6.
not(p9) or not(p7) or p1 or p5.
if p9 and p6 and p5 and p1 then p0.
if p8 and p7 and p6 then p5.
if p8 and p7 and p5 then p9.
if p8 and p7 and p3 then p2.
if p8 and p5 and p2 then p1.
not(p8) or not(p5) or p2 or p6.
not(p8) or not(p5) or p4 or p10.
not(p8) or not(p3) or p2 or p4.
not(p7) or not(p6) or p1 or p4.
if p7 and p5 and p2 then p10.
if p7 and p5 and p1 then p3.
if p7 and p5 and p1 then p10.
if p7 and p4 and p3 then p2.
not(p7) or not(p4) or p2 or p8.
not(p7) or not(p2) or p3 or p5.
not(p7) or p2 or p5 or p6.
if p6 and p5 and p4 then p9.
not(p6) or not(p4) or p2 or p9.
not(p6) or not(p4) or p8 or p10.
if p6 and p3 and p2 then p4.
not(p6) or p1 or p7 or p9.
not(p6) or p2 or p5 or p10.
not(p5) or not(p1) or p3 or p9.
not(p5) or not(p1) or p8 or p9.
not(p5) or p7 or p8 or p9.
not(p4) or p2 or p3 or p10.
not(p4) or p3 or p6 or p10.
not(p3) or p2 or p4 or p7.
not(p2) or p1 or p3 or p7.
not(p2) or p4 or p6 or p7.
not(p1) or p2 or p4 or p7.
p3 or p6 or p7 or p8.
p4 or p5 or p6 or p10.
```

- high: maxvars=15, maxlen=4, satflag=0

```
p9 or p15.
if p15 and p13 and p8 then p0.
if p15 and p1 then p5.
not(p15) or p1 or p11.
if p14 and p6 then p11.
if p13 and p8 and p3 then p0.
if p13 and p2 then p1.
not(p13) or p6 or p15.
if p12 and p7 then p6.
if p12 and p4 then p6.
if p12 and p3 then p10.
not(p12) or p3 or p7.
not(p12) or p7 or p10.
not(p11) or p2 or p6.
if p10 and p8 then p11.
if p10 and p2 and p1 then p0.
not(p10) or p8 or p13.
if p9 and p6 then p7.
not(p9) or p4 or p13.
if p8 and p3 then p9.
if p7 and p6 then p14.
if p15 and p13 and p11 and p9 then p0.
if p15 and p13 and p9 and p2 then p0.
if p15 and p13 and p7 then p4.
not(p15) or not(p12) or p8 or p13.
if p15 and p11 and p9 and p4 then p0.
if p15 and p11 and p3 then p8.
if p15 and p8 and p7 and p5 then p0.
if p15 and p8 and p7 then p11.
not(p15) or not(p7) or p3 or p12.
not(p15) or not(p6) or p2 or p10.
not(p15) or not(p6) or p10 or p13.
if p15 and p4 and p1 then p3.
not(p15) or p9 or p12 or p13.
if p14 and p13 and p8 then p12.
not(p14) or not(p13) or p3 or p7.
if p14 and p12 and p11 then p8.
if p14 and p12 and p7 then p2.
if p14 and p12 and p3 then p4.
if p14 and p10 and p4 then p1.
not(p14) or not(p10) or p5 or p12.
if p14 and p9 and p6 then p12.
not(p14) or not(p5) or p3 or p9.
not(p14) or not(p4) or p1 or p12.
not(p14) or not(p4) or p3 or p12.
not(p14) or not(p3) or p5 or p11.
not(p14) or not(p2) or p4 or p10.
not(p14) or not(p2) or p8 or p9.
not(p14) or not(p1) or p3 or p4.
not(p14) or p4 or p6 or p8.
not(p14) or p11 or p12 or p13.
if p13 and p12 and p2 and p1 then p0.
if p13 and p10 and p1 then p15.
if p13 and p9 and p1 then p15.
if p13 and p8 and p3 then p15.
not(p13) or not(p7) or p8 or p11.
not(p13) or not(p6) or p2 or p8.
if p13 and p5 and p3 then p9.
if p13 and p4 and p1 then p7.
not(p13) or not(p2) or p5 or p12.
not(p13) or p1 or p7 or p8.
not(p13) or p5 or p6 or p7.
not(p13) or p5 or p7 or p14.
not(p12) or not(p11) or p8 or p10.
if p12 and p6 and p1 then p13.
if p12 and p4 and p2 then p6.
not(p11) or not(p10) or p1 or p4.
not(p11) or not(p2) or p4 or p5.
not(p11) or not(p2) or p8 or p13.
not(p11) or not(p1) or p8 or p15.
not(p11) or p1 or p6 or p13.
not(p11) or p7 or p10 or p13.
if p10 and p8 and p5 then p7.
if p10 and p7 and p6 then p4.
if p10 and p7 and p5 and p1 then p0.
not(p10) or p4 or p7 or p11.
not(p10) or p5 or p8 or p11.
not(p10) or p7 or p11 or p13.
if p9 and p5 and p1 then p10.
not(p9) or not(p4) or p2 or p8.
not(p9) or not(p2) or p12 or p15.
if p8 and p6 and p2 then p10.
if p8 and p6 and p1 then p13.
not(p8) or not(p3) or p1 or p6.
not(p8) or p1 or p2 or p13.
not(p8) or p2 or p13 or p15.
not(p8) or p6 or p12 or p15.
if p7 and p6 and p4 then p12.
not(p7) or not(p4) or p6 or p12.
if p7 and p3 and p2 then p10.
not(p7) or not(p3) or p2 or p15.
not(p7) or p3 or p10 or p15.
not(p7) or p4 or p8 or p12.
not(p7) or p11 or p12 or p14.
not(p6) or not(p1) or p4 or p5.
not(p6) or not(p1) or p4 or p11.
not(p6) or p1 or p9 or p14.
not(p5) or not(p4) or p1 or p14.
if p5 and p3 and p1 then p13.
not(p5) or not(p1) or p2 or p10.
not(p5) or p3 or p8 or p11.
not(p5) or p8 or p9 or p13.
not(p2) or p3 or p5 or p8.
not(p1) or p2 or p13 or p15.
not(p1) or p3 or p8 or p9.
not(p1) or p6 or p8 or p13.
not(p1) or p7 or p11 or p15.
p1 or p2 or p3 or p15.
p1 or p2 or p4 or p11.
p1 or p3 or p6 or p10.
p1 or p10 or p11 or p14.
p2 or p4 or p5 or p7.
p2 or p10 or p11 or p12.
p6 or p9 or p10 or p11.
```

Examples (horn=1):

- low: maxvars=4, maxlen=2, satflag=1

```
if p4 then p0.
p2.
if p3 then p1.
if p3 then p4.
if p2 then p1.
```

- mid: maxvars=10, maxlen=4, satflag=1

```
p10.
if p10 then p6.
if p9 then p6.
if p9 then p10.
if p8 then p9.
if p8 then p10.
if p6 then p9.
if p4 then p1.
if p4 then p6.
if p2 then p1.
if p2 then p10.
if p1 then p5.
if p1 then p10.
if p10 and p7 then p9.
if p10 and p4 then p1.
if p10 and p4 then p8.
if p10 and p3 then p2.
if p10 and p3 then p7.
if p8 and p7 then p9.
if p7 and p6 then p4.
if p7 and p5 then p4.
if p7 and p2 then p5.
if p4 and p3 then p8.
if p4 and p3 then p10.
if p10 and p9 and p7 and p2 then p0.
if p10 and p7 and p5 then p3.
if p10 and p6 and p5 then p7.
if p7 and p6 and p5 then p10.
if p7 and p6 and p4 then p3.
if p7 and p6 and p3 then p2.
if p7 and p4 and p2 then p8.
```

- high: maxvars=15, maxlen=5, satflag=1

```
p2.
if p15 then p4.
if p15 then p8.
if p14 then p5.
if p14 then p7.
if p12 then p9.
if p11 then p8.
if p11 then p10.
if p10 then p4.
if p10 then p11.
if p9 then p5.
if p7 then p12.
if p3 then p1.
if p3 then p8.
if p2 then p11.
if p1 then p3.
if p1 then p4.
if p1 then p12.
if p15 and p14 then p6.
if p15 and p10 then p12.
if p15 and p1 then p9.
if p13 and p10 then p8.
if p13 and p10 then p15.
if p13 and p6 then p7.
if p13 and p3 then p4.
if p12 and p11 then p14.
if p12 and p9 then p11.
if p12 and p5 then p1.
if p12 and p5 then p6.
if p12 and p5 then p14.
if p12 and p4 then p15.
if p11 and p4 then p10.
if p10 and p8 then p11.
if p10 and p1 then p15.
if p9 and p6 then p14.
if p9 and p5 then p11.
if p9 and p1 then p4.
if p8 and p7 then p11.
if p8 and p2 then p4.
if p7 and p2 then p3.
if p6 and p5 then p9.
if p5 and p1 then p2.
if p4 and p3 then p11.
if p4 and p2 then p11.
if p14 and p13 and p6 then p1.
if p14 and p13 and p2 then p8.
if p14 and p10 and p9 and p3 then p0.
if p14 and p10 and p8 and p2 then p0.
if p13 and p10 and p9 then p15.
if p12 and p10 and p7 then p8.
if p12 and p9 and p6 then p8.
if p12 and p8 and p6 then p4.
if p12 and p4 and p1 then p2.
if p11 and p10 and p1 then p9.
if p11 and p8 and p5 then p12.
if p11 and p8 and p1 then p10.
if p10 and p8 and p6 then p9.
if p10 and p4 and p2 then p11.
if p9 and p6 and p3 then p8.
if p8 and p7 and p5 then p1.
if p8 and p7 and p2 then p6.
if p6 and p5 and p4 then p12.
if p15 and p12 and p10 and p5 then p11.
if p15 and p12 and p7 and p6 then p14.
if p15 and p10 and p9 and p2 then p7.
if p15 and p6 and p2 and p1 then p9.
if p14 and p7 and p6 and p1 then p11.
if p13 and p11 and p7 and p4 then p14.
if p13 and p8 and p7 and p3 then p15.
```


---

### prompt_73ecab0579
- prompt_template: ``
- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- leaf_runs_count: 12

_No provenance prompt text was available for this prompt_id._

Examples (horn=1):

- low: maxvars=4, maxlen=2, satflag=1

_Example statements unavailable (missing prompt text)._\

- mid: maxvars=4, maxlen=2, satflag=1

_Example statements unavailable (missing prompt text)._\

- high: maxvars=4, maxlen=2, satflag=1

_Example statements unavailable (missing prompt text)._\


---

### prompt_7b28aa32dc
- prompt_template: `prompts/_template_unified.j2`
- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- leaf_runs_count: 40

Instruction text (before `Statements:`):

```
Your task is to solve a propositional logic problem.

Choose the appropriate interpretation based on how the statements are rendered below.
- If you see facts like "p1." and rules like "if p2 and p3 then p4.", treat them as Horn facts and implications, and determine whether p0 can be derived.
- If you see disjunctions like "p1 is true or p2 is false." or compact forms like "p1 or not(p2).", treat them as CNF clauses, and determine whether the set is a contradiction (unsatisfiable) or satisfiable.
Horn answer rule
- Output ONLY a single final word: "yes" if p0 is derivable, otherwise "no". Do not output any other words.

Conventions
- Propositional variables are written as pN, where N is a number.
- All statements are jointly assumed true (conjoined).

Answer format
- For Horn tasks (style: horn_if_then): Output exactly one final word on the last line, lowercase with no punctuation: "yes" if p0 is derivable from the given facts and rules; otherwise "no". Do not output any other words (do not output "contradiction"/"satisfiable"/"unknown").
- For CNF contradiction tasks (styles: cnf_v1 or cnf_v2): Output exactly one final word on the last line, lowercase with no punctuation: "contradiction" if the set is a contradiction (unsatisfiable); otherwise "satisfiable", or "unknown" if undecidable. Do not output any other words (do not output "yes"/"no").

Examples (Horn, yes/no)
- p1. if p1 then p0. → yes
- p1. if p1 then p9. → no
- p1. if p1 then p2. if p2 then p0. → yes

Examples (CNF, contradiction)
- p1 is true. not(p1) or p2. p2 is false. → contradiction.
- p1. not(p1) or p2. not(p2). → contradiction.
- p1. p1 or p2. not(p2). → satisfiable.
```

Examples (horn=1):

- low: maxvars=4, maxlen=2, satflag=1

```
if p4 then p0.
p2.
if p3 then p1.
if p3 then p4.
if p2 then p1.
```

- mid: maxvars=12, maxlen=4, satflag=1

```
p1.
p3.
p4.
p5.
p8.
if p12 then p1.
if p12 then p8.
if p9 then p5.
if p8 then p7.
if p8 then p11.
if p7 then p12.
if p4 then p2.
if p4 then p7.
if p3 then p2.
if p3 then p9.
if p2 then p6.
if p12 and p4 then p6.
if p11 and p10 then p6.
if p11 and p1 then p4.
if p10 and p9 then p4.
if p10 and p3 then p2.
if p9 and p6 then p1.
if p8 and p7 then p12.
if p7 and p3 then p1.
if p7 and p3 then p8.
if p7 and p1 then p5.
if p3 and p2 then p12.
if p12 and p9 and p5 then p6.
if p12 and p7 and p3 then p8.
if p12 and p7 and p1 then p9.
if p12 and p6 and p3 then p4.
if p11 and p9 and p5 then p12.
if p10 and p7 and p6 and p2 then p0.
if p10 and p7 and p2 then p11.
if p9 and p7 and p5 then p6.
if p7 and p6 and p4 then p8.
if p6 and p2 and p1 then p7.
```

- high: maxvars=20, maxlen=5, satflag=0

```
p6.
p11.
p16.
p17.
if p20 then p2.
if p20 then p10.
if p20 then p14.
if p19 then p9.
if p18 then p2.
if p16 then p11.
if p15 then p14.
if p15 then p17.
if p14 then p19.
if p12 then p8.
if p11 then p8.
if p9 then p1.
if p9 then p15.
if p8 then p4.
if p8 then p12.
if p7 then p1.
if p6 then p11.
if p3 then p2.
if p2 then p14.
if p2 then p18.
if p2 then p19.
if p20 and p10 then p7.
if p20 and p3 then p13.
if p19 and p8 then p18.
if p18 and p9 then p3.
if p17 and p11 then p10.
if p17 and p10 then p14.
if p16 and p14 then p3.
if p16 and p10 then p13.
if p15 and p11 then p19.
if p15 and p9 then p10.
if p15 and p6 then p4.
if p15 and p5 then p6.
if p14 and p12 then p4.
if p14 and p9 then p20.
if p14 and p6 then p9.
if p14 and p5 then p16.
if p14 and p4 then p11.
if p14 and p2 then p1.
if p12 and p9 then p17.
if p12 and p2 then p11.
if p11 and p7 then p8.
if p11 and p7 then p16.
if p11 and p5 then p7.
if p11 and p3 then p13.
if p10 and p5 then p4.
if p10 and p2 then p18.
if p10 and p1 then p16.
if p9 and p1 then p15.
if p8 and p4 then p3.
if p8 and p1 then p4.
if p6 and p4 then p18.
if p4 and p2 then p3.
if p20 and p16 and p14 then p10.
if p20 and p15 and p14 then p16.
if p20 and p12 and p8 then p4.
if p19 and p5 and p4 then p16.
if p18 and p16 and p15 then p13.
if p18 and p15 and p9 and p4 then p0.
if p18 and p15 and p7 then p13.
if p18 and p11 and p5 then p4.
if p17 and p16 and p9 then p13.
if p17 and p13 and p2 then p10.
if p17 and p13 and p1 then p4.
if p17 and p9 and p6 then p14.
if p16 and p14 and p3 then p18.
if p16 and p9 and p4 then p19.
if p16 and p2 and p1 then p17.
if p15 and p10 and p6 then p20.
if p15 and p9 and p3 then p10.
if p14 and p12 and p4 then p1.
if p14 and p10 and p8 then p1.
if p14 and p8 and p2 then p10.
if p13 and p11 and p1 then p17.
if p12 and p9 and p8 then p18.
if p12 and p7 and p3 and p2 then p0.
if p10 and p8 and p7 then p18.
if p6 and p4 and p3 then p20.
if p20 and p17 and p14 and p8 then p19.
if p19 and p17 and p12 and p2 then p10.
if p18 and p17 and p16 and p6 then p10.
if p17 and p12 and p10 and p6 then p19.
if p17 and p12 and p10 and p1 then p2.
if p16 and p15 and p10 and p1 then p9.
if p16 and p9 and p4 and p3 then p13.
if p14 and p12 and p7 and p5 then p20.
if p13 and p10 and p4 and p1 then p8.
if p8 and p7 and p3 and p1 then p17.
```


---

### prompt_83b02d3a05
- prompt_template: `prompts/exp1_cnf_v1_contradiction.j2`
- prompt_style: `cnf_v1`
- parse_family: `contradiction`
- leaf_runs_count: 9

Instruction text (before `Statements:`):

```
Your task is to solve a problem in propositional logic.
You will get a list of statements and have to determine whether the statements form a logical contradiction or not.
If the statements form a contradiction, the last word of your answer should be 'contradiction',
otherwise the last word should be either 'satisfiable' or 'unknown'.

Propositional variables are represent as 'pN' where N is a number. They are either true or false.
'X or Y' means that X is true or Y is true or both X and Y are true.
All the given statements are implicitly connected with 'and': they are all claimed to be true.

Two examples:
Example 1.
```

Examples (horn=1):

- low: maxvars=10, maxlen=3, satflag=1

```
p1 is true. p1 is false or p2 is true. p2 is false. Answer: contradiction.
Example 2. Statements: p1 is true. p1 is true or p2 is true. p2 is false. Answer: satisfiable.

Statements:
p2 is true.
p4 is true.
p10 is false or p2 is true.
p10 is false or p4 is true.
p9 is false or p1 is false.
p9 is false or p1 is true.
p8 is false or p2 is true.
p8 is false or p4 is true.
p8 is false or p5 is true.
p7 is false or p3 is true.
p6 is false or p2 is true.
p6 is false or p3 is true.
p6 is false or p10 is true.
p3 is false or p9 is true.
p2 is false or p8 is true.
p2 is false or p10 is true.
p10 is false or p3 is false or p2 is false.
p10 is false or p3 is false or p6 is true.
p6 is false or p4 is false or p1 is true.
p3 is false or p1 is false or p7 is true.

Please think step by step and answer whether the given statements form a logical contradiction or is satisfiable.
```

- mid: maxvars=10, maxlen=3, satflag=1

```
p1 is true. p1 is false or p2 is true. p2 is false. Answer: contradiction.
Example 2. Statements: p1 is true. p1 is true or p2 is true. p2 is false. Answer: satisfiable.

Statements:
p1 is true.
p4 is true.
p6 is true.
p10 is false or p9 is true.
p7 is false or p1 is true.
p6 is false or p7 is true.
p5 is false or p2 is true.
p5 is false or p10 is true.
p3 is false or p4 is true.
p10 is false or p8 is false or p2 is true.
p10 is false or p7 is false or p2 is true.
p10 is false or p7 is false or p6 is true.
p10 is false or p5 is false or p8 is true.
p9 is false or p8 is false or p1 is true.
p9 is false or p5 is false or p1 is true.
p9 is false or p4 is false or p3 is false.
p9 is false or p3 is false or p10 is true.
p6 is false or p3 is false or p2 is true.
p6 is false or p3 is false or p8 is true.
p2 is false or p1 is false or p8 is true.

Please think step by step and answer whether the given statements form a logical contradiction or is satisfiable.
```

- high: maxvars=10, maxlen=3, satflag=1

```
p1 is true. p1 is false or p2 is true. p2 is false. Answer: contradiction.
Example 2. Statements: p1 is true. p1 is true or p2 is true. p2 is false. Answer: satisfiable.

Statements:
p3 is true.
p5 is true.
p8 is true.
p10 is false or p4 is true.
p9 is false or p3 is true.
p9 is false or p7 is true.
p7 is false or p1 is true.
p7 is false or p5 is true.
p6 is false or p3 is false.
p3 is false or p5 is true.
p1 is false or p3 is true.
p1 is false or p7 is true.
p10 is false or p4 is false or p1 is false.
p10 is false or p1 is false or p2 is true.
p10 is false or p1 is false or p7 is true.
p9 is false or p7 is false or p3 is false.
p7 is false or p2 is false or p10 is true.
p6 is false or p4 is false or p3 is true.
p6 is false or p3 is false or p2 is true.
p5 is false or p2 is false or p1 is false.

Please think step by step and answer whether the given statements form a logical contradiction or is satisfiable.
```


---

### prompt_c012d6f2e6
- prompt_template: `prompts/_template_unified.j2`
- prompt_style: `cnf_v2`
- parse_family: `contradiction`
- leaf_runs_count: 89

Instruction text (before `Statements:`):

```
Your task is to solve a propositional logic problem.

Choose the appropriate interpretation based on how the statements are rendered below.
- If you see facts like "p1." and rules like "if p2 and p3 then p4.", treat them as Horn facts and implications, and determine whether p0 can be derived.
- If you see disjunctions like "p1 is true or p2 is false." or compact forms like "p1 or not(p2).", treat them as CNF clauses, and determine whether the set is a contradiction (unsatisfiable) or satisfiable.

Conventions
- Propositional variables are written as pN, where N is a number.
- All statements are jointly assumed true (conjoined).

Answer format
- For Horn tasks (style: horn_if_then): Output exactly one final word on the last line, lowercase with no punctuation: "yes" if p0 is derivable from the given facts and rules; otherwise "no". Do not output any other words (do not output "contradiction"/"satisfiable"/"unknown").
- For CNF contradiction tasks (styles: cnf_v1 or cnf_v2): Output exactly one final word on the last line, lowercase with no punctuation: "contradiction" if the set is a contradiction (unsatisfiable); otherwise "satisfiable", or "unknown" if undecidable. Do not output any other words (do not output "yes"/"no").

Examples (Horn, yes/no)
- p1. if p1 then p0. → yes
- p1. if p1 then p9. → no
- p1. if p1 then p2. if p2 then p0. → yes

Examples (CNF, contradiction)
- p1 is true. not(p1) or p2. p2 is false. → contradiction.
- p1. not(p1) or p2. not(p2). → contradiction.
- p1. p1 or p2. not(p2). → satisfiable.
```

Examples (horn=0):

- low: maxvars=4, maxlen=2, satflag=1

```
p4.
not(p4) or not(p1).
not(p3) or not(p1).
not(p3) or p4.
not(p2) or not(p1).
not(p1) or p4.
p2 or p4.
```

- mid: maxvars=12, maxlen=4, satflag=1

```
not(p4) or not(p2).
p1 or p11.
not(p12) or p7 or p11.
not(p11) or p1 or p7.
not(p11) or p2 or p12.
not(p10) or not(p9) or p5.
not(p10) or not(p4) or not(p2).
not(p10) or not(p2) or p8.
not(p10) or not(p1) or p8.
not(p10) or not(p1) or p12.
not(p10) or p11 or p12.
not(p9) or not(p3) or not(p1).
not(p9) or p5 or p6.
not(p8) or not(p4) or p7.
not(p5) or p1 or p9.
p3 or p8 or p10.
p4 or p5 or p10.
p7 or p10 or p12.
not(p12) or not(p10) or not(p6) or p9.
not(p12) or not(p10) or not(p4) or not(p2).
not(p12) or not(p9) or not(p3) or p6.
not(p12) or not(p9) or p1 or p3.
not(p12) or not(p9) or p6 or p8.
not(p12) or not(p8) or not(p7) or not(p3).
not(p12) or not(p7) or p1 or p5.
not(p12) or not(p7) or p6 or p9.
not(p12) or not(p5) or not(p4) or p6.
not(p12) or not(p5) or p3 or p6.
not(p12) or not(p4) or p2 or p10.
not(p12) or not(p2) or p7 or p10.
not(p12) or p1 or p3 or p4.
not(p12) or p1 or p8 or p10.
not(p11) or not(p10) or not(p8) or p12.
not(p11) or not(p10) or not(p6) or not(p3).
not(p11) or not(p10) or not(p3) or p6.
not(p11) or not(p10) or not(p1) or p5.
not(p11) or not(p9) or p4 or p8.
not(p11) or not(p7) or not(p4) or p9.
not(p11) or not(p6) or not(p5) or p7.
not(p11) or not(p5) or not(p4) or p1.
not(p11) or not(p5) or not(p2) or p6.
not(p11) or not(p5) or not(p1) or p12.
not(p11) or not(p3) or p1 or p12.
not(p11) or not(p1) or p4 or p6.
not(p11) or p1 or p5 or p12.
not(p11) or p5 or p7 or p12.
not(p10) or not(p8) or not(p6) or not(p3).
not(p10) or not(p7) or not(p6) or p1.
not(p10) or not(p7) or p1 or p2.
not(p10) or not(p6) or not(p4) or p2.
not(p10) or not(p6) or p2 or p12.
not(p10) or not(p2) or p4 or p5.
not(p10) or p1 or p3 or p11.
not(p10) or p3 or p6 or p8.
not(p9) or not(p7) or not(p6) or p11.
not(p9) or not(p6) or p2 or p5.
not(p9) or not(p5) or p1 or p6.
not(p9) or not(p4) or not(p2) or p10.
not(p9) or not(p4) or p6 or p12.
not(p9) or not(p3) or p4 or p12.
not(p9) or p1 or p6 or p10.
not(p8) or not(p6) or p3 or p10.
not(p8) or not(p6) or p9 or p10.
not(p8) or not(p4) or not(p1) or p3.
not(p8) or not(p4) or p9 or p11.
not(p8) or not(p1) or p10 or p12.
not(p8) or p1 or p3 or p7.
not(p8) or p2 or p3 or p12.
not(p7) or not(p5) or not(p3) or p6.
not(p7) or not(p4) or p1 or p8.
not(p7) or not(p4) or p5 or p11.
not(p7) or not(p3) or not(p2) or p8.
not(p7) or not(p2) or p5 or p9.
not(p7) or not(p1) or p9 or p10.
not(p7) or not(p1) or p10 or p12.
not(p7) or p3 or p5 or p6.
not(p6) or not(p5) or not(p2) or p7.
not(p6) or not(p5) or not(p1) or p2.
not(p6) or not(p1) or p3 or p12.
not(p6) or not(p1) or p10 or p12.
not(p5) or not(p2) or p6 or p12.
not(p5) or not(p2) or p11 or p12.
not(p5) or p1 or p2 or p6.
not(p5) or p3 or p7 or p12.
not(p4) or p2 or p6 or p8.
not(p2) or p1 or p3 or p6.
not(p2) or p1 or p6 or p7.
not(p2) or p6 or p9 or p10.
not(p1) or p4 or p5 or p10.
p1 or p6 or p8 or p10.
p8 or p10 or p11 or p12.
```

- high: maxvars=50, maxlen=3, satflag=0

```
not(p49) or p21.
not(p31) or not(p18).
p25 or p40.
p42 or p49.
not(p50) or not(p27) or not(p7).
not(p50) or not(p10) or p8.
not(p50) or not(p5) or p29.
not(p50) or p7 or p16.
not(p50) or p7 or p42.
not(p50) or p39 or p46.
not(p49) or not(p47) or not(p23).
not(p49) or not(p41) or p46.
not(p49) or not(p36) or not(p14).
not(p49) or not(p15) or p48.
not(p49) or p16 or p41.
not(p49) or p17 or p18.
not(p49) or p22 or p31.
not(p48) or not(p43) or p20.
not(p48) or not(p40) or not(p30).
not(p48) or not(p25) or not(p15).
not(p48) or not(p9) or p21.
not(p48) or not(p6) or p29.
not(p48) or p12 or p25.
not(p47) or not(p46) or p42.
not(p47) or not(p44) or not(p1).
not(p47) or not(p33) or not(p12).
not(p47) or not(p21) or not(p15).
not(p47) or p9 or p40.
not(p46) or not(p35) or p49.
not(p46) or not(p25) or p10.
not(p46) or not(p25) or p48.
not(p46) or p1 or p17.
not(p46) or p6 or p49.
not(p46) or p39 or p45.
not(p45) or not(p36) or p24.
not(p45) or not(p30) or not(p6).
not(p45) or not(p30) or p13.
not(p45) or not(p3) or p38.
not(p45) or p7 or p17.
not(p45) or p27 or p44.
not(p45) or p32 or p43.
not(p44) or not(p39) or p23.
not(p44) or p16 or p36.
not(p43) or not(p29) or p38.
not(p43) or not(p28) or not(p10).
not(p43) or not(p8) or p14.
not(p43) or p6 or p19.
not(p43) or p27 or p50.
not(p42) or not(p39) or p28.
not(p42) or not(p25) or p37.
not(p42) or not(p9) or p39.
not(p42) or p24 or p46.
not(p41) or not(p30) or p18.
not(p41) or p4 or p15.
not(p41) or p6 or p8.
not(p40) or not(p37) or not(p3).
not(p39) or not(p10) or p14.
not(p39) or p2 or p20.
not(p38) or not(p24) or p33.
not(p38) or not(p18) or p49.
not(p38) or p3 or p7.
not(p38) or p6 or p48.
not(p38) or p7 or p47.
not(p38) or p15 or p30.
not(p38) or p27 or p29.
not(p37) or not(p24) or not(p12).
not(p37) or p9 or p19.
not(p37) or p10 or p32.
not(p37) or p23 or p46.
not(p36) or not(p32) or not(p25).
not(p36) or not(p22) or p20.
not(p36) or not(p16) or not(p5).
not(p36) or not(p2) or p23.
not(p35) or not(p26) or p18.
not(p35) or not(p8) or p31.
not(p35) or not(p6) or p14.
not(p35) or p3 or p5.
not(p35) or p45 or p48.
not(p34) or not(p22) or p48.
not(p34) or not(p18) or p27.
not(p34) or p3 or p46.
not(p34) or p7 or p39.
not(p33) or not(p31) or not(p12).
not(p33) or not(p11) or not(p10).
not(p33) or not(p10) or p9.
not(p33) or not(p1) or p40.
not(p33) or p12 or p37.
not(p33) or p19 or p20.
not(p32) or not(p31) or not(p27).
not(p32) or not(p22) or p17.
not(p32) or not(p4) or p34.
not(p32) or p10 or p30.
not(p32) or p19 or p30.
not(p31) or not(p23) or p37.
not(p31) or not(p23) or p41.
not(p31) or not(p17) or p40.
not(p31) or not(p16) or p37.
not(p31) or not(p8) or not(p3).
not(p31) or p38 or p39.
not(p30) or not(p18) or p34.
not(p30) or not(p17) or p50.
not(p30) or not(p3) or p29.
not(p30) or p2 or p49.
not(p30) or p49 or p50.
not(p29) or not(p27) or p7.
not(p29) or not(p8) or p41.
not(p29) or not(p6) or p27.
not(p29) or p2 or p8.
not(p28) or not(p18) or p8.
not(p28) or not(p12) or p30.
not(p28) or p4 or p14.
not(p28) or p16 or p35.
not(p27) or not(p24) or not(p11).
not(p27) or not(p18) or not(p16).
not(p26) or not(p13) or p15.
not(p26) or p4 or p33.
not(p26) or p17 or p45.
not(p26) or p38 or p46.
not(p25) or not(p23) or not(p3).
not(p25) or not(p23) or p26.
not(p25) or p2 or p17.
not(p25) or p9 or p45.
not(p25) or p12 or p32.
not(p25) or p20 or p49.
not(p25) or p43 or p48.
not(p25) or p45 or p49.
not(p24) or not(p15) or p32.
not(p24) or not(p5) or p18.
not(p23) or p10 or p33.
not(p23) or p31 or p35.
not(p22) or not(p19) or p6.
not(p22) or not(p17) or p24.
not(p22) or p10 or p33.
not(p22) or p11 or p43.
not(p22) or p16 or p30.
not(p21) or not(p12) or p46.
not(p21) or not(p6) or p37.
not(p21) or p19 or p25.
not(p21) or p22 or p35.
not(p20) or not(p16) or p28.
not(p20) or not(p9) or p29.
not(p20) or p11 or p41.
not(p20) or p35 or p40.
not(p19) or not(p1) or p46.
not(p18) or not(p16) or p8.
not(p18) or not(p10) or not(p5).
not(p18) or not(p1) or p10.
not(p18) or p4 or p39.
not(p18) or p23 or p39.
not(p17) or not(p1) or p19.
not(p17) or p2 or p28.
not(p17) or p14 or p19.
not(p16) or p29 or p46.
not(p15) or not(p13) or p10.
not(p15) or p16 or p32.
not(p14) or p5 or p19.
not(p13) or not(p11) or not(p6).
not(p13) or not(p5) or p46.
not(p13) or not(p4) or p19.
not(p13) or p19 or p24.
not(p12) or p13 or p39.
not(p11) or p20 or p45.
not(p11) or p21 or p27.
not(p10) or not(p1) or p18.
not(p10) or p7 or p47.
not(p8) or not(p4) or p48.
not(p8) or p12 or p27.
not(p8) or p14 or p47.
not(p8) or p24 or p26.
not(p7) or p11 or p21.
not(p6) or not(p1) or p50.
not(p6) or p29 or p38.
not(p6) or p38 or p46.
not(p5) or p1 or p8.
not(p5) or p21 or p25.
not(p5) or p29 or p36.
not(p3) or p19 or p47.
not(p3) or p27 or p40.
not(p1) or p28 or p43.
p1 or p12 or p15.
p2 or p5 or p7.
p2 or p7 or p16.
p3 or p10 or p34.
p3 or p38 or p43.
p4 or p8 or p27.
p4 or p45 or p48.
p7 or p17 or p41.
p7 or p41 or p46.
p8 or p32 or p35.
p10 or p35 or p40.
p12 or p16 or p44.
p12 or p32 or p43.
p14 or p25 or p35.
p15 or p27 or p50.
p18 or p25 or p31.
p19 or p33 or p39.
p21 or p23 or p50.
p21 or p26 or p42.
p24 or p45 or p46.
p31 or p34 or p49.
```

Examples (horn=1):

- low: maxvars=4, maxlen=2, satflag=1

```
not(p4).
p2.
not(p3) or p1.
not(p3) or p4.
not(p2) or p1.
```

- mid: maxvars=14, maxlen=4, satflag=1

```
p1.
p2.
p4.
p9.
p12.
not(p11) or p4.
not(p7) or p5.
not(p5) or p10.
not(p4) or p7.
not(p3) or p1.
not(p14) or not(p5) or p4.
not(p13) or not(p2) or p5.
not(p12) or not(p10) or p7.
not(p12) or not(p7) or p11.
not(p12) or not(p7) or p13.
not(p12) or not(p5) or p2.
not(p12) or not(p1) or p4.
not(p11) or not(p8) or p3.
not(p11) or not(p6) or p14.
not(p11) or not(p3) or p14.
not(p10) or not(p9) or p11.
not(p10) or not(p7) or p13.
not(p10) or not(p2) or p1.
not(p10) or not(p2) or p12.
not(p9) or not(p8) or p11.
not(p9) or not(p7) or p2.
not(p9) or not(p5) or p2.
not(p7) or not(p4) or p12.
not(p7) or not(p2) or p14.
not(p6) or not(p5) or p7.
not(p5) or not(p3) or p12.
not(p4) or not(p1) or p12.
not(p14) or not(p12) or not(p3) or p7.
not(p14) or not(p11) or not(p5) or not(p3).
not(p14) or not(p10) or not(p8) or p3.
not(p13) or not(p10) or not(p6) or p12.
not(p13) or not(p9) or not(p7) or p12.
not(p13) or not(p7) or not(p3) or p11.
not(p12) or not(p5) or not(p2) or p6.
not(p11) or not(p8) or not(p2) or p4.
not(p10) or not(p6) or not(p3) or p4.
not(p8) or not(p5) or not(p3) or not(p1).
not(p7) or not(p4) or not(p1) or p13.
```

- high: maxvars=50, maxlen=3, satflag=0

```
p4.
p17.
p24.
p28.
p29.
p31.
p40.
p47.
p50.
not(p50) or p22.
not(p49) or p10.
not(p46) or p14.
not(p46) or p30.
not(p45) or not(p42).
not(p45) or p28.
not(p43) or p25.
not(p42) or p21.
not(p41) or p11.
not(p41) or p19.
not(p40) or p20.
not(p40) or p23.
not(p38) or p7.
not(p38) or p8.
not(p38) or p25.
not(p37) or p13.
not(p37) or p47.
not(p28) or p23.
not(p28) or p43.
not(p26) or p16.
not(p25) or p21.
not(p24) or p21.
not(p23) or p25.
not(p22) or p1.
not(p22) or p30.
not(p21) or p14.
not(p21) or p45.
not(p19) or p37.
not(p17) or p19.
not(p16) or p46.
not(p15) or p10.
not(p15) or p12.
not(p15) or p34.
not(p14) or p20.
not(p13) or p49.
not(p11) or p2.
not(p11) or p28.
not(p11) or p39.
not(p6) or p8.
not(p6) or p9.
not(p4) or p14.
not(p3) or p7.
not(p1) or p13.
not(p50) or not(p44) or p43.
not(p50) or not(p43) or p45.
not(p50) or not(p37) or p48.
not(p49) or not(p46) or not(p34).
not(p49) or not(p42) or p20.
not(p49) or not(p20) or p13.
not(p49) or not(p10) or p24.
not(p49) or not(p4) or p7.
not(p48) or not(p46) or not(p11).
not(p47) or not(p40) or p30.
not(p47) or not(p28) or p25.
not(p46) or not(p39) or p37.
not(p46) or not(p37) or not(p36).
not(p45) or not(p18) or p2.
not(p45) or not(p13) or p1.
not(p44) or not(p42) or p22.
not(p44) or not(p40) or p1.
not(p44) or not(p40) or p9.
not(p44) or not(p34) or not(p18).
not(p44) or not(p11) or p20.
not(p43) or not(p17) or not(p4).
not(p43) or not(p1) or p15.
not(p42) or not(p22) or p11.
not(p42) or not(p2) or p12.
not(p41) or not(p28) or not(p15).
not(p40) or not(p22) or not(p8).
not(p37) or not(p26) or p4.
not(p37) or not(p18) or p15.
not(p36) or not(p31) or not(p12).
not(p36) or not(p2) or p27.
not(p35) or not(p29) or p1.
not(p35) or not(p9) or p41.
not(p33) or not(p2) or p20.
not(p32) or not(p26) or p34.
not(p31) or not(p24) or not(p13).
not(p31) or not(p22) or p16.
not(p30) or not(p13) or p2.
not(p29) or not(p15) or p27.
not(p28) or not(p24) or not(p8).
not(p27) or not(p25) or p35.
not(p25) or not(p11) or p48.
not(p24) or not(p23) or not(p4).
not(p24) or not(p4) or p41.
not(p22) or not(p4) or p17.
not(p18) or not(p9) or p23.
not(p16) or not(p11) or p50.
not(p10) or not(p2) or p49.
not(p6) or not(p3) or p32.
```


---

### prompt_c1b2be97aa
- prompt_template: `prompts/_template_unified.j2`
- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- leaf_runs_count: 120

Instruction text (before `Statements:`):

```
Your task is to solve a propositional logic problem.

Choose the appropriate interpretation based on how the statements are rendered below.
- If you see facts like "p1." and rules like "if p2 and p3 then p4.", treat them as Horn facts and implications, and determine whether p0 can be derived.
- If you see disjunctions like "p1 is true or p2 is false." or compact forms like "p1 or not(p2).", treat them as CNF clauses, and determine whether the set is a contradiction (unsatisfiable) or satisfiable.

Conventions
- Propositional variables are written as pN, where N is a number.
- All statements are jointly assumed true (conjoined).

Answer format
- For Horn tasks (style: horn_if_then): Output only a final single word "yes" if p0 is derivable from the given facts and rules, or "no" otherwise.
- For CNF contradiction tasks (styles: cnf_v1 or cnf_v2): Output a final single word as your last token: "contradiction" if the set is a contradiction (unsatisfiable), otherwise "satisfiable" or "unknown".

Examples (Horn, yes/no)
- p1. if p1 then p0. → yes
- p1. if p1 then p9. → no
- p1. if p1 then p2. if p2 then p0. → yes

Examples (CNF, contradiction)
- p1 is true. not(p1) or p2. p2 is false. → contradiction.
- p1. not(p1) or p2. not(p2). → contradiction.
- p1. p1 or p2. not(p2). → satisfiable.
```

Examples (horn=0):

- low: maxvars=4, maxlen=2, satflag=1

```
p4.
if p4 and p1 then p0.
if p3 and p1 then p0.
if p3 then p4.
if p2 and p1 then p0.
if p1 then p4.
p2 or p4.
```

- mid: maxvars=4, maxlen=2, satflag=0

```
if p4 then p0.
if p4 and p2 then p0.
if p4 then p2.
if p3 then p1.
if p3 then p4.
if p2 then p1.
p3 or p4.
```

- high: maxvars=4, maxlen=2, satflag=1

```
p4.
if p4 and p1 then p0.
if p3 and p1 then p0.
if p3 then p4.
if p2 and p1 then p0.
if p1 then p4.
p2 or p4.
```

Examples (horn=1):

- low: maxvars=4, maxlen=2, satflag=1

```
if p4 then p0.
p2.
if p3 then p1.
if p3 then p4.
if p2 then p1.
```

- mid: maxvars=12, maxlen=4, satflag=1

```
p1.
p3.
p4.
p5.
p8.
if p12 then p1.
if p12 then p8.
if p9 then p5.
if p8 then p7.
if p8 then p11.
if p7 then p12.
if p4 then p2.
if p4 then p7.
if p3 then p2.
if p3 then p9.
if p2 then p6.
if p12 and p4 then p6.
if p11 and p10 then p6.
if p11 and p1 then p4.
if p10 and p9 then p4.
if p10 and p3 then p2.
if p9 and p6 then p1.
if p8 and p7 then p12.
if p7 and p3 then p1.
if p7 and p3 then p8.
if p7 and p1 then p5.
if p3 and p2 then p12.
if p12 and p9 and p5 then p6.
if p12 and p7 and p3 then p8.
if p12 and p7 and p1 then p9.
if p12 and p6 and p3 then p4.
if p11 and p9 and p5 then p12.
if p10 and p7 and p6 and p2 then p0.
if p10 and p7 and p2 then p11.
if p9 and p7 and p5 then p6.
if p7 and p6 and p4 then p8.
if p6 and p2 and p1 then p7.
```

- high: maxvars=20, maxlen=5, satflag=0

```
p6.
p11.
p16.
p17.
if p20 then p2.
if p20 then p10.
if p20 then p14.
if p19 then p9.
if p18 then p2.
if p16 then p11.
if p15 then p14.
if p15 then p17.
if p14 then p19.
if p12 then p8.
if p11 then p8.
if p9 then p1.
if p9 then p15.
if p8 then p4.
if p8 then p12.
if p7 then p1.
if p6 then p11.
if p3 then p2.
if p2 then p14.
if p2 then p18.
if p2 then p19.
if p20 and p10 then p7.
if p20 and p3 then p13.
if p19 and p8 then p18.
if p18 and p9 then p3.
if p17 and p11 then p10.
if p17 and p10 then p14.
if p16 and p14 then p3.
if p16 and p10 then p13.
if p15 and p11 then p19.
if p15 and p9 then p10.
if p15 and p6 then p4.
if p15 and p5 then p6.
if p14 and p12 then p4.
if p14 and p9 then p20.
if p14 and p6 then p9.
if p14 and p5 then p16.
if p14 and p4 then p11.
if p14 and p2 then p1.
if p12 and p9 then p17.
if p12 and p2 then p11.
if p11 and p7 then p8.
if p11 and p7 then p16.
if p11 and p5 then p7.
if p11 and p3 then p13.
if p10 and p5 then p4.
if p10 and p2 then p18.
if p10 and p1 then p16.
if p9 and p1 then p15.
if p8 and p4 then p3.
if p8 and p1 then p4.
if p6 and p4 then p18.
if p4 and p2 then p3.
if p20 and p16 and p14 then p10.
if p20 and p15 and p14 then p16.
if p20 and p12 and p8 then p4.
if p19 and p5 and p4 then p16.
if p18 and p16 and p15 then p13.
if p18 and p15 and p9 and p4 then p0.
if p18 and p15 and p7 then p13.
if p18 and p11 and p5 then p4.
if p17 and p16 and p9 then p13.
if p17 and p13 and p2 then p10.
if p17 and p13 and p1 then p4.
if p17 and p9 and p6 then p14.
if p16 and p14 and p3 then p18.
if p16 and p9 and p4 then p19.
if p16 and p2 and p1 then p17.
if p15 and p10 and p6 then p20.
if p15 and p9 and p3 then p10.
if p14 and p12 and p4 then p1.
if p14 and p10 and p8 then p1.
if p14 and p8 and p2 then p10.
if p13 and p11 and p1 then p17.
if p12 and p9 and p8 then p18.
if p12 and p7 and p3 and p2 then p0.
if p10 and p8 and p7 then p18.
if p6 and p4 and p3 then p20.
if p20 and p17 and p14 and p8 then p19.
if p19 and p17 and p12 and p2 then p10.
if p18 and p17 and p16 and p6 then p10.
if p17 and p12 and p10 and p6 then p19.
if p17 and p12 and p10 and p1 then p2.
if p16 and p15 and p10 and p1 then p9.
if p16 and p9 and p4 and p3 then p13.
if p14 and p12 and p7 and p5 then p20.
if p13 and p10 and p4 and p1 then p8.
if p8 and p7 and p3 and p1 then p17.
```


---

### prompt_c6875730a1
- prompt_template: `prompts/exp6_horn_yesno.j2`
- prompt_style: `horn_if_then`
- parse_family: `yes_no`
- leaf_runs_count: 9

Instruction text (before `Statements:`):

```
Your task is to solve a problem in propositional logic containing both facts and if-then rules.
You will get a list of facts and if-then rules and have to determine whether a fact p0 can be derived from this list.
If a fact p0 can be derived, the last word of your answer should be 'yes',
otherwise the last word should be 'no'.

Facts are represented as 'pN' where N is a number. 
All the statements are either facts or if-then rules allowing to derive a single fact.  
All the given statements are implicitly connected with 'and': they are all claimed to be true.
 
Do not print out anything except the final yes or no.

Twelve examples:
Example 1.
```

Examples (horn=1):

- low: maxvars=3, maxlen=3, satflag=1

```
p1. p2. if p1 then p0. Answer: yes.
Example 2. Statements: p1. p2. if p1 then p9. Answer: no.
Example 3. Statements: p1. if p1 then p2. if p2 then p0. Answer: yes.
Example 4. Statements: p1. if p1 then p3. if p2 and p1 then p0. Answer: no.
Example 5. Statements: p1. if p1 then p2. if p2 then p3. if p3 then p0. Answer: yes.
Example 6. Statements: p1. if p1 then p2. if p2 then p1. if p3 then p0. Answer: no.
Example 7. Statements: p1. p3. if p1 then p2. if p2 and p3 then p4. if p4 then p0. Answer: yes.
Example 8. Statements: p1. if p1 then p2. if p2 and p3 then p4. if p4 then p0. Answer: no.
Example 9.  Statements: p6. p3. if p3 then p1. if p3 then p1. if p4 and p5 then p0. if p1 and p6 then p4. Answer: yes.
Example 10. Statements: p6. p3. if p3 then p1. if p4 then p5. if p1 and p6 then p4. Answer: no
Example 11. Statements: p6. if p3 then p4. if p6 then p7. if p5 and p6 then p0. if p7 then p3. if p4 then p5.  Answer: yes.
Example 12. Statements: p6. if p3 then p4. if p6 then p7. if p5 and p6 then p0. if p7 then p3. if p4 then p7.  Answer: no.

Please answer whether a fact p0 can be derived from the following facts and rules.

Statements:
p1.
if p3 then p1.
if p3 then p2.
if p2 and p1 then p0.
if p2 then p1.
if p3 and p2 then p1.
```

- mid: maxvars=9, maxlen=4, satflag=1

```
p1. p2. if p1 then p0. Answer: yes.
Example 2. Statements: p1. p2. if p1 then p9. Answer: no.
Example 3. Statements: p1. if p1 then p2. if p2 then p0. Answer: yes.
Example 4. Statements: p1. if p1 then p3. if p2 and p1 then p0. Answer: no.
Example 5. Statements: p1. if p1 then p2. if p2 then p3. if p3 then p0. Answer: yes.
Example 6. Statements: p1. if p1 then p2. if p2 then p1. if p3 then p0. Answer: no.
Example 7. Statements: p1. p3. if p1 then p2. if p2 and p3 then p4. if p4 then p0. Answer: yes.
Example 8. Statements: p1. if p1 then p2. if p2 and p3 then p4. if p4 then p0. Answer: no.
Example 9.  Statements: p6. p3. if p3 then p1. if p3 then p1. if p4 and p5 then p0. if p1 and p6 then p4. Answer: yes.
Example 10. Statements: p6. p3. if p3 then p1. if p4 then p5. if p1 and p6 then p4. Answer: no
Example 11. Statements: p6. if p3 then p4. if p6 then p7. if p5 and p6 then p0. if p7 then p3. if p4 then p5.  Answer: yes.
Example 12. Statements: p6. if p3 then p4. if p6 then p7. if p5 and p6 then p0. if p7 then p3. if p4 then p7.  Answer: no.

Please answer whether a fact p0 can be derived from the following facts and rules.

Statements:
p5.
if p9 then p4.
if p9 then p8.
if p8 then p3.
if p7 then p9.
if p6 then p4.
if p4 then p7.
if p1 then p7.
if p9 and p4 then p8.
if p8 and p7 then p2.
if p8 and p6 then p1.
if p8 and p4 then p1.
if p8 and p3 then p5.
if p7 and p2 then p6.
if p6 and p4 then p8.
if p6 and p1 then p8.
if p5 and p4 and p2 then p0.
if p5 and p2 then p4.
if p5 and p1 then p2.
if p5 and p1 then p9.
if p3 and p1 then p2.
if p9 and p7 and p6 and p4 then p0.
if p9 and p6 and p1 then p5.
if p9 and p5 and p3 then p2.
if p8 and p2 and p1 then p6.
if p6 and p2 and p1 then p7.
if p4 and p2 and p1 then p7.
```

- high: maxvars=15, maxlen=4, satflag=0

```
p1. p2. if p1 then p0. Answer: yes.
Example 2. Statements: p1. p2. if p1 then p9. Answer: no.
Example 3. Statements: p1. if p1 then p2. if p2 then p0. Answer: yes.
Example 4. Statements: p1. if p1 then p3. if p2 and p1 then p0. Answer: no.
Example 5. Statements: p1. if p1 then p2. if p2 then p3. if p3 then p0. Answer: yes.
Example 6. Statements: p1. if p1 then p2. if p2 then p1. if p3 then p0. Answer: no.
Example 7. Statements: p1. p3. if p1 then p2. if p2 and p3 then p4. if p4 then p0. Answer: yes.
Example 8. Statements: p1. if p1 then p2. if p2 and p3 then p4. if p4 then p0. Answer: no.
Example 9.  Statements: p6. p3. if p3 then p1. if p3 then p1. if p4 and p5 then p0. if p1 and p6 then p4. Answer: yes.
Example 10. Statements: p6. p3. if p3 then p1. if p4 then p5. if p1 and p6 then p4. Answer: no
Example 11. Statements: p6. if p3 then p4. if p6 then p7. if p5 and p6 then p0. if p7 then p3. if p4 then p5.  Answer: yes.
Example 12. Statements: p6. if p3 then p4. if p6 then p7. if p5 and p6 then p0. if p7 then p3. if p4 then p7.  Answer: no.

Please answer whether a fact p0 can be derived from the following facts and rules.

Statements:
p2.
p12.
if p15 then p5.
if p15 then p6.
if p15 then p11.
if p14 then p15.
if p10 then p2.
if p10 then p13.
if p9 then p4.
if p8 then p5.
if p6 then p11.
if p6 then p14.
if p5 then p2.
if p4 then p1.
if p2 then p11.
if p2 then p14.
if p1 then p12.
if p15 and p13 then p12.
if p15 and p12 then p9.
if p15 and p9 then p13.
if p15 and p7 then p9.
if p15 and p1 then p9.
if p14 and p12 then p7.
if p14 and p9 then p3.
if p14 and p3 then p11.
if p13 and p10 then p4.
if p12 and p3 then p5.
if p11 and p4 then p6.
if p10 and p4 then p15.
if p9 and p6 then p8.
if p9 and p3 then p13.
if p9 and p2 then p1.
if p8 and p7 then p3.
if p8 and p2 then p11.
if p7 and p1 then p12.
if p6 and p1 then p7.
if p15 and p13 and p12 then p6.
if p15 and p13 and p5 and p4 then p0.
if p15 and p12 and p2 then p8.
if p15 and p11 and p3 then p4.
if p14 and p8 and p2 then p5.
if p13 and p8 and p5 then p10.
if p11 and p8 and p3 then p6.
if p11 and p7 and p5 and p4 then p0.
if p10 and p6 and p4 and p1 then p0.
if p9 and p2 and p1 then p15.
```


---

