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

Detached launch output is written to ignored local files under `pet-studio-widget\project-room-widget.log` and `pet-studio-widget\project-room-widget.err.log`.

## Controls

- Drag a prop or pet with the left mouse button.
- Drag locked room/background or empty space to move the host window.
- Double-click to cycle animation state.
- Right-click to open the context menu.
- Use the context menu to cycle state, reset a registered project layout, adjust a selected entity's layer order, resize the widget, toggle the speech bubble, or close.
- Press `Ctrl` + `+` / `Ctrl` + `-` to resize the widget, or `Ctrl` + `0` to reset size.
- Press `Escape` to close.

## Session Restore

Registered project launches restore the last visible session from `project-room-session.json` by default. The session snapshot stores the last widget state, speech bubble visibility, message, window position, scale, update time, and whether the state came from the bridge or a manual widget action. Direct `--kit` launches do not use session restore.

Startup priority is:

1. Explicit CLI values such as `--state`, `--x`, `--y`, and `--scale`
2. Fresh `project-room-state.json` bridge payloads
3. `project-room-session.json`
4. Registry defaults and `project-room-window.json`

The bridge is considered stale after 300000 ms by default for active working states such as `running`, `waiting`, `review`, `failed`, `blocked`, and `handoff`. Override the threshold with `--state-stale-after-ms`.

Use `--no-restore-session` for deterministic QA, render checks, or debugging:

```powershell
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25 --no-restore-session
```

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

## Codex Integration

For hook installation, event mapping, troubleshooting, and the full Codex integration guide, see `docs/CODEX_INTEGRATION.md`.

For the architecture boundary between Core and Adapter layers, see `docs/ADAPTER_BOUNDARY.md`.
