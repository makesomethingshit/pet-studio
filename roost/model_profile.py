"""Model profile helpers for local agent adapters."""

from __future__ import annotations

import os
from collections.abc import Mapping
from typing import Any

from roost.auth_config import apply_auth_config_env

MODEL_TIER_ORDER = {
    "closed": 0,
    "open-sota": 1,
    "local": 2,
    "value": 3,
    "free": 4,
}
MODEL_PROFILE_ORDER = {
    "codex/default": 0,
    "closed/claude": 1,
    "openrouter/sota": 10,
    "local/default": 20,
    "openrouter/fast": 30,
    "openrouter/cheap": 40,
}
MODEL_COST_UNITS = {
    "free": 0,
    "low": 1,
    "high": 3,
}
PROVIDER_MODEL_ENV_KEYS = ("OPENROUTER_MODEL", "CODEX_MODEL")


def model_profile_tier(profile: Mapping[str, Any] | None) -> str:
    """Return the user-facing hierarchy tier for a model profile."""
    if not profile:
        return "value"

    explicit = str(profile.get("tier", "")).strip().lower()
    if explicit in MODEL_TIER_ORDER:
        return explicit

    profile_id = str(profile.get("id", "")).lower()
    provider = str(profile.get("provider", "")).lower()
    model = str(profile.get("model", "")).lower()
    cost = str(profile.get("cost", "")).lower()
    haystack = f"{profile_id} {provider} {model}"

    if provider in {"codex", "openai", "anthropic"} or any(word in haystack for word in ("gpt", "claude")):
        return "closed"
    if provider == "local" or "local/" in profile_id:
        return "local"
    if cost == "free" or any(word in haystack for word in ("free", "cheap")):
        return "free"
    if cost == "low" or any(word in haystack for word in ("fast", "value")):
        return "value"
    if any(word in haystack for word in ("sota", "open")):
        return "open-sota"
    return "value"


def model_profile_sort_key(profile: Mapping[str, Any]) -> tuple[int, int, str]:
    tier = model_profile_tier(profile)
    profile_id = str(profile.get("id", ""))
    return (MODEL_TIER_ORDER.get(tier, 99), MODEL_PROFILE_ORDER.get(profile_id, 100), profile_id)


def model_profile_cost_units(profile: Mapping[str, Any] | None) -> int:
    """Return a small relative cost unit for credit planning.

    This is not a price estimate. It only compares the existing profile cost
    hints so team presets can show whether work moved off the expensive route.
    """
    if not profile:
        return MODEL_COST_UNITS["low"]

    cost = str(profile.get("cost", "")).strip().lower()
    if cost in MODEL_COST_UNITS:
        return MODEL_COST_UNITS[cost]

    tier = model_profile_tier(profile)
    if tier in {"free", "local"}:
        return MODEL_COST_UNITS["free"]
    if tier == "value":
        return MODEL_COST_UNITS["low"]
    return MODEL_COST_UNITS["high"]


def estimate_role_model_plan_savings(
    role_model_plan: list[Mapping[str, Any]],
    lead_profile: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Estimate relative savings versus routing every role through Lead."""
    roles = [item for item in role_model_plan if isinstance(item, Mapping)]
    role_count = len(roles) or 3
    lead_units = model_profile_cost_units(lead_profile)
    baseline_units = lead_units * role_count
    plan_units = 0
    for item in roles:
        profile = item.get("profile")
        plan_units += model_profile_cost_units(profile if isinstance(profile, Mapping) else None)
    saved_units = baseline_units - plan_units
    saved_percent = round((saved_units / baseline_units) * 100) if baseline_units else 0
    return {
        "baseline": "lead-only",
        "baselineUnits": baseline_units,
        "planUnits": plan_units,
        "savedUnits": saved_units,
        "savedPercent": saved_percent,
    }


def model_profile_env_overrides(profile: Mapping[str, Any] | None) -> dict[str, str]:
    """Return environment variables implied by a model profile."""
    if not profile:
        return {}

    profile_id = str(profile.get("id", "")).strip()
    provider = str(profile.get("provider", "")).strip()
    model = str(profile.get("model", "")).strip()

    overrides: dict[str, str] = {}
    if profile_id:
        overrides["PET_STUDIO_MODEL_PROFILE"] = profile_id
        overrides["HERMES_MODEL_PROFILE"] = profile_id
    if provider:
        overrides["PET_STUDIO_MODEL_PROVIDER"] = provider
        overrides["HERMES_MODEL_PROVIDER"] = provider
    if model:
        overrides["PET_STUDIO_MODEL"] = model
        overrides["HERMES_MODEL"] = model

    provider_key = provider.lower()
    if provider_key == "openrouter" and model:
        overrides["OPENROUTER_MODEL"] = model
    elif provider_key == "codex" and model:
        overrides["CODEX_MODEL"] = model

    return overrides


def model_profile_env_clear(profile: Mapping[str, Any] | None) -> list[str]:
    """Return provider-specific model variables to clear for this profile."""
    if not profile:
        return []
    overrides = model_profile_env_overrides(profile)
    return [key for key in PROVIDER_MODEL_ENV_KEYS if key not in overrides]


def model_profile_powershell_env_lines(profile: Mapping[str, Any] | None) -> list[str]:
    """Return PowerShell assignment lines for a model profile."""
    overrides = model_profile_env_overrides(profile)
    lines = [
        f"Remove-Item Env:{key} -ErrorAction SilentlyContinue"
        for key in model_profile_env_clear(profile)
    ]
    for key, value in sorted(overrides.items()):
        escaped = value.replace("'", "''")
        lines.append(f"$env:{key} = '{escaped}'")
    return lines


def role_model_env_overrides(role_model_plan: list[Mapping[str, Any]]) -> dict[str, dict[str, str]]:
    """Return model environment variables grouped by team role."""
    env_by_role = {}
    for item in role_model_plan:
        if not isinstance(item, Mapping):
            continue
        role = str(item.get("role", "")).strip().lower()
        profile = item.get("profile")
        if not role or not isinstance(profile, Mapping):
            continue
        env_by_role[role] = model_profile_env_overrides(profile)
    return env_by_role


def role_model_env_clear(role_model_plan: list[Mapping[str, Any]]) -> dict[str, list[str]]:
    """Return provider-specific variables to clear, grouped by team role."""
    clear_by_role = {}
    for item in role_model_plan:
        if not isinstance(item, Mapping):
            continue
        role = str(item.get("role", "")).strip().lower()
        profile = item.get("profile")
        if not role or not isinstance(profile, Mapping):
            continue
        clear_by_role[role] = model_profile_env_clear(profile)
    return clear_by_role


def role_model_plan_powershell_env_lines(role_model_plan: list[Mapping[str, Any]]) -> list[str]:
    """Return PowerShell env sections for a role model plan."""
    lines = [
        "# Pet Studio team model env plan",
        "# Copy one role section at a time; later sections reuse the same env variable names.",
    ]
    for item in role_model_plan:
        if not isinstance(item, Mapping):
            continue
        role = str(item.get("role", "")).strip().lower()
        profile = item.get("profile")
        if not role or not isinstance(profile, Mapping):
            continue
        lines.append("")
        lines.append(f"# {role}: {profile.get('id', '')}")
        lines.extend(model_profile_powershell_env_lines(profile))
    return lines


def build_model_profile_env(
    profile: Mapping[str, Any] | None,
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build a subprocess environment for the selected model profile."""
    env = apply_auth_config_env(os.environ if base_env is None else base_env)
    overrides = model_profile_env_overrides(profile)
    for key in model_profile_env_clear(profile):
        env.pop(key, None)
    env.update(overrides)
    return env
