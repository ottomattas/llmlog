from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


SECRETS_FILE = "secrets.json"


def load_secrets(path: Optional[str] = None) -> Dict[str, Any]:
    """Load provider secrets from a JSON file and overlay environment variables.

    Priority:
    - explicit `path` if provided
    - `secrets.json` in the current working directory
    - env vars (always override)
    """
    filepath = Path(path or SECRETS_FILE)
    try:
        data = json.loads(filepath.read_text())
        if not isinstance(data, dict):
            data = {}
    except FileNotFoundError:
        data = {}
    except Exception as e:
        raise RuntimeError(f"Could not load secrets file {filepath}: {e}")

    env_overrides = {
        "anthropic": {"api_key": os.getenv("ANTHROPIC_API_KEY")},
        "google": {"api_key": os.getenv("GOOGLE_API_KEY")},
        "gemini": {"api_key": os.getenv("GEMINI_API_KEY")},
        "openai": {"api_key": os.getenv("OPENAI_API_KEY")},
        # optional
        "azure_openai": {
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        },
    }
    for provider, cfg in env_overrides.items():
        for k, v in (cfg or {}).items():
            if v:
                data.setdefault(provider, {})
                data[provider][k] = v
    return data


def get_provider_key(secrets: Dict[str, Any], provider: str, key: str = "api_key") -> Optional[str]:
    provider = (provider or "").lower()
    section = secrets.get(provider) or {}
    return section.get(key)


