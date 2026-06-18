"""Team Room popup for Project Room Widget.

Shows pending approvals, staff status, and roost queue.
Fixed: proper positioning, role badges, queue action buttons.
"""

from __future__ import annotations

import tkinter as tk
from typing import Any

ROLE_BADGE: dict[str, str] = {
    "scout": "🔍",
    "coordinator": "📋",
    "lead": "⭐",
    "worker": "🔧",
}
ROLE_LABEL: dict[str, str] = {
    "scout": "Scout",
    "coordinator": "Coordinator",
    "lead": "Lead",
    "worker": "Worker",
}
STATUS_COLORS = {
    "idle": "#888888",
    "running": "#22c55e",
    "review": "#f59e0b",
    "blocked": "#ef4444",
    "done": "#3b82f6",
}


def show_team_room(widget) -> None:
    """Show Team Room popup anchored to widget edge."""
    if widget._team_state is None:
        return
    try:
        pending = widget._team_state.get_pending_approvals()
        employees = widget._team_state.get_employees()
        queue = widget._team_state.get_roost_queue()

        # Close existing if open
        if widget._team_room_panel is not None:
            try:
                widget._team_room_panel.destroy()
            except tk.TclError:
                pass

        popup = tk.Toplevel(widget.root)
        popup.title("Team Room")
        popup.resizable(False, False)
        popup.attributes("-topmost", True)  # 위젯보다 위에 표시
        widget._team_room_panel = popup

        def close_team_room() -> None:
            try:
                popup.destroy()
            finally:
                if widget._team_room_panel is popup:
                    widget._team_room_panel = None

        popup.protocol("WM_DELETE_WINDOW", close_team_room)

        frame = tk.Frame(popup, padx=12, pady=8)
        frame.pack(fill="both", expand=True)

        # --- Approvals ---
        tk.Label(frame, text="Approvals", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        if pending:
            for a in pending[:5]:
                _approval_row(frame, widget, a, popup)
        else:
            tk.Label(frame, text="  No pending approvals", font=("Segoe UI", 8), fg="gray").pack(anchor="w")

        tk.Frame(frame, height=1, bg="#ccc").pack(fill="x", pady=4)

        # --- Staff ---
        tk.Label(frame, text="Staff", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        if employees:
            for emp in employees:
                _staff_row(frame, emp)
        else:
            tk.Label(frame, text="  No staff assigned", font=("Segoe UI", 8), fg="gray").pack(anchor="w")

        tk.Frame(frame, height=1, bg="#ccc").pack(fill="x", pady=4)

        # --- Queue ---
        tk.Label(frame, text=f"Queue ({len(queue)} items)", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        if queue:
            for item in queue[:3]:
                tk.Label(frame, text=f"  {item.get('type', 'unknown')}", font=("Segoe UI", 8)).pack(anchor="w")
            if len(queue) > 3:
                tk.Label(frame, text=f"  ... +{len(queue) - 3} more", font=("Segoe UI", 8), fg="gray").pack(anchor="w")
        else:
            tk.Label(frame, text="  Queue empty", font=("Segoe UI", 8), fg="gray").pack(anchor="w")

        tk.Button(frame, text="Close", command=close_team_room).pack(pady=(6, 0))

        # Position: anchor to widget right edge, keep on screen
        popup.update_idletasks()
        rx = widget.root.winfo_rootx()
        ry = widget.root.winfo_rooty()
        rw = widget.root.winfo_width()
        pw = popup.winfo_width()
        ph = popup.winfo_height()

        x = rx + rw + 4
        y = ry

        screen_w = popup.winfo_screenwidth()
        screen_h = popup.winfo_screenheight()
        if x + pw > screen_w:
            x = rx - pw - 4
        if y + ph > screen_h:
            y = screen_h - ph - 4
        if y < 0:
            y = 0

        popup.geometry(f"+{x}+{y}")

    except Exception:  # noqa: BLE001
        from ui.toast import show_toast
        show_toast(widget, "Team Room failed", level="error")


def _approval_row(parent: tk.Frame, widget: Any, a: dict, popup: tk.Toplevel) -> None:
    row = tk.Frame(parent)
    row.pack(fill="x", pady=1)

    tk.Label(row, text=a.get("action", "?"), font=("Segoe UI", 8)).pack(side="left")
    tk.Label(row, text=a.get("projectId", ""), font=("Segoe UI", 8), fg="gray").pack(side="left", padx=4)

    def resolve(approved: bool) -> None:
        if widget._team_state is not None:
            widget._team_state.resolve_approval(a["id"], approved)
        popup.destroy()
        show_team_room(widget)

    tk.Button(row, text="Approve", font=("Segoe UI", 7),
              command=lambda: resolve(True)).pack(side="right")
    tk.Button(row, text="Reject", font=("Segoe UI", 7),
              command=lambda: resolve(False)).pack(side="right", padx=2)


def _staff_row(parent: tk.Frame, emp: dict) -> None:
    row = tk.Frame(parent)
    row.pack(fill="x", pady=1)

    role = emp.get("role", "worker")
    badge = ROLE_BADGE.get(role, "👤")
    role_label = ROLE_LABEL.get(role, role.capitalize())

    tk.Label(row, text=f"{badge} {emp.get('name', '?')}", font=("Segoe UI", 8)).pack(side="left")
    tk.Label(row, text=role_label, font=("Segoe UI", 7), fg="gray").pack(side="left", padx=4)

    status = emp.get("status", "idle")
    color = STATUS_COLORS.get(status, "#888")
    tk.Label(row, text=f"● {status}", font=("Segoe UI", 8), fg=color).pack(side="right")
