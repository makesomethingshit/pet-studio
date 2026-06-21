# Codex Integration

Pet Studio's Codex integration is an optional local hook/file bridge. It is not
an official Codex dashboard API.

The bridge writes project state into local JSON files that the widget watches.
State messages appear as runtime speech bubbles near the main pet.

## Architecture Overview

```text
Codex lifecycle event
    -> .codex/hooks.json
    -> pet-studio-widget/codex_pet_hook.py
    -> pet-studio-widget/codex_state_adapter.py
    -> pet-studio-widget/set_project_state.py
    -> pet-studio-widget/project-room-state.json

Audit log:
    -> pet-studio-widget/project-room-hook-events.jsonl
```

`pet_studio_core` owns shared registry and state bridge primitives. Codex files
stay in the adapter layer.

## Install The Local Bridge

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_codex_integration.py --project-id gakju-archive-demo
```

The installer:

1. Installs the `$pet-studio` skill under `%USERPROFILE%\.codex\skills\pet-studio`
2. Writes project-local `.codex\hooks.json` entries for `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PreCompact`, and `Stop`
3. Optionally wraps the user-level Codex `notify` command in `.codex\config.toml` with `--install-notify`
4. Writes an active project pin when `--project-id` is provided

After installation, restart Codex or open `/hooks` to review and trust the new
commands. Pet Studio cannot detect that trust approval directly, so preflight
prints a reminder when hooks are installed.

## Hook Event To State Mapping

| Codex hook | Pet Studio event | Default message | Auto-reset |
| --- | --- | --- | --- |
| `SessionStart` | `idle` | `Pet Studio ready` | No |
| `UserPromptSubmit` | `running` | `Working: <prompt text>` | No |
| `PreToolUse` | `running` | `Using <tool name>` | No |
| `PostToolUse` | `running` | `Working` | No |
| `PreCompact` | `waiting` | `Compacting context` | No |
| `Stop` | `done` | `Done` | `idle` after 1.5s |
| `notify` | `done` | `Turn ended` | `idle` after 1.5s |

Widget state aliases:

- `done` maps to the hatch-pet `jumping` row
- `blocked` maps to `failed`
- `handoff` maps to `review`

## Manual Project State

Update a project state directly:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\set_pet_studio_state.py --project-id gakju-archive-demo --state running --message "building room kit"
```

Publish a Codex-style event:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_event_adapter.py --project-id gakju-archive-demo --event start --message "working"
```

Send the JSON payload shape used by the hook bridge:

```powershell
'{"event":"start","message":"working","projectId":"gakju-archive-demo"}' | .\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_event_adapter.py --event-json -
```

Run the demo state sequence for README GIF capture or manual QA:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_demo_states.py --project-id gakju-archive-demo --once --delay-seconds 2
```

Use `--dry-run` to inspect payloads without writing
`project-room-state.json`.

## Project ID Resolution

When no project id is provided, the adapter resolves project identity in this
order:

1. Explicit `projectId` argument or JSON payload field
2. Active project pin in `project-room-active.json`
3. Registry `workspacePaths` matching against `project-room-projects.json`

Pin an active project when several rooms share one workspace:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\set_active_pet_studio.py --project-id gakju-archive-demo --cwd .
```

## Inspect Hook Activity

Quick health check:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_hook_status.py
.\tools\pet_studio_python.cmd tools\pet_studio_hook_status.py --json
```

Checks performed:

- `hooks-installed`: lifecycle hooks registered in `.codex/hooks.json`
- `skill-installed`: `$pet-studio` skill found under the Codex skills folder
- `hook-activity`: recent `project-room-hook-events.jsonl` entries
- `state-bridge`: current `project-room-state.json`, including stale-state checks
- `active-project`: active project pin status
- `registry`: registered and enabled project status

Also inspect recent hook activity via preflight:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --skip-render --show-hook-log
```

## Troubleshooting

### Hooks not firing after installation

1. Run `install_pet_studio_codex_integration.py` again and check the reported `hooksFile` path
2. Open `/hooks` in Codex and trust the Pet Studio hook commands
3. Restart Codex after trust approval
4. Check `pet-studio-widget\project-room-hook-events.jsonl` for new entries

### Widget not updating after hook fires

1. Verify `project-room-state.json` is being written
2. Confirm the project id in the state file matches the registered project
3. Check that the widget is running with `--project-id <id>`, not `--kit`
4. Look for errors in `pet-studio-widget\project-room-widget.err.log`

### Wrong project receives state updates

1. Check whether `project-room-active.json` is pinning a different project
2. Verify `project-room-projects.json` workspace path matching
3. Use explicit `--project-id` in hook commands to bypass inference

### notify command not wrapped

1. Run installer with `--install-notify`
2. Check `.codex\config.toml` for the `notify = [ ... ]` line
3. Previous notify commands are preserved as passthrough
