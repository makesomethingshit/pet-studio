# Pet Studio Widget

Frameless desktop scene-host runtime for Pet Studio kits.

The widget keeps room, props, main pet, helper pets, and speech bubbles as separate Canvas entities inside one transparent host window. It is not a single precomposited image.

## Run A Sample

Launch the checked-in Gakju sample:

```powershell
.\tools\pet_studio_python.cmd project-room-widget\pet_studio_widget.py --kit runs\gakju-imagegen-room-v1\kit --scale 1.25
```

Launch a registered project:

```powershell
.\tools\pet_studio_python.cmd project-room-widget\pet_studio_widget.py --project-id gakju-archive-demo --scale 1.25
```

List registered projects:

```powershell
.\tools\pet_studio_python.cmd project-room-widget\pet_studio_widget.py --list-projects
```

Registered projects live in the v1 compatibility registry file `project-room-projects.json`.

## Controls

- Drag a prop or pet with the left mouse button.
- Drag locked room/background or empty space to move the host window.
- Double-click to cycle animation state.
- Right-click to open the context menu.
- Use the context menu to cycle state, reset a registered project layout, adjust a selected entity's layer order, resize the widget, toggle the speech bubble, or close.
- Press `Ctrl` + `+` / `Ctrl` + `-` to resize the widget, or `Ctrl` + `0` to reset size.
- Press `Escape` to close.

Registered projects persist moved entity anchors and layer-order overrides in `project-room-layouts.json`, and host window position/scale in `project-room-window.json`. Those filenames remain the v1 compatibility storage contract. Direct `--kit` runs allow session-only movement and do not write layout or window overrides.

When a registered project is launched with `--project-id`, the widget also writes `project-room-active.json` so Codex event adapters can resolve the currently selected Pet Studio project. Saved entity anchors outside the source room canvas are ignored on load and new drag positions are clamped to the canvas.

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

Supported external states are `idle`, `running`, `waiting`, `review`, `failed`, `done`, `blocked`, and `handoff`. The widget maps `done` to the hatch-pet `jumping` row, `blocked` to `failed`, and `handoff` to `review`.

If the state file includes `message`, the scene host shows that message as a runtime-only speech bubble near the main pet. Messages are whitespace-normalized and capped at 80 characters. Without a message, the host uses short state defaults such as `Working`, `Waiting`, `Reviewing`, `Need input`, or `Done`.

Bubble styling follows the selected Pet Studio kit. The runtime resolves style in this order: `project-room.json` `bubbleStyle`, main pet `spritesheet.asset.json` `bubbleStyle`, automatic color extraction from the main pet spritesheet, then the default compact style.

Write the bridge file with:

```powershell
.\tools\pet_studio_python.cmd project-room-widget\set_pet_studio_state.py --project-id gakju-archive-demo --state running --message "building room kit"
```

For Codex-like task events, use the adapter instead of writing bridge states directly:

```powershell
.\tools\pet_studio_python.cmd project-room-widget\pet_studio_event_adapter.py --event start --message "working"
.\tools\pet_studio_python.cmd project-room-widget\pet_studio_event_adapter.py --project-id gakju-archive-demo --event review --message "ready for review"
.\tools\pet_studio_python.cmd project-room-widget\pet_studio_event_adapter.py --project-id gakju-archive-demo --event block --message "needs input"
.\tools\pet_studio_python.cmd project-room-widget\pet_studio_event_adapter.py --project-id gakju-archive-demo --event done --message "finished"
```

When `--project-id` is omitted, the adapter resolves project identity in this order:

1. Explicit `projectId`
2. Active project pin
3. Registry `workspacePaths`

Pin an active project when multiple room projects share a workspace:

```powershell
.\tools\pet_studio_python.cmd project-room-widget\set_active_pet_studio.py --project-id gakju-archive-demo --cwd .
```

Codex host hooks can call the same adapter with a JSON payload:

```powershell
'{"event":"start","message":"working","projectId":"gakju-archive-demo"}' | .\tools\pet_studio_python.cmd project-room-widget\pet_studio_event_adapter.py --event-json -
```

For local Codex Desktop bubble integration, install the Pet Studio Codex bridge:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_codex_integration.py
```

That installer installs the skill as `$pet-studio` and writes project-local `.codex\hooks.json` lifecycle hooks. Pass `--project-id <id>` when you also want to write an active project pin during installation. Pass `--install-notify` only if you intentionally want to wrap the user-level Codex `notify` command.

The installed hooks cover `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PreCompact`, and `Stop`. Restart Codex or open `/hooks` to review and trust the command hooks if Codex asks.

## Render Checks

Render a direct kit:

```powershell
.\tools\pet_studio_python.cmd project-room-widget\pet_studio_widget.py --kit runs\gakju-imagegen-room-v1\kit --render-once runs\widget-render-test.png
```

Render a registered project:

```powershell
.\tools\pet_studio_python.cmd project-room-widget\pet_studio_widget.py --project-id gakju-archive-demo --render-project-once runs\widget-render-test.png
```

Use custom persistence files:

```powershell
.\tools\pet_studio_python.cmd project-room-widget\pet_studio_widget.py --project-id gakju-archive-demo --layout-file project-room-widget\project-room-layouts.json
.\tools\pet_studio_python.cmd project-room-widget\pet_studio_widget.py --project-id gakju-archive-demo --window-file project-room-widget\project-room-window.json
```
