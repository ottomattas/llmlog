"""Dataset reading + filtering utilities.

The canonical dataset shape is the legacy 8-column array row:
[id, maxvarnr, maxlen, mustbehorn, issatisfiable, problem, proof_or_model, horn_units]
"""

from .schema import ProblemRow
from .reader import iter_problem_arrays, iter_problem_rows, read_jsonl_values
from .filters import horn_only, nonhorn_only, limit, skip

__all__ = [
    "ProblemRow",
    "read_jsonl_values",
    "iter_problem_arrays",
    "iter_problem_rows",
    "skip",
    "limit",
    "horn_only",
    "nonhorn_only",
]


