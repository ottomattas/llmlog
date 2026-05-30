#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Set, Tuple


REP_LABEL: Mapping[str, str] = {
    "cnf_compact": "Compact CNF",
    "cnf_nl": "Natural Language CNF",
    "horn_if_then": "If-then CNF",
}

PROMPT_LABEL: Mapping[str, str] = {
    "examples_only": "examples-only",
    "horn_alg_from": "Horn alg (from)",
    "horn_alg_linear": "Horn alg (linear)",
    "dpll_alg_from": "DPLL (from)",
    "dpll_alg_linear": "DPLL (linear)",
}


def _utc_now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _iter_jsonl(path: Path) -> Iterator[Dict[str, Any]]:
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


def _prompt_label_from_template(template_path: Optional[str]) -> str:
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


def _safe_int(x: Any) -> Optional[int]:
    try:
        if x is None:
            return None
        return int(x)
    except Exception:
        return None


def _parse_csv_ints(raw: Optional[Sequence[str]]) -> Optional[Set[int]]:
    if not raw:
        return None
    out: Set[int] = set()
    for item in raw:
        if item is None:
            continue
        for part in str(item).split(","):
            p = part.strip()
            if not p:
                continue
            try:
                out.add(int(p))
            except Exception:
                continue
    return out or None


def _parse_csv_strs(raw: Optional[Sequence[str]]) -> Optional[Set[str]]:
    if not raw:
        return None
    out: Set[str] = set()
    for item in raw:
        if item is None:
            continue
        for part in str(item).split(","):
            p = part.strip()
            if not p:
                continue
            out.add(p)
    return out or None


def _map_parsed_answer(parsed_answer: Any, answer_format: Optional[str]) -> Optional[str]:
    if parsed_answer is None:
        return None
    try:
        v = int(parsed_answer)
    except Exception:
        return str(parsed_answer)
    af = str(answer_format or "")
    if af == "contradiction_satisfiable":
        return {0: "contradiction", 1: "satisfiable", 2: "unknown"}.get(v, str(v))
    if af == "yes_no":
        return {0: "no", 1: "yes", 2: "unknown"}.get(v, str(v))
    return str(v)


@dataclass(frozen=True)
class TargetInfo:
    suite: str
    run: str
    provider_dir: str
    model_dir: str
    thinking_mode_dir: str
    provenance_path: Path
    provenance_rel_repo: str

    @property
    def target_key(self) -> str:
        # Keep this stable and compact in Markdown.
        return f"{self.provider_dir}/{self.model_dir}/{self.thinking_mode_dir}"

    @property
    def run_key(self) -> str:
        # Unique id for a target run folder.
        return f"{self.suite}/{self.run}/{self.target_key}"


SliceKey = Tuple[int, int, int, str, str]  # (maxvars, maxlen, horn, representation, prompt_label)


def _slice_title(sk: SliceKey) -> str:
    maxvars, maxlen, horn, representation, prompt_label = sk
    subset = "Horn-only" if horn == 1 else "Non-Horn-only"
    rep = REP_LABEL.get(representation, representation)
    prompt = PROMPT_LABEL.get(prompt_label, prompt_label.replace("_", "-"))
    return f"{subset} · {rep} · {prompt} · k={maxlen} · n={maxvars}"


def _is_pending_row(row: Dict[str, Any]) -> bool:
    if row.get("error"):
        return False
    if row.get("parsed_answer") is not None:
        return False
    return bool(row.get("openai_response_id") or row.get("submission_id"))


def _matches_regex(text: str, rex: Optional[re.Pattern[str]]) -> bool:
    if rex is None:
        return True
    return bool(rex.search(text))


def _anchor_safe(s: str) -> str:
    """Make a stable, HTML-id-safe anchor slug."""
    t = str(s or "").strip().lower()
    # Keep alnum, underscore, hyphen. Convert everything else to hyphen.
    t = re.sub(r"[^a-z0-9_-]+", "-", t)
    t = re.sub(r"-{2,}", "-", t).strip("-")
    return t or "x"


def _fenced_text_block_lines(text: str, *, lang: str = "text") -> List[str]:
    """Return markdown fence lines that won't break if the text contains backticks."""
    s = str(text or "").rstrip("\n")
    max_run = 0
    for m in re.finditer(r"`+", s):
        max_run = max(max_run, len(m.group(0)))
    fence_len = max(3, max_run + 1)
    fence = "`" * fence_len
    return [f"{fence}{lang}", s, fence]


def _sort_key_rep(rep: str) -> Tuple[int, str]:
    order = {"cnf_compact": 0, "cnf_nl": 1, "horn_if_then": 2}
    r = str(rep or "")
    return (order.get(r, 999), r)


def _sort_key_prompt(prompt_label: str) -> Tuple[int, str]:
    order = {
        "examples_only": 0,
        "horn_alg_from": 1,
        "horn_alg_linear": 2,
        "dpll_alg_from": 3,
        "dpll_alg_linear": 4,
    }
    p = str(prompt_label or "")
    return (order.get(p, 999), p)


def _select_provenance_files(runs_dir: Path) -> List[Path]:
    """Prefer v2 when present; otherwise fall back to v1."""
    v2 = sorted(runs_dir.glob("**/results.provenance.v2.jsonl"))
    v2_parents = {p.parent.resolve() for p in v2}
    v1: List[Path] = []
    for p in sorted(runs_dir.glob("**/results.provenance.jsonl")):
        try:
            parent = p.parent.resolve()
        except Exception:
            parent = p.parent
        if parent in v2_parents:
            continue
        v1.append(p)
    return v2 + v1


def _infer_target_info(*, runs_dir: Path, repo_root: Path, provenance_path: Path) -> Optional[TargetInfo]:
    try:
        rel = provenance_path.resolve().relative_to(runs_dir.resolve())
    except Exception:
        try:
            rel = provenance_path.relative_to(runs_dir)
        except Exception:
            return None

    # rel: <suite>/<run>/<provider>/<model>/<thinking>/results.provenance(.v2).jsonl
    if len(rel.parts) < 6:
        return None
    suite, run, provider_dir, model_dir, thinking_mode_dir = rel.parts[:5]
    try:
        rel_repo = provenance_path.resolve().relative_to(repo_root.resolve())
        rel_repo_s = str(rel_repo).replace("\\", "/")
    except Exception:
        rel_repo_s = str(provenance_path)
    return TargetInfo(
        suite=str(suite),
        run=str(run),
        provider_dir=str(provider_dir),
        model_dir=str(model_dir),
        thinking_mode_dir=str(thinking_mode_dir),
        provenance_path=provenance_path,
        provenance_rel_repo=rel_repo_s,
    )


def _scan_target_rows(
    *,
    provenance_path: Path,
    maxvars_allow: Optional[Set[int]],
    maxlen_allow: Optional[Set[int]],
    horn_allow: Optional[Set[int]],
    representation_allow: Optional[Set[str]],
    prompt_label_allow: Optional[Set[str]],
) -> Dict[str, Dict[str, Any]]:
    """Return latest row per id (string id) for rows matching slice filters."""
    latest: Dict[str, Dict[str, Any]] = {}
    for row in _iter_jsonl(provenance_path):
        rid = row.get("id")
        if rid is None:
            continue
        rid_s = str(rid)

        meta = row.get("meta") or {}
        if not isinstance(meta, dict):
            continue
        mv = _safe_int(meta.get("maxvars"))
        ml = _safe_int(meta.get("maxlen"))
        h = _safe_int(meta.get("horn"))
        if mv is None or ml is None or h is None:
            continue

        if maxvars_allow is not None and mv not in maxvars_allow:
            continue
        if maxlen_allow is not None and ml not in maxlen_allow:
            continue
        if horn_allow is not None and h not in horn_allow:
            continue

        rep = str(row.get("representation") or "")
        if not rep:
            continue
        if representation_allow is not None and rep not in representation_allow:
            continue

        prompt_label = _prompt_label_from_template(row.get("prompt_template"))
        if prompt_label_allow is not None and prompt_label not in prompt_label_allow:
            continue

        prev = latest.get(rid_s)
        if prev is None:
            latest[rid_s] = row
            continue

        # Keep "latest row" semantics, but avoid losing important fields when later events
        # (e.g. collect error snapshots) omit them.
        merged: Dict[str, Any] = dict(prev)
        merged.update(row)

        def _keep_nonempty_str(key: str) -> None:
            new_v = merged.get(key)
            if isinstance(new_v, str) and new_v.strip():
                return
            old_v = prev.get(key)
            if isinstance(old_v, str) and old_v.strip():
                merged[key] = old_v

        def _keep_truthy(key: str) -> None:
            if merged.get(key):
                return
            old_v = prev.get(key)
            if old_v:
                merged[key] = old_v

        _keep_nonempty_str("prompt")
        _keep_nonempty_str("completion_text")
        _keep_nonempty_str("thinking_text")
        _keep_truthy("prompt_template")
        _keep_truthy("representation")
        _keep_truthy("answer_format")
        # meta should stay as a dict when possible
        if not isinstance(merged.get("meta"), dict) and isinstance(prev.get("meta"), dict):
            merged["meta"] = prev.get("meta")

        latest[rid_s] = merged
    return latest


def export_validation_slices_markdown(
    *,
    runs_dir: str,
    out_md: str,
    maxvars: Optional[Sequence[str]] = None,
    maxlen: Optional[Sequence[str]] = None,
    horn: Optional[Sequence[str]] = None,
    representation: Optional[Sequence[str]] = None,
    prompt_label: Optional[Sequence[str]] = None,
    include_suite_regex: Optional[str] = None,
    include_run_regex: Optional[str] = None,
    include_target_regex: Optional[str] = None,
    ids_mode: str = "union",
    max_ids_per_slice: Optional[int] = None,
    include_thinking: bool = False,
) -> None:
    runs_path = Path(runs_dir).resolve()
    project_root = Path(__file__).resolve().parents[1]
    repo_root = project_root
    out_path = Path(out_md).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    maxvars_allow = _parse_csv_ints(maxvars)
    maxlen_allow = _parse_csv_ints(maxlen)
    horn_allow = _parse_csv_ints(horn)
    rep_allow = _parse_csv_strs(representation)
    prompt_allow = _parse_csv_strs(prompt_label)

    rex_suite = re.compile(include_suite_regex, re.IGNORECASE) if include_suite_regex else None
    rex_run = re.compile(include_run_regex, re.IGNORECASE) if include_run_regex else None
    rex_target = re.compile(include_target_regex, re.IGNORECASE) if include_target_regex else None

    provenance_files = _select_provenance_files(runs_path)
    targets: Dict[str, TargetInfo] = {}
    # slice -> target_run_key -> {id -> row}
    slices: Dict[SliceKey, Dict[str, Dict[str, Any]]] = defaultdict(lambda: defaultdict(dict))

    for prov_path in provenance_files:
        ti = _infer_target_info(runs_dir=runs_path, repo_root=repo_root, provenance_path=prov_path)
        if ti is None:
            continue
        if not _matches_regex(ti.suite, rex_suite):
            continue
        if not _matches_regex(ti.run, rex_run):
            continue
        if not _matches_regex(ti.target_key, rex_target):
            continue

        rows_by_id = _scan_target_rows(
            provenance_path=prov_path,
            maxvars_allow=maxvars_allow,
            maxlen_allow=maxlen_allow,
            horn_allow=horn_allow,
            representation_allow=rep_allow,
            prompt_label_allow=prompt_allow,
        )
        if not rows_by_id:
            continue

        targets[ti.run_key] = ti
        for rid_s, row in rows_by_id.items():
            meta = row.get("meta") or {}
            if not isinstance(meta, dict):
                continue
            mv = _safe_int(meta.get("maxvars"))
            ml = _safe_int(meta.get("maxlen"))
            h = _safe_int(meta.get("horn"))
            if mv is None or ml is None or h is None:
                continue
            rep = str(row.get("representation") or "")
            if not rep:
                continue
            pl = _prompt_label_from_template(row.get("prompt_template"))
            sk: SliceKey = (int(mv), int(ml), int(h), rep, pl)
            slices[sk][ti.run_key][rid_s] = row

    # Sort targets for stable output.
    target_order = sorted(
        targets.keys(),
        key=lambda rk: (
            targets[rk].provider_dir,
            targets[rk].model_dir,
            targets[rk].thinking_mode_dir,
            targets[rk].suite,
            targets[rk].run,
        ),
    )
    slice_order = sorted(slices.keys(), key=lambda sk: (sk[0], sk[1], sk[2], sk[3], sk[4]))

    def _select_ids(per_target: Dict[str, Dict[str, Any]]) -> List[str]:
        if not per_target:
            return []
        id_sets = [set(rows.keys()) for rows in per_target.values()]
        if ids_mode == "intersection":
            ids: Set[str] = set.intersection(*id_sets) if id_sets else set()
        elif ids_mode == "first":
            first_key = sorted(per_target.keys())[0]
            ids = set(per_target.get(first_key, {}).keys())
        else:
            # union (default)
            ids = set.union(*id_sets) if id_sets else set()
        out = sorted(ids, key=lambda x: int(x) if x.isdigit() else x)
        if max_ids_per_slice is not None:
            out = out[: int(max_ids_per_slice)]
        return out

    def _slice_anchor(sk: SliceKey) -> str:
        mv, ml, h, rep, pl = sk
        return f"slice-n{mv}-{_anchor_safe(rep)}-{_anchor_safe(pl)}-h{int(h)}-k{int(ml)}"

    def _slice_summary(sk: SliceKey, *, ids_n: int, targets_n: int) -> str:
        _, ml, h, rep, pl = sk
        rep_p = REP_LABEL.get(rep, rep)
        pl_p = PROMPT_LABEL.get(pl, pl.replace("_", "-"))
        subset = "Horn-only" if int(h) == 1 else "Non-Horn-only"
        return f"{rep_p} · {pl_p} · {subset} · k={int(ml)} · ids={ids_n} · target-runs={targets_n}"

    def _id_status_summary(*, target_runs: Sequence[str], per_target: Dict[str, Dict[str, Any]], rid: str) -> str:
        total = int(len(target_runs))
        present = 0
        pending = 0
        errors = 0
        correct_true = 0
        correct_false = 0
        unclear = 0
        for rk in target_runs:
            row = (per_target.get(rk) or {}).get(rid)
            if not isinstance(row, dict):
                continue
            present += 1
            if row.get("error"):
                errors += 1
            elif _is_pending_row(row):
                pending += 1
            if row.get("correct") is True:
                correct_true += 1
            elif row.get("correct") is False:
                correct_false += 1
            try:
                if int(row.get("parsed_answer")) == 2 and not row.get("error") and not _is_pending_row(row):
                    unclear += 1
            except Exception:
                pass

        missing = total - present
        parts: List[str] = [f"present={present}/{total}", f"correct={correct_true}", f"wrong={correct_false}"]
        if unclear:
            parts.append(f"unclear={unclear}")
        if pending:
            parts.append(f"pending={pending}")
        if errors:
            parts.append(f"errors={errors}")
        if missing:
            parts.append(f"missing={missing}")
        return " · ".join(parts)

    # Precompute slice payloads so we can build a top index.
    slice_payloads: List[Dict[str, Any]] = []
    for sk in slice_order:
        per_target = slices.get(sk) or {}
        ids = _select_ids(per_target)
        if not ids:
            continue
        target_runs = [rk for rk in target_order if rk in per_target]
        if not target_runs:
            continue
        mv, ml, h, rep, pl = sk
        slice_payloads.append(
            {
                "sk": sk,
                "maxvars": int(mv),
                "maxlen": int(ml),
                "horn": int(h),
                "representation": str(rep),
                "prompt_label": str(pl),
                "ids": ids,
                "target_runs": target_runs,
                "anchor": _slice_anchor(sk),
            }
        )

    # Stable slice order for output: representation -> prompt -> subset -> k.
    slice_payloads.sort(
        key=lambda p: (
            _sort_key_rep(p["representation"]),
            _sort_key_prompt(p["prompt_label"]),
            -int(p["horn"]),
            int(p["maxlen"]),
            int(p["maxvars"]),
        )
    )

    by_rep: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for p in slice_payloads:
        by_rep[str(p.get("representation") or "unknown")].append(p)
    rep_order = sorted(by_rep.keys(), key=_sort_key_rep)

    with out_path.open("w", encoding="utf-8") as f:
        def w(line: str = "") -> None:
            f.write(line + "\n")

        w("# Validation slices")
        w("")
        w("This file is auto-exported from `runs/**/results.provenance*.jsonl` for quick manual validation.")
        w("")
        w("- **navigation tips**: use the **Index** below, expand `<details>` blocks, and use find (Cmd-F) for `id=...`.")
        w("")
        w(f"- **generated_at**: `{_utc_now_iso()}`")
        w(f"- **runs_dir**: `{str(runs_path)}`")
        w(f"- **targets_included**: `{len(target_order)}`")
        w(f"- **slices_included**: `{len(slice_payloads)}`")
        if maxvars_allow is not None:
            w(f"- **filter.maxvars**: `{sorted(maxvars_allow)}`")
        if maxlen_allow is not None:
            w(f"- **filter.maxlen**: `{sorted(maxlen_allow)}`")
        if horn_allow is not None:
            w(f"- **filter.horn**: `{sorted(horn_allow)}`")
        if rep_allow is not None:
            w(f"- **filter.representation**: `{sorted(rep_allow)}`")
        if prompt_allow is not None:
            w(f"- **filter.prompt_label**: `{sorted(prompt_allow)}`")
        if include_suite_regex:
            w(f"- **filter.suite_regex**: `{include_suite_regex}`")
        if include_run_regex:
            w(f"- **filter.run_regex**: `{include_run_regex}`")
        if include_target_regex:
            w(f"- **filter.target_regex**: `{include_target_regex}`")
        w("")

        w('<a id="index"></a>')
        w("## Index (by representation → prompt → subset → k)")
        w("")
        w("Each row links to a slice section. Inside a slice, each `id=...` and each target response is also collapsible.")
        w("")

        for rep in rep_order:
            rep_p = REP_LABEL.get(rep, rep)
            rep_slices = by_rep.get(rep) or []
            rep_slices.sort(
                key=lambda p: (
                    _sort_key_prompt(p["prompt_label"]),
                    -int(p["horn"]),
                    int(p["maxlen"]),
                    int(p["maxvars"]),
                )
            )
            w("<details open>")
            w(f"<summary><b>{rep_p}</b> ({len(rep_slices)} slices)</summary>")
            w("")
            w("| prompt | subset | k | ids | target-runs | link |")
            w("|---|---|---:|---:|---:|---|")
            for p in rep_slices:
                pl_p = PROMPT_LABEL.get(p["prompt_label"], str(p["prompt_label"]).replace("_", "-"))
                subset = "Horn" if int(p["horn"]) == 1 else "Non-Horn"
                w(
                    f"| {pl_p} | {subset} | {int(p['maxlen'])} | {len(p['ids'])} | {len(p['target_runs'])} | [go](#{p['anchor']}) |"
                )
            w("")
            w("</details>")
            w("")

        w("---")
        w("")

        for p in slice_payloads:
            sk = p["sk"]
            per_target = slices.get(sk) or {}
            ids = list(p["ids"])
            target_runs = list(p["target_runs"])
            anchor = str(p["anchor"])

            w(f'<a id="{anchor}"></a>')
            w("<details>")
            w(f"<summary><b>{_slice_summary(sk, ids_n=len(ids), targets_n=len(target_runs))}</b></summary>")
            w("")
            w(
                f"- **slice**: maxvars={p['maxvars']} · maxlen={p['maxlen']} · horn={p['horn']} · representation=`{p['representation']}` · prompt_label=`{p['prompt_label']}`"
            )
            w(f"- **ids_mode**: `{ids_mode}`")
            w("")

            w("<details>")
            w("<summary><b>Targets (provenance sources)</b></summary>")
            w("")
            for rk in target_runs:
                ti = targets[rk]
                w(f"- `{ti.target_key}` · run=`{ti.run}` · suite=`{ti.suite}` · provenance=`{ti.provenance_rel_repo}`")
            w("")
            w("</details>")
            w("")

            w("<details>")
            w("<summary><b>IDs in this slice</b></summary>")
            w("")
            id_links = []
            for rid in ids:
                id_anchor = f"{anchor}--id-{_anchor_safe(rid)}"
                id_links.append(f"[`{rid}`](#{id_anchor})")
            w(" ".join(id_links))
            w("")
            w("</details>")
            w("")

            for rid in ids:
                ref_row: Optional[Dict[str, Any]] = None
                for rk in target_runs:
                    r = (per_target.get(rk) or {}).get(rid)
                    if isinstance(r, dict):
                        ref_row = r
                        break
                if ref_row is None:
                    continue

                meta = ref_row.get("meta") if isinstance(ref_row.get("meta"), dict) else {}
                meta_s = json.dumps(meta, sort_keys=True)
                satflag = _safe_int(meta.get("satflag")) if isinstance(meta, dict) else None
                sat_s = "?" if satflag is None else str(int(satflag))

                id_anchor = f"{anchor}--id-{_anchor_safe(rid)}"
                status = _id_status_summary(target_runs=target_runs, per_target=per_target, rid=rid)

                w(f'<a id="{id_anchor}"></a>')
                w("<details>")
                w(f"<summary><code>id={rid}</code> · satflag={sat_s} · {status}</summary>")
                w("")
                w(f"- **meta**: `{meta_s}`")
                w("")

                prompt_text = ""
                for rk in target_runs:
                    row = (per_target.get(rk) or {}).get(rid)
                    if not isinstance(row, dict):
                        continue
                    ptxt = row.get("prompt")
                    if isinstance(ptxt, str) and ptxt.strip():
                        prompt_text = ptxt
                        break
                if not prompt_text:
                    prompt_text = ref_row.get("prompt") if isinstance(ref_row.get("prompt"), str) else ""

                w("<details>")
                w("<summary><b>Prompt (exact)</b></summary>")
                w("")
                for ln in _fenced_text_block_lines(prompt_text, lang="text"):
                    w(ln)
                w("")
                w("</details>")
                w("")

                w("| target | run | parsed | mapped | correct | status |")
                w("|---|---|---:|---|---|---|")
                for rk in target_runs:
                    ti = targets.get(rk)
                    if ti is None:
                        continue
                    row = (per_target.get(rk) or {}).get(rid)
                    if not isinstance(row, dict):
                        w(f"| `{ti.target_key}` | `{ti.run}` |  |  |  | missing |")
                        continue
                    answer_format = row.get("answer_format")
                    mapped = _map_parsed_answer(row.get("parsed_answer"), answer_format)
                    pa = row.get("parsed_answer")
                    corr = row.get("correct")
                    if row.get("error"):
                        st = "error"
                    elif _is_pending_row(row):
                        st = "pending"
                    else:
                        st = "ok"
                    mapped_s = mapped if mapped is not None else ""
                    corr_s = "" if corr is None else str(corr)
                    pa_s = "" if pa is None else str(pa)
                    w(f"| `{ti.target_key}` | `{ti.run}` | {pa_s} | {mapped_s} | {corr_s} | {st} |")
                w("")

                w("<details>")
                w("<summary><b>Responses (raw)</b></summary>")
                w("")
                for rk in target_runs:
                    ti = targets.get(rk)
                    if ti is None:
                        continue
                    row = (per_target.get(rk) or {}).get(rid)
                    if not isinstance(row, dict):
                        continue

                    answer_format = row.get("answer_format")
                    mapped = _map_parsed_answer(row.get("parsed_answer"), answer_format)
                    pa = row.get("parsed_answer")
                    corr = row.get("correct")
                    err = row.get("error")
                    pending_flag = _is_pending_row(row)
                    st = "error" if err else ("pending" if pending_flag else "ok")
                    mapped_s = mapped if mapped is not None else ""
                    pa_s = "" if pa is None else str(pa)
                    corr_s = "" if corr is None else str(corr)

                    w("<details>")
                    w(
                        f"<summary><code>{ti.target_key}</code> · run={ti.run} · parsed={pa_s} · mapped={mapped_s} · correct={corr_s} · {st}</summary>"
                    )
                    w("")
                    if row.get("prompt_template"):
                        w(f"- **prompt_template**: `{row.get('prompt_template')}`")
                    if row.get("model_resolved"):
                        w(f"- **model_resolved**: `{row.get('model_resolved')}`")
                    if err:
                        w(f"- **error**: `{str(err)}`")
                    elif pending_flag:
                        w("- **pending**: `True`")
                    w("")

                    completion = row.get("completion_text")
                    thinking = row.get("thinking_text")
                    if isinstance(completion, str) and completion.strip():
                        for ln in _fenced_text_block_lines(completion, lang="text"):
                            w(ln)
                    else:
                        w("_No completion text captured for this id._")
                    w("")

                    if include_thinking and isinstance(thinking, str) and thinking.strip():
                        w("<details>")
                        w("<summary><b>Thinking (raw text)</b></summary>")
                        w("")
                        for ln in _fenced_text_block_lines(thinking, lang="text"):
                            w(ln)
                        w("")
                        w("</details>")
                        w("")

                    w("</details>")
                    w("")

                w("</details>")
                w("")

                w("</details>")
                w("")

            w(f"[↑ Index](#index)")
            w("")
            w("</details>")
            w("")


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Export validation slices to a single Markdown file (grouped by slice, with per-id results across targets)."
    )
    ap.add_argument("--runs-dir", default="runs", help="Runs directory (default: runs)")
    ap.add_argument("--out", required=True, help="Output markdown path")

    ap.add_argument("--maxvars", action="append", default=None, help="Filter by maxvars; repeatable or comma-separated")
    ap.add_argument("--maxlen", action="append", default=None, help="Filter by maxlen; repeatable or comma-separated")
    ap.add_argument("--horn", action="append", default=None, help="Filter by horn (0/1); repeatable or comma-separated")
    ap.add_argument("--representation", action="append", default=None, help="Filter by representation; repeatable or comma-separated")
    ap.add_argument("--prompt-label", action="append", default=None, help="Filter by prompt label; repeatable or comma-separated")

    ap.add_argument("--suite-regex", default=None, help="Regex filter over suite name")
    ap.add_argument("--run-regex", default=None, help="Regex filter over run name")
    ap.add_argument("--target-regex", default=None, help="Regex filter over target key provider/model/thinking")

    ap.add_argument(
        "--ids-mode",
        choices=["union", "intersection", "first"],
        default="union",
        help="How to choose ids per slice across targets (default: union)",
    )
    ap.add_argument("--max-ids-per-slice", type=int, default=None, help="Cap ids exported per slice (for debugging)")
    ap.add_argument("--include-thinking", action="store_true", help="Include thinking_text blocks when present")

    args = ap.parse_args()

    export_validation_slices_markdown(
        runs_dir=args.runs_dir,
        out_md=args.out,
        maxvars=args.maxvars,
        maxlen=args.maxlen,
        horn=args.horn,
        representation=args.representation,
        prompt_label=args.prompt_label,
        include_suite_regex=args.suite_regex,
        include_run_regex=args.run_regex,
        include_target_regex=args.target_regex,
        ids_mode=args.ids_mode,
        max_ids_per_slice=args.max_ids_per_slice,
        include_thinking=bool(args.include_thinking),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

