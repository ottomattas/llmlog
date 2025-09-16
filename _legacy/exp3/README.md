# experiments v3: specifically horn problems

**Just 200 first horn clauses only, asking for a linear p1, p2, ... etc CoT output with derived variables printed out one by one**

problems_dist20_v1.js:
Problem set: 3..15 vars, 3..4 cllen, both horn and non-horn, 20 problems per distribution.

Main result file:  horn_gptresults_v3.js,  gpt solutions for the first 200 horn problems in the set above.

Usage:
    gpt-4o-2024-11-20
    temperature=0
    seed=1234
    max_tokens=2000

The difference from exp2 (v2): 
* horn only
* we give a specific method for producing CoT output, along with 12 examples: print all derivable variables until contradiction
or no more can be found

Useful important prompt details:

    example="Twelve examples:\n"
    example+="Example 1. Statements: p1. p2. not(p1). Answer: contradiction.\n"
    example+="Example 2. Statements: p1. p2. not(p3). Answer: satisfiable.\n"
    example+="Example 3. Statements: p1. not(p1) or p2. not(p2). Answer: p2 contradiction.\n"
    example+="Example 4. Statements: p1. not(p1) or p3. not(p2) or not(p1). Answer: p3 satisfiable.\n"
    example+="Example 5. Statements: p1. not(p1) or p2. not(p2) or p3. not(p3). Answer: p2 p3 contradiction.\n"
    example+="Example 6. Statements: p1. not(p1) or p2. not(p2) or p1. not(p3). Answer: p2 satisfiable.\n"
    example+="Example 7. Statements: p1. p3. not(p1) or p2. not(p2) or not(p3) or p4. not(p4). Answer: p2 p4 contradiction.\n"
    example+="Example 8. Statements: p1. not(p1) or p2. not(p2) or not(p3) or p3. not(p3). Answer: p2 satisfiable.\n"
    example+="Example 9.  Statements: p6. p3. not(p3) or p1. not(p4) or p5. not(p5) or not(p4). not(p1) or not(p6) or p4. Answer: p1 p4 p5 contradiction.\n"
    example+="Example 10. Statements: p6. p3. not(p3) or p1. not(p4) or p5. not(p1) or not(p6) or p4. Answer: p1 p4 p5 satisfiable.\n"
    example+="Example 11. Statements: p6. not(p3) or p4. not(p6) or p7. not(p5) or not(p6). not(p7) or p3. not(p4) or p5.  Answer: p7 p3 p4 p5 contradiction.\n"
    example+="Example 12. Statements: p6. not(p3) or p4. not(p6) or p7. not(p5) or not(p6). not(p7) or p3. not(p4) or p7.  Answer: p7 p3 p4 satisfiable.\n"



