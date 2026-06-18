# Pet Studio Demo Script

Use this for a 10-15 second GitHub README GIF, release post, or X/Twitter clip.

## Goal

Show the idea in one sentence:

> Every project gets its own tiny desktop room with a pet team.

## 10-15 Second Shot List

1. Start on the desktop with the Pet Studio widget closed.
2. Run or double-click the launcher for the sample project room.
3. The tiny room appears: background, props, main pet, and speech bubble.
4. Trigger a state change: `Working...` or `Using shell...`.
5. The speech bubble changes while the room stays alive.
6. Trigger `blocked`, `review`, or `done`.
7. The room changes state; the helper pet appears for collaboration moments.
8. Right-click → open Team Room Panel → show staff cards.
9. End on the room with this caption:

```text
Every project gets a room.
```

## Suggested Commands

Launch the included room:

```powershell
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25
```

Cycle demo state changes from the widget context menu:

```text
Right-click the Pet Studio Widget → Cycle state
```

The menu action runs the 7-step demo cycle:

```text
idle
running / Working...
waiting / Compacting context...
blocked / Needs input
review / Ready for review
done / Done
idle
```

Scripted capture:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_demo_states.py --project-id gakju-archive-demo --delay-seconds 2
```

Other options:

```powershell
# One pass
.\tools\pet_studio_python.cmd tools\pet_studio_demo_states.py --project-id gakju-archive-demo --once --delay-seconds 2

# Dry run (preview payloads)
.\tools\pet_studio_python.cmd tools\pet_studio_demo_states.py --project-id gakju-archive-demo --dry-run
```

Real Codex `PreToolUse` hooks produce tool-specific wording such as `Using shell...` after the local hook bridge is installed and trusted.

## Visual Direction

- Keep the desktop clean.
- Place the widget near a corner so it feels like a companion, not a full app.
- Use one clear speech bubble at a time.
- Keep the final frame on screen long enough to read.
- If recording a terminal, keep it secondary. The room is the point.
- Step 8 (Team Panel) is new in v0.6 — show staff cards if possible.

## Optional Caption Text

```text
Instead of watching logs, watch your project room react.
```

```text
Local-first AI workroom. Tiny pet team energy.
```
