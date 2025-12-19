#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _bootstrap_import_path() -> None:
    here = Path(__file__).resolve()
    refactor_root = here.parents[1]
    sys.path.insert(0, str(refactor_root / "src"))


def main() -> int:
    _bootstrap_import_path()

    from llmlog.models import list_models

    ap = argparse.ArgumentParser(description="List available models from a provider API.")
    ap.add_argument("--provider", required=True, help="Provider key: openai | anthropic | google")
    ap.add_argument("--secrets", default=None, help="Optional path to secrets.json (defaults to ./secrets.json)")
    ap.add_argument("--json", action="store_true", help="Emit JSON instead of plain lines")
    args = ap.parse_args()

    models = list_models(args.provider, secrets_path=args.secrets)
    ids = sorted({m.id for m in models})

    if args.json:
        payload = {"provider": args.provider, "count": len(ids), "models": ids}
        print(json.dumps(payload, indent=2))
    else:
        for mid in ids:
            print(mid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


