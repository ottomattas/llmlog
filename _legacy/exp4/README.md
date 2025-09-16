# experiments v4: specifically horn problems, with a detailed proof output

**Just 200 first horn clauses only, asking for a linear p1 [parents], p2 [parents], ... etc CoT output with concrete derivation steps**

problems_dist20_v1.js:
Problem set: 3..15 vars, 3..4 cllen, both horn and non-horn, 20 problems per distribution.

Main result file:  horn_gptresults_v4.js,  gpt solutions for the first 200 horn problems in the set above.

Usage:
    gpt-4o-2024-11-20
    temperature=0
    seed=1234
    max_tokens=2000

The difference from exp3 (v3): 
* the specific method for producing CoT output contains also explicit proof steps
* also single proof steps are separately described plus examples given


Useful important prompt details:

    details+="A true variable X is directly derivable by a statement S if and only if S consists of X and a number of negative variables not(Y), not(Z) etc, so that \n"
    details+="each of these negative variables Y, Z etc is true, that is, present as a given positive statement consisting of just this sole variable, or it has been derived earlier.\n"
    details+="In other words, a variable X is directly derivable by some statements S1,...,Sn if X must be inevitably true in case all the statements in S1,...,Sn are true.\n"
    details+="For example, p2 is derivable from 'not(p1) or not(p3) or p2' if and only if both p1 and p3 are either input statements like 'p1. p3.' or have\n"
    details+="been derived earlier as true variables.\n"
    details+="As a counter-example, p2 is not directly derivable from the statements (not(p3) or p2) and not(p3). p2 would be derivable from (not(p3) or p2) and a true variable p3.\n"
    details+="As another counter-example, p1 is not directly derivable from the statements (not(p3) or not(p2) or p1) and p2 alone, in case p3 is not known to be a true variable. \n"
    details+="As a yet another counter-example, p3 is not directly derivable from (not(p3) or not(p2)) and p2 and p1.\n"
    details+="As a yet another counter-example, p3 is not directly derivable from (not(p3) or p2) and p2.\n\n"

    details+="After each derived variable print 'from' and the statements used for deriving it.\n"
    details+="Then, print out all the true variables (along with the statements used for deriving) \n"
    details+"which can be similarly directly derived by some given statement and both the newly printed true variables and given true variable statements, \n"
    details+="pand which have not been printed earlier.\n"
    details+="Then continue the same procedure of printing out new directly derivable true variables from the statements, until either no new variables can be derived or a direct contradiction\n"
    details+="is found with input and derived variables on one hand and some fully negative given statement on the other hand.\n"
    details+="In case a contradiction is found, finally print 'contradiction' followed by 'from' and the statements used for the contradiction. \n"
    details+"In case no direct contradiction is found and no new true variables can be derived,\n"
    details+="finally print 'satisfiable'.\n\n"

    details+="Do not print out anything except the derivable true variables, the statements used for deriving them, and the final answer."

    example="Twelve examples:\n"
    example+="Example 1. Statements: p1. p2. not(p1). Answer: contradiction from (not(p1) and p1).\n"
    example+="Example 2. Statements: p1. p2. not(p3). Answer: satisfiable.\n"
    example+="Example 3. Statements: p1. not(p1) or p2. not(p2). Answer: p2 from (not(p1) or p2) and p1, contradiction from not(p2) and p2.\n"
    example+="Example 4. Statements: p1. not(p1) or p3. not(p2) or not(p1). Answer: p3 from (not(p1) or p3) and p1, satisfiable.\n"
    example+="Example 5. Statements: p1. not(p1) or p2. not(p2) or p3. not(p3). Answer: p2 from (not(p1) or p2) and p1, p3 from (not(p2) or p3) and p2, contradiction from not(p3) and p3.\n"
    example+="Example 6. Statements: p1. not(p1) or p2. not(p2) or p1. not(p3). Answer: p2 from (not(p1) or p2) and p1, satisfiable.\n"
    example+="Example 7. Statements: p1. p3. not(p1) or p2. not(p2) or not(p3) or p4. not(p4). Answer: p2 from (not(p1) or p2) and p1, p4 from (not(p2) or not(p3) or p4) and p2 and p3, contradiction from not(p4) and p4.\n"
    example+="Example 8. Statements: p1. not(p1) or p2. not(p2) or not(p3) or p3. not(p3). Answer: p2 from (not(p1) or p2) and p1, satisfiable.\n"
    example+="Example 9.  Statements: p6. p3. not(p3) or p1. not(p4) or p5. not(p5) or not(p4). not(p1) or not(p6) or p4. Answer: p1 from (not(p3) or p1) and p3, p4 from (not(p1) or not(p6) or p4) and p1 and p6, p5 from (not(p4) or p5) and p4, contradiction from (not(p5) or not(p4)) and p5 and p4.\n"
    example+="Example 10. Statements: p6. p3. not(p3) or p1. not(p4) or p5. not(p1) or not(p6) or p4. Answer: p1 from (not(p3) or p1) and p3, p4 from (not(p1) or not(p6) or p4) and p1 and p6, p5 from (not(p4) or p5) and p4, satisfiable.\n"
    example+="Example 11. Statements: p6. not(p3) or p4. not(p6) or p7. not(p5) or not(p6). not(p7) or p3. not(p4) or p5.  Answer: p7 from (not(p6) or p7) and p6, p3 from (not(p7) or p3) and p7, p4 from (not(p3) or p4) and p3, p5 from (not(p4) or p5) and p4, contradiction from (not(p5) or not(p6)) and p5 and p6.\n"
    example+="Example 12. Statements: p6. not(p3) or p4. not(p6) or p7. not(p5) or not(p6). not(p7) or p3. not(p4) or p7.  Answer: p7 from (not(p6) or p7) and p6, p3 from (not(p7) or p3) and p7, p4 from (not(p3) or p4) and p3, satisfiable.\n"


