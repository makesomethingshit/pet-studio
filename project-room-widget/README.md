# Project Room Widget

Frameless desktop scene-host runtime for Project Room Kit packages.

The runtime keeps room, props, main pet, and helper pets as separate Canvas entities inside one transparent host window. It is not a single precomposited widget image.

## Run Gakju Archive Room

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe D:\pet-studio\project-room-widget\project_room_widget.py --kit D:\pet-studio\runs\gakju-archive-room-skill-run\kit --scale 1.25 --x 1200 --y 620
```

## Run A Registered Project

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe D:\pet-studio\project-room-widget\project_room_widget.py --project-id gakju-archive-demo --scale 1.25 --x 1200 --y 620
```

Registered projects live in `project-room-projects.json`. The widget also supports:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe D:\pet-studio\project-room-widget\project_room_widget.py --list-projects
```

Controls:

- Drag a prop or pet with the left mouse button.
- Drag locked room/background or empty space to move the host window.
- Double-click to cycle animation state.
- Right-click or Escape to close.

Registered projects persist moved entity anchors in `project-room-layouts.json`. Direct `--kit` runs allow session-only movement and do not write project layout overrides.

## State Bridge

Use `project-room-state.json` as the first file-based bridge from external project status to widget state:

```json
{
  "projectId": "gakju-archive-demo",
  "state": "running",
  "message": "working on it",
  "updatedAt": "2026-06-12T00:00:00Z"
}
```

Supported external states are `idle`, `running`, `waiting`, `review`, `failed`, `done`, `blocked`, and `handoff`. The widget maps `done` to the hatch-pet `jumping` row, `blocked` to `failed`, and `handoff` to `review`.

Write the bridge file with:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe D:\pet-studio\project-room-widget\set_project_state.py --project-id gakju-archive-demo --state running --message "building room kit"
```

Helper pets appear in `review`/`handoff` scenes and in the `failed` scene used by `blocked`, when the selected kit has a helper layer. Kits without helper assets continue rendering the main pet only.

For Codex-like task events, use the adapter instead of writing bridge states directly:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe D:\pet-studio\project-room-widget\codex_state_adapter.py --event start --message "working"
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe D:\pet-studio\project-room-widget\codex_state_adapter.py --project-id gakju-archive-demo --event start --message "implementing adapter"
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe D:\pet-studio\project-room-widget\codex_state_adapter.py --project-id gakju-archive-demo --event review --message "ready for review"
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe D:\pet-studio\project-room-widget\codex_state_adapter.py --project-id gakju-archive-demo --event block --message "needs input"
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe D:\pet-studio\project-room-widget\codex_state_adapter.py --project-id gakju-archive-demo --event done --message "finished"
```

The adapter maps `start` to `running`, `wait` to `waiting`, `review` to `review`, `block` to `blocked`, `fail` to `failed`, `done` to `done`, and `idle` to `idle`. When `--project-id` is omitted, the adapter infers the project from the current workspace using registry `workspacePaths`; pass `--project-id` to override inference.

## Render Test

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe D:\pet-studio\project-room-widget\project_room_widget.py --kit D:\pet-studio\runs\gakju-archive-room-skill-run\kit --render-once D:\pet-studio\runs\widget-render-test.png
```

Render a registered project once:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe D:\pet-studio\project-room-widget\project_room_widget.py --project-id gakju-archive-demo --render-project-once D:\pet-studio\runs\widget-render-test.png
```

Use a custom layout file:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe D:\pet-studio\project-room-widget\project_room_widget.py --project-id gakju-archive-demo --layout-file D:\pet-studio\project-room-widget\project-room-layouts.json
```
