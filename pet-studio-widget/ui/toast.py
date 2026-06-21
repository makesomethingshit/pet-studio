"""Toast overlay for Project Room Widget.

Provides on-screen error/warn/info messages rendered on the widget canvas.
"""

from __future__ import annotations

import tkinter as tk

STATUS_BAR_HEIGHT = 20
STATUS_BAR_FONT = "Segoe UI"

TOAST_COLORS = {
    "error": "#e07b70",
    "warn": "#e1b66f",
    "info": "#8fd7c2",
}

TOAST_BG = {
    "error": "#44221f",
    "warn": "#3d3120",
    "info": "#20352d",
}


def clear_toast(widget) -> None:
    """Remove all toast canvas items and cancel pending auto-hide."""
    for item in widget._toast_items:
        widget.canvas.delete(item)
    widget._toast_items.clear()
    if widget._toast_job_id is not None:
        try:
            widget.root.after_cancel(widget._toast_job_id)
        except tk.TclError:
            pass
        widget._toast_job_id = None
    widget._toast_message = None
    widget._toast_level = None
    # Restore status bar visibility
    for item in widget._status_bar_items:
        widget.canvas.itemconfigure(item, state=tk.NORMAL)


def show_toast(widget, message: str, level: str = "error", duration_ms: int = 3000) -> None:
    """Show a toast message on the widget canvas.

    Args:
        widget: ProjectRoomWidget instance.
        message: Text to display.
        level: "error", "warn", or "info".
        duration_ms: Auto-hide delay in milliseconds.
    """
    widget._toast_message = message
    widget._toast_level = level
    # Hide status bar text while toast is active
    for item in widget._status_bar_items:
        widget.canvas.itemconfigure(item, state=tk.HIDDEN)
    _render_toast(widget)
    if widget._toast_job_id is not None:
        try:
            widget.root.after_cancel(widget._toast_job_id)
        except tk.TclError:
            pass
    widget._toast_job_id = widget.root.after(duration_ms, lambda: clear_toast(widget))


def _render_toast(widget) -> None:
    """Render the current toast message on the canvas."""
    # Remove only toast items (not status bar)
    for item in widget._toast_items:
        widget.canvas.delete(item)
    widget._toast_items.clear()
    if not widget._toast_message:
        return
    cw = int(widget.canvas.cget("width"))
    room_h = widget._canvas_height
    sb_h = STATUS_BAR_HEIGHT
    fg = TOAST_COLORS.get(widget._toast_level, TOAST_COLORS["error"])
    font_size = max(8, int(round(9 * widget.scale)))
    text_item = widget.canvas.create_text(
        cw // 2,
        room_h + sb_h // 2,
        text=widget._toast_message,
        fill=fg,
        font=(STATUS_BAR_FONT, font_size, "bold"),
        anchor=tk.CENTER,
        tags=("toast",),
    )
    widget._toast_items.append(text_item)
    widget.canvas.tag_raise(text_item)
