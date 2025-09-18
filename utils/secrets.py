import json
import os
from typing import Any, Dict, Optional


SECRETS_FILE = "secrets.json"


def load_secrets(path: Optional[str] = None) -> Dict[str, Any]:
    filepath = path or SECRETS_FILE
    try:
        with open(filepath, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}
    except Exception as e:
        raise RuntimeError(f"Could not load secrets file {filepath}: {e}")
    # overlay environment variables
    env_overrides = {
        "openai": {"api_key": os.getenv("OPENAI_API_KEY")},
        "anthropic": {"api_key": os.getenv("ANTHROPIC_API_KEY")},
        "google": {"api_key": os.getenv("GOOGLE_API_KEY")},
        "azure_openai": {
            "api_key": os.getenv("AZURE_OPENAI_API_KEY"),
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT"),
            "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT"),
        },
        "groq": {"api_key": os.getenv("GROQ_API_KEY")},
    }
    for provider, cfg in env_overrides.items():
        for k, v in (cfg or {}).items():
            if v:
                data.setdefault(provider, {})
                data[provider][k] = v
    return data


def get_provider_key(secrets: Dict[str, Any], provider: str, key: str = "api_key") -> Optional[str]:
    provider = provider.lower()
    section = secrets.get(provider) or {}
    return section.get(key)


