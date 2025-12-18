"""Prompt rendering helpers and templates.

This module separates:
- **representation**: how a CNF formula is rendered (horn_rules, cnf_nl, cnf_compact)
- **prompt_profile**: whether the prompt includes one instruction block (direct) or multiple (mixed_interpretation)
- **response_style**: answer_only vs explain_then_answer (implemented via template choice)
"""

from .render import render_clauses, render_prompt

__all__ = ["render_clauses", "render_prompt"]


