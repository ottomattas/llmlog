#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


def _bootstrap_import_path() -> Path:
    """Allow running from repo root without installing the package.

    Returns the `_refactor/` root directory.
    """
    here = Path(__file__).resolve()
    refactor_root = here.parents[1]
    src = refactor_root / "src"
    sys.path.insert(0, str(src))
    return refactor_root


@dataclass(frozen=True)
class ActiveProc:
    pid: int
    command: str
    suite: Optional[str]
    run: Optional[str]


def _ps_lines() -> List[str]:
    out = subprocess.check_output(["ps", "-ax", "-o", "pid=,command="], text=True)
    return [ln.rstrip("\n") for ln in out.splitlines() if ln.strip()]


def find_active_run_procs() -> List[ActiveProc]:
    procs: List[ActiveProc] = []
    for ln in _ps_lines():
        # format: "<pid> <command...>"
        parts = ln.strip().split(maxsplit=1)
        if not parts:
            continue
        try:
            pid = int(parts[0])
        except Exception:
            continue
        cmd = parts[1] if len(parts) > 1 else ""
        if "scripts/run.py" not in cmd:
            continue
        suite = None
        run = None
        try:
            argv = shlex.split(cmd)
            # naive arg parse
            for i, tok in enumerate(argv):
                if tok == "--suite" and i + 1 < len(argv):
                    suite = argv[i + 1]
                if tok == "--run" and i + 1 < len(argv):
                    run = argv[i + 1]
        except Exception:
            pass
        procs.append(ActiveProc(pid=pid, command=cmd, suite=suite, run=run))
    return sorted(procs, key=lambda p: p.pid)


def cmd_active(_: argparse.Namespace) -> int:
    procs = find_active_run_procs()
    if not procs:
        print("No active `scripts/run.py` processes found.")
        return 0
    for p in procs:
        extra = []
        if p.suite:
            extra.append(f"suite={p.suite}")
        if p.run:
            extra.append(f"run={p.run}")
        extra_s = (" " + " ".join(extra)) if extra else ""
        print(f"{p.pid}{extra_s}\n  {p.command}")
    return 0


def _pid_exists(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def cmd_stop(args: argparse.Namespace) -> int:
    if not args.yes:
        raise SystemExit("Refusing to stop processes without --yes")
    procs = find_active_run_procs()
    if not procs:
        print("No active `scripts/run.py` processes found.")
        return 0

    pids = [p.pid for p in procs]
    print(f"Stopping {len(pids)} run process(es): {pids}")

    # Try SIGINT first (graceful, like Ctrl+C)
    for pid in pids:
        try:
            os.kill(pid, signal.SIGINT)
        except Exception:
            pass
    time.sleep(float(args.grace_seconds))

    still = [pid for pid in pids if _pid_exists(pid)]
    if still:
        print(f"Still running after SIGINT: {still}. Sending SIGTERM…")
        for pid in still:
            try:
                os.kill(pid, signal.SIGTERM)
            except Exception:
                pass
        time.sleep(1.0)

    still2 = [pid for pid in pids if _pid_exists(pid)]
    if still2:
        print(f"Still running after SIGTERM: {still2}. Sending SIGKILL…")
        for pid in still2:
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception:
                pass

    final = [pid for pid in pids if _pid_exists(pid)]
    if final:
        print(f"WARNING: Some PIDs still exist: {final}")
        return 1
    print("All run processes stopped.")
    return 0


def _rel_symlink_target(from_dir: Path, to_path: Path) -> str:
    """Return a relative symlink target string from `from_dir` to `to_path`."""
    try:
        return os.path.relpath(str(to_path), start=str(from_dir))
    except Exception:
        return str(to_path)


def cmd_index(args: argparse.Namespace) -> int:
    refactor_root = _bootstrap_import_path()
    runs_dir = (refactor_root / args.runs_dir).resolve()
    out_dir = (refactor_root / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    made = 0
    for suite_dir in sorted(runs_dir.iterdir()):
        if not suite_dir.is_dir():
            continue
        suite_name = suite_dir.name
        for run_dir in sorted(suite_dir.iterdir()):
            if not run_dir.is_dir() and not run_dir.is_symlink():
                continue
            run_id = run_dir.name
            target = run_dir.resolve()
            link_parent = out_dir / run_id
            link_parent.mkdir(parents=True, exist_ok=True)
            link_path = link_parent / suite_name

            if link_path.exists() or link_path.is_symlink():
                # keep existing if it already points correctly
                try:
                    if link_path.is_symlink() and link_path.resolve() == target:
                        continue
                except Exception:
                    pass
                # remove and recreate
                if link_path.is_dir() and not link_path.is_symlink():
                    # Avoid destructive deletes of real dirs
                    print(f"SKIP (not a symlink): {link_path}")
                    continue
                try:
                    link_path.unlink()
                except Exception:
                    pass

            rel_target = _rel_symlink_target(link_parent, target)
            try:
                os.symlink(rel_target, link_path)
                made += 1
            except FileExistsError:
                pass
            except Exception as e:
                print(f"ERROR creating symlink {link_path} -> {rel_target}: {e}")

    print(f"Wrote/updated {made} symlink(s) under {out_dir}")
    return 0


def _vars_label(maxvars_spec: str) -> str:
    s = (maxvars_spec or "").strip()
    if not s:
        return "vars"
    # 35-45
    if "-" in s and "," not in s:
        a, b = s.split("-", 1)
        a = a.strip()
        b = b.strip()
        if a.isdigit() and b.isdigit():
            return f"vars{int(a)}_{int(b)}"
    # 10,20,30...
    if "," in s:
        vals = []
        for p in s.split(","):
            p = p.strip()
            if p.isdigit():
                vals.append(int(p))
        if vals:
            return f"vars{min(vals)}_{max(vals)}"
    # single
    if s.isdigit():
        return f"vars{int(s)}"
    # fallback: sanitize
    safe = re.sub(r"[^0-9a-zA-Z_]+", "_", s)
    return f"vars{safe}"


@dataclass
class SuiteSpec:
    prefix: str
    suite_path: str


def _parse_suite_specs(specs: Sequence[str]) -> List[SuiteSpec]:
    out: List[SuiteSpec] = []
    for s in specs:
        if "=" not in s:
            raise SystemExit(f"--suite must be PREFIX=path.yaml, got: {s}")
        prefix, path = s.split("=", 1)
        prefix = prefix.strip()
        path = path.strip()
        if not prefix or not path:
            raise SystemExit(f"Invalid --suite value: {s}")
        out.append(SuiteSpec(prefix=prefix, suite_path=path))
    return out


def _parse_int_list(spec: str) -> List[int]:
    vals: List[int] = []
    for p in (spec or "").split(","):
        p = p.strip()
        if not p:
            continue
        try:
            vals.append(int(p))
        except Exception:
            raise SystemExit(f"Invalid int in list: {p}")
    return vals


def _run_cmd(cmd: List[str], *, cwd: Path) -> int:
    p = subprocess.Popen(cmd, cwd=str(cwd))
    return p.wait()


def cmd_queue(args: argparse.Namespace) -> int:
    refactor_root = _bootstrap_import_path()

    # Optional: stop any existing runs first
    if args.stop_active:
        if not args.yes:
            raise SystemExit("--stop-active requires --yes")
        stop_ns = argparse.Namespace(yes=True, grace_seconds=args.stop_grace_seconds)
        cmd_stop(stop_ns)

    suites = _parse_suite_specs(args.suite)
    lens = _parse_int_list(args.lens)
    vars_label = _vars_label(args.maxvars)

    # Import helpers (in venv) to estimate expected rows and enumerate targets.
    from llmlog.preflight import preflight_suite
    from llmlog.problems.filters import parse_int_set_spec

    only_maxvars = parse_int_set_spec(args.maxvars) if args.maxvars else None

    # Build job list
    jobs: List[Dict[str, object]] = []
    for s in suites:
        for ln in lens:
            run_id = f"{s.prefix}_len{ln}_{vars_label}_case{int(args.case_limit)}"
            pf = preflight_suite(
                suite_path=str((refactor_root / s.suite_path).resolve()),
                only_maxvars=only_maxvars,
                only_maxlen={int(ln)},
                case_limit=int(args.case_limit),
            )
            jobs.append(
                {
                    "suite_name": pf.suite_name,
                    "suite_path": s.suite_path,
                    "run_id": run_id,
                    "len": int(ln),
                    "expected_rows": int(pf.run_rows),
                    "targets": pf.targets,
                }
            )

    # Helper: ensure runs_by_run index exists for a specific (suite_name, run_id)
    def ensure_symlink_for_run(*, suite_name: str, run_id: str) -> None:
        if not args.canonical_by_run:
            return
        runs_dir = refactor_root / "runs"
        by_run = refactor_root / "runs_by_run"
        # canonical: runs_by_run/<run_id>/<suite_name>
        canon = by_run / run_id / suite_name
        canon.parent.mkdir(parents=True, exist_ok=True)
        if not canon.exists():
            canon.mkdir(parents=True, exist_ok=True)
        # legacy: runs/<suite_name>/<run_id> -> symlink to canon
        legacy_parent = runs_dir / suite_name
        legacy_parent.mkdir(parents=True, exist_ok=True)
        legacy = legacy_parent / run_id
        if legacy.exists() and not legacy.is_symlink():
            # already a real dir; leave it
            return
        if legacy.is_symlink():
            try:
                if legacy.resolve() == canon.resolve():
                    return
            except Exception:
                pass
            try:
                legacy.unlink()
            except Exception:
                return
        rel = _rel_symlink_target(legacy_parent, canon)
        try:
            os.symlink(rel, legacy)
        except Exception:
            pass

    # Read latest-per-id status for a results file
    def latest_status(path: Path) -> Tuple[int, int, int]:
        if not path.exists():
            return (0, 0, 0)
        latest: Dict[str, Dict[str, object]] = {}
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except Exception:
                continue
            rid = row.get("id")
            if rid is None:
                continue
            latest[str(rid)] = row
        errors = sum(1 for r in latest.values() if r.get("error"))
        unclear = sum(1 for r in latest.values() if (r.get("parsed_answer") == 2 and not r.get("error")))
        return (len(latest), errors, unclear)

    def is_done(job: Dict[str, object]) -> bool:
        suite_name = str(job["suite_name"])
        run_id = str(job["run_id"])
        expected = int(job["expected_rows"])
        ok = True
        for t in job["targets"]:  # type: ignore[assignment]
            provider = getattr(t, "provider")
            model = getattr(t, "model")
            thinking_mode = getattr(t, "thinking_mode")
            res_path = refactor_root / "runs" / suite_name / run_id / provider / model / thinking_mode / "results.jsonl"
            n, e, u = latest_status(res_path)
            if not (n >= expected and e == 0 and u == 0):
                ok = False
        return ok

    # Round-robin scheduler: keep at most N processes running at once.
    max_par = int(args.max_parallel)
    pending = jobs[:]
    active: List[Tuple[subprocess.Popen[bytes], Dict[str, object]]] = []

    def start_job(job: Dict[str, object]) -> subprocess.Popen[bytes]:
        suite_path = str(job["suite_path"])
        run_id = str(job["run_id"])
        ln = int(job["len"])
        suite_abs = str((refactor_root / suite_path).resolve())
        ensure_symlink_for_run(suite_name=str(job["suite_name"]), run_id=run_id)

        cmd = [
            sys.executable,
            "scripts/run.py",
            "--suite",
            suite_abs,
            "--run",
            run_id,
            "--maxvars",
            str(args.maxvars),
            "--maxlen",
            str(ln),
            "--case-limit",
            str(int(args.case_limit)),
            "--resume",
            "--lockstep",
        ]
        if args.rerun_errors:
            cmd.append("--rerun-errors")
        if args.rerun_unclear:
            cmd.append("--rerun-unclear")
        print(f"[start] run={run_id} suite={job['suite_name']} len={ln}")
        return subprocess.Popen(cmd, cwd=str(refactor_root))

    # Initial filter: drop jobs already done
    still: List[Dict[str, object]] = []
    for j in pending:
        if is_done(j):
            print(f"[done] run={j['run_id']} suite={j['suite_name']} (already complete)")
        else:
            still.append(j)
    pending = still

    passes = 0
    while pending or active:
        # Launch until max parallel
        while pending and len(active) < max_par:
            job = pending.pop(0)
            proc = start_job(job)
            active.append((proc, job))

        # Poll
        time.sleep(0.5)
        next_active: List[Tuple[subprocess.Popen[bytes], Dict[str, object]]] = []
        for proc, job in active:
            rc = proc.poll()
            if rc is None:
                next_active.append((proc, job))
                continue

            passes += 1
            if rc != 0:
                print(f"[warn] run exited nonzero rc={rc}: run={job['run_id']} suite={job['suite_name']}")
                # backoff and requeue
                time.sleep(float(args.backoff_seconds))
                pending.append(job)
                continue

            if is_done(job):
                print(f"[done] run={job['run_id']} suite={job['suite_name']}")
            else:
                print(f"[retry] run={job['run_id']} suite={job['suite_name']} (not complete yet)")
                time.sleep(float(args.backoff_seconds))
                pending.append(job)
        active = next_active

        # optional periodic index refresh (cheap and keeps browsing clear)
        if args.index_each_pass:
            idx_ns = argparse.Namespace(runs_dir=args.runs_dir, out_dir=args.index_out_dir)
            cmd_index(idx_ns)

        # safety valve
        if args.max_passes is not None and passes >= int(args.max_passes):
            raise SystemExit(f"Reached --max-passes={args.max_passes} without finishing all jobs.")

    print("All queued runs complete.")
    return 0


def cmd_migrate(args: argparse.Namespace) -> int:
    """Move runs/<suite>/<run_id> -> runs_by_run/<run_id>/<suite> and leave symlink behind.

    This keeps existing tooling compatible (it still reads `runs/<suite>/<run_id>`),
    while giving a canonical by-run view in `runs_by_run/<run_id>/<suite>`.
    """
    refactor_root = _bootstrap_import_path()
    runs_dir = (refactor_root / "runs").resolve()
    by_run = (refactor_root / "runs_by_run").resolve()
    by_run.mkdir(parents=True, exist_ok=True)

    if not args.yes:
        raise SystemExit("Refusing to migrate without --yes (this moves files).")

    # Refuse to run if active runner processes exist unless --force
    if not args.force:
        procs = find_active_run_procs()
        if procs:
            raise SystemExit(
                "Active runs detected. Stop them first (manage_runs.py stop --yes) or pass --force."
            )

    moves = 0
    for suite_dir in sorted(runs_dir.iterdir()):
        if not suite_dir.is_dir():
            continue
        suite_name = suite_dir.name
        for run_dir in sorted(suite_dir.iterdir()):
            if not run_dir.exists():
                continue
            if run_dir.is_symlink():
                continue
            if not run_dir.is_dir():
                continue
            run_id = run_dir.name
            dest = by_run / run_id / suite_name
            if dest.exists():
                print(f"SKIP (dest exists): {dest}")
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            print(f"MOVE {run_dir} -> {dest}")
            shutil.move(str(run_dir), str(dest))
            # Create symlink in legacy location
            rel = _rel_symlink_target(suite_dir, dest)
            try:
                os.symlink(rel, run_dir)
            except Exception as e:
                print(f"ERROR creating symlink {run_dir} -> {rel}: {e}")
            moves += 1

    print(f"Migrated {moves} run dir(s) into {by_run} (legacy paths now symlink to canonical).")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Utilities for managing `_refactor` runs.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sp = sub.add_parser("active", help="List active `scripts/run.py` processes.")
    sp.set_defaults(func=cmd_active)

    sp = sub.add_parser("stop", help="Stop active `scripts/run.py` processes (SIGINT -> SIGTERM -> SIGKILL).")
    sp.add_argument("--yes", action="store_true", help="Required to actually stop processes.")
    sp.add_argument("--grace-seconds", type=float, default=2.0, help="Seconds to wait after SIGINT.")
    sp.set_defaults(func=cmd_stop)

    sp = sub.add_parser("index", help="Create/update a by-run symlink index under runs_by_run_view/ (non-destructive).")
    sp.add_argument("--runs-dir", default="runs", help="Runs dir (relative to _refactor/)")
    sp.add_argument("--out-dir", default="runs_by_run_view", help="Output dir for symlink index")
    sp.set_defaults(func=cmd_index)

    sp = sub.add_parser(
        "migrate",
        help="Move runs/<suite>/<run_id> into runs_by_run/<run_id>/<suite> and leave symlink behind (destructive).",
    )
    sp.add_argument("--yes", action="store_true", help="Required (this moves files).")
    sp.add_argument("--force", action="store_true", help="Allow migration even if active runs are detected.")
    sp.set_defaults(func=cmd_migrate)

    sp = sub.add_parser(
        "queue",
        help="Run a list of suite/len jobs with a global concurrency limit until each is complete.",
    )
    sp.add_argument(
        "--suite",
        action="append",
        default=[],
        help="Suite as PREFIX=path.yaml (repeatable). Example: horn_alg_linear_cnf_compact=configs/suites/....yaml",
    )
    sp.add_argument("--lens", default="3,4,5", help="Comma-separated list of lens (e.g. 3,4,5)")
    sp.add_argument("--maxvars", default="10,20,30,40,50", help="Maxvars spec for filters (same syntax as scripts/run.py)")
    sp.add_argument("--case-limit", type=int, default=10, help="Rows per case")
    sp.add_argument("--max-parallel", type=int, default=3, help="Max concurrent runs")
    sp.add_argument("--rerun-errors", action="store_true", default=True, help="Pass --rerun-errors (default on)")
    sp.add_argument("--rerun-unclear", action="store_true", default=True, help="Pass --rerun-unclear (default on)")
    sp.add_argument("--backoff-seconds", type=float, default=2.0, help="Sleep between retry passes for a job")
    sp.add_argument("--max-passes", type=int, default=None, help="Safety cap: max completed process passes before aborting")
    sp.add_argument("--stop-active", action="store_true", help="Stop active runs before starting the queue (requires --yes)")
    sp.add_argument("--stop-grace-seconds", type=float, default=2.0, help="Grace period for --stop-active")
    sp.add_argument("--yes", action="store_true", help="Confirmation flag for destructive actions")
    sp.add_argument(
        "--canonical-by-run",
        action="store_true",
        help="Ensure legacy runs/<suite>/<run_id> is a symlink into runs_by_run/<run_id>/<suite> before launching jobs.",
    )
    sp.add_argument(
        "--index-each-pass",
        action="store_true",
        help="Refresh symlink index after each completed process pass (keeps browsing clearer).",
    )
    sp.add_argument("--index-out-dir", default="runs_by_run_view", help="Output dir for --index-each-pass")
    sp.add_argument("--runs-dir", default="runs", help="Runs dir (relative to _refactor/); used by --index-each-pass")
    sp.set_defaults(func=cmd_queue)

    args = ap.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())


