"""Local auth connection wizard for optional Pet Studio adapters."""

from __future__ import annotations

import json
import os
import tkinter as tk
from pathlib import Path
from typing import Any

from roost.auth_config import AUTH_ENV_KEYS, DEFAULT_AUTH_CONFIG, load_auth_config

WIZARD_BG = "#111318"
WIZARD_SURFACE = "#181b22"
WIZARD_FG = "#eef2f8"
WIZARD_MUTED = "#9aa6b5"
WIZARD_ACCENT = "#6aa6ff"
WIZARD_DANGER = "#ff6b7a"
WIZARD_INPUT = "#0c0f14"
WIZARD_FONT = "Segoe UI"

FIELD_SPECS = (
    ("OpenRouter key", "OPENROUTER_API_KEY", "sk-or-..."),
    ("Local gateway URL", "HERMES_GATEWAY_URL", "http://127.0.0.1:8787/v1"),
    ("Gateway auth token", "HERMES_GATEWAY_TOKEN", "optional"),
    ("Hermes base URL", "HERMES_BASE_URL", "optional"),
    ("Hermes command", "HERMES_CMD", "hermes"),
    ("Codex command", "CODEX_CMD", "codex"),
    ("Codex OAuth token", "CODEX_OAUTH_TOKEN", "optional"),
    ("Codex auth token", "CODEX_AUTH_TOKEN", "optional"),
    ("Codex API key", "CODEX_API_KEY", "optional"),
)


def _auth_path_for(team_state: Any) -> Path:
    if team_state and hasattr(team_state, "state_file"):
        return Path(team_state.state_file).parent / ".pet_studio_keys.json"
    return DEFAULT_AUTH_CONFIG


def _detected_keys(auth_path: Path) -> dict[str, bool]:
    stored = load_auth_config(auth_path)
    return {key: bool(os.environ.get(key) or stored.get(key)) for key in AUTH_ENV_KEYS}


def show_api_key_wizard(parent: tk.Tk | tk.Toplevel, team_state: Any) -> bool:
    """Show the local auth wizard.

    Returns True if at least one value was saved to the ignored local config.
    """
    auth_path = _auth_path_for(team_state)
    existing = load_auth_config(auth_path)
    saved = False

    wizard = tk.Toplevel(parent)
    wizard.title("Connect adapters")
    wizard.geometry("560x560")
    wizard.configure(bg=WIZARD_BG)
    wizard.resizable(False, False)
    wizard.transient(parent)
    wizard.grab_set()

    header = tk.Frame(wizard, bg=WIZARD_SURFACE, height=82)
    header.pack(fill=tk.X)
    header.pack_propagate(False)
    tk.Label(
        header,
        text="Connect Hermes / Codex",
        fg=WIZARD_FG,
        bg=WIZARD_SURFACE,
        font=(WIZARD_FONT, 14, "bold"),
    ).pack(padx=18, pady=(12, 2), anchor=tk.W)
    tk.Label(
        header,
        text="Values are stored only in ignored local config, not in tracked source.",
        fg=WIZARD_MUTED,
        bg=WIZARD_SURFACE,
        font=(WIZARD_FONT, 9),
    ).pack(padx=18, anchor=tk.W)

    form = tk.Frame(wizard, bg=WIZARD_BG)
    form.pack(fill=tk.BOTH, expand=True, padx=18, pady=14)

    auth_status = _detected_keys(auth_path)
    configured = [key for key, ok in auth_status.items() if ok]
    status_text = f"Detected: {', '.join(configured)}" if configured else "No adapter auth detected yet."
    tk.Label(
        form,
        text=status_text,
        fg=WIZARD_MUTED,
        bg=WIZARD_BG,
        font=(WIZARD_FONT, 8),
        wraplength=470,
        justify=tk.LEFT,
    ).pack(fill=tk.X, pady=(0, 10), anchor=tk.W)

    entries: dict[str, tk.Entry] = {}
    for label, env_var, placeholder in FIELD_SPECS:
        row = tk.Frame(form, bg=WIZARD_BG)
        row.pack(fill=tk.X, pady=(5, 0))
        tk.Label(
            row,
            text=label,
            fg=WIZARD_FG,
            bg=WIZARD_BG,
            font=(WIZARD_FONT, 9),
            width=18,
            anchor=tk.W,
        ).pack(side=tk.LEFT)
        entry = tk.Entry(
            row,
            fg=WIZARD_FG,
            bg=WIZARD_INPUT,
            insertbackground=WIZARD_FG,
            relief=tk.FLAT,
            font=(WIZARD_FONT, 9),
            show="*" if any(word in env_var for word in ("KEY", "TOKEN")) else "",
        )
        entry.insert(0, existing.get(env_var) or placeholder)
        entry.bind("<FocusIn>", lambda _event, ent=entry, ph=placeholder: _clear_placeholder(ent, ph))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        entries[env_var] = entry

    tk.Label(
        form,
        text=f"Local file: {auth_path}",
        fg=WIZARD_MUTED,
        bg=WIZARD_BG,
        font=(WIZARD_FONT, 8),
        wraplength=470,
        justify=tk.LEFT,
    ).pack(fill=tk.X, pady=(12, 0), anchor=tk.W)

    status = tk.Label(form, text="", fg=WIZARD_MUTED, bg=WIZARD_BG, font=(WIZARD_FONT, 8))
    status.pack(pady=(8, 0), anchor=tk.W)

    btn_frame = tk.Frame(wizard, bg=WIZARD_SURFACE, height=48)
    btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
    btn_frame.pack_propagate(False)

    def _on_save() -> None:
        nonlocal saved
        values: dict[str, str] = {}
        for env_var, entry in entries.items():
            value = entry.get().strip()
            placeholder = next((spec[2] for spec in FIELD_SPECS if spec[1] == env_var), "")
            if value and value != placeholder and value != "optional":
                values[env_var] = value
                os.environ[env_var] = value
        if not values:
            status.config(text="Enter at least one adapter value.", fg=WIZARD_DANGER)
            return
        _persist_keys(auth_path, values)
        saved = True
        status.config(text=f"Saved {len(values)} value(s).", fg="#66d9a6")
        wizard.after(900, wizard.destroy)

    def _on_skip() -> None:
        wizard.destroy()

    skip_btn = tk.Label(
        btn_frame,
        text="Skip",
        fg=WIZARD_MUTED,
        bg=WIZARD_SURFACE,
        font=(WIZARD_FONT, 9),
        cursor="hand2",
    )
    skip_btn.pack(side=tk.RIGHT, padx=14, pady=12)
    skip_btn.bind("<Button-1>", lambda _event: _on_skip())

    save_btn = tk.Label(
        btn_frame,
        text="Save local auth",
        fg=WIZARD_ACCENT,
        bg=WIZARD_SURFACE,
        font=(WIZARD_FONT, 9, "bold"),
        cursor="hand2",
    )
    save_btn.pack(side=tk.RIGHT, padx=4, pady=12)
    save_btn.bind("<Button-1>", lambda _event: _on_save())

    wizard.wait_window()
    return saved


def _clear_placeholder(entry: tk.Entry, placeholder: str) -> None:
    if entry.get() == placeholder:
        entry.delete(0, tk.END)


def _persist_keys(auth_path: Path, values: dict[str, str]) -> None:
    keys: dict[str, str] = {}
    if auth_path.exists():
        try:
            data = json.loads(auth_path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                keys = {str(key): str(value) for key, value in data.items()}
        except (json.JSONDecodeError, OSError):
            keys = {}
    keys.update(values)
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    auth_path.write_text(json.dumps(keys, indent=2), encoding="utf-8")
