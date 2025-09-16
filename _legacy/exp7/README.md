# experiments v7: specifically horn problems, with a detailed proof output

**All horn clauses (520) in problems_dist20_v1.js, in the if...then representation, asking for a linear p1, p2, ... etc CoT output without full derivation steps**

**This experiment supersedes exp5: no need to look at exp5**

problems_dist20_v1.js:
Problem set: 3..15 vars, 3..4 cllen, both horn and non-horn, 20 problems per distribution.

Main result file: merged_horn_gptresults.js, with 520 horn problems

Usage:
    gpt-4o-2024-11-20
    temperature=0
    seed=1234
    max_tokens=2000

NB! 
* The output file to use is `merged_horn_gptresults.js`: it is a concatenation of an earlier experiment `exp5_fixed_horn_gptresults.js` and current `horn_gptresults.js`
* The `askllm.py` skips first 298 problems, since they were handled by exp5.

The core difference from exp3 (v3): 
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
    
    details+="In order to solve a given problem, you must use the following method:\n"
    details+="First, derive and print out all the facts which can be derived directly by some given if-then rule from the given facts in the input\n"
    details+="and which are not already present in the list of given statements as facts. \n\n"

    details+="Then, print out all the facts \n"
    details+="which can be similarly directly derived by some if-then rule from the newly printed facts and initially given facts \n"
    details+="and which have not been printed earlier.\n"
    details+="Then continue the same procedure of printing out new facts, until either no new facts can be derived or the fact p0 is derived.\n"
    details+="If the fact p0 is derived and printed, then finally print 'yes'. \n"
    details+="If no new facts can be derived and p0 is not derived, then finally print 'no'.\n\n"

    details+="Do not print out anything except the derivable facts and the final yes or no.\n\n"

    example="Twelve examples:\n"
    example+="Example 1. Statements: p1. p2. if p1 then p0. Answer: p0 yes.\n"
    example+="Example 2. Statements: p1. p2. if p1 then p9. Answer: p9 no.\n"
    example+="Example 3. Statements: p1. if p1 then p2. if p2 then p0. Answer: p2 p0 yes.\n"
    example+="Example 4. Statements: p1. if p1 then p3. if p2 and p1 then p0. Answer: p3 no.\n"
    example+="Example 5. Statements: p1. if p1 then p2. if p2 then p3. if p3 then p0. Answer: p2 p3 p0 yes.\n"
    example+="Example 6. Statements: p1. if p1 then p2. if p2 then p1. if p3 then p0. Answer: p2 no.\n"
    example+="Example 7. Statements: p1. p3. if p1 then p2. if p2 and p3 then p4. if p4 then p0. Answer: p2 p4 p0 yes.\n"
    example+="Example 8. Statements: p1. if p1 then p2. if p2 and p3 then p4. if p4 then p0. Answer: p2 no.\n"
    example+="Example 9.  Statements: p6. p3. if p3 then p1. if p3 then p1. if p4 and p5 then p0. if p1 and p6 then p4. Answer: p1 p4 p5 p0 yes.\n"
    example+="Example 10. Statements: p6. p3. if p3 then p1. if p4 then p5. if p1 and p6 then p4. Answer: p1 p4 p5 no\n"
    example+="Example 11. Statements: p6. if p3 then p4. if p6 then p7. if p5 and p6 then p0. if p7 then p3. if p4 then p5.  Answer: p7 p3 p4 p5 p0 yes.\n"
    example+="Example 12. Statements: p6. if p3 then p4. if p6 then p7. if p5 and p6 then p0. if p7 then p3. if p4 then p7.  Answer: p7 p3 p4 no.\n"
