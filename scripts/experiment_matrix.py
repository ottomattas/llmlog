#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import yaml


def _bootstrap_import_path() -> Path:
    """Allow running from repo root without installing the package.

    Returns the project root directory.
    """
    here = Path(__file__).resolve()
    project_root = here.parents[1]
    sys.path.insert(0, str(project_root / "src"))
    return project_root


def _read_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise SystemExit(f"Expected YAML mapping in {path}, got {type(data)}")
    return data


def _iter_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            txt = line.strip()
            if not txt:
                continue
            try:
                obj = json.loads(txt)
            except Exception:
                continue
            if isinstance(obj, dict):
                yield obj


def _latest_rows_by_id(path: Path) -> Dict[str, Dict[str, Any]]:
    """Return latest JSONL row per `id` from an append-only results file."""
    latest: Dict[str, Dict[str, Any]] = {}
    for row in _iter_jsonl(path):
        rid = row.get("id")
        if rid is None:
            continue
        latest[str(rid)] = row
    return latest


def _is_pending(row: Dict[str, Any]) -> bool:
    """Pending = submit-only row that has a submission id but no parsed answer yet.

    - OpenAI submit-only rows carry `openai_response_id`.
    - Non-OpenAI submit-only rows carry a local `submission_id` (collector executes later).
    """
    if row.get("error"):
        return False
    return bool((row.get("openai_response_id") or row.get("submission_id")) and row.get("parsed_answer") is None)


def _prompt_label_from_template(template_path: str) -> str:
    """Derive a short prompt mechanism label from a template file path.

    Example: "prompts/sat_decision__cnf_nl__dpll_alg_linear.j2" -> "dpll_alg_linear"
    """
    if not template_path:
        return "unknown"
    name = Path(str(template_path)).name
    if name.endswith(".j2"):
        name = name[: -len(".j2")]
    parts = [p for p in name.split("__") if p]
    return parts[-1] if parts else (name or "unknown")


@dataclass
class Counts:
    total: int = 0
    pending: int = 0
    errors: int = 0
    unclear: int = 0
    answered: int = 0
    correct: int = 0

    def accuracy_answered(self) -> Optional[float]:
        if self.answered <= 0:
            return None
        return float(self.correct) / float(self.answered)

    def status(self, *, expected: int) -> str:
        if self.total <= 0:
            return "MISSING"
        if self.pending > 0:
            return "PENDING"
        if self.errors > 0:
            return "ERRORS"
        if self.unclear > 0:
            return "UNCLEAR"
        if expected > 0 and self.total < expected:
            return "PARTIAL"
        return "DONE"


def _counts_from_latest(latest: Dict[str, Dict[str, Any]]) -> Dict[Tuple[int, int, int], Counts]:
    """Aggregate latest rows into buckets keyed by (maxlen, horn, maxvars)."""
    buckets: Dict[Tuple[int, int, int], Counts] = {}
    for row in latest.values():
        meta = row.get("meta") or {}
        if not isinstance(meta, dict):
            continue
        try:
            maxlen = int(meta.get("maxlen"))
            horn = int(meta.get("horn"))
            maxvars = int(meta.get("maxvars"))
        except Exception:
            continue

        key = (maxlen, horn, maxvars)
        c = buckets.get(key)
        if c is None:
            c = Counts()
            buckets[key] = c

        c.total += 1

        if _is_pending(row):
            c.pending += 1
            continue

        if row.get("error"):
            c.errors += 1
            continue

        parsed = row.get("parsed_answer")
        parsed_i: Optional[int]
        try:
            parsed_i = int(parsed) if parsed is not None else None
        except Exception:
            parsed_i = None

        if parsed_i in (0, 1):
            c.answered += 1
            if row.get("correct") is True:
                c.correct += 1
        else:
            # parsed_answer==2 or missing (without pending) are treated as unclear.
            c.unclear += 1

    return buckets


def _sum_buckets(
    buckets: Dict[Tuple[int, int, int], Counts],
    *,
    maxlen: int,
    horn_values: Sequence[int],
    maxvars_set: Optional[set[int]],
) -> Counts:
    out = Counts()
    for (ln, horn, maxvars), c in buckets.items():
        if ln != int(maxlen):
            continue
        if int(horn) not in horn_values:
            continue
        if maxvars_set is not None and int(maxvars) not in maxvars_set:
            continue
        out.total += c.total
        out.pending += c.pending
        out.errors += c.errors
        out.unclear += c.unclear
        out.answered += c.answered
        out.correct += c.correct
    return out


@dataclass(frozen=True)
class TargetKey:
    provider: str
    model: str
    thinking_mode: str

    def label(self) -> str:
        return f"{self.provider}/{self.model}/{self.thinking_mode}"


@dataclass(frozen=True)
class SuiteRow:
    suite_path: Path
    suite_name: str
    subset: str
    representation: str
    prompt_label: str


def _parse_suite_items(items: Any) -> List[Path]:
    if items is None:
        return []
    if not isinstance(items, list):
        raise SystemExit("Matrix config must contain `suites: [...]`")

    out: List[Path] = []
    for it in items:
        if isinstance(it, str):
            out.append(Path(it))
            continue
        if isinstance(it, dict):
            p = it.get("path")
            if not p:
                raise SystemExit(f"Suite entry missing `path`: {it}")
            out.append(Path(str(p)))
            continue
        raise SystemExit(f"Unsupported suite entry type: {type(it)}")
    return out


def _parse_lens(v: Any) -> List[int]:
    if v is None:
        return []
    if isinstance(v, list):
        out = []
        for x in v:
            try:
                out.append(int(x))
            except Exception:
                raise SystemExit(f"Invalid lens entry (expected int): {x}")
        return out
    if isinstance(v, str):
        out = []
        for p in v.split(","):
            p = p.strip()
            if not p:
                continue
            try:
                out.append(int(p))
            except Exception:
                raise SystemExit(f"Invalid lens entry (expected int): {p}")
        return out
    raise SystemExit(f"Invalid `lens` value type: {type(v)}")


def _fmt_cell(*, counts: Counts, expected: int, run_id: Optional[str]) -> str:
    status = counts.status(expected=expected)
    if status == "MISSING":
        return "MISSING"

    acc = counts.accuracy_answered()
    parts: List[str] = [status]
    if run_id:
        parts.append(run_id)

    if expected > 0:
        parts.append(f"{counts.total}/{expected}")
    else:
        parts.append(str(counts.total))

    if acc is not None:
        parts.append(f"acc={acc:.2f}")

    extra = []
    if counts.pending:
        extra.append(f"pending={counts.pending}")
    if counts.errors:
        extra.append(f"errors={counts.errors}")
    if counts.unclear:
        extra.append(f"unclear={counts.unclear}")
    if extra and status != "DONE":
        parts.append("(" + ", ".join(extra) + ")")

    return " ".join(parts)


def main() -> int:
    project_root = _bootstrap_import_path()

    from llmlog.config.loader import resolve_suite
    from llmlog.preflight import preflight_suite
    from llmlog.problems.filters import parse_int_set_spec

    ap = argparse.ArgumentParser(
        description="Generate a Markdown matrix of what has been run vs what is missing (based on runs/**/results.jsonl)."
    )
    ap.add_argument("--matrix", required=True, help="Matrix YAML config path (relative to repo root or absolute)")
    ap.add_argument("--output", required=True, help="Output Markdown path")
    ap.add_argument(
        "--runs-dir",
        default=None,
        help="Override runs dir (default: from matrix config, else runs)",
    )
    args = ap.parse_args()

    matrix_path = Path(args.matrix)
    if not matrix_path.is_absolute():
        matrix_path = (project_root / matrix_path).resolve()
    matrix = _read_yaml(matrix_path)

    name = str(matrix.get("name") or matrix_path.stem)
    runs_dir = Path(args.runs_dir or matrix.get("runs_dir") or (project_root / "runs")).resolve()
    maxvars_spec = str(matrix.get("maxvars") or "")
    lens = _parse_lens(matrix.get("lens"))
    case_limit = matrix.get("case_limit")
    try:
        case_limit_i = int(case_limit) if case_limit is not None else None
    except Exception:
        raise SystemExit(f"Invalid case_limit: {case_limit}")

    suite_paths = _parse_suite_items(matrix.get("suites"))
    if not suite_paths:
        raise SystemExit("No suites provided in matrix config.")

    maxvars_set = parse_int_set_spec(maxvars_spec) if maxvars_spec else None

    # Load suite metadata (for row labels) + infer targets (from preflight).
    suite_rows: List[SuiteRow] = []
    all_targets: Dict[TargetKey, None] = {}
    suite_targets: Dict[str, set[TargetKey]] = {}
    expected_rows: Dict[Tuple[str, int], int] = {}

    for p in suite_paths:
        suite_path = p
        if not suite_path.is_absolute():
            suite_path = (project_root / suite_path).resolve()
        cfg = resolve_suite(str(suite_path))

        if cfg.prompting.render_policy != "fixed":
            # We can support match_formula later, but for now keep matrix semantics clear.
            raise SystemExit(
                f"Suite {cfg.name} uses render_policy={cfg.prompting.render_policy}; "
                "experiment_matrix currently supports only fixed prompting suites."
            )

        prompt_label = _prompt_label_from_template(str(cfg.prompting.template))
        suite_rows.append(
            SuiteRow(
                suite_path=suite_path,
                suite_name=str(cfg.name),
                subset=str(cfg.subset.value),
                representation=str(cfg.prompting.representation.value),
                prompt_label=prompt_label,
            )
        )

        # Preflight once per len to get expected rows, and collect targets.
        suite_target_keys: set[TargetKey] = set()
        for ln in lens:
            pf = preflight_suite(
                suite_path=str(suite_path),
                only_maxvars=maxvars_set,
                only_maxlen={int(ln)},
                case_limit=case_limit_i,
            )
            expected_rows[(cfg.name, int(ln))] = int(pf.run_rows)
            for t in pf.targets:
                tk = TargetKey(provider=t.provider, model=t.model, thinking_mode=t.thinking_mode)
                all_targets[tk] = None
                suite_target_keys.add(tk)
        suite_targets[cfg.name] = suite_target_keys

    targets = sorted(all_targets.keys(), key=lambda t: (t.provider, t.model, t.thinking_mode))

    def horn_values_for_subset(subset: str) -> List[int]:
        if subset == "hornonly":
            return [1]
        if subset == "nonhornonly":
            return [0]
        return [0, 1]

    # Pre-scan candidate run dirs per suite to avoid repeated filesystem walks.
    suite_run_dirs: Dict[str, List[Path]] = {}
    for s in suite_rows:
        suite_dir = runs_dir / s.suite_name
        if not suite_dir.exists():
            suite_run_dirs[s.suite_name] = []
            continue
        run_dirs = []
        for child in sorted(suite_dir.iterdir()):
            if child.is_dir() or child.is_symlink():
                run_dirs.append(child)
        suite_run_dirs[s.suite_name] = run_dirs

    # Cache: results.jsonl -> buckets
    buckets_cache: Dict[str, Dict[Tuple[int, int, int], Counts]] = {}

    def buckets_for_results(path: Path) -> Dict[Tuple[int, int, int], Counts]:
        k = str(path.resolve())
        cached = buckets_cache.get(k)
        if cached is not None:
            return cached
        latest = _latest_rows_by_id(path)
        b = _counts_from_latest(latest)
        buckets_cache[k] = b
        return b

    # Build Markdown output
    out_lines: List[str] = []
    out_lines.append(f"## Experiment matrix: {name}")
    out_lines.append("")
    out_lines.append(f"- **Matrix config**: `{matrix_path}`")
    out_lines.append(f"- **Runs dir**: `{runs_dir}`")
    out_lines.append(f"- **maxvars**: `{maxvars_spec or '(none)'}`")
    out_lines.append(f"- **lens**: `{','.join(str(x) for x in lens)}`")
    out_lines.append(f"- **case_limit**: `{case_limit_i if case_limit_i is not None else '(none)'}`")
    out_lines.append("")
    out_lines.append(
        "Notes:"
        "\n- Status is computed from **latest-per-id** rows in `results.jsonl` (append-only logs)."
        "\n- `run.manifest.json` can be overwritten by later `--ids` reruns; this tool avoids relying on it for selection."
    )
    out_lines.append("")

    for t in targets:
        out_lines.append(f"### Target: {t.label()}")
        out_lines.append("")

        header = ["subset", "repr", "prompt", "suite"] + [f"len={ln}" for ln in lens]
        out_lines.append("| " + " | ".join(header) + " |")
        out_lines.append("| " + " | ".join(["---"] * len(header)) + " |")

        for s in sorted(suite_rows, key=lambda r: (r.subset, r.representation, r.prompt_label, r.suite_name)):
            # Only show suite rows that actually include this target.
            if t not in suite_targets.get(s.suite_name, set()):
                continue
            horn_vals = horn_values_for_subset(s.subset)

            cells: List[str] = []
            for ln in lens:
                expected = expected_rows.get((s.suite_name, int(ln)), 0)
                best_run: Optional[str] = None
                best_counts = Counts()
                best_score: Optional[Tuple[int, int, int, int]] = None

                for run_dir in suite_run_dirs.get(s.suite_name, []):
                    results_path = run_dir / t.provider / t.model / t.thinking_mode / "results.jsonl"
                    if not results_path.exists():
                        # Back-compat: older runs used "nothink" for disabled thinking.
                        if t.thinking_mode == "think_none":
                            alt = run_dir / t.provider / t.model / "nothink" / "results.jsonl"
                            if alt.exists():
                                results_path = alt
                            else:
                                continue
                        else:
                            continue
                    buckets = buckets_for_results(results_path)
                    c = _sum_buckets(buckets, maxlen=int(ln), horn_values=horn_vals, maxvars_set=maxvars_set)
                    # Score: prefer more coverage; fewer pending/errors/unclear.
                    score = (c.total, -c.pending, -c.errors, -c.unclear)
                    if best_score is None or score > best_score:
                        best_score = score
                        best_counts = c
                        best_run = run_dir.name

                cells.append(_fmt_cell(counts=best_counts, expected=int(expected), run_id=best_run))

            row = [s.subset, s.representation, s.prompt_label, f"`{s.suite_name}`"] + cells
            out_lines.append("| " + " | ".join(row) + " |")

        out_lines.append("")

    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = (project_root / out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    print(f"Wrote matrix: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


