from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from ..problems.schema import CNF, ProblemRow


def render_clauses(problem: CNF, representation: str) -> str:
    """Render CNF clauses into a text block for the given representation.

    Representation mapping (compat with experiments.runner.render_prompt):
    - horn_rules    -> horn_if_then
    - cnf_nl        -> cnf_v1
    - cnf_compact   -> cnf_v2
    """
    rep = (representation or "").strip().lower()
    if rep in ("horn_rules", "horn_if_then", ""):
        lines: List[str] = []
        for clause in problem:
            pos: List[int] = []
            neg: List[int] = []
            for var in clause:
                if var > 0:
                    pos.append(var)
                else:
                    neg.append(var)
            if pos and not neg and len(pos) == 1:
                lines.append(f"p{pos[0]}.")
            elif neg and not pos:
                prem = " and ".join([f"p{0 - el}" for el in neg])
                lines.append(f"if {prem} then p0.")
            elif neg and len(pos) == 1:
                prem = " and ".join([f"p{0 - el}" for el in neg])
                lines.append(f"if {prem} then p{pos[0]}.")
            else:
                # Non-Horn clause: render in compact CNF inside Horn block (hybrid)
                parts: List[str] = []
                for var in clause:
                    parts.append(f"p{var}" if var > 0 else f"not(p{0 - var})")
                lines.append(" or ".join(parts) + ".")
        return "\n".join(lines)

    if rep in ("cnf_nl", "cnf_v1", "nl"):
        lines: List[str] = []
        for clause in problem:
            parts: List[str] = []
            for var in clause:
                if var > 0:
                    parts.append(f"p{var} is true")
                else:
                    parts.append(f"p{0 - var} is false")
            lines.append(" or ".join(parts) + ".")
        return "\n".join(lines)

    if rep in ("cnf_compact", "cnf_v2", "compact"):
        lines: List[str] = []
        for clause in problem:
            parts: List[str] = []
            for var in clause:
                parts.append(f"p{var}" if var > 0 else f"not(p{0 - var})")
            lines.append(" or ".join(parts) + ".")
        return "\n".join(lines)

    raise ValueError(f"Unknown representation: {representation!r}")


def render_prompt(
    *,
    problem: ProblemRow,
    template_path: str,
    representation: str,
    variables: Optional[Dict[str, Any]] = None,
) -> str:
    """Render a full prompt using a Jinja template and a ProblemRow."""
    if not problem.problem:
        raise ValueError("ProblemRow has no CNF problem payload")

    tmpl_path = Path(template_path)
    if not tmpl_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")

    env = Environment(
        loader=FileSystemLoader(str(tmpl_path.parent)),
        undefined=StrictUndefined,
        autoescape=False,
        keep_trailing_newline=True,
    )
    tmpl = env.get_template(tmpl_path.name)

    clauses_txt = render_clauses(problem.problem, representation=representation)
    ctx = dict(variables or {})
    ctx.setdefault("clauses", clauses_txt)
    return tmpl.render(**ctx)


