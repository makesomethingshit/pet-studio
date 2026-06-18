"""Team Room Panel — compact embeddable panel for Pet Studio widget.

Slides in from the right side of the widget root.
Uses tk.Frame packed directly on root (not on canvas) so it doesn't
interfere with the transparent chroma-canvas layout.
"""

from __future__ import annotations

import logging
import tkinter as tk
from typing import Any

logger = logging.getLogger(__name__)

PANEL_WIDTH = 260
PANEL_MIN_HEIGHT = 120
SLIDE_STEP = 20  # pixels per animation frame
SLIDE_DELAY = 8  # ms between frames


class TeamRoomPanel:
    """Compact team room panel that slides in/out from the right."""

    def __init__(self, root: tk.Tk, team_state: Any) -> None:
        self._root = root
        self._state = team_state
        self._panel: tk.Frame | None = None
        self._visible = False
        self._animating = False
        self._canvas_width = 0
        self._canvas_height = 0

    # --- Public API ---

    def toggle(self) -> None:
        if self._visible:
            self._slide_out()
        else:
            self._slide_in()

    def is_visible(self) -> bool:
        return self._visible

    def refresh(self) -> None:
        """Rebuild panel content if visible."""
        if self._visible and self._panel is not None:
            self._build_content()

    # --- Internal ---

    def _get_canvas_size(self) -> tuple[int, int]:
        try:
            cw = self._root.winfo_width()
            ch = self._root.winfo_height()
            return max(cw, 100), max(ch, 100)
        except tk.TclError:
            return 400, 400

    def _slide_in(self) -> None:
        if self._animating:
            return
        self._animating = True

        cw, ch = self._get_canvas_size()
        self._canvas_width = cw
        self._canvas_height = ch

        panel_height = max(ch - 4, PANEL_MIN_HEIGHT)

        # Create frame
        self._panel = tk.Frame(
            self._root,
            bg="#1e1e2e",
            highlightthickness=1,
            highlightbackground="#45475a",
            padx=0,
            pady=0,
        )
        self._panel.place(x=cw, y=2, width=PANEL_WIDTH, height=panel_height)
        self._build_content()

        # Animate
        self._animate(cw, cw - PANEL_WIDTH, True)

    def _slide_out(self) -> None:
        if self._animating or self._panel is None:
            return
        self._animating = True

        cw = self._canvas_width
        self._animate(self._panel.winfo_x(), cw, False)

    def _animate(self, current: int, target: int, opening: bool) -> None:
        if self._panel is None:
            self._animating = False
            return

        remaining = abs(target - current)
        if remaining < SLIDE_STEP:
            if not opening:
                self._panel.destroy()
                self._panel = None
                self._visible = False
            else:
                self._panel.place(x=target)
                self._visible = True
            self._animating = False
            return

        direction = -1 if opening else 1
        next_x = current + direction * SLIDE_STEP
        self._panel.place(x=next_x)
        self._root.after(SLIDE_DELAY, self._animate, next_x, target, opening)

    def _clear(self) -> None:
        if self._panel is None:
            return
        for child in self._panel.winfo_children():
            child.destroy()

    def _build_content(self) -> None:
        if self._panel is None:
            return
        self._clear()

        inner = tk.Frame(self._panel, bg="#1e1e2e", padx=8, pady=6)
        inner.pack(fill="both", expand=True)

        # --- Header ---
        header = tk.Frame(inner, bg="#1e1e2e")
        header.pack(fill="x", pady=(0, 4))
        tk.Label(
            header,
            text="Team Room",
            font=("Segoe UI", 9, "bold"),
            fg="#cdd6f4",
            bg="#1e1e2a",
        ).pack(side="left")
        tk.Label(
            header,
            text="✕",
            font=("Segoe UI", 8),
            fg="#6c7086",
            bg="#1e1e2e",
            cursor="hand2",
        ).pack(side="right").bind("<Button-1>", lambda _e: self._slide_out())

        _sep(inner)

        # --- Approvals ---
        tk.Label(
            inner,
            text="Approvals",
            font=("Segoe UI", 8, "bold"),
            fg="#a6adc8",
            bg="#1e1e2e",
        ).pack(anchor="w", pady=(2, 0))
        try:
            pending = self._state.get_pending_approvals()
        except Exception:  # noqa: BLE001
            pending = []
        if pending:
            for a in pending[:5]:
                self._approval_row(inner, a)
        else:
            tk.Label(
                inner,
                text="  No pending",
                font=("Segoe UI", 8),
                fg="#585b70",
                bg="#1e1e2e",
            ).pack(anchor="w", pady=1)

        _sep(inner)

        # --- Staff ---
        tk.Label(
            inner,
            text="Staff",
            font=("Segoe UI", 8, "bold"),
            fg="#a6adc8",
            bg="#1e1e2e",
        ).pack(anchor="w", pady=(2, 0))
        try:
            employees = self._state.get_employees()
        except Exception:  # noqa: BLE001
            employees = []
        status_colors = {"idle": "#6c7086", "running": "#a6e3a1", "review": "#f9e2af"}
        if employees:
            for emp in employees:
                row = tk.Frame(inner, bg="#1e1e2e")
                row.pack(fill="x", pady=0)
                name = emp.get("name", emp.get("id", "?"))
                status = emp.get("status", "idle")
                color = status_colors.get(status, "#6c7086")
                tk.Label(
                    row,
                    text=f"  {name}",
                    font=("Segoe UI", 8),
                    fg="#cdd6f4",
                    bg="#1e1e2e",
                ).pack(side="left")
                tk.Label(
                    row,
                    text=status,
                    font=("Segoe UI", 8),
                    fg=color,
                    bg="#1e1e2e",
                ).pack(side="right")
        else:
            tk.Label(
                inner,
                text="  No staff",
                font=("Segoe UI", 8),
                fg="#585b70",
                bg="#1e1e2e",
            ).pack(anchor="w", pady=1)

        _sep(inner)

        # --- Queue ---
        try:
            queue = self._state.get_roost_queue()
        except Exception:  # noqa: BLE001
            queue = []
        tk.Label(
            inner,
            text=f"Queue ({len(queue)})",
            font=("Segoe UI", 8, "bold"),
            fg="#a6adc8",
            bg="#1e1e2e",
        ).pack(anchor="w", pady=(2, 0))
        if queue:
            for item in queue[:3]:
                t = item.get("type", "unknown")
                tk.Label(
                    inner,
                    text=f"  {t}",
                    font=("Segoe UI", 8),
                    fg="#cdd6f4",
                    bg="#1e1e2e",
                ).pack(anchor="w")
            if len(queue) > 3:
                tk.Label(
                    inner,
                    text=f"  +{len(queue) - 3} more",
                    font=("Segoe UI", 8),
                    fg="#585b70",
                    bg="#1e1e2e",
                ).pack(anchor="w")
        else:
            tk.Label(
                inner,
                text="  Empty",
                font=("Segoe UI", 8),
                fg="#585b70",
                bg="#1e1e2e",
            ).pack(anchor="w", pady=1)

    def _approval_row(self, parent: tk.Frame, approval: dict) -> None:
        row = tk.Frame(parent, bg="#1e1e2e")
        row.pack(fill="x", pady=1)
        action = approval.get("action", "?")
        proj = approval.get("projectId", "")
        aid = approval.get("id", "")

        tk.Label(
            row,
            text=f"  {action}",
            font=("Segoe UI", 8),
            fg="#cdd6f4",
            bg="#1e1e2e",
        ).pack(side="left")
        tk.Label(
            row,
            text=proj,
            font=("Segoe UI", 7),
            fg="#585b70",
            bg="#1e1e2e",
        ).pack(side="left", padx=2)

        def resolve(apprv_id: str, approved: bool) -> None:
            try:
                self._state.resolve_approval(apprv_id, approved)
            except Exception:  # noqa: BLE001
                pass
            self._build_content()

        tk.Button(
            row,
            text="OK",
            font=("Segoe UI", 7),
            fg="#a6e3a1",
            bg="#313244",
            relief="flat",
            padx=2,
            pady=0,
            command=lambda a=aid: resolve(a, True),
        ).pack(side="right")
        tk.Button(
            row,
            text="NO",
            font=("Segoe UI", 7),
            fg="#f38ba8",
            bg="#313244",
            relief="flat",
            padx=2,
            pady=0,
            command=lambda a=aid: resolve(a, False),
        ).pack(side="right", padx=1)


def _sep(parent: tk.Frame) -> tk.Frame:
    """Horizontal separator line."""
    line = tk.Frame(parent, height=1, bg="#313244")
    line.pack(fill="x", pady=3)
    return line
