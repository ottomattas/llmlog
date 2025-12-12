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
  - empty clause (end of proof): [ 1 ] or [ -1 ] (rare)
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
import time
from typing import List, Optional, Sequence, Tuple

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


def _sha256_file(path: str) -> str:
    import hashlib

    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _format_int_list_for_filename(values: List[int]) -> str:
    if not values:
        return "none"
    vals = sorted({int(v) for v in values})
    if len(vals) == 1:
        return str(vals[0])
    if vals == list(range(vals[0], vals[-1] + 1)):
        return f"{vals[0]}-{vals[-1]}"
    if len(vals) <= 6:
        return "_".join(str(v) for v in vals)
    return f"{vals[0]}-{vals[-1]}_n{len(vals)}"


def _default_output_name(
    *,
    mode: str,
    seed: int,
    varnr_range: List[int],
    cl_len_range: List[int],
    horn: str,
    percase: int,
) -> str:
    vars_part = _format_int_list_for_filename(varnr_range)
    lens_part = _format_int_list_for_filename(cl_len_range)
    return f"problems_{mode}_seed{seed}_vars{vars_part}_len{lens_part}_horn{horn}_percase{percase}.jsonl"


def _project_root() -> str:
    # scripts/ lives directly under the project root (currently `_refactor/`).
    return os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def _resolve_output_path(
    *,
    output: Optional[str],
    dataset: Optional[str],
    name: Optional[str],
    mode: str,
    seed: int,
    varnr_range: List[int],
    cl_len_range: List[int],
    horn: str,
    percase: int,
) -> str:
    # If the user provided an explicit path, respect it verbatim.
    if output:
        return str(output)

    ds = dataset or ("legacy" if mode == "legacy" else "validation")
    out_dir = os.path.join(_project_root(), "datasets", ds)
    fname = (name or _default_output_name(
        mode=mode,
        seed=seed,
        varnr_range=varnr_range,
        cl_len_range=cl_len_range,
        horn=horn,
        percase=percase,
    )).strip()
    if not fname:
        fname = _default_output_name(
            mode=mode,
            seed=seed,
            varnr_range=varnr_range,
            cl_len_range=cl_len_range,
            horn=horn,
            percase=percase,
        )
    if not fname.endswith(".jsonl"):
        fname = fname + ".jsonl"
    return os.path.join(out_dir, fname)


def _apply_legacy_overrides(
    *,
    varnr_range: List[int],
    cl_len_range: List[int],
    horn_flags: List[bool],
    percase: int,
) -> None:
    # Override legacy globals so legacy.main() can be parameterized without editing legacy.
    legacy.varnr_range = list(varnr_range)
    legacy.cl_len_range = list(cl_len_range)
    legacy.horn_flags = list(horn_flags)
    legacy.probs_for_onecase = int(percase)


def _run_seeded_legacy_to_file(
    *,
    out_path: str,
    seed: int,
    varnr_range: List[int],
    cl_len_range: List[int],
    horn_flags: List[bool],
    percase: int,
) -> None:
    """
    Run legacy.main() with seeded RNG and parameter overrides, capturing its stdout.

    This is the 'legacy parity' mode: output bytes match the legacy generator's
    stdout for the same seed/params.
    """
    random.seed(int(seed))
    try:
        legacy.random.seed(int(seed))
    except Exception:
        pass

    _apply_legacy_overrides(
        varnr_range=varnr_range,
        cl_len_range=cl_len_range,
        horn_flags=horn_flags,
        percase=percase,
    )

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    old_stdout = sys.stdout
    try:
        with open(out_path, "w") as out:
            sys.stdout = out
            legacy.main()
    finally:
        sys.stdout = old_stdout


def _choose_clause_var_ratio(
    *,
    varnr: int,
    cllen: int,
    hornflag: bool,
    goodratios: dict,
    ratio_nonhorn_override: Optional[float],
    ratio_horn_override: Optional[float],
) -> float:
    """Pick a clause/variable ratio (m/n) for the current case."""
    if hornflag and ratio_horn_override is not None:
        return float(ratio_horn_override)
    if (not hornflag) and ratio_nonhorn_override is not None:
        return float(ratio_nonhorn_override)

    entry = goodratios[cllen]
    ratios = entry[1] if hornflag else entry[0]
    if isinstance(ratios, list):
        return float(ratios[varnr] if varnr < len(ratios) else ratios[-1])
    return float(ratios)


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


def _kissat_decide(
    clauses: Sequence[Sequence[int]],
    *,
    kissat_cmd: str = "kissat",
    timeout_s: float = 5.0,
) -> Optional[bool]:
    """Return SAT/UNSAT using Kissat, or None if timed out/unknown."""
    if not shutil.which(kissat_cmd):
        raise RuntimeError(f"kissat not found on PATH: {kissat_cmd}")

    with tempfile.TemporaryDirectory() as td:
        cnf_path = os.path.join(td, "input.cnf")
        with open(cnf_path, "w") as f:
            f.write(_clauses_to_dimacs(clauses))

        try:
            proc = subprocess.run(
                [kissat_cmd, cnf_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=float(timeout_s),
            )
        except subprocess.TimeoutExpired:
            return None

        if proc.returncode == 10:
            return True
        if proc.returncode == 20:
            return False
        return None

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
    max_attempts: Optional[int] = None,
    progress_every: int = 0,
) -> List:
    true_problems: List[Tuple[List[List[int]], List[int]]] = []
    false_problems: List[Tuple[List[List[int]], List[List[int]]]] = []
    truecount = 0
    falsecount = 0
    attempts = 0
    started = time.time()

    while True:
        attempts += 1
        if max_attempts is not None and attempts > max_attempts:
            elapsed = time.time() - started
            raise SystemExit(
                f"Failed to generate a balanced set after {attempts} attempts (elapsed {elapsed:.1f}s). "
                f"Collected SAT={len(true_problems)} UNSAT={len(false_problems)}. "
                f"Try adjusting the clause/variable ratio (e.g. --ratio-nonhorn / --ratio-horn) "
                f"or generating SAT/UNSAT separately."
            )
        if progress_every and (attempts % int(progress_every) == 0):
            elapsed = time.time() - started
            print(
                f"# progress attempts={attempts} sat_seen={truecount} unsat_seen={falsecount} "
                f"sat_kept={len(true_problems)} unsat_kept={len(false_problems)} elapsed_s={elapsed:.1f}",
                file=sys.stderr,
                flush=True,
            )

        raw_problem = legacy.make_prop_problem(varnr, maxlen, ratio, hornflag)
        problem = legacy.normalize_problem(raw_problem)
        if not problem:
            continue

        try:
            sat, payload = _solve_with_pysat_and_kissat(
                problem,
                pysat_solver=pysat_solver,
                kissat_cmd=kissat_cmd,
                kissat_timeout=kissat_timeout,
            )
        except subprocess.TimeoutExpired:
            # Likely a hard UNSAT proof attempt. Skip and sample a new instance.
            continue
        except Exception:
            # Any solver/proof error: skip and sample a new instance.
            continue

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
    ap = argparse.ArgumentParser(description="Generate propositional logic datasets.")
    ap.add_argument(
        "--output",
        default=None,
        help="Output dataset path (JSONL). If omitted, writes under datasets/<dataset>/ with a generated name.",
    )
    ap.add_argument(
        "--dataset",
        choices=["legacy", "validation", "production"],
        default=None,
        help="When --output is omitted, choose datasets/<dataset>/ (default: legacy for --mode legacy, else validation).",
    )
    ap.add_argument(
        "--name",
        default=None,
        help="When --output is omitted, output file name (default: generated from params).",
    )
    ap.add_argument(
        "--mode",
        choices=["legacy", "pysat_kissat"],
        default="pysat_kissat",
        help="Generation mode: legacy parity output, or PySAT+Kissat proofs.",
    )
    ap.add_argument("--seed", type=int, default=12345, help="Random seed.")
    ap.add_argument("--vars", dest="vars", default=None, help="Variable numbers: '3-15' or '3,4,5'.")
    ap.add_argument("--clens", dest="clens", default=None, help="Clause lengths: '3-4' or '3,4'.")
    ap.add_argument("--horn", choices=["mixed", "only", "no"], default="mixed", help="Generate horn-only, non-horn, or mixed.")
    ap.add_argument("--percase", type=int, default=None, help="Problems per (varnr,maxlen,hornflag) case (even).")
    ap.add_argument("--probe-samples", type=int, default=0, help="Probe SAT/UNSAT balance only; do not write a dataset.")
    ap.add_argument(
        "--probe-output",
        default=None,
        help="Optional JSONL path to write probed samples (includes CNF + SAT/UNSAT). Requires --probe-samples>0.",
    )
    ap.add_argument(
        "--probe-timeout",
        type=float,
        default=5.0,
        help="Per-sample timeout (seconds) used by probe solver (default: 5.0).",
    )
    ap.add_argument("--progress-every", type=int, default=0, help="Print progress every N samples while balancing.")
    ap.add_argument("--max-attempts", type=int, default=0, help="Abort balancing after N attempts (0 = no limit).")
    ap.add_argument(
        "--ratio-nonhorn",
        type=float,
        default=None,
        help="Override the clause/variable ratio (m/n) for non-Horn cases (e.g., 21.1 for 5-SAT @ n~100).",
    )
    ap.add_argument(
        "--ratio-horn",
        type=float,
        default=None,
        help="Override the clause/variable ratio (m/n) for Horn cases.",
    )
    ap.add_argument("--pysat", default="g3", help="PySAT solver name (default: g3).")
    ap.add_argument("--kissat", default="kissat", help="Kissat command (default: kissat).")
    ap.add_argument("--kissat-timeout", type=float, default=30.0, help="Kissat timeout seconds.")
    ap.add_argument("--print-sha256", action="store_true", help="Print SHA-256 of the output file.")
    ap.add_argument("--expect-sha256", default=None, help="Fail if SHA-256(output) != this value.")
    args = ap.parse_args(list(argv) if argv is not None else None)

    if args.percase is None:
        percase = int(getattr(legacy, "probs_for_onecase", 20))
    else:
        percase = int(args.percase)
    if percase % 2 != 0:
        raise SystemExit("--percase must be even")

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

    out_path = _resolve_output_path(
        output=args.output,
        dataset=args.dataset,
        name=args.name,
        mode=str(args.mode),
        seed=int(args.seed),
        varnr_range=varnr_range,
        cl_len_range=cl_len_range,
        horn=str(args.horn),
        percase=int(percase),
    )

    # ---- probe mode --------------------------------------------------------
    if int(args.probe_samples) > 0:
        sample_out = str(args.probe_output) if args.probe_output else None
        out_f = None
        if sample_out:
            os.makedirs(os.path.dirname(sample_out) or ".", exist_ok=True)
            out_f = open(sample_out, "w", buffering=1)
            out_f.write(
                json.dumps(
                    [
                        "trial_id",
                        "maxvarnr",
                        "maxlen",
                        "mustbehorn",
                        "ratio_m_over_n",
                        "issatisfiable",
                        "problem",
                    ]
                )
                + "\n"
            )

        try:
            trial_id = 0
            for varnr in varnr_range:
                for cllen in cl_len_range:
                    for hornflag in horn_flags:
                        ratio = _choose_clause_var_ratio(
                            varnr=int(varnr),
                            cllen=int(cllen),
                            hornflag=bool(hornflag),
                            goodratios=goodratios,
                            ratio_nonhorn_override=args.ratio_nonhorn,
                            ratio_horn_override=args.ratio_horn,
                        )

                        sat_cnt = 0
                        unsat_cnt = 0
                        unk_cnt = 0
                        gen_s = 0.0
                        solve_s = 0.0
                        samples_target = int(args.probe_samples)
                        started_case = time.time()
                        for i in range(samples_target):
                            trial_id += 1
                            t0 = time.time()
                            raw_problem = legacy.make_prop_problem(int(varnr), int(cllen), float(ratio), bool(hornflag))
                            problem = legacy.normalize_problem(raw_problem)
                            gen_s += time.time() - t0
                            if not problem:
                                continue
                            t1 = time.time()
                            sat = _kissat_decide(
                                problem,
                                kissat_cmd=str(args.kissat),
                                timeout_s=float(args.probe_timeout),
                            )
                            solve_s += time.time() - t1
                            if sat is None:
                                unk_cnt += 1
                            else:
                                if sat:
                                    sat_cnt += 1
                                else:
                                    unsat_cnt += 1
                                if out_f:
                                    row = [
                                        trial_id,
                                        int(varnr),
                                        int(cllen),
                                        1 if bool(hornflag) else 0,
                                        float(ratio),
                                        1 if sat else 0,
                                        problem,
                                    ]
                                    out_f.write(json.dumps(row) + "\n")

                            if int(args.progress_every) and (i + 1) % int(args.progress_every) == 0:
                                elapsed = time.time() - started_case
                                print(
                                    f"# probe_progress case_var={varnr} case_len={cllen} horn={int(bool(hornflag))} "
                                    f"i={i+1}/{samples_target} sat={sat_cnt} unsat={unsat_cnt} unk={unk_cnt} elapsed_s={elapsed:.1f}",
                                    file=sys.stderr,
                                    flush=True,
                                )

                        print(
                            f"probe var={varnr} len={cllen} horn={int(bool(hornflag))} ratio={ratio:.3f} "
                            f"sat={sat_cnt} unsat={unsat_cnt} unk={unk_cnt} "
                            f"avg_gen_s={gen_s/max(1,samples_target):.4f} "
                            f"avg_solve_s={solve_s/max(1,samples_target):.4f}",
                            flush=True,
                        )
        finally:
            if out_f:
                out_f.close()

        return 0

    # ---- legacy parity mode ------------------------------------------------
    if args.mode == "legacy":
        _run_seeded_legacy_to_file(
            out_path=out_path,
            seed=int(args.seed),
            varnr_range=varnr_range,
            cl_len_range=cl_len_range,
            horn_flags=horn_flags,
            percase=percase,
        )

        if args.print_sha256 or args.expect_sha256:
            sha = _sha256_file(out_path)
            if args.print_sha256:
                print(sha)
            if args.expect_sha256 and sha.lower() != str(args.expect_sha256).strip().lower():
                raise SystemExit(f"SHA256 mismatch: got {sha}, expected {args.expect_sha256}")
        return 0

    # ---- PySAT+Kissat mode -------------------------------------------------
    random.seed(int(args.seed))
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
    with open(out_path, "w", buffering=1) as out:
        out.write(json.dumps(header) + "\n")
        out.flush()

        for varnr in varnr_range:
            for cllen in cl_len_range:
                for hornflag in horn_flags:
                    ratio = _choose_clause_var_ratio(
                        varnr=int(varnr),
                        cllen=int(cllen),
                        hornflag=bool(hornflag),
                        goodratios=goodratios,
                        ratio_nonhorn_override=args.ratio_nonhorn,
                        ratio_horn_override=args.ratio_horn,
                    )

                    _, _, truelist, falselist = _make_balanced_prop_problem_list(
                        percase,
                        varnr,
                        cllen,
                        float(ratio),
                        bool(hornflag),
                        pysat_solver=str(args.pysat),
                        kissat_cmd=str(args.kissat),
                        kissat_timeout=float(args.kissat_timeout),
                        max_attempts=(int(args.max_attempts) if int(args.max_attempts) > 0 else None),
                        progress_every=int(args.progress_every),
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
                        out.flush()

                        choosefrom = not choosefrom

    if args.print_sha256 or args.expect_sha256:
        sha = _sha256_file(out_path)
        if args.print_sha256:
            print(sha)
        if args.expect_sha256 and sha.lower() != str(args.expect_sha256).strip().lower():
            raise SystemExit(f"SHA256 mismatch: got {sha}, expected {args.expect_sha256}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
