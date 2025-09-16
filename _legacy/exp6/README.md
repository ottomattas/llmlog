# experiments v6: specifically horn problems, with a yes/no output, no details asked

**Just 300 first horn clauses only, in the if...then representation, asking for just a yes/no output without CoT**

**This experiment is superseded by exp8: better look at exp8**

problems_dist20_v1.js:
Problem set: 3..15 vars, 3..4 cllen, both horn and non-horn, 20 problems per distribution.

Main result file: horn_gptresults.js, with 300 first horn problems

Usage:
    gpt-4o-2024-11-20
    temperature=0
    seed=1234
    max_tokens=2000

The difference from exp3 (v3): 
* instead of representation with or-clauses, we use if...then clauses like "if p1 and p2 then p3".
* instead of asking about contradiction / satisfiability we ask whether a special variable p0 is derivable


Useful important prompt details:

    prefix="Your task is to solve a problem in propositional logic containing both facts and if-then rules.\n"
    prefix+="You will get a list of facts and if-then rules and have to determine whether a fact p0 can be derived from this list.\n"
    prefix+="If a fact p0 can be derived, the last word of your answer should be 'yes',\n"
    prefix+="otherwise the last word should be 'no'.\n\n"

    details="Facts are represented as 'pN' where N is a number. \n"
    details+="All the statements are either facts or if-then rules allowing to derive a single fact.  \n"
    details+="All the given statements are implicitly connected with 'and': they are all claimed to be true.\n" 

    details+="Do not print out anything except the final yes or no.\n\n"

    example="Twelve examples:\n"
    example+="Example 1. Statements: p1. p2. if p1 then p0. Answer: yes.\n"
    example+="Example 2. Statements: p1. p2. if p1 then p9. Answer: no.\n"
    example+="Example 3. Statements: p1. if p1 then p2. if p2 then p0. Answer: yes.\n"
    example+="Example 4. Statements: p1. if p1 then p3. if p2 and p1 then p0. Answer: no.\n"
    example+="Example 5. Statements: p1. if p1 then p2. if p2 then p3. if p3 then p0. Answer: yes.\n"
    example+="Example 6. Statements: p1. if p1 then p2. if p2 then p1. if p3 then p0. Answer: no.\n"
    example+="Example 7. Statements: p1. p3. if p1 then p2. if p2 and p3 then p4. if p4 then p0. Answer: yes.\n"
    example+="Example 8. Statements: p1. if p1 then p2. if p2 and p3 then p4. if p4 then p0. Answer: no.\n"
    example+="Example 9.  Statements: p6. p3. if p3 then p1. if p3 then p1. if p4 and p5 then p0. if p1 and p6 then p4. Answer: yes.\n"
    example+="Example 10. Statements: p6. p3. if p3 then p1. if p4 then p5. if p1 and p6 then p4. Answer: no\n"
    example+="Example 11. Statements: p6. if p3 then p4. if p6 then p7. if p5 and p6 then p0. if p7 then p3. if p4 then p5.  Answer: yes.\n"
    example+="Example 12. Statements: p6. if p3 then p4. if p6 then p7. if p5 and p6 then p0. if p7 then p3. if p4 then p7.  Answer: no.\n"

  