#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from llmlog.config.converter import write_converted_configs


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert experiments/configs/*.yaml into _refactor suite/target YAMLs.")
    ap.add_argument("--config", required=True, help="Path to an experiments config YAML (e.g. experiments/configs/foo.yaml)")
    ap.add_argument(
        "--out-dir",
        default=str(Path(__file__).resolve().parents[1] / "configs"),
        help="Output directory containing {suites,targets}/ (default: _refactor/configs)",
    )
    ap.add_argument("--overwrite", action="store_true", help="Overwrite existing files")
    args = ap.parse_args()

    cfg_path = Path(args.config).resolve()
    old = yaml.safe_load(cfg_path.read_text())
    if not isinstance(old, dict):
        raise SystemExit(f"Expected mapping in {cfg_path}")

    suite_file, target_file = write_converted_configs(old_config=old, out_dir=args.out_dir, overwrite=args.overwrite)
    print(f"Wrote suite:  {suite_file}")
    print(f"Wrote targets:{target_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


