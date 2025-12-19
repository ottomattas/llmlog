from __future__ import annotations

import http.client
import json
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from ..providers.secrets import get_provider_key, load_secrets


@dataclass(frozen=True)
class ProviderModel:
    provider: str
    id: str
    raw: Dict[str, Any]


def _http_get_json(*, host: str, path: str, headers: Dict[str, str]) -> Dict[str, Any]:
    conn = http.client.HTTPSConnection(host)
    conn.request("GET", path, headers=headers)
    resp = conn.getresponse()
    raw = resp.read()
    if resp.status != 200:
        try:
            data = json.loads(raw)
            msg = (data.get("error") or {}).get("message") or str(data)
        except Exception:
            msg = raw.decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {resp.status} {resp.reason} from {host}{path}: {msg}")
    try:
        return json.loads(raw)
    except Exception:
        raise RuntimeError(f"Response is not JSON from {host}{path}: {raw!r}")
    finally:
        conn.close()


def _iter_openai_model_ids(data: Dict[str, Any]) -> Iterable[ProviderModel]:
    # OpenAI list: {"object":"list","data":[{"id":...}, ...]}
    items = data.get("data") or []
    if not isinstance(items, list):
        return []
    for it in items:
        if not isinstance(it, dict):
            continue
        mid = it.get("id")
        if isinstance(mid, str) and mid:
            yield ProviderModel(provider="openai", id=mid, raw=it)


def _iter_anthropic_model_ids(data: Dict[str, Any]) -> Iterable[ProviderModel]:
    # Anthropic list: {"data":[{"id":...}, ...], "has_more": bool, ...}
    items = data.get("data") or []
    if not isinstance(items, list):
        return []
    for it in items:
        if not isinstance(it, dict):
            continue
        mid = it.get("id")
        if isinstance(mid, str) and mid:
            yield ProviderModel(provider="anthropic", id=mid, raw=it)


def _iter_gemini_model_ids(data: Dict[str, Any]) -> Iterable[ProviderModel]:
    # Gemini list: {"models":[{"name":"models/gemini-2.5-pro", ...}, ...], ...}
    items = data.get("models") or data.get("data") or []
    if not isinstance(items, list):
        return []
    for it in items:
        if not isinstance(it, dict):
            continue
        name = it.get("name") or it.get("id") or it.get("model")
        if not isinstance(name, str) or not name:
            continue
        # normalize "models/<id>" -> "<id>"
        mid = name.split("/", 1)[-1] if "/" in name else name
        if mid:
            yield ProviderModel(provider="google", id=mid, raw=it)


def list_models(provider: str, *, secrets_path: Optional[str] = None) -> List[ProviderModel]:
    """List models via provider APIs.

    Supported providers:
    - openai: `GET /v1/models` (`https://platform.openai.com/docs/api-reference/models`)
    - anthropic: `GET /v1/models` (`https://platform.claude.com/docs/en/api/models/list`)
    - google: `GET /v1beta/models` (`https://ai.google.dev/api/models`)
    """
    prov = (provider or "").lower()
    secrets = load_secrets(secrets_path)

    if prov == "openai":
        key = get_provider_key(secrets, "openai")
        if not key:
            raise RuntimeError("Missing OpenAI API key in secrets.json or OPENAI_API_KEY")
        data = _http_get_json(
            host="api.openai.com",
            path="/v1/models",
            headers={"Authorization": f"Bearer {key}"},
        )
        return list(_iter_openai_model_ids(data))

    if prov == "anthropic":
        key = get_provider_key(secrets, "anthropic")
        if not key:
            raise RuntimeError("Missing Anthropic API key in secrets.json or ANTHROPIC_API_KEY")
        # Anthropic requires an API version header for most endpoints.
        # We use the stable version header; adjust if Anthropic changes requirements.
        data = _http_get_json(
            host="api.anthropic.com",
            path="/v1/models",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
        )
        return list(_iter_anthropic_model_ids(data))

    if prov in ("google", "gemini"):
        key = get_provider_key(secrets, "google") or get_provider_key(secrets, "gemini")
        if not key:
            raise RuntimeError("Missing Google/Gemini API key in secrets.json or GOOGLE_API_KEY/GEMINI_API_KEY")
        data = _http_get_json(
            host="generativelanguage.googleapis.com",
            path=f"/v1beta/models?key={key}",
            headers={"x-goog-api-key": key},
        )
        return list(_iter_gemini_model_ids(data))

    raise NotImplementedError(f"Provider not supported for model listing: {provider}")



