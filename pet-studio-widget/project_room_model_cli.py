"""Model profile CLI helpers for the Pet Studio widget entrypoint."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from project_room_registry import DEFAULT_STATE_FILE

MODEL_PROFILE_ALIASES = {
    "codex": "codex/default",
    "default": "codex/default",
    "closed": "codex/default",
    "closed-model": "codex/default",
    "gpt": "codex/default",
    "claude": "closed/claude",
    "openrouter": "openrouter/sota",
    "open": "openrouter/sota",
    "open-sota": "openrouter/sota",
    "fusion": "fusion/local",
    "gateway": "fusion/local",
    "local": "local/default",
    "local-model": "local/default",
    "fast": "openrouter/fast",
    "value": "openrouter/fast",
    "budget": "openrouter/fast",
    "sota": "openrouter/sota",
    "cheap": "openrouter/cheap",
    "free": "openrouter/cheap",
}


def team_state_path_for_cli(state_file_arg: str | None = None) -> Path:
    state_bridge = Path(state_file_arg).expanduser() if state_file_arg else DEFAULT_STATE_FILE
    return state_bridge.parent / "team_state.json"


def resolve_model_profile_alias(profile_id: str) -> str:
    text = profile_id.strip()
    return MODEL_PROFILE_ALIASES.get(text.lower(), text)


def _profile_env_lines(profile: dict[str, Any]) -> list[str]:
    from roost.model_profile import model_profile_powershell_env_lines

    return model_profile_powershell_env_lines(profile)


def _role_model_profile_for_env(team_state: Any, role: str) -> dict[str, Any]:
    role_name = role.strip().lower()
    if role_name not in {"scout", "coordinator", "lead"}:
        raise ValueError(f"Unknown role: {role!r}")
    return team_state.get_role_model_profile(role_name)


def _role_model_env_for_status(team_state: Any) -> dict[str, dict[str, str]]:
    from roost.model_profile import role_model_env_overrides

    return role_model_env_overrides(team_state.list_role_model_plan())


def _role_model_env_clear_for_status(team_state: Any) -> dict[str, list[str]]:
    from roost.model_profile import role_model_env_clear

    return role_model_env_clear(team_state.list_role_model_plan())


def _team_model_env_lines(team_state: Any) -> list[str]:
    from roost.model_profile import role_model_plan_powershell_env_lines

    return role_model_plan_powershell_env_lines(team_state.list_role_model_plan())


def _explain_backend_version_failure(
    command: str,
    returncode: int,
    stderr: str,
    diagnostics: dict[str, Any],
) -> str:
    runtime_failure = (
        "Unable to create process using" in stderr
        or ("python.exe" in stderr and ("Access is denied" in stderr or "access is denied" in stderr.lower()))
    )
    if not runtime_failure:
        return f"{command} --version failed with exit code {returncode}"

    python_match = re.search(r'["\']([^"\']*python\.exe)["\']', stderr, re.IGNORECASE)
    if python_match:
        python_path = python_match.group(1)
        diagnostics["pythonRuntimePath"] = python_path
        try:
            diagnostics["pythonRuntimeExists"] = Path(python_path).exists()
            diagnostics["pythonRuntimeAccessible"] = True
        except OSError as error:
            diagnostics["pythonRuntimeExists"] = None
            diagnostics["pythonRuntimeAccessible"] = False
            diagnostics["pythonRuntimeError"] = str(error)
    diagnostics["repairHint"] = (
        "Repair or reinstall Hermes so its virtualenv launcher can start its Python runtime. "
        "Pet Studio already passed the selected model env to Hermes."
    )
    return f"{command} launcher could not start its Python runtime"


def test_model_profile(profile: dict[str, Any]) -> dict[str, Any]:
    from roost.auth_config import masked_auth_status
    from roost.model_profile import build_model_profile_env, model_profile_env_overrides

    backend_name = profile.get("backend", "hermes")
    profile_env = build_model_profile_env(profile)
    diagnostics: dict[str, Any] = {
        "env": model_profile_env_overrides(profile),
        "secrets": {
            "OPENROUTER_API_KEY": bool(profile_env.get("OPENROUTER_API_KEY")),
            "CODEX_OAUTH_TOKEN": bool(profile_env.get("CODEX_OAUTH_TOKEN")),
            "CODEX_AUTH_TOKEN": bool(profile_env.get("CODEX_AUTH_TOKEN")),
            "CODEX_API_KEY": bool(profile_env.get("CODEX_API_KEY")),
            "HERMES_GATEWAY_TOKEN": bool(profile_env.get("HERMES_GATEWAY_TOKEN")),
            "HERMES_API_KEY": bool(profile_env.get("HERMES_API_KEY")),
        },
        "auth": masked_auth_status(profile_env),
    }

    from roost.dispatcher import BackendRegistry

    try:
        backend_cls = BackendRegistry().get(backend_name)
        backend = backend_cls()
        if hasattr(backend, "set_model_profile"):
            backend.set_model_profile(profile)
        command = getattr(backend, "hermes_cmd", None) or getattr(backend, "codex_cmd", None)
        if command:
            command_path = shutil.which(command)
            diagnostics["command"] = command
            diagnostics["commandPath"] = command_path
            diagnostics["commandFound"] = command_path is not None
        ok = bool(backend.health_check()) if hasattr(backend, "health_check") else False
        reason = ""
        if not ok and diagnostics.get("commandFound") is False:
            reason = f"Command not found on PATH: {diagnostics.get('command')}"
        elif not ok and profile.get("provider") == "openrouter" and not diagnostics["secrets"]["OPENROUTER_API_KEY"]:
            reason = "OPENROUTER_API_KEY is not set"
        elif not ok and command:
            try:
                probe = subprocess.run(
                    [command, "--version"],
                    capture_output=True,
                    encoding="utf-8",
                    errors="replace",
                    text=True,
                    timeout=5,
                    env=build_model_profile_env(profile),
                )
                diagnostics["versionProbe"] = {
                    "returnCode": probe.returncode,
                    "stdout": probe.stdout.strip()[:500],
                    "stderr": probe.stderr.strip()[:500],
                }
                reason = _explain_backend_version_failure(
                    command,
                    probe.returncode,
                    probe.stderr,
                    diagnostics,
                )
            except Exception as probe_error:
                error_text = str(probe_error)
                diagnostics["versionProbe"] = {"error": error_text}
                reason = _explain_backend_version_failure(command, -1, error_text, diagnostics)
        return {
            "ok": ok,
            "status": "ok" if ok else "failed",
            "profile": profile,
            "backend": backend_name,
            "diagnostics": diagnostics,
            "reason": reason,
        }
    except Exception as error:
        return {
            "ok": False,
            "status": "error",
            "profile": profile,
            "backend": backend_name,
            "diagnostics": diagnostics,
            "error": str(error),
        }


def handle_model_profile_cli(args: argparse.Namespace, parser: argparse.ArgumentParser) -> bool:
    wants_model_action = any(
        (
            args.list_model_profiles,
            args.model,
            args.model_status,
            args.use_model_profile,
            args.set_model_profile,
            args.set_role_model,
            args.clear_role_model,
            args.team_model_preset,
            args.remove_model_profile,
            args.test_model_profile is not None,
            args.print_model_env is not None,
            args.print_role_model_env is not None,
            args.print_team_model_env is not None,
        )
    )
    if not wants_model_action:
        return False

    from roost.state import TeamState

    team_state = TeamState(team_state_path_for_cli(args.state_file))

    try:
        if args.set_model_profile:
            if not args.model_provider:
                parser.error("--set-model-profile requires --model-provider")
            if not args.model_name:
                parser.error("--set-model-profile requires --model-name")
            team_state.set_model_profile(
                args.project_id,
                args.set_model_profile,
                args.model_backend,
                args.model_provider,
                args.model_name,
                args.model_cost,
                args.model_tier,
            )
            if args.use_model_profile == args.set_model_profile:
                team_state.set_active_model_profile(args.project_id, args.set_model_profile)

        if args.set_role_model:
            role, profile_id = args.set_role_model
            team_state.set_role_model_profile(role, resolve_model_profile_alias(profile_id), project_id=args.project_id)

        if args.clear_role_model:
            team_state.clear_role_model_profile(args.clear_role_model, project_id=args.project_id)

        if args.team_model_preset:
            team_state.apply_team_model_preset(args.team_model_preset, project_id=args.project_id)

        selected_model = args.model or args.use_model_profile
        if selected_model and selected_model != args.set_model_profile:
            team_state.set_active_model_profile(args.project_id, resolve_model_profile_alias(selected_model))

        if args.remove_model_profile:
            team_state.remove_model_profile(args.project_id, args.remove_model_profile)
    except Exception as error:
        parser.error(str(error))

    active_id = team_state.get_active_model_profile_id()
    profile_id = args.print_model_env or active_id
    if args.model_status:
        profile = next((item for item in team_state.list_model_profiles() if item["id"] == active_id), None)
        if profile is None:
            parser.error(f"Unknown model profile: {active_id!r}")
        print(
            json.dumps(
                {
                    "ok": True,
                    "activeModelProfile": active_id,
                    "profile": profile,
                    "teamModelPreset": team_state.get_team_model_preset_id(),
                    "roleModelPlan": team_state.list_role_model_plan(),
                    "roleModelEnv": _role_model_env_for_status(team_state),
                    "roleModelEnvClear": _role_model_env_clear_for_status(team_state),
                    "teamModelSavings": team_state.estimate_team_model_savings(),
                    "teamModelPresets": team_state.list_team_model_presets(),
                    "test": test_model_profile(profile),
                    "teamState": str(team_state.state_file),
                },
                indent=2,
            )
        )
        return True

    if args.test_model_profile is not None:
        profile_id = resolve_model_profile_alias(args.test_model_profile) if args.test_model_profile else active_id
        profile = next((item for item in team_state.list_model_profiles() if item["id"] == profile_id), None)
        if profile is None:
            parser.error(f"Unknown model profile: {profile_id!r}")
        print(json.dumps(test_model_profile(profile), indent=2))
        return True

    if args.print_model_env is not None:
        profile_id = resolve_model_profile_alias(profile_id)
        profile = next((item for item in team_state.list_model_profiles() if item["id"] == profile_id), None)
        if profile is None:
            parser.error(f"Unknown model profile: {profile_id!r}")
        print("\n".join(_profile_env_lines(profile)))
        return True

    if args.print_role_model_env is not None:
        try:
            profile = _role_model_profile_for_env(team_state, args.print_role_model_env)
        except Exception as error:
            parser.error(str(error))
        print("\n".join(_profile_env_lines(profile)))
        return True

    if args.print_team_model_env is not None:
        print("\n".join(_team_model_env_lines(team_state)))
        return True

    print(
        json.dumps(
            {
                "ok": True,
                "activeModelProfile": active_id,
                "teamModelPreset": team_state.get_team_model_preset_id(),
                "profiles": team_state.list_model_profiles(),
                "roleModelPlan": team_state.list_role_model_plan(),
                "roleModelEnv": _role_model_env_for_status(team_state),
                "roleModelEnvClear": _role_model_env_clear_for_status(team_state),
                "teamModelSavings": team_state.estimate_team_model_savings(),
                "teamModelPresets": team_state.list_team_model_presets(),
                "teamState": str(team_state.state_file),
            },
            indent=2,
        )
    )
    return True
