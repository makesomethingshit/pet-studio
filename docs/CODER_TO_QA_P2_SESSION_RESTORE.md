# Coder To QA: P2 Last Widget Session Restore

## Scope

P2 adds last-session restore for registered Pet Studio widget projects. Direct `--kit` launches are unchanged.

## What Changed

- Registered project launches now use `pet-studio-widget/project-room-session.json`.
- Session snapshot stores `state`, `message`, `bubbleVisible`, `window.x/y/scale`, `updatedAt`, and `stateSource`.
- Startup priority is CLI overrides, fresh state bridge, session snapshot, then registry/window defaults.
- Stale bridge states older than 300000 ms are ignored for startup and refresh, so old `running` or `review` states should not pin the widget after reopening.
- `--no-restore-session` disables session restore for deterministic QA/debug launches.

## Suggested QA Commands

```powershell
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25 --no-restore-session
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_widget.py --project-id gakju-archive-demo --state idle --render-project-once runs\widget-session-restore-check.png
```

## Verification Points

- Move the registered widget, resize it, toggle the bubble, close it, and reopen it. The last window position, scale, state, and bubble visibility should restore.
- Repeat the launch with `--no-restore-session`. The previous session should be ignored.
- Write a fresh `project-room-state.json` `running` payload. It should override the session.
- Write an old `running`, `waiting`, `review`, `failed`, `blocked`, or `handoff` payload older than five minutes. Reopening should prefer session/default instead of the old bridge state.
- Confirm direct `--kit` launches do not create or restore `project-room-session.json`.

## Local-Only Note

`project-room-session.json` is runtime state and should stay ignored by git.
