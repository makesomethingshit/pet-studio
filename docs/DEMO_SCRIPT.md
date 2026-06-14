# Pet Studio Demo Script

Use this for a 10-15 second GitHub README GIF, release post, or X/Twitter clip.

This is the current recommended demo path until a real GIF is checked into the README.

## Goal

Show the idea in one sentence:

> Every Codex project gets its own tiny desktop room.

## 10-15 Second Shot List

1. Start on the desktop with the Pet Studio widget closed.
2. Run or double-click the launcher for the sample project room.
3. The tiny room appears: background, desk props, main pet, and helper area.
4. Trigger a Codex-style event: `Working...` or `Using shell...`.
5. The speech bubble changes while the room stays alive.
6. Trigger `blocked`, `review`, or `done`.
7. The room changes state and the helper pet appears for collaboration/problem-solving moments.
8. End on the room with this caption:

```text
Every project gets a room.
```

## Release Capture Checklist

- Use the included sample project room unless a cleaner generated room is available.
- Keep private project names, paths, prompts, tokens, and chat content out of frame.
- Capture a real state change, not only a static room.
- Show one speech bubble update such as `Using shell...`.
- Show one collaboration/problem-solving state such as `blocked` or `review`.
- End on a readable final frame for at least two seconds.

## Suggested Commands

Launch the included room:

```powershell
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25
```

Send state changes:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_event_adapter.py --project-id gakju-archive-demo --event start --message "Working..."
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_event_adapter.py --project-id gakju-archive-demo --event start --message "Using shell..."
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_event_adapter.py --project-id gakju-archive-demo --event block --message "Needs input"
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_event_adapter.py --project-id gakju-archive-demo --event review --message "Ready for review"
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_event_adapter.py --project-id gakju-archive-demo --event done --message "Done"
```

Real Codex `PreToolUse` hooks produce tool-specific wording such as `Using shell...` after the local hook bridge is installed and trusted.

## Visual Direction

- Keep the desktop clean.
- Place the widget near a corner so it feels like a companion, not a full app.
- Use one clear speech bubble at a time.
- Keep the final frame on screen long enough to read.
- If recording a terminal, keep it secondary. The room is the point.

## Optional Caption Copy

```text
Instead of watching logs, watch your Codex project room react.
```

```text
Local-first agent dashboard. Tiny pet room energy.
```
