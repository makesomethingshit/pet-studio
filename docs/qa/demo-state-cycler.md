# CODER_TO_QA: Demo State Cycler

## Summary

Added `tools/pet_studio_demo_states.py`, a small 0.2.0 demo helper that reuses the existing Pet Studio state bridge to cycle a registered project through README GIF and manual QA states.

## Scope

- No Codex hook installer changes.
- No new runtime state file.
- No Team Room, Project Hub, dashboard, orchestration, or simulation behavior.
- Writes only the existing `pet-studio-widget/project-room-state.json` unless `--state-file` is overridden.

## Commands

Continuous demo loop:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_demo_states.py --project-id gakju-archive-demo --delay-seconds 2
```

One pass:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_demo_states.py --project-id gakju-archive-demo --once --delay-seconds 2
```

Dry run:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_demo_states.py --project-id gakju-archive-demo --dry-run
```

## Sequence

```text
idle
running / Working...
waiting / Compacting context...
blocked / Needs input
review / Ready for review
done / Done
idle
```

The cycler does not add `resetAfterMs` to the `done` payload; the sequence itself writes the final `idle` after the configured delay. This prevents the widget from auto-resetting before the explicit final idle write.

## QA Focus

- With the widget running, `--once --delay-seconds 1` visibly updates bubble text and state rows.
- `--dry-run` prints JSON and does not write the state bridge.
- The final state after `--once --delay-seconds 0` is `idle`.
- `--delay` and `--delay-seconds` both work.
- Output remains JSON, not prose.
- Existing Codex hook installation behavior is unchanged.
