#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

import yaml


def _bootstrap_import_path() -> Path:
    here = Path(__file__).resolve()
    refactor_root = here.parents[1]
    sys.path.insert(0, str(refactor_root / "src"))
    return refactor_root


def main() -> int:
    refactor_root = _bootstrap_import_path()

    from llmlog.models import list_models, select_default_latest_targets

    ap = argparse.ArgumentParser(
        description="Sync a small 'latest models' target set from provider model listing APIs."
    )
    ap.add_argument(
        "--out",
        default=str(refactor_root / "configs" / "targets" / "generated_latest_models.yaml"),
        help="Output YAML path for a generated TargetSetConfig.",
    )
    ap.add_argument("--name", default="generated_latest_models", help="Target set name field.")
    ap.add_argument(
        "--providers",
        default="anthropic,google,openai",
        help="Comma-separated providers to include (anthropic,google,openai).",
    )
    ap.add_argument("--secrets", default=None, help="Optional path to secrets.json (defaults to ./secrets.json)")
    ap.add_argument(
        "--inventory-out",
        default=None,
        help="Optional JSON output path to write the raw model id inventory used for selection.",
    )
    ap.add_argument("--dry-run", action="store_true", help="Do not write files; print to stdout")
    args = ap.parse_args()

    providers = [p.strip().lower() for p in (args.providers or "").split(",") if p.strip()]
    if not providers:
        raise SystemExit("No providers selected")

    models_by_provider: Dict[str, List[str]] = {}
    for prov in providers:
        listed = list_models(prov, secrets_path=args.secrets)
        models_by_provider[prov] = sorted({m.id for m in listed})

    targets = select_default_latest_targets(models_by_provider)

    yaml_obj = {"name": args.name, "targets": targets}
    out_text = yaml.safe_dump(yaml_obj, sort_keys=False)

    if args.dry_run:
        print(out_text)
    else:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(out_text)
        print(f"Wrote {out_path}")

    if args.inventory_out:
        inv_path = Path(args.inventory_out)
        inv_path.parent.mkdir(parents=True, exist_ok=True)
        inv_path.write_text(json.dumps(models_by_provider, indent=2, sort_keys=True) + "\n")
        if not args.dry_run:
            print(f"Wrote {inv_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())


