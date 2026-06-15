# Codex Integration

Pet Studio's Codex integration is a local hook/file bridge. It is not an official Codex dashboard API.

The bridge writes project state into local JSON files that the widget watches. State messages appear as runtime speech bubbles near the main pet.

## Architecture Overview

```
Codex CLI lifecycle events
        │
        ▼
  .codex/hooks.json          <-- hook declarations (SessionStart, UserPromptSubmit, etc.)
        │
        ▼
  codex_pet_hook.py          <-- entry point per hook; reads stdin payload, resolves project
        │
        ├──► codex_state_adapter.py   <-- event→state translation, project ID resolution
        │         │
        │         └──► set_project_state.py   <-- writes project-room-state.json
        │
        └──► project-room-hook-events.jsonl   <-- local audit log (git-ignored)
```

## Install The Local Bridge

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_codex_integration.py --project-id gakju-archive-demo
```

The installer does four things:
1. Installs the skill as `$pet-studio` under `%USERPROFILE%\.codex\skills\pet-studio`
2. Writes project-local `.codex\hooks.json` entries for `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PreCompact`, and `Stop`
3. Optionally wraps the user-level Codex `notify` command in `.codex\config.toml` (only with `--install-notify`)
4. Writes an active project pin when `--project-id` is provided

After installation, restart Codex or open `/hooks` to review and trust the new command hooks when Codex asks. Pet Studio cannot detect that trust approval directly, so the preflight prints a reminder when hooks are installed.

## Hook Event → State Mapping

| Codex Hook | Pet Studio Event | Default Message | Auto-reset |
| --- | --- | --- | --- |
| `SessionStart` | `idle` | "Pet Studio ready" | — |
| `UserPromptSubmit` | `running` | "Working: <prompt text>" | — |
| `PreToolUse` | `running` | "Using <tool name>" | — |
| `PostToolUse` | `running` | "Working" | — |
| `PreCompact` | `waiting` | "Compacting context" | — |
| `Stop` | `done` | "Done" | → `idle` after 1.5s |
| `notify` | `done` | "Turn ended" | → `idle` after 1.5s |

State aliases used by the widget: `done` → `jumping` (hatch-pet row), `blocked` → `failed`, `handoff` → `review`.

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

## Project ID Resolution

When no project id is provided, the adapter resolves project identity in this order:

1. Explicit `projectId` argument or JSON payload field
2. Active project pin (`project-room-active.json`)
3. Registry `workspacePaths` matching against `project-room-projects.json`

Pin an active project when several rooms share one workspace:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\set_active_pet_studio.py --project-id gakju-archive-demo --cwd .
```

## Hook Bubble Policy

- `UserPromptSubmit` shows `Working: ...`
- `PreToolUse` shows `Using <tool>`
- `PostToolUse` stays in `Working`, not `Ready for review`
- `PreCompact` shows `Compacting context`
- `Stop` shows `Done` briefly, then the widget falls back to idle
- `blocked` and explicit review/handoff events are the normal paths to review-style messaging

Long state messages are whitespace-normalized and capped at 80 characters so hook output stays compact.

## Inspect Hook Activity

Quick health check — verifies hooks installed, reachable, events flowing, state freshness:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_hook_status.py
```

JSON output for machine parsing:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_hook_status.py --json
```

Checks performed:
- **hooks-installed** — all 6 lifecycle hooks registered in `.codex/hooks.json`
- **skill-installed** — `$pet-studio` skill found at `%USERPROFILE%\.codex\skills\pet-studio`
- **hook-reachable** — `codex_pet_hook.py` exists and Python is available
- **hook-activity** — recent events from `project-room-hook-events.jsonl` (last 20), with per-hook counts and staleness detection
- **state-bridge** — current `project-room-state.json` state, with stale-state detection (>5min for active states)
- **active-project** — active project pin status
- **registry** — project registered and enabled
- **widget-check** — Python/Tkinter runtime reachable

Also inspect raw hook event log:

```powershell
type pet-studio-widget\project-room-hook-events.jsonl
```

Each line is a JSON object with `timestamp`, `hook`, `event`, `projectId`, `state`, `message`, and `payloadKeys`.

Also inspect recent hook activity via preflight:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --skip-render --show-hook-log
```

## Troubleshooting

### Hooks not firing after installation
1. Run `install_pet_studio_codex_integration.py` again — check output for `hooksFile` path
2. Open `/hooks` in Codex and verify trust approval for each Pet Studio hook command
3. Restart Codex after trust approval
4. Check `pet-studio-widget\project-room-hook-events.jsonl` for new entries

### Widget not updating after hook fires
1. Verify `project-room-state.json` is being written: check file timestamp
2. Confirm the project id in the state file matches the registered project
3. Check that the widget is running with `--project-id <id>` (not `--kit`)
4. Look for errors in `pet-studio-widget\project-room-widget.err.log`

### Wrong project receives state updates
1. Check `project-room-active.json` — may be pinning a different project
2. Verify `project-room-projects.json` workspace path matching
3. Use explicit `--project-id` in hook commands to bypass inference

### notify command not wrapped
1. Run installer with `--install-notify` flag
2. Check `.codex\config.toml` for `notify = [ ... ]` line
3. Previous notify commands are preserved as passthrough (Pet Studio wraps, does not replace)

### Hook command timeout
Default hook timeout is 30 seconds. If `codex_pet_hook.py` takes longer, check:
- Python path resolution (use full path via `sys.executable`)
- Registry file locks (close editors that have `project-room-projects.json` open)
