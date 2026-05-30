from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Sequence, Union


Clause = List[int]
CNF = List[Clause]


@dataclass(frozen=True)
class ProblemRow:
    """Typed view of a single dataset row.

    The dataset format is legacy-compatible and stored as JSON arrays:
      [id, maxvarnr, maxlen, mustbehorn, issatisfiable, problem, proof_or_model, horn_units]
    """

    id: Union[int, str]
    maxvarnr: Optional[int]
    maxlen: Optional[int]
    mustbehorn: Optional[int]
    issatisfiable: Optional[int]
    problem: Optional[CNF]
    proof_or_model: Any
    horn_units: Any
    raw: List[Any]

    @staticmethod
    def is_header_row(row: Any) -> bool:
        if not isinstance(row, list):
            return False
        if not row:
            return False
        # First element in header is usually "id"
        return all(isinstance(x, str) for x in row) and "id" in row

    @classmethod
    def from_array(cls, row: Sequence[Any]) -> "ProblemRow":
        if not isinstance(row, (list, tuple)):
            raise TypeError(f"Expected list/tuple row, got {type(row)}")
        if len(row) < 8:
            raise ValueError(f"Expected 8 columns, got {len(row)}: {row!r}")

        rid = row[0]
        maxvarnr = row[1]
        maxlen = row[2]
        mustbehorn = row[3]
        issatisfiable = row[4]
        problem = row[5]
        proof_or_model = row[6]
        horn_units = row[7]

        def _to_int_or_none(v: Any) -> Optional[int]:
            if v is None:
                return None
            try:
                return int(v)
            except Exception:
                return None

        def _to_int01_or_none(v: Any) -> Optional[int]:
            iv = _to_int_or_none(v)
            if iv is None:
                return None
            if iv in (0, 1):
                return iv
            # allow truthy/falsey integers but normalize to 0/1 when possible
            if iv == 0:
                return 0
            if iv != 0:
                return 1
            return None

        # CNF normalization: ensure list[list[int]] or None
        cnf: Optional[CNF]
        if isinstance(problem, list):
            cnf = []
            for cl in problem:
                if not isinstance(cl, list):
                    continue
                lits: List[int] = []
                for lit in cl:
                    try:
                        lits.append(int(lit))
                    except Exception:
                        continue
                if lits:
                    cnf.append(lits)
        else:
            cnf = None

        return cls(
            id=(int(rid) if isinstance(rid, bool) is False and isinstance(rid, int) else rid),  # keep str ids as-is
            maxvarnr=_to_int_or_none(maxvarnr),
            maxlen=_to_int_or_none(maxlen),
            mustbehorn=_to_int01_or_none(mustbehorn),
            issatisfiable=_to_int01_or_none(issatisfiable),
            problem=cnf,
            proof_or_model=proof_or_model,
            horn_units=horn_units,
            raw=list(row),
        )


