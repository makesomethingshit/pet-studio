"""Project Hub panel for Pet Studio Widget.

Provides a Toplevel window with:
- Project list + switching
- Mission input
- Task Cards (waiting/running/done columns)
- Codex packet export
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

from roost.packet import export_codex_packet


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
    hub.geometry("560x480")
    hub.resizable(True, True)
    hub.configure(bg="#1e1e2e")

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

    tk.Label(
        header,
        text="launcher",
        fg="#6c7086",
        bg="#181825",
        font=("Segoe UI", 8),
    ).pack(side=tk.LEFT, padx=0, pady=8)

    # --- Notebook (Projects / Tasks) ---
    notebook = ttk.Notebook(hub)
    notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 0))

    # Tab 1: Projects
    projects_tab = tk.Frame(notebook, bg="#1e1e2e")
    notebook.add(projects_tab, text="Projects")

    # Tab 2: Tasks
    tasks_tab = tk.Frame(notebook, bg="#1e1e2e")
    notebook.add(tasks_tab, text="Tasks")

    # Tab 3: Endpoints
    endpoints_tab = tk.Frame(notebook, bg="#1e1e2e")
    notebook.add(endpoints_tab, text="Endpoints")

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

    # ===== Projects Tab =====
    _build_projects_tab(projects_tab, widget, hub, status_label)

    # ===== Tasks Tab =====
    _build_tasks_tab(tasks_tab, widget, status_label)

    # ===== Endpoints Tab =====
    _build_endpoints_tab(endpoints_tab, widget, hub, status_label)

    # --- Close handler ---
    def _on_close() -> None:
        widget._hub_window = None
        hub.destroy()

    hub.protocol("WM_DELETE_WINDOW", _on_close)


def _build_projects_tab(
    parent: tk.Frame,
    widget: Any,
    hub: tk.Toplevel,
    status_label: tk.Label,
) -> None:
    """Build the Projects tab content."""
    # Project list
    list_frame = tk.Frame(parent, bg="#1e1e2e")
    list_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(4, 2))

    columns = ("name", "status")
    tree = ttk.Treeview(
        list_frame,
        columns=columns,
        show="headings",
        selectmode="browse",
        height=6,
    )
    tree.heading("name", text="Project")
    tree.heading("status", text="Status")
    tree.column("name", width=300, minwidth=120)
    tree.column("status", width=100, minwidth=60, anchor=tk.CENTER)

    scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # Mission input
    mission_frame = tk.Frame(parent, bg="#181825", height=70)
    mission_frame.pack(fill=tk.X, padx=4, pady=(2, 4))
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

    # Populate
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

    # Handlers
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
            status_label.config(text="더블클릭하여 전환")

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
            if pid in project_map:
                project_map[pid]["mission"] = mission
            status_label.config(text="미션 저장 완료")
        else:
            status_label.config(text="TeamState 없음 — 저장 불가")

    tree.bind("<<TreeviewSelect>>", _on_select)
    tree.bind("<Double-1>", _on_double_click)
    save_btn.bind("<Button-1>", lambda e: _on_save())
    mission_entry.bind("<Return>", lambda e: _on_save())


def _build_tasks_tab(
    parent: tk.Frame,
    widget: Any,
    status_label: tk.Label,
) -> None:
    """Build the Tasks tab content with waiting/running/done columns."""
    # Toolbar
    toolbar = tk.Frame(parent, bg="#181825", height=28)
    toolbar.pack(fill=tk.X, padx=4, pady=(4, 2))
    toolbar.pack_propagate(False)

    export_btn = tk.Label(
        toolbar,
        text="Export Codex Packet",
        fg="#89b4fa",
        bg="#181825",
        font=("Segoe UI", 8, "underline"),
        cursor="hand2",
    )
    export_btn.pack(side=tk.RIGHT, padx=8, pady=4)

    import_btn = tk.Label(
        toolbar,
        text="Import Packet",
        fg="#89b4fa",
        bg="#181825",
        font=("Segoe UI", 8, "underline"),
        cursor="hand2",
    )
    import_btn.pack(side=tk.RIGHT, padx=4, pady=4)

    refresh_btn = tk.Label(
        toolbar,
        text="새로고침",
        fg="#6c7086",
        bg="#181825",
        font=("Segoe UI", 8),
        cursor="hand2",
    )
    refresh_btn.pack(side=tk.RIGHT, padx=4, pady=4)

    # Columns frame
    columns_frame = tk.Frame(parent, bg="#1e1e2e")
    columns_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(2, 4))

    # Configure grid weights for 3 equal columns
    for i in range(3):
        columns_frame.columnconfigure(i, weight=1, uniform="tasks")
    columns_frame.rowconfigure(0, weight=1)

    COLORS = {
        "waiting": ("#1a1e2e", "#89b4fa"),
        "running": ("#1a2e1a", "#a6e3a1"),
        "done": ("#1e1e2e", "#6c7086"),
    }
    COL_HEADERS = {"waiting": "대기", "running": "작업중", "done": "완료"}

    task_vars: dict[str, list] = {"waiting": [], "running": [], "done": []}

    for col_idx, col_key in enumerate(["waiting", "running", "done"]):
        bg, fg = COLORS[col_key]
        col_frame = tk.Frame(columns_frame, bg=bg)
        col_frame.grid(row=0, column=col_idx, sticky="nsew", padx=(0, 2))

        tk.Label(
            col_frame,
            text=COL_HEADERS[col_key],
            fg=fg,
            bg=bg,
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor=tk.W, padx=8, pady=(4, 2))

        listbox = tk.Listbox(
            col_frame,
            fg="#cdd6f4",
            bg="#11111b",
            selectbackground="#313244",
            relief=tk.FLAT,
            font=("Segoe UI", 8),
            activestyle="none",
        )
        listbox.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        task_vars[col_key] = [listbox]

    def _refresh_tasks() -> None:
        """Reload tasks from team_state into listboxes."""
        for col_key in ["waiting", "running", "done"]:
            lb = task_vars[col_key][0]
            lb.delete(0, tk.END)

        if widget._team_state is None or not widget.project_id:
            status_label.config(text="TeamState 또는 프로젝트 없음")
            return

        try:
            queue = widget._team_state.get_project_queue(widget.project_id)
        except Exception:
            queue = []

        for item in queue:
            task_type = item.get("type", item.get("task", "unknown"))
            status = item.get("status", "waiting")
            enqueued = item.get("enqueuedAt", "")[:16]
            display = f"{task_type}  ({enqueued})"

            if status in ("running", "in_progress"):
                target = "running"
            elif status in ("done", "completed", "approved"):
                target = "done"
            else:
                target = "waiting"

            lb = task_vars[target][0]
            lb.insert(tk.END, display)

        status_label.config(text=f"태스크 {len(queue)}개 로드됨")

    def _on_export() -> None:
        """Export codex packet for current project."""
        if widget._team_state is None or not widget.project_id:
            status_label.config(text="TeamState 또는 프로젝트 없음")
            return
        try:
            out_path = export_codex_packet(
                project_id=widget.project_id,
                team_state=widget._team_state,
                state=widget.state,
            )
            status_label.config(text=f"내보내기 완료: {out_path}")
        except Exception as e:
            status_label.config(text=f"내보내기 실패: {e}")

    def _on_import() -> None:
        """Import codex packet from file dialog."""
        from pathlib import Path
        from tkinter import filedialog

        from roost.packet import import_codex_packet

        if widget._team_state is None or not widget.project_id:
            status_label.config(text="TeamState 또는 프로젝트 없음")
            return
        packet_dir = Path.cwd() / "codex-packets"
        file_path = filedialog.askopenfilename(
            title="Import Codex Packet",
            initialdir=str(packet_dir) if packet_dir.exists() else str(Path.cwd()),
            filetypes=[("Codex Packet", "*.json")],
        )
        if not file_path:
            return
        try:
            import_codex_packet(file_path, widget._team_state)
            status_label.config(text=f"가져오기 완료: {Path(file_path).name}")
            _refresh_tasks()
        except Exception as e:
            status_label.config(text=f"가져오기 실패: {e}")

    export_btn.bind("<Button-1>", lambda e: _on_export())
    import_btn.bind("<Button-1>", lambda e: _on_import())
    refresh_btn.bind("<Button-1>", lambda e: _refresh_tasks())

    # Initial load
    parent.after(100, _refresh_tasks)


def _get_projects(widget: Any) -> list[dict]:
    """Get project list from registry or team state."""
    projects: list[dict] = []
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


def _build_endpoints_tab(
    tab: tk.Frame,
    widget: Any,
    hub: tk.Toplevel,
    status_label: tk.Label,
) -> None:
    """Build the Endpoints tab with endpoint registry, role mapping, and skills."""
    from roost.state import TeamState

    team_state = widget._team_state if hasattr(widget, "_team_state") else TeamState()
    endpoints_data = team_state._data.setdefault(
        "endpoints",
        {
            "local/fast": {"backend": "script", "cost": "free"},
            "remote/sota": {"backend": "hermes", "cost": "high"},
        },
    )

    # --- Endpoint Registry ---
    ep_label_frame = tk.LabelFrame(
        tab,
        text="Endpoint Registry",
        fg="#cdd6f4",
        bg="#1e1e2e",
        font=("Segoe UI", 9, "bold"),
    )
    ep_label_frame.pack(fill=tk.X, padx=8, pady=(8, 4))

    # Treeview for endpoints
    columns = ("alias", "backend", "cost")
    ep_tree = ttk.Treeview(ep_label_frame, columns=columns, show="headings", height=4)
    ep_tree.heading("alias", text="Alias")
    ep_tree.heading("backend", text="Backend")
    ep_tree.heading("cost", text="Cost")
    ep_tree.column("alias", width=140)
    ep_tree.column("backend", width=100)
    ep_tree.column("cost", width=60)
    ep_tree.pack(fill=tk.X, padx=4, pady=4)

    def _refresh_endpoints():
        ep_tree.delete(*ep_tree.get_children())
        for alias, info in endpoints_data.items():
            ep_tree.insert("", tk.END, values=(alias, info.get("backend", ""), info.get("cost", "")))

    _refresh_endpoints()

    # Buttons
    btn_frame = tk.Frame(ep_label_frame, bg="#1e1e2e")
    btn_frame.pack(fill=tk.X, padx=4, pady=(0, 4))

    def _test_endpoint():
        sel = ep_tree.selection()
        if not sel:
            status_label.config(text="Endpoint를 선택하세요")
            return
        alias = ep_tree.item(sel[0])["values"][0]
        backend_name = ep_tree.item(sel[0])["values"][1]
        from roost.dispatcher import BackendRegistry

        reg = BackendRegistry()
        try:
            cls = reg.get(backend_name)
            inst = cls()
            ok = inst.health_check()
            status_label.config(text=f"[Test] {alias}: {'OK' if ok else 'FAIL'}")
        except Exception as e:
            status_label.config(text=f"[Test] {alias}: ERROR — {e}")

    def _remove_endpoint():
        sel = ep_tree.selection()
        if not sel:
            return
        alias = ep_tree.item(sel[0])["values"][0]
        if alias in endpoints_data:
            del endpoints_data[alias]
            team_state.save()
            _refresh_endpoints()
            status_label.config(text=f"삭제: {alias}")

    tk.Button(btn_frame, text="+ Add", command=lambda: _add_endpoint_dialog()).pack(side=tk.LEFT, padx=(0, 4))
    tk.Button(btn_frame, text="Test", command=_test_endpoint).pack(side=tk.LEFT, padx=(0, 4))
    tk.Button(btn_frame, text="Remove", command=_remove_endpoint).pack(side=tk.LEFT)

    def _add_endpoint_dialog():
        dialog = tk.Toplevel(hub)
        dialog.title("Add Endpoint")
        dialog.geometry("300x160")
        dialog.configure(bg="#1e1e2e")
        dialog.resizable(False, False)

        tk.Label(dialog, text="Alias:", fg="#cdd6f4", bg="#1e1e2e").pack(anchor=tk.W, padx=8, pady=(8, 0))
        alias_entry = tk.Entry(dialog, bg="#313244", fg="#cdd6f4", insertbackground="#cdd6f4")
        alias_entry.pack(fill=tk.X, padx=8, pady=4)

        tk.Label(dialog, text="Backend:", fg="#cdd6f4", bg="#1e1e2e").pack(anchor=tk.W, padx=8)
        backend_var = tk.StringVar(value="hermes")
        backend_combo = ttk.Combobox(dialog, textvariable=backend_var, values=["script", "hermes"], state="readonly")
        backend_combo.pack(fill=tk.X, padx=8, pady=4)

        tk.Label(dialog, text="Cost:", fg="#cdd6f4", bg="#1e1e2e").pack(anchor=tk.W, padx=8)
        cost_var = tk.StringVar(value="high")
        cost_combo = ttk.Combobox(dialog, textvariable=cost_var, values=["free", "low", "high"], state="readonly")
        cost_combo.pack(fill=tk.X, padx=8, pady=4)

        def _save():
            alias = alias_entry.get().strip()
            if alias and alias not in endpoints_data:
                endpoints_data[alias] = {"backend": backend_var.get(), "cost": cost_var.get()}
                team_state.save()
                _refresh_endpoints()
                status_label.config(text=f"추가: {alias}")
            dialog.destroy()

        tk.Button(dialog, text="Save", command=_save).pack(pady=(4, 8))

    # --- Role Mapping ---
    role_frame = tk.LabelFrame(
        tab,
        text="Role Mapping",
        fg="#cdd6f4",
        bg="#1e1e2e",
        font=("Segoe UI", 9, "bold"),
    )
    role_frame.pack(fill=tk.X, padx=8, pady=4)

    role_backend_map = team_state._data.setdefault(
        "role_backends",
        {
            "scout": "script",
            "coordinator": "hermes",
            "lead": "hermes",
        },
    )
    all_ep_aliases = list(endpoints_data.keys())

    for role_name, default_be in [("scout", "script"), ("coordinator", "hermes"), ("lead", "hermes")]:
        row = tk.Frame(role_frame, bg="#1e1e2e")
        row.pack(fill=tk.X, padx=4, pady=2)
        tk.Label(row, text=f"{role_name.capitalize()}:", fg="#cdd6f4", bg="#1e1e2e", width=14, anchor=tk.W).pack(
            side=tk.LEFT
        )
        var = tk.StringVar(value=role_backend_map.get(role_name, default_be))
        cb = ttk.Combobox(row, textvariable=var, values=all_ep_aliases, state="readonly", width=20)
        cb.pack(side=tk.LEFT, padx=(0, 4))

        def _save_role(rn=role_name, v=var):
            role_backend_map[rn] = v.get()
            team_state.save()
            status_label.config(text=f"Role 매핑 저장: {rn} → {v.get()}")

        var.trace_add("write", lambda *a, f=_save_role: f())

    # --- Skills ---
    skills_frame = tk.LabelFrame(
        tab,
        text="Skills",
        fg="#cdd6f4",
        bg="#1e1e2e",
        font=("Segoe UI", 9, "bold"),
    )
    skills_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

    skills_data = team_state._data.setdefault(
        "skills",
        {
            "file-scan": {"enabled": True, "endpoint": "local/fast"},
            "log-summary": {"enabled": True, "endpoint": "local/fast"},
            "draft-packet": {"enabled": True, "endpoint": "local/fast"},
            "deploy": {"enabled": False, "endpoint": "remote/sota"},
            "team-reconfigure": {"enabled": False, "endpoint": "remote/sota"},
        },
    )

    for skill_id, skill_info in skills_data.items():
        row = tk.Frame(skills_frame, bg="#1e1e2e")
        row.pack(fill=tk.X, padx=4, pady=1)
        var = tk.BooleanVar(value=skill_info.get("enabled", False))

        def _toggle(sid=skill_id, v=var):
            skills_data[sid]["enabled"] = v.get()
            team_state.save()
            status_label.config(text=f"Skill {'ON' if v.get() else 'OFF'}: {sid}")

        cb = tk.Checkbutton(
            row,
            text=skill_id,
            variable=var,
            command=_toggle,
            fg="#cdd6f4",
            bg="#1e1e2e",
            selectcolor="#313244",
            activeforeground="#cdd6f4",
            activebackground="#1e1e2e",
        )
        cb.pack(side=tk.LEFT)
        ep_str = skill_info.get("endpoint", "")
        tk.Label(row, text=f"→ {ep_str}", fg="#6c7086", bg="#1e1e2e").pack(side=tk.RIGHT, padx=4)


def _close_hub(widget: Any, hub: tk.Toplevel) -> None:
    widget._hub_window = None
    try:
        hub.destroy()
    except tk.TclError:
        pass
