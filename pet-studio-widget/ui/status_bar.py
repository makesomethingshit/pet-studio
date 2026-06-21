"""Status bar renderer for Project Room Widget."""

from __future__ import annotations

import tkinter as tk

STATUS_BAR_HEIGHT = 20
STATUS_BAR_BG = "#241f18"
STATUS_BAR_FG = "#f7ead7"
STATUS_BAR_FONT = "Segoe UI"

STATUS_LABELS = {
    "idle": "idle",
    "running": "running",
    "waiting": "waiting",
    "review": "review",
    "failed": "failed",
    "blocked": "blocked",
    "handoff": "handoff",
    "jumping": "done",
    "done": "done",
}

STATE_BG = {
    "running": "#20352d",
    "done": "#20352d",
    "failed": "#44221f",
    "blocked": "#3d3120",
    "review": "#3d3120",
    "waiting": "#30281f",
    "handoff": "#30281f",
    "jumping": "#20352d",
}

STATE_FG = {
    "running": "#8fd7c2",
    "done": "#9dd6a5",
    "failed": "#e07b70",
    "blocked": "#e1b66f",
    "review": "#e1b66f",
    "waiting": "#d7bfa3",
    "handoff": "#d7bfa3",
    "jumping": "#9dd6a5",
}

TOAST_BG = {
    "error": "#44221f",
    "warn": "#3d3120",
    "info": "#20352d",
}


def _roost_status_icon(widget) -> str:
    """Return roost status emoji icon based on project state."""
    try:
        from roost.state import TeamState

        ts = TeamState()
        status = ts.roost_status
        return {"active": "\U0001f7e2", "idle": "\u26aa", "error": "\U0001f534"}.get(status, "\u26aa")
    except Exception:
        return ""


def draw_status_bar(widget) -> None:
    """Draw the status bar at the bottom of the widget canvas."""
    for item in widget._status_bar_items:
        widget.canvas.delete(item)
    widget._status_bar_items.clear()

    cw = int(widget.canvas.cget("width"))
    sb_h = STATUS_BAR_HEIGHT
    room_h = widget._canvas_height

    if widget._toast_message and widget._toast_level:
        bg = TOAST_BG.get(widget._toast_level, STATUS_BAR_BG)
    else:
        bg = STATE_BG.get(widget.state, STATUS_BAR_BG)
    rect = widget.canvas.create_rectangle(0, room_h, cw, room_h + sb_h, fill=bg, outline="")
    widget._status_bar_items.append(rect)

    if widget._toast_message:
        return

    if widget.project_id:
        name = widget._project_display_name or widget.project_id
        font_size = max(8, int(round(9 * widget.scale)))
        fg = STATE_FG.get(widget.state, STATUS_BAR_FG)
        name_item = widget.canvas.create_text(
            6,
            room_h + sb_h // 2,
            text=name,
            fill=fg,
            font=(STATUS_BAR_FONT, font_size, "bold"),
            anchor=tk.W,
            tags=("statusbar",),
        )
        widget._status_bar_items.append(name_item)

    state_text = STATUS_LABELS.get(widget.state, widget.state)
    roost_icon = _roost_status_icon(widget)
    display = f"[{state_text}] {roost_icon}" if roost_icon else f"[{state_text}]"
    font_size = max(8, int(round(9 * widget.scale)))
    fg = STATE_FG.get(widget.state, STATUS_BAR_FG)
    state_item = widget.canvas.create_text(
        cw - 6,
        room_h + sb_h // 2,
        text=display,
        fill=fg,
        font=(STATUS_BAR_FONT, font_size),
        anchor=tk.E,
        tags=("statusbar",),
    )
    widget._status_bar_items.append(state_item)
