#!/usr/bin/env python3
"""Preview rendered prompts without calling APIs."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from runner import render_prompt


def main():
    # Load dataset
    dataset_path = "data/problems_quicktest.js"
    problems = []
    with open(dataset_path) as f:
        for i, line in enumerate(f):
            if i == 0:  # skip header
                continue
            if i > 3:  # only first 3 problems
                break
            problems.append(json.loads(line.strip()))
    
    # Load template
    template_path = "prompts/_template_unified.j2"
    template_text = Path(template_path).read_text()
    
    # Test different styles
    styles = [
        ("horn_if_then", "Horn (facts and if-then rules)"),
        ("cnf_v1", "CNF Verbose (p1 is true or p2 is false)"),
        ("cnf_v2", "CNF Compact (p1 or not(p2))"),
    ]
    
    for style, desc in styles:
        print(f"\n{'='*70}")
        print(f"STYLE: {style} — {desc}")
        print(f"{'='*70}\n")
        
        for i, problem in enumerate(problems[:2], 1):
            print(f"--- Problem {problem[0]} (vars={problem[1]}, len={problem[2]}, horn={problem[3]}, sat={problem[4]}) ---\n")
            
            try:
                prompt = render_prompt(problem, template_text, style)
                print(prompt)
            except Exception as e:
                print(f"ERROR: {e}")
            
            print()


if __name__ == "__main__":
    main()

