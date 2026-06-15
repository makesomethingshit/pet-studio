# Codex Integration

Pet Studio's Codex integration is a local hook/file bridge. It is not an official Codex dashboard API.

The bridge writes project state into local JSON files that the widget watches. State messages appear as runtime speech bubbles near the main pet.

## Install The Local Bridge

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_codex_integration.py --project-id gakju-archive-demo
```

The installer:

- installs the skill as `$pet-studio` under `%USERPROFILE%\.codex\skills\pet-studio`
- writes project-local `.codex\hooks.json` entries for `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PreCompact`, and `Stop`
- writes an active project pin when `--project-id` is provided
- only wraps the user-level Codex `notify` command when `--install-notify` is provided

After installation, restart Codex or open `/hooks` to review and trust the new command hooks when Codex asks. Pet Studio cannot detect that trust approval directly, so the preflight prints a reminder when hooks are installed.

## Hook Bubble Policy

- `UserPromptSubmit` shows `Working: ...`
- `PreToolUse` shows `Using <tool>`
- `PostToolUse` stays in `Working`, not `Ready for review`
- `PreCompact` shows `Compacting context`
- `Stop` shows `Done` briefly, then the widget falls back to idle
- `blocked` and explicit review/handoff events are the normal paths to review-style messaging

Inspect recent hook activity:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --skip-render --show-hook-log
```

## Manual Project State

Update a project state directly:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\set_pet_studio_state.py --project-id gakju-archive-demo --state running --message "building room kit"
```

Publish a Codex-style event:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_event_adapter.py --project-id gakju-archive-demo --event start --message "working"
```

Run the demo state sequence for README GIF capture or manual QA:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_demo_states.py --project-id gakju-archive-demo --once --delay-seconds 2
```

Use `--dry-run` to inspect the exact state bridge payloads without writing `project-room-state.json`.

Send a structured JSON payload, which is the command target used by the lifecycle hook bridge:

```powershell
'{"event":"start","message":"working","projectId":"gakju-archive-demo"}' | .\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_event_adapter.py --event-json -
```

When no project id is provided, the adapter resolves project identity in this order:

1. Explicit `projectId`
2. Active project pin
3. Workspace path matching

Pin an active project when several rooms share one workspace:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\set_active_pet_studio.py --project-id gakju-archive-demo --cwd .
```

Long state messages are whitespace-normalized and capped at 80 characters so hook output stays compact.
