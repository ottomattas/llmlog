from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Optional, Tuple


def _jsonl_iter(path: Path) -> Iterator[Dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if isinstance(obj, dict):
                yield obj


def _read_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _find_project_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(12):
        if (cur / "configs").exists() and (cur / "src").exists():
            return cur
        if cur.parent == cur:
            break
        cur = cur.parent
    return start.resolve().parents[0]


def _infer_pricing_tier(*, run_dir: Path, provider: str, default: str = "standard") -> str:
    # Prefer explicit field in manifest if present.
    manifest = _read_json(run_dir / "run.manifest.json")
    if manifest:
        t = manifest.get("pricing_tier")
        if isinstance(t, str) and t.strip():
            return t.strip()
        tgt = manifest.get("target")
        if isinstance(tgt, dict):
            t2 = tgt.get("pricing_tier")
            if isinstance(t2, str) and t2.strip():
                return t2.strip()

    # Next: infer from invocation traces (submit-only -> batch for Anthropic/Gemini).
    inv_path = run_dir / "run.invocations.jsonl"
    prov_l = (provider or "").lower()
    for inv in _jsonl_iter(inv_path):
        submit_only = bool(inv.get("submit_only"))
        if submit_only and prov_l in ("anthropic", "google", "gemini"):
            return "batch"

    return default


def _sum_cost_from_provenance(*, prov_path: Path, rate: Any) -> Dict[str, float]:
    totals: Dict[str, float] = {"cost_total_usd": 0.0, "cost_input_usd": 0.0, "cost_output_usd": 0.0}
    if not prov_path.exists() or rate is None:
        return totals

    # Import lazily so this script can run from repo root without installation.
    from llmlog.pricing.cost import compute_cost_usd

    for obj in _jsonl_iter(prov_path):
        usage = obj.get("usage") or {}
        if not isinstance(usage, dict):
            usage = {}
        try:
            c = compute_cost_usd(rate, usage)
            totals["cost_total_usd"] += float(c.get("total_usd") or 0.0)
            totals["cost_input_usd"] += float(c.get("input_usd") or 0.0)
            totals["cost_output_usd"] += float(c.get("output_usd") or 0.0)
        except Exception:
            continue
    return totals


@dataclass(frozen=True)
class RunPaths:
    run_dir: Path
    summary_path: Path
    manifest_path: Path
    provenance_path: Path


def _iter_runs(runs_dir: Path) -> Iterator[RunPaths]:
    for summary_path in runs_dir.rglob("results.summary.json"):
        run_dir = summary_path.parent
        prov2 = run_dir / "results.provenance.v2.jsonl"
        prov1 = run_dir / "results.provenance.jsonl"
        yield RunPaths(
            run_dir=run_dir,
            summary_path=summary_path,
            manifest_path=run_dir / "run.manifest.json",
            provenance_path=(prov2 if prov2.exists() else prov1),
        )


def main(argv: Optional[Iterable[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Backfill pricing_rate/pricing_tier + recompute costs for existing runs.")
    ap.add_argument("--runs-dir", default="runs", help="Path to runs directory (default: runs/)")
    ap.add_argument(
        "--default-pricing-table",
        default="configs/pricing/multivendor_2025-12-19.yaml",
        help="Fallback pricing table path (used when run summary/manifest omits pricing_table).",
    )
    ap.add_argument("--dry-run", action="store_true", help="Do not write changes; just report.")
    args = ap.parse_args(list(argv) if argv is not None else None)

    runs_dir = Path(args.runs_dir).resolve()
    if not runs_dir.exists():
        raise FileNotFoundError(f"Runs dir not found: {runs_dir}")
    project_root = _find_project_root(runs_dir)

    # Imports (repo-local)
    import sys

    sys.path.insert(0, str((project_root / "src").resolve()))
    from llmlog.pricing.loader import load_pricing_table
    from llmlog.pricing.cost import match_rate

    tbl_cache: Dict[str, Any] = {}

    changed = 0
    missing_rate = 0
    total = 0

    for rp in _iter_runs(runs_dir):
        total += 1
        summary = _read_json(rp.summary_path) or {}
        manifest = _read_json(rp.manifest_path) or {}

        provider = str(summary.get("provider") or manifest.get("target", {}).get("provider") or manifest.get("provider") or "")
        model = str(summary.get("model") or manifest.get("target", {}).get("model") or manifest.get("model") or "")
        if not provider or not model:
            continue

        # Pricing table
        pricing_table = summary.get("pricing_table") or manifest.get("pricing_table") or args.default_pricing_table
        pricing_table_s = str(pricing_table)
        pt_path = Path(pricing_table_s)
        if not pt_path.is_absolute():
            pt_path = (project_root / pricing_table_s).resolve()
        if not pt_path.exists():
            # Keep existing values if we can't load the table.
            continue

        # Tier
        tier = _infer_pricing_tier(run_dir=rp.run_dir, provider=provider, default="standard")

        # Load pricing table (cache)
        key = str(pt_path)
        tbl = tbl_cache.get(key)
        if tbl is None:
            tbl = load_pricing_table(str(pt_path))
            tbl_cache[key] = tbl

        rate = match_rate(tbl, provider=provider, model=model, tier=tier)
        if rate is None:
            missing_rate += 1

        new_pricing_rate = rate.model_dump(mode="json", exclude_none=True) if rate is not None else None

        # Recompute costs
        cost = _sum_cost_from_provenance(prov_path=rp.provenance_path, rate=rate)

        # Apply updates
        did_change = False
        # summary
        if summary.get("pricing_table") != pricing_table_s:
            summary["pricing_table"] = pricing_table_s
            did_change = True
        if summary.get("pricing_tier") != tier:
            summary["pricing_tier"] = tier
            did_change = True
        if summary.get("pricing_rate") != new_pricing_rate:
            summary["pricing_rate"] = new_pricing_rate
            did_change = True
        stats = summary.get("stats")
        if not isinstance(stats, dict):
            stats = {}
            summary["stats"] = stats
            did_change = True
        for k in ("cost_total_usd", "cost_input_usd", "cost_output_usd"):
            if abs(float(stats.get(k) or 0.0) - float(cost.get(k) or 0.0)) > 1e-9:
                stats[k] = float(cost.get(k) or 0.0)
                did_change = True

        # manifest
        if manifest:
            if manifest.get("pricing_table") != pricing_table_s:
                manifest["pricing_table"] = pricing_table_s
                did_change = True
            if manifest.get("pricing_tier") != tier:
                manifest["pricing_tier"] = tier
                did_change = True
            if manifest.get("pricing_rate") != new_pricing_rate:
                manifest["pricing_rate"] = new_pricing_rate
                did_change = True

        if did_change:
            changed += 1
            if not args.dry_run:
                _write_json(rp.summary_path, summary)
                if manifest:
                    _write_json(rp.manifest_path, manifest)

    print(f"backfill_pricing: total={total} changed={changed} missing_rate={missing_rate} dry_run={bool(args.dry_run)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

