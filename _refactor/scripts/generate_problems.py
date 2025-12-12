#!/usr/bin/env python3

"""Generate propositional-logic problem datasets.

This script is intentionally a *thin wrapper* around the legacy generator:
- We reuse `_legacy/makeproblems.py` for problem construction (random CNF/Horn clause sets).
- We add deterministic seeding plus modern solver integration:
  - SAT models via PySAT (solver: g3)
  - UNSAT proofs via Kissat (DRAT, stored in a JSON-compatible numeric encoding)

Output is JSONL:
- First line: header (JSON array of column names)
- Next lines: problem rows (JSON arrays)

Row schema matches the legacy 8-column shape:
[id, maxvarnr, maxlen, mustbehorn, issatisfiable, problem, proof_or_model, horn_units]

Notes on UNSAT proof encoding:
- Kissat emits DRAT with optional deletions.
- We encode each proof line as a list of ints to stay JSON-compatible:
  - additions:  [ 1, lit1, lit2, ... ]
  - deletions:  [ -1, lit1, lit2, ... ]
  - empty clause (end of proof): [1]
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
from typing import Iterable, List, Optional, Sequence, Tuple

# ---- Import legacy generator primitives ------------------------------------

def _add_repo_root_to_syspath() -> None:
    """Make `_legacy` importable both from `_refactor/` and final repo root."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.abspath(os.path.join(script_dir, "..")),      # expected final repo root
        os.path.abspath(os.path.join(script_dir, "../..")),   # current repo root when running under _refactor/
    ]
    for root in candidates:
        if os.path.isdir(os.path.join(root, "_legacy")):
            if root not in sys.path:
                sys.path.append(root)
            return


_add_repo_root_to_syspath()

try:
    import _legacy.makeproblems as legacy  # type: ignore
except Exception as e:
    raise SystemExit(
        "Failed to import _legacy.makeproblems. "
        "Run from the repo (or ensure repo root is on PYTHONPATH).\n"
        f"Import error: {e}"
    )


# ---- Optional PySAT --------------------------------------------------------

try:
    from pysat.formula import CNF  # type: ignore
    from pysat.solvers import Solver  # type: ignore

    _HAS_PYSAT = True
except Exception:
    _HAS_PYSAT = False


# ---- Parsing helpers -------------------------------------------------------

def _parse_int_list(spec: str) -> List[int]:
    """Parse "3-10" or "3,4,7" into a list of ints."""
    s = (spec or "").strip()
    if not s:
        return []
    if "-" in s:
        a, b = s.split("-", 1)
        start = int(a.strip())
        end = int(b.strip())
        if end < start:
            start, end = end, start
        return list(range(start, end + 1))
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return [int(p) for p in parts]


def _clauses_to_dimacs(clauses: Sequence[Sequence[int]]) -> str:
    maxvar = 0
    for cl in clauses:
        for lit in cl:
            if abs(lit) > maxvar:
                maxvar = abs(lit)
    lines = [f"p cnf {maxvar} {len(clauses)}"]
    for cl in clauses:
        lines.append(" ".join(str(l) for l in cl) + " 0")
    return "\n".join(lines) + "\n"


# ---- Solvers ---------------------------------------------------------------

def _pysat_solve_model(clauses: Sequence[Sequence[int]], solver_name: str = "g3") -> Tuple[bool, Optional[List[int]]]:
    if not _HAS_PYSAT:
        raise RuntimeError("PySAT not installed. Install python-sat to use PySAT solving.")
    cnf = CNF(from_clauses=[list(cl) for cl in clauses])
    with Solver(name=solver_name, bootstrap_with=cnf, with_proof=False) as s:
        sat = bool(s.solve())
        if not sat:
            return False, None
        model = s.get_model() or []
        return True, [int(x) for x in model]


def _kissat_unsat_proof(
    clauses: Sequence[Sequence[int]],
    kissat_cmd: str = "kissat",
    timeout_s: float = 30.0,
    include_deletions: bool = True,
) -> List[List[int]]:
    """Return DRAT proof as JSON-friendly int lists.

    Each proof line is encoded as:
      - add clause: [1, lits...]
      - delete clause: [-1, lits...]  (if include_deletions=True)
      - empty clause: [1]
    """
    if not shutil.which(kissat_cmd):
        raise RuntimeError(f"kissat not found on PATH: {kissat_cmd}")

    with tempfile.TemporaryDirectory() as td:
        cnf_path = os.path.join(td, "input.cnf")
        proof_path = os.path.join(td, "proof.drat")
        with open(cnf_path, "w") as f:
            f.write(_clauses_to_dimacs(clauses))

        # kissat: kissat [options] <dimacs> [<proof>]
        args = [kissat_cmd, "--no-binary", cnf_path, proof_path, "-f"]
        proc = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=timeout_s)

        if proc.returncode == 10:
            # SAT (unexpected if caller asked for UNSAT proof)
            raise RuntimeError("kissat returned SAT while UNSAT proof was requested")
        if proc.returncode != 20:
            raise RuntimeError(
                f"kissat failed rc={proc.returncode}; stderr={proc.stderr.strip()!r}; stdout={proc.stdout.strip()!r}"
            )

        steps: List[List[int]] = []
        if not os.path.exists(proof_path):
            return steps
        with open(proof_path, "r") as pf:
            for line in pf:
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                action = 1
                if parts[0] == "d":
                    if not include_deletions:
                        continue
                    action = -1
                    parts = parts[1:]
                lits: List[int] = []
                for p in parts:
                    try:
                        v = int(p)
                    except Exception:
                        continue
                    if v == 0:
                        break
                    lits.append(v)
                # empty clause is a valid proof terminator
                if not lits:
                    steps.append([action])
                else:
                    steps.append([action] + lits)
        return steps


# ---- Generation ------------------------------------------------------------

def _solve_with_pysat_and_kissat(
    problem: List[List[int]],
    pysat_solver: str,
    kissat_cmd: str,
    kissat_timeout: float,
) -> Tuple[bool, List]:
    sat, model = _pysat_solve_model(problem, solver_name=pysat_solver)
    if sat:
        return True, model or []
    proof = _kissat_unsat_proof(problem, kissat_cmd=kissat_cmd, timeout_s=kissat_timeout)
    return False, proof


def _make_balanced_prop_problem_list(
    wanted: int,
    varnr: int,
    maxlen: int,
    ratio: float,
    hornflag: bool,
    pysat_solver: str,
    kissat_cmd: str,
    kissat_timeout: float,
) -> List:
    true_problems: List[Tuple[List[List[int]], List[int]]] = []
    false_problems: List[Tuple[List[List[int]], List[List[int]]]] = []
    truecount = 0
    falsecount = 0

    while True:
        raw_problem = legacy.make_prop_problem(varnr, maxlen, ratio, hornflag)
        problem = legacy.normalize_problem(raw_problem)
        if not problem:
            continue

        sat, payload = _solve_with_pysat_and_kissat(
            problem,
            pysat_solver=pysat_solver,
            kissat_cmd=kissat_cmd,
            kissat_timeout=kissat_timeout,
        )

        if sat:
            truecount += 1
            if len(true_problems) > len(false_problems):
                continue
            true_problems.append((problem, payload))
        else:
            falsecount += 1
            if len(false_problems) > len(true_problems):
                continue
            false_problems.append((problem, payload))

        if len(true_problems) + len(false_problems) >= wanted:
            break

    return [truecount, falsecount, true_problems, false_problems]


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Generate propositional logic datasets (PySAT g3 + Kissat DRAT proofs).")
    ap.add_argument("--output", required=True, help="Output dataset path (JSONL).")
    ap.add_argument("--seed", type=int, default=12345, help="Random seed.")
    ap.add_argument("--vars", dest="vars", default=None, help="Variable numbers: '3-15' or '3,4,5'.")
    ap.add_argument("--clens", dest="clens", default=None, help="Clause lengths: '3-4' or '3,4'.")
    ap.add_argument("--horn", choices=["mixed", "only", "no"], default="mixed", help="Generate horn-only, non-horn, or mixed.")
    ap.add_argument("--percase", type=int, default=None, help="Problems per (varnr,maxlen,hornflag) case (even).")
    ap.add_argument("--pysat", default="g3", help="PySAT solver name (default: g3).")
    ap.add_argument("--kissat", default="kissat", help="Kissat command (default: kissat).")
    ap.add_argument("--kissat-timeout", type=float, default=30.0, help="Kissat timeout seconds.")
    args = ap.parse_args(list(argv) if argv is not None else None)

    if args.percase is None:
        percase = int(getattr(legacy, "probs_for_onecase", 20))
    else:
        percase = int(args.percase)
    if percase % 2 != 0:
        raise SystemExit("--percase must be even")

    random.seed(int(args.seed))

    varnr_range = _parse_int_list(args.vars) if args.vars else list(getattr(legacy, "varnr_range", list(range(3, 16))))
    cl_len_range = _parse_int_list(args.clens) if args.clens else list(getattr(legacy, "cl_len_range", [3, 4]))

    if args.horn == "only":
        horn_flags = [True]
    elif args.horn == "no":
        horn_flags = [False]
    else:
        horn_flags = [True, False]

    # Ratios copied from legacy main() (kept stable for continuity)
    goodratios = {
        2: [1.9, 1.3],
        3: [4.0, 2.0],
        4: [[0, 0, 0, 3.2, 4.4, 5.6, 6.4, 6.9, 6.7, 7.6], 3.1],
        5: [[0, 0, 0, 3.3, 5.5, 7.7, 9.4, 10.8, 11.6, 12.4, 12.9, 13.9, 14.1], 4.6],
    }

    out_path = args.output
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    header = [
        "id",
        "maxvarnr",
        "maxlen",
        "mustbehorn",
        "issatisfiable",
        "problem",
        "proof_of_inconsistency_or_satisfying_valuation",
        "units_derived_by_horn_clauses",
    ]

    probnr = 0
    with open(out_path, "w") as out:
        out.write(json.dumps(header) + "\n")

        for varnr in varnr_range:
            for cllen in cl_len_range:
                for hornflag in horn_flags:
                    ratios = goodratios[cllen]
                    ratios = ratios[1] if hornflag else ratios[0]
                    if isinstance(ratios, list):
                        ratio = ratios[varnr] if varnr < len(ratios) else ratios[-1]
                    else:
                        ratio = ratios

                    _, _, truelist, falselist = _make_balanced_prop_problem_list(
                        percase,
                        varnr,
                        cllen,
                        float(ratio),
                        bool(hornflag),
                        pysat_solver=str(args.pysat),
                        kissat_cmd=str(args.kissat),
                        kissat_timeout=float(args.kissat_timeout),
                    )

                    choosefrom = True
                    while True:
                        if not truelist and not falselist:
                            break

                        if choosefrom:
                            if not truelist:
                                choosefrom = False
                                continue
                            prob, model = truelist.pop(0)
                            truth = 1
                            proof_or_model = model
                        else:
                            if not falselist:
                                choosefrom = True
                                continue
                            prob, proof = falselist.pop(0)
                            truth = 0
                            proof_or_model = proof

                        probnr += 1
                        horn = 1 if hornflag else 0
                        horn_units = legacy.solve_prop_horn_problem(prob)
                        row = [probnr, varnr, cllen, horn, truth, prob, proof_or_model, horn_units]
                        out.write(json.dumps(row) + "\n")

                        choosefrom = not choosefrom

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
