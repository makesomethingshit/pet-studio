"""Status bar renderer for Project Room Widget.

Draws the bottom status bar with project name, state label, and roost icon.
"""

from __future__ import annotations

import tkinter as tk

STATUS_BAR_HEIGHT = 20
STATUS_BAR_BG = "#1e1e2e"
STATUS_BAR_FG = "#cdd6f4"
STATUS_BAR_FONT = "Segoe UI"

STATUS_LABELS = {
    "idle": "대기",
    "running": "작업중",
    "waiting": "대기중",
    "review": "리뷰",
    "failed": "실패",
    "blocked": "차단됨",
    "handoff": "전환",
    "jumping": "완료",
    "done": "완료",
}

STATE_BG = {
    "running": "#1a2e1a",
    "done": "#1a2e1a",
    "failed": "#2e1a1a",
    "blocked": "#2e1a1a",
    "review": "#2e2a1a",
    "waiting": "#1a1e2e",
    "handoff": "#1a1e2e",
    "jumping": "#1a2e1a",
}

STATE_FG = {
    "running": "#a6e3a1",
    "done": "#a6e3a1",
    "failed": "#f38ba8",
    "blocked": "#f38ba8",
    "review": "#f9e2af",
    "waiting": "#89b4fa",
    "handoff": "#89b4fa",
    "jumping": "#a6e3a1",
}

TOAST_BG = {
    "error": "#4c1c24",
    "warn": "#4c4420",
    "info": "#1c2e4c",
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

    # Background (use toast bg color if toast is active)
    bg = STATUS_BAR_BG
    if widget._toast_message and widget._toast_level:
        bg = TOAST_BG.get(widget._toast_level, STATUS_BAR_BG)
    else:
        bg = STATE_BG.get(widget.state, STATUS_BAR_BG)
    rect = widget.canvas.create_rectangle(0, room_h, cw, room_h + sb_h, fill=bg, outline="")
    widget._status_bar_items.append(rect)

    # Skip text when toast is active (toast renders in same area)
    if widget._toast_message:
        return

    # Project name (only when project_id is set)
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

    # State label + roost icon (always visible)
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
