# experiments v1

**Base experiment with GPT-4o and 800 problems**

problems_dist20_v1.js:
Problem set: 3..15 vars, 3..4 cllen, both horn and non-horn, 20 problems per distribution.

Main result file: gptresults_v1.js,  gpt solutions for the first 800 problems in the set above.

Usage:
    gpt-4o-2024-11-20
    temperature=0
    seed=1234
    max_tokens=2000


Useful important prompt details:

  prefix="Your task is to solve a problem in propositional logic.\n"
  prefix+="You will get a list of statements and have to determine whether the statements form a logical contradiction or not.\n"
  prefix+="If the statements form a contradiction, the last word of your answer should be 'contradiction',\n"
  prefix+="otherwise the last word should be either 'satisfiable' or 'unknown'.\n"

  details="Propositional variables are represent as 'pN' where N is a number. They are either true or false.\n"
  details+="'X or Y' means that X is true or Y is true or both X and Y are true.\n"
  details+="All the given statements are implicitly connected with 'and': they are all claimed to be true.\n"
  
  example="Two examples:\n"
  example+="Example 1. Statements: p1 is true. p1 is false or p2 is true. p2 is false. Answer: contradiction.\n"
  example+="Example 2. Statements: p1 is true. p1 is true or p2 is true. p2 is false. Answer: satisfiable.\n"


