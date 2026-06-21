"""Local auth configuration helpers for optional model adapters.

Secrets are loaded from environment variables or ignored local JSON files. The
tracked repository must never contain real API keys or OAuth tokens.
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AUTH_CONFIG = ROOT / "pet-studio-widget" / ".pet_studio_keys.json"
DEFAULT_CODEX_AUTH_CONFIG = Path.home() / ".codex" / "auth.json"

AUTH_ENV_KEYS = (
    "OPENROUTER_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "CODEX_API_KEY",
    "CODEX_OAUTH_TOKEN",
    "CODEX_AUTH_TOKEN",
    "CODEX_CMD",
    "HERMES_API_KEY",
    "HERMES_GATEWAY_URL",
    "HERMES_GATEWAY_TOKEN",
    "HERMES_BASE_URL",
    "HERMES_CMD",
)


def auth_config_path() -> Path:
    configured = os.environ.get("PET_STUDIO_AUTH_CONFIG", "").strip()
    return Path(configured).expanduser() if configured else DEFAULT_AUTH_CONFIG


def auth_config_path_for(env: Mapping[str, str] | None = None) -> Path:
    configured = (env or os.environ).get("PET_STUDIO_AUTH_CONFIG", "").strip()
    return Path(configured).expanduser() if configured else DEFAULT_AUTH_CONFIG


def load_auth_config(path: Path | None = None) -> dict[str, str]:
    config_path = path or auth_config_path()
    try:
        data = json.loads(config_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    result: dict[str, str] = {}
    for key in AUTH_ENV_KEYS:
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            result[key] = value.strip()
    return result


def load_codex_oauth_config(path: Path | None = None) -> dict[str, str]:
    config_path = path or DEFAULT_CODEX_AUTH_CONFIG
    try:
        data = json.loads(config_path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}

    result: dict[str, str] = {}
    tokens = data.get("tokens")
    if isinstance(tokens, dict):
        access_token = tokens.get("access_token")
        if isinstance(access_token, str) and access_token.strip():
            result["CODEX_OAUTH_TOKEN"] = access_token.strip()
            result["CODEX_AUTH_TOKEN"] = access_token.strip()
    openai_key = data.get("OPENAI_API_KEY")
    if isinstance(openai_key, str) and openai_key.strip():
        result["OPENAI_API_KEY"] = openai_key.strip()
    return result


def apply_auth_config_env(
    env: Mapping[str, str] | None = None,
    path: Path | None = None,
) -> dict[str, str]:
    merged = dict(os.environ if env is None else env)
    for key, value in load_auth_config(path or auth_config_path_for(merged)).items():
        if not merged.get(key):
            merged[key] = value
    for key, value in load_codex_oauth_config().items():
        if not merged.get(key):
            merged[key] = value
    return merged


def masked_auth_status(env: Mapping[str, str] | None = None, path: Path | None = None) -> dict[str, object]:
    merged = apply_auth_config_env(env, path)
    return {
        "authConfig": str(path or auth_config_path()),
        "configured": {key: bool(merged.get(key)) for key in AUTH_ENV_KEYS},
    }
