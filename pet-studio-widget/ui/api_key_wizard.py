"""API Key Connection Wizard for Pet Studio.

A simple dialog that helps first-time users connect their API keys.
Launched automatically when no model profiles are configured.
"""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from typing import Any

WIZARD_BG = "#1e1e2e"
WIZARD_SURFACE = "#181825"
WIZARD_FG = "#cdd6f4"
WIZARD_MUTED = "#6c7086"
WIZARD_ACCENT = "#89b4fa"
WIZARD_FONT = "Segoe UI"


def _detect_api_keys() -> dict[str, str]:
    """Detect existing API keys from environment or common config files."""
    import os
    keys: dict[str, str] = {}
    env_keys = {
        "OPENROUTER_API_KEY": "OpenRouter",
        "OPENAI_API_KEY": "OpenAI (GPT)",
        "ANTHROPIC_API_KEY": "Anthropic (Claude)",
        "CODEX_API_KEY": "Codex",
    }
    for env_var, name in env_keys.items():
        val = os.environ.get(env_var, "").strip()
        if val:
            keys[name] = val
    return keys


def show_api_key_wizard(parent: tk.Tk | tk.Toplevel, team_state: Any) -> bool:
    """Show the API key connection wizard.

    Returns True if at least one API key was saved.
    """
    existing = _detect_api_keys()
    saved = False

    wizard = tk.Toplevel(parent)
    wizard.title("API 키 연결")
    wizard.geometry("420x360")
    wizard.configure(bg=WIZARD_BG)
    wizard.resizable(False, False)
    wizard.transient(parent)
    wizard.grab_set()

    # Header
    header = tk.Frame(wizard, bg=WIZARD_SURFACE, height=60)
    header.pack(fill=tk.X)
    header.pack_propagate(False)
    tk.Label(
        header,
        text="🔑  API 키 연결",
        fg=WIZARD_FG,
        bg=WIZARD_SURFACE,
        font=(WIZARD_FONT, 12, "bold"),
    ).pack(padx=16, pady=10, anchor=tk.W)
    tk.Label(
        header,
        text="사용할 AI 서비스의 API 키를 입력하세요.",
        fg=WIZARD_MUTED,
        bg=WIZARD_SURFACE,
        font=(WIZARD_FONT, 9),
    ).pack(padx=16, anchor=tk.W)

    # Form
    form = tk.Frame(wizard, bg=WIZARD_BG)
    form.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

    # Detected keys info
    if existing:
        detect_frame = tk.Frame(form, bg="#1a2e1a")
        detect_frame.pack(fill=tk.X, pady=(0, 8))
        detect_text = "감지된 API 키: " + ", ".join(existing.keys())
        tk.Label(
            detect_frame,
            text=detect_text,
            fg="#a6e3a1",
            bg="#1a2e1a",
            font=(WIZARD_FONT, 8),
        ).pack(padx=8, pady=4)

    # API key entries
    entries: dict[str, tk.Entry] = {}
    providers = [
        ("OpenRouter", "OPENROUTER_API_KEY", "OpenRouter API 키"),
        ("OpenAI (GPT)", "OPENAI_API_KEY", "sk-..."),
        ("Anthropic (Claude)", "ANTHROPIC_API_KEY", "sk-ant-..."),
    ]

    for display_name, env_var, placeholder in providers:
        row = tk.Frame(form, bg=WIZARD_BG)
        row.pack(fill=tk.X, pady=(4, 0))

        tk.Label(
            row,
            text=display_name,
            fg=WIZARD_FG,
            bg=WIZARD_BG,
            font=(WIZARD_FONT, 9),
            width=18,
            anchor=tk.W,
        ).pack(side=tk.LEFT)

        entry = tk.Entry(
            row,
            fg=WIZARD_FG,
            bg="#11111b",
            insertbackground=WIZARD_FG,
            relief=tk.FLAT,
            font=(WIZARD_FONT, 9),
            show="•",
        )
        entry.insert(0, placeholder)
        entry.bind("<FocusIn>", lambda e, ent=entry, ph=placeholder: _clear_placeholder(ent, ph))
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))
        entries[env_var] = entry

    # Status
    status = tk.Label(
        form,
        text="",
        fg=WIZARD_MUTED,
        bg=WIZARD_BG,
        font=(WIZARD_FONT, 8),
    )
    status.pack(pady=(8, 0))

    # Buttons
    btn_frame = tk.Frame(wizard, bg=WIZARD_SURFACE, height=44)
    btn_frame.pack(fill=tk.X, side=tk.BOTTOM)
    btn_frame.pack_propagate(False)

    def _on_save() -> None:
        nonlocal saved
        import os
        count = 0
        for env_var, entry in entries.items():
            val = entry.get().strip()
            if val and "..." not in val:
                os.environ[env_var] = val
                count += 1
                # Also save to team_state if available
                if team_state and hasattr(team_state, "state_file"):
                    _persist_key(team_state.state_file.parent, env_var, val)

        if count > 0:
            saved = True
            status.config(text=f"{count}개 API 키가 저장되었습니다 ✓", fg="#a6e3a1")
            wizard.after(1200, wizard.destroy)
        else:
            status.config(text="API 키를 하나 이상 입력해주세요.", fg="#f38ba8")

    def _on_skip() -> None:
        wizard.destroy()

    skip_btn = tk.Label(
        btn_frame,
        text="건너뛰기",
        fg=WIZARD_MUTED,
        bg=WIZARD_SURFACE,
        font=(WIZARD_FONT, 9),
        cursor="hand2",
    )
    skip_btn.pack(side=tk.RIGHT, padx=12, pady=10)
    skip_btn.bind("<Button-1>", lambda e: _on_skip())

    save_btn = tk.Label(
        btn_frame,
        text="저장",
        fg=WIZARD_ACCENT,
        bg=WIZARD_SURFACE,
        font=(WIZARD_FONT, 9, "bold"),
        cursor="hand2",
    )
    save_btn.pack(side=tk.RIGHT, padx=4, pady=10)
    save_btn.bind("<Button-1>", lambda e: _on_save())

    wizard.wait_window()
    return saved


def _clear_placeholder(entry: tk.Entry, placeholder: str) -> None:
    """Clear placeholder text on first focus."""
    if entry.get() == placeholder:
        entry.delete(0, tk.END)
        entry.config(show="•")


def _persist_key(state_dir: Path, env_var: str, value: str) -> None:
    """Persist API key to a local config file next to team_state.json."""
    config_file = state_dir / ".pet_studio_keys.json"
    keys: dict[str, str] = {}
    if config_file.exists():
        try:
            keys = json.loads(config_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            keys = {}
    keys[env_var] = value
    config_file.write_text(
        json.dumps(keys, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
