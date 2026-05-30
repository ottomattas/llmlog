from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .schema import SuiteConfig, TargetSetConfig


def _read_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping in {path}, got {type(data)}")
    return data


def load_target_set_config(path: str) -> TargetSetConfig:
    p = Path(path)
    return TargetSetConfig(**_read_yaml(p))


def load_suite_config(path: str) -> SuiteConfig:
    p = Path(path)
    return SuiteConfig(**_read_yaml(p))


def resolve_suite(path: str) -> SuiteConfig:
    """Load a suite config and expand referenced target sets into inline targets.

    Resolution rules:
    - `targets` may be provided inline.
    - `targets_ref` may contain one or more YAML files; their targets are concatenated.
    - Relative target paths are resolved relative to the suite config directory.
    """
    suite_path = Path(path)
    suite = load_suite_config(str(suite_path))

    if suite.targets_ref:
        expanded = []
        for ref in suite.targets_ref:
            ref_path = Path(ref)
            if not ref_path.is_absolute():
                ref_path = (suite_path.parent / ref_path).resolve()
            ts = load_target_set_config(str(ref_path))
            expanded.extend(ts.targets)
        # merge with inline targets if present
        if suite.targets:
            expanded.extend(suite.targets)
        suite.targets = expanded
        suite.targets_ref = None

    if not suite.targets:
        raise ValueError("SuiteConfig must define targets or targets_ref")
    return suite


