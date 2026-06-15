# Pet Studio Widget

Frameless desktop scene-host runtime for Pet Studio kits.

The widget keeps room, props, main pet, helper pets, and speech bubbles as separate Canvas entities inside one transparent host window. It is not a single precomposited image.

## Run A Sample

Launch the checked-in Gakju sample:

```powershell
.\tools\pet_studio_widget.cmd --kit runs\gakju-imagegen-room-v1\kit --scale 1.25
```

Launch a registered project:

```powershell
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25
```

List registered projects:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_widget.py --list-projects
```

Registered projects live in the v1 compatibility registry file `project-room-projects.json`.

Use `tools\pet_studio_widget.cmd` for normal widget launches. It starts `pet_studio_widget.py` through `pythonw` when available, so the command prompt does not stay attached. Normal launches are single-instance: if a `Pet Studio Widget` window already exists, the launcher brings it forward instead of starting another copy.

For debugging, pass `--foreground` so output and errors stay in the current terminal:

```powershell
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25 --foreground
```

Detached launch output is written to ignored local files under `pet-studio-widget\project-room-widget.log` and `pet-studio-widget\project-room-widget.err.log`. Use `tools\pet_studio_python.cmd` for listing projects, rendering files, and tests.

Run the public preflight when checking a fresh clone or release candidate:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --show-hook-log
```

## Controls

- Drag a prop or pet with the left mouse button.
- Drag locked room/background or empty space to move the host window.
- Double-click to cycle animation state.
- Right-click to open the context menu.
- Use the context menu to cycle state, reset a registered project layout, adjust a selected entity's layer order, resize the widget, toggle the speech bubble, or close.
- Press `Ctrl` + `+` / `Ctrl` + `-` to resize the widget, or `Ctrl` + `0` to reset size.
- Press `Escape` to close.

Registered projects persist moved entity anchors and layer-order overrides in `project-room-layouts.json`, and host window position/scale in `project-room-window.json`. Those filenames remain the v1 compatibility storage contract. Direct `--kit` runs allow temporary movement and do not write layout, window, or session overrides.

When a registered project is launched with `--project-id`, the widget also writes `project-room-active.json` so Codex event adapters can resolve the currently selected Pet Studio project. Saved entity anchors outside the source room canvas are ignored on load and new drag positions are clamped to the canvas.

## Session Restore

Registered project launches restore the last visible session from `project-room-session.json` by default. The session snapshot stores the last widget state, speech bubble visibility, message, window position, scale, update time, and whether the state came from the bridge or a manual widget action. Direct `--kit` launches do not use session restore.

Startup priority is:

1. Explicit CLI values such as `--state`, `--x`, `--y`, and `--scale`
2. Fresh `project-room-state.json` bridge payloads
3. `project-room-session.json`
4. Registry defaults and `project-room-window.json`

The bridge is considered stale after 300000 ms by default for active working states such as `running`, `waiting`, `review`, `failed`, `blocked`, and `handoff`. This prevents an old Codex hook state from reopening the widget in a stale working/review state. Override the threshold with `--state-stale-after-ms`.

Use `--no-restore-session` for deterministic QA, render checks, or debugging:

```powershell
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25 --no-restore-session
```

## State Bridge

Use `project-room-state.json` as the v1 file-based bridge from external task status to widget state:

```json
{
  "projectId": "gakju-archive-demo",
  "state": "running",
  "message": "working on it",
  "updatedAt": "2026-06-12T00:00:00Z"
}
```

Supported external states are `idle`, `running`, `waiting`, `review`, `failed`, `done`, `blocked`, and `handoff`. The widget maps `done` to the hatch-pet `jumping` row, `blocked` to `failed`, and `handoff` to `review`. A state payload may include `resetAfterMs` and `resetToState`; after that delay the widget displays the reset target without rewriting the state file.

If the state file includes `message`, the scene host shows that message as a runtime-only speech bubble near the main pet. Messages are whitespace-normalized and capped at 80 characters. Without a message, the host uses short state defaults such as `Working`, `Waiting`, `Reviewing`, `Need input`, or `Done`.

Bubble styling follows the selected Pet Studio kit. The runtime resolves style in this order: `project-room.json` `bubbleStyle`, main pet `spritesheet.asset.json` `bubbleStyle`, automatic color extraction from the main pet spritesheet, then the default compact style.

Bubble text prefers installed Noto Sans families first, including Noto Sans CJK, Arabic, Hebrew, Indic, Thai, and emoji variants when the message contains those scripts. If Noto fonts are not installed, the widget falls back to common platform fonts such as Segoe UI, Malgun Gothic, Microsoft YaHei UI, Yu Gothic UI, Nirmala UI, Apple SD Gothic Neo, PingFang SC, DejaVu Sans, and TkDefaultFont.

Full bidirectional text layout is not implemented yet. CJK and Indic messages can render when matching fonts are available, but Arabic and Hebrew bubble text should be treated as a current limitation until a bidi-aware text layout path is added.

Write the bridge file with:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\set_pet_studio_state.py --project-id gakju-archive-demo --state running --message "building room kit"
```

For Codex-like task events, use the adapter instead of writing bridge states directly:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_event_adapter.py --event start --message "working"
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_event_adapter.py --project-id gakju-archive-demo --event review --message "ready for review"
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_event_adapter.py --project-id gakju-archive-demo --event block --message "needs input"
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_event_adapter.py --project-id gakju-archive-demo --event done --message "finished"
```

When `--project-id` is omitted, the adapter resolves project identity in this order:

1. Explicit `projectId`
2. Active project pin
3. Registry `workspacePaths`

Pin an active project when multiple room projects share a workspace:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\set_active_pet_studio.py --project-id gakju-archive-demo --cwd .
```

Codex host hooks can call the same adapter with a JSON payload:

```powershell
'{"event":"start","message":"working","projectId":"gakju-archive-demo"}' | .\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_event_adapter.py --event-json -
```

For local Codex Desktop bubble integration, install the Pet Studio Codex bridge:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_codex_integration.py
```

That installer installs the skill as `$pet-studio` and writes project-local `.codex\hooks.json` lifecycle hooks. Pass `--project-id <id>` when you also want to write an active project pin during installation. Pass `--install-notify` only if you intentionally want to wrap the user-level Codex `notify` command.

The installed hooks cover `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PreCompact`, and `Stop`. Restart Codex or open `/hooks` to review and trust the command hooks if Codex asks.

Hook events are also appended to the local ignored file `project-room-hook-events.jsonl`. Use it to confirm that `UserPromptSubmit`, tool use, and `Stop` are reaching the widget bridge.

Default hook messages intentionally avoid overstating progress:

- `UserPromptSubmit` sets `running` with `Working: ...`.
- `PreToolUse` keeps `running` and names the tool.
- `PostToolUse` stays `running` with `Working`.
- `Stop` writes `done` plus idle reset metadata.
- Review wording is reserved for explicit review/handoff states, not every completed tool call.

## Render Checks

Render a direct kit:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_widget.py --kit runs\gakju-imagegen-room-v1\kit --render-once runs\widget-render-test.png
```

Render a registered project:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_widget.py --project-id gakju-archive-demo --render-project-once runs\widget-render-test.png
```

Render commands ignore session restore. Add `--state idle` or another explicit state when the output must be independent of any bridge file.

Use custom persistence files:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_widget.py --project-id gakju-archive-demo --layout-file pet-studio-widget\project-room-layouts.json
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_widget.py --project-id gakju-archive-demo --window-file pet-studio-widget\project-room-window.json
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_widget.py --project-id gakju-archive-demo --session-file pet-studio-widget\project-room-session.json
```
