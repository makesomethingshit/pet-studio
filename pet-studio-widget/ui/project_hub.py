"""Project Hub panel for Pet Studio Widget.

Provides a Toplevel window listing registered projects with
status, mission preview, and one-click switching.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any


def show_project_hub(widget: Any) -> None:
    """Open the Project Hub Toplevel window.

    Args:
        widget: ProjectRoomWidget instance.
    """
    if widget._hub_window is not None:
        try:
            widget._hub_window.lift()
            widget._hub_window.focus_force()
        except tk.TclError:
            widget._hub_window = None
        else:
            return

    hub = tk.Toplevel(widget.root)
    hub.title("Project Hub")
    hub.geometry("420x440")
    hub.resizable(True, True)
    hub.configure(bg="#1e1e2e")
    hub.attributes("-topmost", True)

    widget._hub_window = hub

    # --- Header ---
    header = tk.Frame(hub, bg="#181825", height=36)
    header.pack(fill=tk.X, padx=0, pady=0)
    header.pack_propagate(False)
    tk.Label(
        header,
        text="Project Hub",
        fg="#cdd6f4",
        bg="#181825",
        font=("Segoe UI", 11, "bold"),
    ).pack(side=tk.LEFT, padx=12, pady=8)

    # --- Project list ---
    list_frame = tk.Frame(hub, bg="#1e1e2e")
    list_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(8, 4))

    columns = ("name", "status")
    tree = ttk.Treeview(
        list_frame,
        columns=columns,
        show="headings",
        selectmode="browse",
        height=8,
    )
    tree.heading("name", text="Project")
    tree.heading("status", text="Status")
    tree.column("name", width=260, minwidth=120)
    tree.column("status", width=100, minwidth=60, anchor=tk.CENTER)

    scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # --- Mission input ---
    mission_frame = tk.Frame(hub, bg="#181825", height=80)
    mission_frame.pack(fill=tk.X, padx=12, pady=(0, 4))
    mission_frame.pack_propagate(False)

    tk.Label(
        mission_frame,
        text="Mission",
        fg="#6c7086",
        bg="#181825",
        font=("Segoe UI", 8),
    ).pack(anchor=tk.W, padx=8, pady=(4, 0))

    mission_var = tk.StringVar()
    mission_entry = tk.Entry(
        mission_frame,
        textvariable=mission_var,
        fg="#cdd6f4",
        bg="#11111b",
        insertbackground="#cdd6f4",
        relief=tk.FLAT,
        font=("Segoe UI", 9),
    )
    mission_entry.pack(fill=tk.X, padx=8, pady=(2, 2))

    save_btn = tk.Label(
        mission_frame,
        text="저장",
        fg="#89b4fa",
        bg="#181825",
        font=("Segoe UI", 8, "underline"),
        cursor="hand2",
    )
    save_btn.pack(anchor=tk.E, padx=8, pady=(0, 4))

    # --- Status bar ---
    status_frame = tk.Frame(hub, bg="#181825", height=28)
    status_frame.pack(fill=tk.X, side=tk.BOTTOM)
    status_frame.pack_propagate(False)
    status_label = tk.Label(
        status_frame,
        text="",
        fg="#6c7086",
        bg="#181825",
        font=("Segoe UI", 8),
    )
    status_label.pack(side=tk.LEFT, padx=12, pady=4)

    # --- Populate ---
    projects = _get_projects(widget)
    current_id = widget.project_id
    project_map = {p["id"]: p for p in projects}

    STATUS_DISPLAY = {
        "idle": "대기",
        "running": "작업중",
        "waiting": "대기중",
        "review": "리뷰",
        "failed": "실패",
        "blocked": "차단됨",
        "done": "완료",
    }

    for p in projects:
        pid = p["id"]
        name = p.get("displayName", pid)
        status = p.get("status", "idle")
        label = STATUS_DISPLAY.get(status, status)
        tags = ("current",) if pid == current_id else ()
        tree.insert("", tk.END, iid=pid, values=(name, label), tags=tags)

    tree.tag_configure("current", foreground="#a6e3a1")

    # --- Handlers ---
    def _on_select(event: tk.Event) -> None:
        sel = tree.selection()
        if not sel:
            return
        pid = sel[0]
        p = project_map.get(pid, {})
        mission_var.set(p.get("mission", ""))
        if pid == current_id:
            status_label.config(text="현재 프로젝트")
        else:
            status_label.config(text="클릭하여 전환")

    def _on_double_click(event: tk.Event) -> None:
        sel = tree.selection()
        if not sel:
            return
        pid = sel[0]
        if pid == current_id:
            return
        status_label.config(text=f"전환 중: {pid}...")
        hub.after(100, lambda: _do_switch(widget, pid, hub, status_label))

    def _on_save() -> None:
        sel = tree.selection()
        if not sel:
            status_label.config(text="프로젝트를 먼저 선택하세요")
            return
        pid = sel[0]
        mission = mission_var.get().strip()
        if widget._team_state is not None:
            widget._team_state.set_project_mission(pid, mission)
            # Update local cache
            if pid in project_map:
                project_map[pid]["mission"] = mission
            status_label.config(text="미션 저장 완료")
        else:
            status_label.config(text="TeamState 없음 — 저장 불가")

    tree.bind("<<TreeviewSelect>>", _on_select)
    tree.bind("<Double-1>", _on_double_click)
    save_btn.bind("<Button-1>", lambda e: _on_save())
    mission_entry.bind("<Return>", lambda e: _on_save())

    # --- Close handler ---
    def _on_close() -> None:
        widget._hub_window = None
        hub.destroy()

    hub.protocol("WM_DELETE_WINDOW", _on_close)


def _get_projects(widget: Any) -> list[dict]:
    """Get project list from registry or team state."""
    projects: list[dict] = []
    # 1. Try registry (full project assignments)
    if widget._registry_path:
        try:
            from project_room_registry import list_projects

            for p in list_projects(widget._registry_path):
                projects.append(
                    {
                        "id": p.project_id,
                        "displayName": p.display_name,
                        "status": "idle",
                    }
                )
        except Exception:
            pass
    # 2. Supplement with team state (status, mission)
    if widget._team_state is not None:
        try:
            ts_projects = widget._team_state.list_projects()
            by_id = {p["id"]: p for p in projects}
            for tp in ts_projects:
                pid = tp["id"]
                if pid in by_id:
                    by_id[pid]["status"] = tp.get("status", "idle")
                    by_id[pid]["mission"] = tp.get("mission", "")
                else:
                    projects.append(
                        {
                            "id": pid,
                            "displayName": tp.get("displayName", pid),
                            "status": tp.get("status", "idle"),
                            "mission": tp.get("mission", ""),
                        }
                    )
        except Exception:
            pass
    return projects


def _do_switch(widget: Any, project_id: str, hub: tk.Toplevel, status_label: tk.Label) -> None:
    try:
        widget.switch_project(project_id)
        status_label.config(text=f"전환 완료: {project_id}")
        hub.after(500, lambda: _close_hub(widget, hub))
    except Exception as e:
        status_label.config(text=f"전환 실패: {e}")


def _close_hub(widget: Any, hub: tk.Toplevel) -> None:
    widget._hub_window = None
    try:
        hub.destroy()
    except tk.TclError:
        pass
