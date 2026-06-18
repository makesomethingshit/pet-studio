"""Team Room panel for Project Room Widget.

Redesigned: Toplevel with custom frame, proper positioning, role badges,
collapsible, queue action buttons.
"""

from __future__ import annotations

import tkinter as tk
from typing import Any

# Role badge config
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

_BG = "#1e1e2e"
_FG = "#cdd6f4"
_DIM = "#6c7086"
_ACCENT = "#89b4fa"
_BORDER = "#313244"
_CARD = "#282838"
_BTN_APPROVE = "#22c55e"
_BTN_REJECT = "#ef4444"
_BTN_ACTION = "#3b82f6"


def show_team_room(widget) -> None:
    """Show Team Room as a properly positioned, collapsible popup."""
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
        popup.overrideredirect(True)  # Remove default window frame
        popup.configure(bg=_BG)
        widget._team_room_panel = popup

        # --- Title bar (drag handle + collapse/close) ---
        title_bar = tk.Frame(popup, bg="#313244", height=28)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        tk.Label(
            title_bar,
            text="Team Room",
            font=("Segoe UI", 9, "bold"),
            bg="#313244",
            fg=_FG,
            padx=8,
        ).pack(side="left")

        # Collapse button
        content_frame = tk.Frame(popup, bg=_BG)
        collapsed = [False]

        def toggle_collapse() -> None:
            if collapsed[0]:
                content_frame.pack(fill="both", expand=True)
                collapse_btn.setText("−")
                collapsed[0] = False
            else:
                content_frame.forget()
                collapse_btn.setText("+")
                collapsed[0] = True

        collapse_btn = tk.Label(
            title_bar,
            text="−",
            font=("Segoe UI", 10, "bold"),
            bg="#313244",
            fg=_FG,
            cursor="hand2",
            padx=6,
        )
        collapse_btn.pack(side="right", padx=2)
        collapse_btn.bind("<Button-1>", lambda e: toggle_collapse())

        # Close button
        tk.Label(
            title_bar,
            text="✕",
            font=("Segoe UI", 10),
            bg="#313244",
            fg="#ef4444",
            cursor="hand2",
            padx=6,
        ).pack(side="right")

        content_frame.pack(fill="both", expand=True)

        # --- Scrollable content ---
        canvas = tk.Canvas(content_frame, bg=_BG, highlightthickness=0)
        scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=_BG)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Section: Approvals ---
        _section_header(scroll_frame, "Approvals")
        if pending:
            for a in pending[:5]:
                _approval_row(scroll_frame, widget, a, popup)
        else:
            _dim_label(scroll_frame, "No pending approvals")

        _separator(scroll_frame)

        # --- Section: Staff ---
        _section_header(scroll_frame, "Staff")
        if employees:
            for emp in employees:
                _staff_row(scroll_frame, emp)
        else:
            _dim_label(scroll_frame, "No staff assigned")

        _separator(scroll_frame)

        # --- Section: Queue ---
        _section_header(scroll_frame, f"Queue ({len(queue)} items)")
        if queue:
            for item in queue[:5]:
                _queue_row(scroll_frame, widget, item)
            if len(queue) > 5:
                _dim_label(scroll_frame, f"... +{len(queue) - 5} more")
        else:
            _dim_label(scroll_frame, "Queue empty")

        # --- Footer ---
        footer = tk.Frame(popup, bg="#313244")
        footer.pack(fill="x")
        tk.Label(
            footer,
            text="Ctrl+Shift+T to toggle",
            font=("Segoe UI", 7),
            bg="#313244",
            fg=_DIM,
        ).pack(side="left", padx=8, pady=2)

        # Position: anchor to widget right edge
        popup.update_idletasks()
        rx = widget.root.winfo_rootx()
        ry = widget.root.winfo_rooty()
        rw = widget.root.winfo_width()
        pw = popup.winfo_width()
        ph = popup.winfo_height()

        # Place to the right of widget, vertically aligned to top
        x = rx + rw + 4
        y = ry

        # Keep on screen
        screen_w = popup.winfo_screenwidth()
        screen_h = popup.winfo_screenheight()
        if x + pw > screen_w:
            x = rx - pw - 4  # flip to left side
        if y + ph > screen_h:
            y = screen_h - ph - 4
        if y < 0:
            y = 0

        popup.geometry(f"+{x}+{y}")

        # Close method
        def close_panel() -> None:
            try:
                popup.destroy()
            except tk.TclError:
                pass
            widget._team_room_panel = None

        popup.close = close_panel  # type: ignore[attr-defined]

    except Exception:  # noqa: BLE001
        from ui.toast import show_toast

        show_toast(widget, "Team Room failed", level="error")


def _section_header(parent: tk.Frame, text: str) -> None:
    tk.Label(
        parent,
        text=text,
        font=("Segoe UI", 9, "bold"),
        bg=_BG,
        fg=_ACCENT,
    ).pack(anchor="w", padx=12, pady=(8, 4))


def _dim_label(parent: tk.Frame, text: str) -> None:
    tk.Label(
        parent,
        text=f"  {text}",
        font=("Segoe UI", 8),
        bg=_BG,
        fg=_DIM,
    ).pack(anchor="w", padx=12, pady=1)


def _separator(parent: tk.Frame) -> None:
    tk.Frame(parent, height=1, bg=_BORDER).pack(fill="x", padx=12, pady=6)


def _approval_row(parent: tk.Frame, widget: Any, a: dict, popup: tk.Toplevel) -> None:
    row = tk.Frame(parent, bg=_CARD, padx=8, pady=4)
    row.pack(fill="x", padx=8, pady=1)

    tk.Label(
        row,
        text=a.get("action", "?"),
        font=("Segoe UI", 8),
        bg=_CARD,
        fg=_FG,
    ).pack(side="left")

    tk.Label(
        row,
        text=a.get("projectId", ""),
        font=("Segoe UI", 7),
        bg=_CARD,
        fg=_DIM,
    ).pack(side="left", padx=4)

    def resolve(approved: bool) -> None:
        if widget._team_state is not None:
            widget._team_state.resolve_approval(a["id"], approved)
        popup.destroy()
        show_team_room(widget)

    tk.Button(
        row,
        text="✓",
        font=("Segoe UI", 7, "bold"),
        bg=_BTN_APPROVE,
        fg="white",
        relief="flat",
        padx=4,
        command=lambda: resolve(True),
    ).pack(side="right", padx=2)

    tk.Button(
        row,
        text="✗",
        font=("Segoe UI", 7, "bold"),
        bg=_BTN_REJECT,
        fg="white",
        relief="flat",
        padx=4,
        command=lambda: resolve(False),
    ).pack(side="right")


def _staff_row(parent: tk.Frame, emp: dict) -> None:
    row = tk.Frame(parent, bg=_CARD, padx=8, pady=4)
    row.pack(fill="x", padx=8, pady=1)

    role = emp.get("role", "worker")
    badge = ROLE_BADGE.get(role, "👤")
    role_label = ROLE_LABEL.get(role, role.capitalize())

    tk.Label(
        row,
        text=f"{badge} {emp.get('name', '?')}",
        font=("Segoe UI", 8),
        bg=_CARD,
        fg=_FG,
    ).pack(side="left")

    tk.Label(
        row,
        text=role_label,
        font=("Segoe UI", 7),
        bg=_CARD,
        fg=_DIM,
    ).pack(side="left", padx=4)

    status = emp.get("status", "idle")
    color = STATUS_COLORS.get(status, _DIM)
    tk.Label(
        row,
        text=f"● {status}",
        font=("Segoe UI", 8),
        bg=_CARD,
        fg=color,
    ).pack(side="right")


def _queue_row(parent: tk.Frame, widget: Any, item: dict) -> None:
    row = tk.Frame(parent, bg=_CARD, padx=8, pady=4)
    row.pack(fill="x", padx=8, pady=1)

    tk.Label(
        row,
        text=item.get("type", "unknown"),
        font=("Segoe UI", 8),
        bg=_CARD,
        fg=_FG,
    ).pack(side="left")

    def assign() -> None:
        # Placeholder: assign to first available staff
        from ui.toast import show_toast

        show_toast(widget, f"Assigned: {item.get('type', '?')}", level="info")

    def remove() -> None:
        from ui.toast import show_toast

        show_toast(widget, f"Removed: {item.get('type', '?')}", level="warn")

    tk.Button(
        row,
        text="Assign",
        font=("Segoe UI", 7),
        bg=_BTN_ACTION,
        fg="white",
        relief="flat",
        padx=6,
        command=assign,
    ).pack(side="right", padx=2)

    tk.Button(
        row,
        text="✗",
        font=("Segoe UI", 7, "bold"),
        bg=_BTN_REJECT,
        fg="white",
        relief="flat",
        padx=4,
        command=remove,
    ).pack(side="right")


def _resolve_approval(widget: Any, approval_id: str, approved: bool) -> None:
    """Resolve an approval request."""
    if widget._team_state is not None:
        widget._team_state.resolve_approval(approval_id, approved)
