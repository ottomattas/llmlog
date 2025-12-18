from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml

from .schema import PricingTable


def load_pricing_table(path: str) -> PricingTable:
    p = Path(path)
    data = yaml.safe_load(p.read_text())
    if not isinstance(data, dict):
        raise ValueError(f"Expected YAML mapping in {p}, got {type(data)}")
    return PricingTable(**data)


