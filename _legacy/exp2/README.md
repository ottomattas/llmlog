# experiments v2

**A more compact representation than used in exp1: seems slightly better**

problems_dist20_v1.js:
Problem set: 3..15 vars, 3..4 cllen, both horn and non-horn, 20 problems per distribution.

Main result file:  gptresults_v2.js,  gpt solutions for the first 800 problems in the set above.

Usage:
    gpt-4o-2024-11-20
    temperature=0
    seed=1234
    max_tokens=2000

The difference from exp1 (v1): instead of saying "pN is true/false" we say "p1" or "not(p1)".
I.e. the problem statements are thus more compact. The explanations in the prompt also reflect this:

Useful important prompt details:

    details="Propositional variables are represent as 'pN' where N is a number. They are either true or false.\n"
    details+="pN means that pN is true. not(pN) means that pN is false.\n"
    details+="'X or Y' means that X is true or Y is true or both X and Y are true.\n"
    details+="All the given statements are implicitly connected with 'and': they are all claimed to be true.\n"
    
    example="Two examples:\n"
    example+="Example 1. Statements: p1. not(p1) or p2. not(p2). Answer: contradiction.\n"
    example+="Example 2. Statements: p1. p1 or p2. not(p2). Answer: satisfiable.\n"
