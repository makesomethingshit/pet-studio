"""Pet Studio UI design tokens."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

DS_COLORS = {
    "page": "#191611",
    "surface": "#241f18",
    "surface_raised": "#30281f",
    "field": "#15120e",
    "line": "#4a3d2f",
    "line_strong": "#6d5742",
    "text": "#f7ead7",
    "muted": "#d7bfa3",
    "quiet": "#9b8064",
    "accent": "#8fd7c2",
    "accent_text": "#12231d",
    "success": "#9dd6a5",
    "warning": "#e1b66f",
    "danger": "#e07b70",
    "selection": "#463728",
}

DS_SPACING = {
    "hair": 4,
    "tight": 8,
    "cluster": 12,
    "section": 16,
    "block": 24,
    "panel": 32,
}

DS_FONTS = {
    "brand": ("Segoe UI Semibold", 16, "bold"),
    "section": ("Segoe UI Semibold", 10, "bold"),
    "body": ("Segoe UI", 9),
    "label": ("Segoe UI", 8),
    "label_bold": ("Segoe UI", 8, "bold"),
    "caption": ("Segoe UI", 8),
}

ROLE_COLORS = {
    "scout": DS_COLORS["muted"],
    "coordinator": DS_COLORS["warning"],
    "lead": DS_COLORS["success"],
}

STATUS_COLORS = {
    "waiting": DS_COLORS["muted"],
    "running": DS_COLORS["accent"],
    "done": DS_COLORS["quiet"],
    "failed": DS_COLORS["danger"],
    "blocked": DS_COLORS["warning"],
}


def hub_colors() -> dict[str, str]:
    """Return the compatibility color names used by Project Hub today."""
    return {
        "bg": DS_COLORS["page"],
        "panel": DS_COLORS["surface"],
        "panel_2": DS_COLORS["surface_raised"],
        "line": DS_COLORS["line"],
        "text": DS_COLORS["text"],
        "muted": DS_COLORS["muted"],
        "subtle": DS_COLORS["quiet"],
        "accent": DS_COLORS["accent"],
        "accent_2": DS_COLORS["success"],
        "danger": DS_COLORS["danger"],
        "input": DS_COLORS["field"],
        "selection": DS_COLORS["selection"],
        "warning": DS_COLORS["warning"],
    }


def role_color(role: str) -> str:
    return ROLE_COLORS.get(role, DS_COLORS["muted"])


def status_color(status: str) -> str:
    return STATUS_COLORS.get(status, DS_COLORS["muted"])


def configure_hub_ttk(root: tk.Misc) -> None:
    """Apply the shared Tk/ttk styling for dense workroom screens."""
    colors = hub_colors()
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(
        "TNotebook",
        background=colors["bg"],
        borderwidth=0,
        tabmargins=(DS_SPACING["tight"], DS_SPACING["tight"], DS_SPACING["tight"], 0),
    )
    style.configure(
        "TNotebook.Tab",
        background=colors["panel"],
        foreground=colors["muted"],
        padding=(DS_SPACING["section"], DS_SPACING["tight"]),
        borderwidth=0,
        font=DS_FONTS["body"],
    )
    style.map(
        "TNotebook.Tab",
        background=[("selected", colors["panel_2"])],
        foreground=[("selected", colors["text"])],
    )
    style.configure(
        "Treeview",
        background=colors["input"],
        fieldbackground=colors["input"],
        foreground=colors["text"],
        borderwidth=0,
        rowheight=26,
        font=DS_FONTS["body"],
    )
    style.configure(
        "Treeview.Heading",
        background=colors["panel_2"],
        foreground=colors["muted"],
        relief=tk.FLAT,
        font=DS_FONTS["label_bold"],
    )
    style.map(
        "Treeview",
        background=[("selected", colors["selection"])],
        foreground=[("selected", colors["text"])],
    )
    style.configure(
        "TCombobox",
        fieldbackground=colors["input"],
        background=colors["panel_2"],
        foreground=colors["text"],
        arrowcolor=colors["muted"],
        bordercolor=colors["line"],
        lightcolor=colors["line"],
        darkcolor=colors["line"],
    )
