# llmlog

**Experiments with LLMs and logic: what can LLMs solve?**

## Code and files

`makeproblems.py` prints out a configurable number of different propositional logic problem distributions along with their proofs or satisfying valuations.
The global configuration variables are at the beginning of the code. The first printed line describes the format of following lines.
Each following line is one propositional problem along with the metainformation and a proof or a satisfying valuation, as a json / python nested list of integers.
The meaning of the list elements, as indicated on the first line:

    ["id","maxvarnr","maxlen","mustbehorn","issatisfiable","problem", 
    "proof_of_inconsistency_or_satisfying_valuation","units_derived_by_horn_clauses"]

* Here "maxvarnr","maxlen","mustbehorn","issatisfiable" indicate the concrete distribution. 
* Problems are represented as clauses, each clause being a list of positive/negative integers. 
* A proof is a list of input and derived clauses in the format 
["clause_number_in_proof","parent_clause_numbers","derived_clause"]. 
* A valuation is a list of positive/negative integers satisfying the problem.
* The "units_derived_by_horn_clauses" is a list of integers representing units derivable by horn clauses in a linear manner. Zero at the end signifies that a a contradiction was derived.

The outer loop of distribution generation is the maximal number of variables allowed (from 3 to 15), followed by the maximal length of a clause (2,3 or 4), followed by horn or not (1 or 0). Inside a distribution the provable/satisfiable clauses are interleaved, with exactly the same number of provable and satisfiable clauses.

`someprop.js` is an example file created by `makeproblems.py`, with 10 provable and 10 satisfiable problems for each distribution.

`gpt.py` is for trying out prompts over the GPT API from the command line. Run without arguments to get a help text.

`askllm.py` is for GPT-solving the problems created by `makeproblems.py`. It reads the file row by row, makes a prompt and asks GPT API.
Run without arguments to get a help text. The output is both printed and written to a file `gptresults.js` row-by-row as json lists. Each list
contains the original full input problem along with metainfo and proofs/valuations, to which is appended the parsed answer, either 0 (GPT claims contradiction) or 1 (GPT claims satisfiable) and finally the whole textual answer given by LLM.

`analyze.py` is for creating statistics about one askllm.py output.

`utils/provider_manager.py` provides a unified interface for handling multiple LLM providers. Currently, it supports the Anthropic provider (via `utils/anthropic_client.py`) and can be extended to support others like OpenAI.

`utils/anthropic_client.py` provides an interface to the Anthropic API (Claude models) for generating completions. It reads API keys from the secrets.json file and offers functions to create a client and generate completions.

## Subfolders and separate experiments 

The *exp* subfolders contain code and data for specific separate experiments. They do typically have their own README.

These exp folders all use the problem file `problems_dist20_v1.js`:

* exp1 : base experiment with GPT-4o and 800 problems, using "p1 is true" and "p1 is false" representation with connecting "or".
* exp2 : a more compact representation ("p1" and "not(p1)") than used in exp1: seems slightly better
* exp3 : just 200 first horn clauses only, asking for a linear p1, p2, ... etc CoT output with derived variables printed out one by one
* exp4 : just 200 first horn clauses only, asking for a linear p1 [parents], p2 [parents], ... etc CoT output with concrete derivation steps
* exp5 : (superseded by exp7) just 300 first horn clauses only, using the "if...then" representation, asking for a linear p1, p2, ... etc CoT output with derived variables printed out 
* exp6 : (superseded by exp8) Just 300 first horn clauses only, in the if...then representation, asking for just a yes/no output without CoT
* exp7 : 520 horn clauses, using the "if...then" representation, asking for a linear p1, p2, ... etc CoT output with derived variables printed out 
* exp8 : 520 horn clauses, using the if...then representation, asking for just a yes/no output without CoT

## Notes on performance 

* exp1 demonstrates generally weak performance, getting worse as problems get more complex
* exp2 shows that a more compact representation ("p1" and "not(p1)") vs ("p1 is true", "p1 is false") is slightly better
* exp3 and exp4 show that the gpt4o does not understand the linear horn solving algorithm well enough when the clause notation with ... or ... is used
* exp7 shows that gpt4o does understand the linear horn solving algorithm well (and performs well) in case the if .. then ... notation is used
* exp8 shows that if linear horn solving algorithm is not described/explicated, then gpt4o performs badly on horn problems

## Environment Setup

It is recommended to use a Python virtual environment to manage dependencies for this project. Follow these steps:

1. Create a new virtual environment:
   ```
   python3 -m venv venv
   ```

2. Activate the virtual environment:
   - On macOS/Linux:
     ```
     source venv/bin/activate
     ```
   - On Windows:
     ```
     venv\Scripts\activate
     ```

3. Install the necessary packages:
   - If a `requirements.txt` file is provided:
     ```
     pip install -r requirements.txt
     ```
   - Otherwise, you can manually install the needed packages. For example, to install matplotlib (which is required by `analyze.py`):
     ```
     pip install matplotlib
     ```

4. Add your API credentials:
   Create a `secrets.json` file in the project root. This file should contain your API keys in valid JSON format. For example:
   ```json
   {
     "gpt_key": "your-openai-api-key-here",
     "anthropic_api_key": "your-anthropic-api-key-here"
   }
   ```
   Make sure to add `secrets.json` to your `.gitignore` file to prevent it from being tracked by version control.
