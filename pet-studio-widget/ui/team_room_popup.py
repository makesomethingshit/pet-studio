"""Team Room popup for Project Room Widget.

Shows pending approvals, staff status, and roost queue in a Toplevel window.
"""

from __future__ import annotations

import tkinter as tk


def show_team_room_popup(widget) -> None:
    """Show a compact Team Room summary popup."""
    if widget._team_state is None:
        return
    try:
        pending = widget._team_state.get_pending_approvals()
        employees = widget._team_state.get_employees()
        queue = widget._team_state.get_roost_queue()

        # Close existing popup if open
        if widget._team_room_popup is not None:
            try:
                widget._team_room_popup.destroy()
            except tk.TclError:
                pass

        popup = tk.Toplevel(widget.root)
        popup.title("Team Room")
        popup.resizable(False, False)
        popup.attributes("-topmost", True)
        widget._team_room_popup = popup

        frame = tk.Frame(padx=12, pady=8)
        frame.pack(fill="both", expand=True)

        # --- Approvals ---
        tk.Label(frame, text="Approvals", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        if pending:
            for a in pending[:5]:
                row = tk.Frame(frame)
                row.pack(fill="x", pady=1)
                tk.Label(row, text=f"  {a['action']}", font=("Segoe UI", 8)).pack(side="left")
                tk.Label(row, text=a["projectId"], font=("Segoe UI", 8), fg="gray").pack(
                    side="left", padx=4
                )
                tk.Button(
                    row,
                    text="Approve",
                    font=("Segoe UI", 7),
                    command=lambda aid=a["id"]: _resolve_approval(widget, aid, True, popup),
                ).pack(side="right")
                tk.Button(
                    row,
                    text="Reject",
                    font=("Segoe UI", 7),
                    command=lambda aid=a["id"]: _resolve_approval(widget, aid, False, popup),
                ).pack(side="right", padx=2)
        else:
            tk.Label(frame, text="  No pending approvals", font=("Segoe UI", 8), fg="gray").pack(
                anchor="w"
            )

        tk.Frame(frame, height=1, bg="#ccc").pack(fill="x", pady=4)

        # --- Employees ---
        tk.Label(frame, text="Staff", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        status_colors = {"idle": "#888", "running": "#0a0", "review": "#c80"}
        if employees:
            for emp in employees:
                row = tk.Frame(frame)
                row.pack(fill="x", pady=1)
                color = status_colors.get(emp.get("status", "idle"), "#888")
                tk.Label(row, text=f"  {emp['name']}", font=("Segoe UI", 8)).pack(side="left")
                tk.Label(row, text=emp.get("status", "idle"), font=("Segoe UI", 8), fg=color).pack(
                    side="right"
                )
        else:
            tk.Label(frame, text="  No staff assigned", font=("Segoe UI", 8), fg="gray").pack(
                anchor="w"
            )

        tk.Frame(frame, height=1, bg="#ccc").pack(fill="x", pady=4)

        # --- Queue ---
        tk.Label(
            frame, text=f"Queue ({len(queue)} items)", font=("Segoe UI", 9, "bold")
        ).pack(anchor="w")
        if queue:
            for item in queue[:3]:
                tk.Label(
                    frame, text=f"  {item.get('type', 'unknown')}", font=("Segoe UI", 8)
                ).pack(anchor="w")
            if len(queue) > 3:
                tk.Label(
                    frame,
                    text=f"  ... +{len(queue) - 3} more",
                    font=("Segoe UI", 8),
                    fg="gray",
                ).pack(anchor="w")
        else:
            tk.Label(frame, text="  Queue empty", font=("Segoe UI", 8), fg="gray").pack(anchor="w")

        tk.Button(frame, text="Close", command=popup.destroy).pack(pady=(6, 0))

        # Position near widget
        popup.update_idletasks()
        rx = widget.root.winfo_rootx()
        ry = widget.root.winfo_rooty()
        popup.geometry(f"+{rx + 40}+{ry + 40}")
    except Exception:  # noqa: BLE001
        from ui.toast import show_toast

        show_toast(widget, "Team Room popup failed", level="error")


def _resolve_approval(widget, approval_id: str, approved: bool, popup: tk.Toplevel) -> None:
    """Resolve an approval request and refresh the popup."""
    if widget._team_state is not None:
        widget._team_state.resolve_approval(approval_id, approved)
    popup.destroy()
    show_team_room_popup(widget)
