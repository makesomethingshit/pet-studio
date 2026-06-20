"""Project Hub panel for Pet Studio Widget.

Provides a Toplevel window with projects, tasks, team status, and endpoint settings.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Mapping
from tkinter import ttk
from typing import Any

from roost.model_profile import (
    model_profile_powershell_env_lines,
    model_profile_tier,
    role_model_plan_powershell_env_lines,
)
from roost.packet import export_work_packet

# Lazy import to avoid circular dependency
_api_key_wizard = None


def _get_api_key_wizard():
    global _api_key_wizard
    if _api_key_wizard is None:
        from ui.api_key_wizard import show_api_key_wizard
        _api_key_wizard = show_api_key_wizard
    return _api_key_wizard


# ---------------------------------------------------------------------------
# User-friendly error messages (비전공자 타겟)
# ---------------------------------------------------------------------------

_USER_MESSAGES: dict[str, str] = {
    # 내부 키 → 사용자 친화적 메시지
    "export_failed": "내보내기에 실패했습니다. 프로젝트를 먼저 선택해주세요.",
    "import_failed": "가져오기에 실패했습니다. 파일 경로를 확인해주세요.",
    "switch_failed": "프로젝트 전환에 실패했습니다. 프로젝트를 선택해주세요.",
    "model_switch_failed": "모델 변경에 실패했습니다. 인터넷 연결을 확인해주세요.",
    "team_preset_failed": "팀 모드 변경에 실패했습니다.",
    "team_state_unavailable": "팀 상태를 불러올 수 없습니다. 다시 시작해주세요.",
    "select_project_first": "프로젝트를 먼저 선택해주세요.",
    "select_task_first": "태스크를 먼저 선택해주세요.",
    "select_staff_first": "스태프를 먼저 선택해주세요.",
    "staff_id_required": "스태프 이름을 입력해주세요.",
    "no_tier_model": "해당 등급의 모델이 없습니다.",
    "mission_saved": "미션이 저장되었습니다 ✓",
    "staff_added": "스태프가 추가되었습니다 ✓",
    "staff_exists": "이미 등록된 스태프입니다.",
    "task_loaded": "태스크를 불러왔습니다 ✓",
    "exported": "패킷을 내보냈습니다 ✓",
    "imported": "패킷을 가져왔습니다 ✓",
    "tasks_cleared": "태스크를 비웠습니다 ✓",
    "queue_empty": "대기열이 비어있습니다.",
    "no_staff": "등록된 스태프가 없습니다. 스태프를 먼저 추가해주세요.",
    "no_approvals": "대기 중인 승인이 없습니다.",
    "approval_resolved": "승인이 처리되었습니다 ✓",
    "dequeued": "작업을 시작했습니다 ✓",
    "dropped": "작업을 제거했습니다 ✓",
    "routed": "작업을 프로젝트로 연결했습니다 ✓",
    "role_saved": "역할이 저장되었습니다 ✓",
    "preset_applied": "프리셋이 적용되었습니다 ✓",
    "switched": "프로젝트를 전환했습니다 ✓",
    "team_room_loaded": "팀 룸을 불러왔습니다 ✓",
    "no_project": "프로젝트가 없습니다. 새 프로젝트를 만들어보세요.",
    "no_tasks": "태스크가 없습니다. 미션을 입력하면 자동으로 생성됩니다.",
    "no_endpoints": "엔드포인트가 없습니다.",
    "no_model_profiles": "모델 프로필이 없습니다.",
}


def _msg(key: str, **kwargs) -> str:
    """Return a user-friendly message by key, with optional format args."""
    text = _USER_MESSAGES.get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


def _friendly_error(e: Exception) -> str:
    """Convert a technical exception to a user-friendly Korean message."""
    text = str(e)
    # 네트워크 관련
    if any(kw in text.lower() for kw in ("connection", "timeout", "network", "unreachable", "refused")):
        return "인터넷 연결을 확인해주세요."
    # 파일 관련
    if any(kw in text.lower() for kw in ("file", "path", "not found", "no such", "permission")):
        return "파일 경로를 확인해주세요."
    # JSON 관련
    if any(kw in text.lower() for kw in ("json", "decode", "parse")):
        return "파일 형식이 올바르지 않습니다."
    # API 관련
    if any(kw in text.lower() for kw in ("api", "key", "auth", "401", "403", "429")):
        return "API 키를 확인해주세요."
    # 기본
    return "문제가 발생했습니다. 다시 시도해주세요."





def _powershell_env_lines_for_profile(profile: Mapping[str, Any] | None) -> list[str]:
    return model_profile_powershell_env_lines(profile)


def _powershell_env_lines_for_role_plan(role_model_plan: list[Mapping[str, Any]]) -> list[str]:
    return role_model_plan_powershell_env_lines(role_model_plan)


def _workroom_geometry(saved: dict[str, int] | None) -> str:
    width = saved.get("width", 900) if saved else 900
    height = saved.get("height", 640) if saved else 640
    geometry = f"{width}x{height}"
    if saved and isinstance(saved.get("x"), int) and isinstance(saved.get("y"), int):
        geometry += f"+{saved['x']}+{saved['y']}"
    return geometry


def _summary_lines(widget: Any) -> tuple[str, str]:
    project_id = getattr(widget, "project_id", None)
    display_name = getattr(widget, "_project_display_name", None) or project_id or "No project"
    status = getattr(widget, "state", "idle") or "idle"
    mission = "No mission"
    model_profile = "open-sota openrouter/sota"
    team_state = getattr(widget, "_team_state", None)
    if team_state is not None and project_id:
        project = team_state.get_project(project_id) or {}
        status = project.get("status", status)
        mission = project.get("mission") or mission
        f"L{project.get('securityLevel', 1)}"
        if hasattr(team_state, "get_active_model_profile_id"):
            active_profile = team_state.get_active_model_profile() if hasattr(team_state, "get_active_model_profile") else {}
            active_profile_id = active_profile.get("id") or team_state.get_active_model_profile_id()
            model_profile = f"{model_profile_tier(active_profile)} {active_profile_id}"
        if hasattr(team_state, "get_team_model_preset_id"):
            team_state.get_team_model_preset_id()
        role_parts = _role_model_plan_parts(team_state)
        if not role_parts:
            for role in ("scout", "coordinator", "lead"):
                if hasattr(team_state, "auto_select_endpoint"):
                    endpoint = team_state.auto_select_endpoint(role)
                else:
                    endpoint = team_state.get_role_backend(role)
                role_parts.append(f"{role.capitalize()} {endpoint}")
        " | ".join(role_parts)
    return (
        f"{display_name} ({project_id or 'no-project'})",
        f"{mission}  |  {status}  |  {model_profile}",
    )


def _role_model_plan_parts(team_state: Any) -> list[str]:
    if not hasattr(team_state, "list_role_model_plan"):
        return []
    parts = []
    for item in team_state.list_role_model_plan():
        role = str(item.get("role", "")).capitalize()
        profile = item.get("profile", {}) if isinstance(item.get("profile"), dict) else {}
        tier = profile.get("tier", "")
        profile_id = profile.get("id", "")
        parts.append(f"{role} {tier}/{profile_id}")
    return parts


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

    is_workroom = bool(getattr(widget, "_workroom_mode", False))
    hub = tk.Toplevel(widget.root)
    hub.title("Pet Studio Workroom" if is_workroom else "Project Hub")
    if is_workroom:
        hub.geometry(_workroom_geometry(getattr(widget, "_workroom_window", None)))
    else:
        hub.geometry("560x480")
    hub.resizable(True, True)
    hub.configure(bg="#1e1e2e")

    widget._hub_window = hub

    # --- Header ---
    # Workroom: 2-row header (title row + controls row)
    # Normal: single 36px title bar
    if is_workroom:
        header_top = tk.Frame(hub, bg="#181825", height=40)
        header_top.pack(fill=tk.X, padx=0, pady=0)
        header_top.pack_propagate(False)
        header_text = tk.Frame(header_top, bg="#181825")
        header_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12, pady=6)
    else:
        header = tk.Frame(hub, bg="#181825", height=36)
        header.pack(fill=tk.X, padx=0, pady=0)
        header.pack_propagate(False)
        header_text = tk.Frame(header, bg="#181825")
        header_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=12, pady=6)
    tk.Label(
        header_text,
        text="Pet Studio Workroom" if is_workroom else "Project Hub",
        fg="#cdd6f4",
        bg="#181825",
        font=("Segoe UI", 11, "bold"),
    ).pack(anchor=tk.W)

    summary_label = tk.Label(
        header_text,
        text="",
        fg="#6c7086",
        bg="#181825",
        font=("Segoe UI", 8),
    )
    meta_label = tk.Label(
        header_text,
        text="",
        fg="#585b70",
        bg="#181825",
        font=("Segoe UI", 8),
    )
    if is_workroom:
        summary_label.pack(anchor=tk.W)
        meta_label.pack(anchor=tk.W)

    model_var = tk.StringVar()
    team_preset_var = tk.StringVar()
    model_picker = None
    team_preset_picker = None
    quick_model_buttons: dict[str, tk.Button] = {}
    if is_workroom and getattr(widget, "_team_state", None) is not None:
        profiles = widget._team_state.list_model_profiles()
        profile_ids = [profile["id"] for profile in profiles]
        # Controls row: model/preset/tier buttons
        header_bot = tk.Frame(hub, bg="#181825", height=68)
        header_bot.pack(fill=tk.X, padx=0, pady=0)
        header_bot.pack_propagate(False)
        model_panel = tk.Frame(header_bot, bg="#181825")
        model_panel.pack(side=tk.LEFT, padx=12, pady=8)
        tk.Label(
            model_panel,
            text="Active model",
            fg="#6c7086",
            bg="#181825",
            font=("Segoe UI", 8),
        ).pack(anchor=tk.W)
        model_var.set(widget._team_state.get_active_model_profile_id())
        model_picker = ttk.Combobox(
            model_panel,
            textvariable=model_var,
            values=profile_ids,
            state="readonly",
            width=22,
        )
        model_picker.pack(anchor=tk.W)
        tk.Label(
            model_panel,
            text="Team mode",
            fg="#6c7086",
            bg="#181825",
            font=("Segoe UI", 8),
        ).pack(anchor=tk.W, pady=(4, 0))
        preset_ids = [preset["id"] for preset in widget._team_state.list_team_model_presets()]
        team_preset_var.set(widget._team_state.get_team_model_preset_id())
        team_preset_picker = ttk.Combobox(
            model_panel,
            textvariable=team_preset_var,
            values=preset_ids,
            state="readonly",
            width=22,
        )
        team_preset_picker.pack(anchor=tk.W)
        quick_frame = tk.Frame(model_panel, bg="#181825")
        quick_frame.pack(anchor=tk.W, pady=(4, 0))
        # Row 1: Closed, Open SOTA, Local
        row1 = tk.Frame(quick_frame, bg="#181825")
        row1.pack(anchor=tk.W)
        for tier, label in (
            ("closed", "Closed"),
            ("open-sota", "Open SOTA"),
            ("local", "Local"),
        ):
            btn = tk.Button(
                row1,
                text=label,
                command=lambda selected=tier: _select_model_tier(selected),
                fg="#cdd6f4",
                bg="#313244",
                activeforeground="#11111b",
                activebackground="#a6e3a1",
                relief=tk.FLAT,
                padx=6,
                pady=1,
                font=("Segoe UI", 8),
            )
            btn.pack(side=tk.LEFT, padx=(0, 3))
            quick_model_buttons[tier] = btn
        # Row 2: Value, Free
        row2 = tk.Frame(quick_frame, bg="#181825")
        row2.pack(anchor=tk.W, pady=(3, 0))
        for tier, label in (
            ("value", "Value"),
            ("free", "Free"),
        ):
            btn = tk.Button(
                row2,
                text=label,
                command=lambda selected=tier: _select_model_tier(selected),
                fg="#cdd6f4",
                bg="#313244",
                activeforeground="#11111b",
                activebackground="#a6e3a1",
                relief=tk.FLAT,
                padx=6,
                pady=1,
                font=("Segoe UI", 8),
            )
            btn.pack(side=tk.LEFT, padx=(0, 3))
            quick_model_buttons[tier] = btn

    def _refresh_summary() -> None:
        summary, meta = _summary_lines(widget)
        summary_label.config(text=summary)
        meta_label.config(text=meta)

    def _profile_for_tier(tier: str) -> dict[str, Any] | None:
        if getattr(widget, "_team_state", None) is None:
            return None
        for profile in widget._team_state.list_model_profiles():
            if profile.get("tier") == tier:
                return profile
        return None

    def _refresh_model_choices() -> None:
        if model_picker is None or getattr(widget, "_team_state", None) is None:
            return
        profile_ids = [profile["id"] for profile in widget._team_state.list_model_profiles()]
        model_picker.configure(values=profile_ids)
        current = widget._team_state.get_active_model_profile_id()
        if current in profile_ids:
            model_var.set(current)
        active_profile = widget._team_state.get_active_model_profile()
        active_tier = model_profile_tier(active_profile)
        for tier, button in quick_model_buttons.items():
            if tier == active_tier:
                button.config(bg="#89b4fa", fg="#11111b")
            else:
                button.config(bg="#313244", fg="#cdd6f4")
        if team_preset_picker is not None:
            preset_ids = [preset["id"] for preset in widget._team_state.list_team_model_presets()]
            team_preset_picker.configure(values=preset_ids)
            current_preset = widget._team_state.get_team_model_preset_id()
            if current_preset in preset_ids or current_preset == "custom":
                team_preset_var.set(current_preset)
        _refresh_summary()

    def _refresh_credit_plan_from_header() -> None:
        refresh_credit_plan = getattr(widget, "_refresh_project_hub_credit_plan", None)
        if callable(refresh_credit_plan):
            refresh_credit_plan()

    def _save_model_profile(_event: tk.Event | None = None) -> None:
        if not is_workroom or getattr(widget, "_team_state", None) is None:
            return
        try:
            widget._team_state.set_active_model_profile(getattr(widget, "project_id", None), model_var.get())
            _refresh_summary()
            _refresh_credit_plan_from_header()
            status_label.config(text=f"모델이 변경되었습니다: {model_var.get()}")
        except Exception as e:
            status_label.config(text=_friendly_error(e))

    def _save_team_model_preset(_event: tk.Event | None = None) -> None:
        if not is_workroom or getattr(widget, "_team_state", None) is None:
            return
        try:
            widget._team_state.apply_team_model_preset(team_preset_var.get(), project_id=getattr(widget, "project_id", None))
            _refresh_model_choices()
            _refresh_credit_plan_from_header()
            status_label.config(text=f"팀 모드가 변경되었습니다: {team_preset_var.get()}")
        except Exception as e:
            status_label.config(text=_friendly_error(e))

    def _select_model_tier(tier: str) -> None:
        if not is_workroom or getattr(widget, "_team_state", None) is None:
            return
        profile = _profile_for_tier(tier)
        if profile is None:
            status_label.config(text=_msg("no_tier_model"))
            return
        try:
            profile_id = profile["id"]
            widget._team_state.set_active_model_profile(getattr(widget, "project_id", None), profile_id)
            model_var.set(profile_id)
            _refresh_model_choices()
            _refresh_credit_plan_from_header()
            status_label.config(text=f"모델이 변경되었습니다: {tier} {profile_id}")
        except Exception as e:
            status_label.config(text=_friendly_error(e))

    if model_picker is not None:
        model_picker.bind("<<ComboboxSelected>>", _save_model_profile)
    if team_preset_picker is not None:
        team_preset_picker.bind("<<ComboboxSelected>>", _save_team_model_preset)

    widget._refresh_project_hub_summary = _refresh_summary
    widget._refresh_project_hub_model_profiles = _refresh_model_choices
    _refresh_summary()

    # --- Notebook (Projects / Tasks) ---
    notebook = ttk.Notebook(hub)
    notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 0))

    # Tab 1: Projects
    projects_tab = tk.Frame(notebook, bg="#1e1e2e")
    notebook.add(projects_tab, text="Projects")

    # Tab 2: Tasks
    tasks_tab = tk.Frame(notebook, bg="#1e1e2e")
    notebook.add(tasks_tab, text="Tasks")

    # Tab 3: Team Room
    team_tab = tk.Frame(notebook, bg="#1e1e2e")
    notebook.add(team_tab, text="Team Room")

    # Tab 4: Endpoints
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

    # ===== Team Room Tab =====
    _build_team_room_tab(team_tab, widget, status_label)

    # ===== Endpoints Tab =====
    _build_endpoints_tab(endpoints_tab, widget, hub, status_label)

    # --- Close handler ---
    def _on_close() -> None:
        widget._hub_window = None
        if is_workroom and hasattr(widget, "save_workroom_window"):
            widget.save_workroom_window(hub)
        hub.destroy()
        if is_workroom:
            widget.root.destroy()

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
    list_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(8, 4))

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

    # Mission input (hidden until project selected)
    mission_frame = tk.Frame(parent, bg="#181825", height=72)
    mission_frame.pack(fill=tk.X, padx=4, pady=(2, 4))
    mission_frame.pack_propagate(False)
    mission_frame.pack_forget()  # hidden initially

    tk.Label(
        mission_frame,
        text="Mission",
        fg="#6c7086",
        bg="#181825",
        font=("Segoe UI", 8),
    ).pack(anchor=tk.W, padx=8, pady=(4, 0))

    mission_var = tk.StringVar()
    mission_row = tk.Frame(mission_frame, bg="#181825")
    mission_row.pack(fill=tk.X, padx=8, pady=(4, 2))
    mission_entry = tk.Entry(
        mission_row,
        textvariable=mission_var,
        fg="#cdd6f4",
        bg="#11111b",
        insertbackground="#cdd6f4",
        relief=tk.FLAT,
        font=("Segoe UI", 9),
    )
    mission_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    save_btn = tk.Label(
        mission_row,
        text="Save",
        fg="#89b4fa",
        bg="#181825",
        font=("Segoe UI", 8, "underline"),
        cursor="hand2",
    )
    save_btn.pack(side=tk.RIGHT, padx=(8, 0))

    # Populate
    projects = _get_projects(widget)
    current_id = widget.project_id
    project_map = {p["id"]: p for p in projects}

    STATUS_DISPLAY = {
        "idle": "Idle",
        "running": "Running",
        "waiting": "Waiting",
        "review": "Review",
        "failed": "Failed",
        "blocked": "Blocked",
        "done": "Done",
    }

    for p in projects:
        pid = p["id"]
        name = p.get("displayName", pid)
        status = p.get("status", "idle")
        label = STATUS_DISPLAY.get(status, status)
        tags = ("current",) if pid == current_id else ()
        tree.insert("", tk.END, iid=pid, values=(name, label), tags=tags)

    tree.tag_configure("current", foreground="#a6e3a1")

    # Empty state hint (shown when no projects exist)
    empty_frame = tk.Frame(parent, bg="#1e1e2e")
    empty_hint = tk.Label(
        empty_frame,
        text="프로젝트가 없습니다.",
        fg="#6c7086",
        bg="#1e1e2e",
        font=("Segoe UI", 10, "bold"),
    )
    empty_hint.pack(pady=(12, 4))
    empty_sub = tk.Label(
        empty_frame,
        text="API 키를 연결하면 AI 팀을 바로 시작할 수 있습니다.",
        fg="#585b70",
        bg="#1e1e2e",
        font=("Segoe UI", 9),
    )
    empty_sub.pack(pady=(0, 8))

    api_key_btn = tk.Label(
        empty_frame,
        text="🔑  API 키 연결하기",
        fg="#89b4fa",
        bg="#1e1e2e",
        font=("Segoe UI", 9, "underline"),
        cursor="hand2",
    )
    api_key_btn.pack(pady=(0, 4))
    api_key_btn.bind(
        "<Button-1>",
        lambda e: _get_api_key_wizard()(hub, getattr(widget, "_team_state", None)),
    )

    if not projects:
        empty_frame.pack(pady=12)

    # Handlers
    def _on_select(event: tk.Event) -> None:
        sel = tree.selection()
        if not sel:
            mission_frame.pack_forget()
            return
        pid = sel[0]
        p = project_map.get(pid, {})
        mission_var.set(p.get("mission", ""))
        mission_frame.pack(fill=tk.X, padx=4, pady=(4, 8), after=tree.master)
        if pid == current_id:
            status_label.config(text="현재 프로젝트입니다")
        else:
            status_label.config(text="더블클릭으로 전환")

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
            status_label.config(text=_msg("select_project_first"))
            return
        pid = sel[0]
        mission = mission_var.get().strip()
        if widget._team_state is not None:
            widget._team_state.set_project_mission(pid, mission)
            if pid in project_map:
                project_map[pid]["mission"] = mission
            refresh_summary = getattr(widget, "_refresh_project_hub_summary", None)
            if callable(refresh_summary):
                refresh_summary()
            status_label.config(text=_msg("mission_saved"))
        else:
            status_label.config(text=_msg("team_state_unavailable"))

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
        text="Export Work Packet",
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
        text="Refresh",
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
    COL_HEADERS = {"waiting": "Waiting", "running": "Running", "done": "Done"}

    task_vars: dict[str, list] = {"waiting": [], "running": [], "done": []}
    task_indexes: dict[str, list[int]] = {"waiting": [], "running": [], "done": []}

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

    action_bar = tk.Frame(parent, bg="#1e1e2e")
    action_bar.pack(fill=tk.X, padx=4, pady=(0, 4))

    # Empty state for tasks tab
    tasks_empty_hint = tk.Label(
        parent,
        text="태스크가 없습니다. 미션을 입력하면 자동으로 생성됩니다.",
        fg="#6c7086",
        bg="#1e1e2e",
        font=("Segoe UI", 9),
    )

    def _show_tasks_empty(show: bool) -> None:
        if show:
            tasks_empty_hint.pack(pady=12)
        else:
            tasks_empty_hint.pack_forget()

    # Check if all columns are empty
    all_empty = all(task_vars[k][0].size() == 0 for k in ("waiting", "running", "done"))
    _show_tasks_empty(all_empty)
    staff_var = tk.StringVar(value="")
    staff_combo = ttk.Combobox(action_bar, textvariable=staff_var, state="readonly", width=22)

    def _selected_task_index() -> int | None:
        for col_key in ["waiting", "running", "done"]:
            lb = task_vars[col_key][0]
            selection = lb.curselection()
            if not selection:
                continue
            idx = selection[0]
            if idx < len(task_indexes[col_key]):
                return task_indexes[col_key][idx]
        return None

    def _task_update(updates: dict[str, Any], message: str) -> None:
        if widget._team_state is None or not widget.project_id:
            status_label.config(text=_msg("team_state_unavailable"))
            return
        task_index = _selected_task_index()
        if task_index is None:
            status_label.config(text=_msg("select_task_first"))
            return
        item = widget._team_state.update_project_queue_item(widget.project_id, task_index, updates)
        _refresh_tasks()
        status_label.config(text=message if item else _msg("no_tasks"))

    def _assign_role(role: str) -> None:
        _task_update({"assignedRole": role}, f"Assigned task to {role}")

    def _assign_staff() -> None:
        selected = staff_var.get()
        if not selected:
            status_label.config(text=_msg("select_staff_first"))
            return
        employee_id, _, label = selected.partition(" ")
        updates = {"assignedEmployee": employee_id}
        if label:
            role = label.strip("() ")
            if role:
                updates["assignedRole"] = role
        _task_update(updates, f"Assigned task to {employee_id}")

    def _set_task_status(status: str) -> None:
        _task_update({"status": status}, f"Marked task {status}")

    def _refresh_tasks() -> None:
        """Reload tasks from team_state into listboxes."""
        for col_key in ["waiting", "running", "done"]:
            lb = task_vars[col_key][0]
            lb.delete(0, tk.END)
            task_indexes[col_key].clear()

        if widget._team_state is None or not widget.project_id:
            status_label.config(text=_msg("team_state_unavailable"))
            return

        try:
            queue = widget._team_state.get_project_queue(widget.project_id)
        except Exception:
            queue = []

        staff_values = []
        try:
            for emp in widget._team_state.get_employees():
                employee_id = emp.get("id", "")
                if employee_id:
                    staff_values.append(f"{employee_id} ({emp.get('role', 'worker')})")
        except Exception:
            staff_values = []
        staff_combo.configure(values=staff_values)
        if staff_values and staff_var.get() not in staff_values:
            staff_var.set(staff_values[0])
        elif not staff_values:
            staff_var.set("")

        for index, item in enumerate(queue):
            task_type = item.get("type", item.get("task", "unknown"))
            status = item.get("status", "waiting")
            enqueued = item.get("enqueuedAt", "")[:16]
            display = f"{task_type}  ({enqueued})"
            assignment = item.get("assignedEmployee") or item.get("assignedRole")
            if assignment:
                display = f"{display}  -> {assignment}"

            if status in ("running", "in_progress"):
                target = "running"
            elif status in ("done", "completed", "approved"):
                target = "done"
            else:
                target = "waiting"

            lb = task_vars[target][0]
            lb.insert(tk.END, display)
            task_indexes[target].append(index)

        status_label.config(text=_msg("task_loaded"))

    def _on_export() -> None:
        """Export work packet for current project."""
        if widget._team_state is None or not widget.project_id:
            status_label.config(text=_msg("team_state_unavailable"))
            return
        try:
            export_work_packet(
                project_id=widget.project_id,
                team_state=widget._team_state,
                state=widget.state,
            )
            status_label.config(text=_msg("exported"))
        except Exception as e:
            status_label.config(text=_friendly_error(e))

    def _on_import() -> None:
        """Import work packet from file dialog."""
        from pathlib import Path
        from tkinter import filedialog

        from roost.packet import import_work_packet

        if widget._team_state is None or not widget.project_id:
            status_label.config(text=_msg("team_state_unavailable"))
            return
        packet_dir = Path.cwd() / "work-packets"
        legacy_packet_dir = Path.cwd() / "codex-packets"
        initial_dir = packet_dir if packet_dir.exists() else legacy_packet_dir
        file_path = filedialog.askopenfilename(
            title="Import Work Packet",
            initialdir=str(initial_dir) if initial_dir.exists() else str(Path.cwd()),
            filetypes=[("Work Packet", "*.json")],
        )
        if not file_path:
            return
        try:
            import_work_packet(file_path, widget._team_state)
            status_label.config(text=_msg("imported"))
            _refresh_tasks()
        except Exception as e:
            status_label.config(text=_friendly_error(e))

    export_btn.bind("<Button-1>", lambda e: _on_export())
    import_btn.bind("<Button-1>", lambda e: _on_import())
    refresh_btn.bind("<Button-1>", lambda e: _refresh_tasks())

    tk.Button(action_bar, text="Scout", command=lambda: _assign_role("scout")).pack(side=tk.LEFT, padx=(0, 4))
    tk.Button(action_bar, text="Coordinator", command=lambda: _assign_role("coordinator")).pack(side=tk.LEFT, padx=(0, 4))
    tk.Button(action_bar, text="Lead", command=lambda: _assign_role("lead")).pack(side=tk.LEFT, padx=(0, 10))
    staff_combo.pack(side=tk.LEFT, padx=(0, 4))
    tk.Button(action_bar, text="Assign staff", command=_assign_staff).pack(side=tk.LEFT, padx=(0, 10))
    tk.Button(action_bar, text="Start", command=lambda: _set_task_status("running")).pack(side=tk.LEFT, padx=(0, 4))
    tk.Button(action_bar, text="Done", command=lambda: _set_task_status("done")).pack(side=tk.LEFT)

    # Initial load
    parent.after(100, _refresh_tasks)


def _build_team_room_tab(
    parent: tk.Frame,
    widget: Any,
    status_label: tk.Label,
) -> None:
    toolbar = tk.Frame(parent, bg="#181825", height=28)
    toolbar.pack(fill=tk.X, padx=4, pady=(4, 2))
    toolbar.pack_propagate(False)

    refresh_btn = tk.Label(
        toolbar,
        text="Refresh",
        fg="#89b4fa",
        bg="#181825",
        font=("Segoe UI", 8, "underline"),
        cursor="hand2",
    )
    refresh_btn.pack(side=tk.RIGHT, padx=8, pady=4)

    columns_frame = tk.Frame(parent, bg="#1e1e2e")
    columns_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=(2, 4))
    for i in range(3):
        columns_frame.columnconfigure(i, weight=1, uniform="team")
    columns_frame.rowconfigure(0, weight=1)

    panels: dict[str, tk.Listbox] = {}
    # Approvals and Queue stay as single panels
    for idx, title in enumerate(("Approvals", "Queue")):
        frame = tk.Frame(columns_frame, bg="#181825")
        frame.grid(row=0, column=idx, sticky="nsew", padx=(0, 2))
        tk.Label(
            frame,
            text=title,
            fg="#cdd6f4",
            bg="#181825",
            font=("Segoe UI", 9, "bold"),
        ).pack(anchor=tk.W, padx=8, pady=(4, 2))
        box = tk.Listbox(
            frame,
            fg="#cdd6f4",
            bg="#11111b",
            selectbackground="#313244",
            relief=tk.FLAT,
            font=("Segoe UI", 8),
            activestyle="none",
        )
        box.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        panels[title] = box

    # Staff panel: 3 role groups (Scout / Coordinator / Lead)
    staff_col = tk.Frame(columns_frame, bg="#181825")
    staff_col.grid(row=0, column=1, sticky="nsew", padx=(0, 2))
    tk.Label(
        staff_col,
        text="Staff",
        fg="#cdd6f4",
        bg="#181825",
        font=("Segoe UI", 9, "bold"),
    ).pack(anchor=tk.W, padx=8, pady=(4, 2))

    staff_inner = tk.Frame(staff_col, bg="#181825")
    staff_inner.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

    ROLE_ORDER = ("scout", "coordinator", "lead")
    ROLE_LABELS = {"scout": "Scout", "coordinator": "Coordinator", "lead": "Lead"}
    ROLE_COLORS = {"scout": "#89b4fa", "coordinator": "#f9e2af", "lead": "#a6e3a1"}
    role_boxes: dict[str, tk.Listbox] = {}
    for role in ROLE_ORDER:
        inner_h = 66
        role_frame = tk.Frame(staff_inner, bg="#181825", height=inner_h)
        role_frame.pack(fill=tk.X, pady=(2, 0))
        role_frame.pack_propagate(False)
        role_frame.grid_propagate(False)
        tk.Label(
            role_frame,
            text=ROLE_LABELS[role],
            fg=ROLE_COLORS[role],
            bg="#181825",
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor=tk.W, padx=4, pady=(2, 0))
        rb = tk.Listbox(
            role_frame,
            fg="#cdd6f4",
            bg="#11111b",
            selectbackground="#313244",
            relief=tk.FLAT,
            font=("Segoe UI", 8),
            activestyle="none",
            height=2,
        )
        rb.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 2))
        role_boxes[role] = rb
        panels[f"staff_{role}"] = rb

    pending_ids: list[str] = []
    queue_indexes: list[int] = []

    def _refresh() -> None:
        pending_ids.clear()
        queue_indexes.clear()
        for box in panels.values():
            box.delete(0, tk.END)
        if widget._team_state is None:
            status_label.config(text=_msg("team_state_unavailable"))
            return

        pending = widget._team_state.get_pending_approvals()
        employees = widget._team_state.get_employees()
        queue = widget._team_state.get_roost_queue()

        for item in pending[:20]:
            pending_ids.append(item.get("id", ""))
            project_id = item.get("projectId", "")
            action = item.get("action", "?")
            panels["Approvals"].insert(tk.END, f"{action} ({project_id})" if project_id else action)
        if not pending:
            panels["Approvals"].insert(tk.END, "No pending approvals")

        # Staff: group by role
        for role in ROLE_ORDER:
            box = panels[f"staff_{role}"]
            box.delete(0, tk.END)
        for emp in employees:
            name = emp.get("name", emp.get("id", "?"))
            role = emp.get("role", "worker")
            status = emp.get("status", "idle")
            box_key = f"staff_{role}"
            if box_key in panels:
                panels[box_key].insert(tk.END, f"{name} ({status})")
        for role in ROLE_ORDER:
            box = panels[f"staff_{role}"]
            if box.size() == 0:
                box.insert(tk.END, "—")

        for idx, item in enumerate(queue[:20]):
            queue_indexes.append(idx)
            panels["Queue"].insert(tk.END, item.get("type", "unknown"))
        if not queue:
            panels["Queue"].insert(tk.END, "Queue empty")

        status_label.config(text=_msg("team_room_loaded"))

    def _resolve_selected(approved: bool) -> None:
        if widget._team_state is None:
            return
        selection = panels["Approvals"].curselection()
        if not selection:
            return
        idx = selection[0]
        if idx >= len(pending_ids) or not pending_ids[idx]:
            return
        widget._team_state.resolve_approval(pending_ids[idx], approved)
        _refresh()

    def _dequeue_next() -> None:
        if widget._team_state is None:
            return
        item = widget._team_state.dequeue_roost()
        _refresh()
        status_label.config(text=_msg("dequeued") if item else _msg("queue_empty"))

    def _drop_selected_queue_item() -> None:
        if widget._team_state is None:
            return
        selection = panels["Queue"].curselection()
        if not selection:
            return
        idx = selection[0]
        if idx >= len(queue_indexes):
            return
        item = widget._team_state.remove_roost_queue_item(queue_indexes[idx])
        _refresh()
        status_label.config(text=_msg("dropped") if item else _msg("queue_empty"))

    def _route_selected_queue_item() -> None:
        if widget._team_state is None or not widget.project_id:
            return
        selection = panels["Queue"].curselection()
        if not selection:
            return
        idx = selection[0]
        if idx >= len(queue_indexes):
            return
        item = widget._team_state.route_roost_queue_item_to_project(queue_indexes[idx], widget.project_id)
        _refresh()
        status_label.config(text=_msg("routed") if item else _msg("queue_empty"))

    def _add_staff_dialog() -> None:
        if widget._team_state is None:
            status_label.config(text=_msg("team_state_unavailable"))
            return
        dialog = tk.Toplevel(parent.winfo_toplevel())
        dialog.title("Add staff")
        dialog.configure(bg="#1e1e2e")
        dialog.resizable(False, False)
        dialog.transient(parent.winfo_toplevel())

        def _entry_row(label: str, default: str = "") -> tk.Entry:
            row = tk.Frame(dialog, bg="#1e1e2e")
            row.pack(fill=tk.X, padx=10, pady=(8, 0))
            tk.Label(row, text=label, fg="#cdd6f4", bg="#1e1e2e", width=10, anchor=tk.W).pack(side=tk.LEFT)
            entry = tk.Entry(row, bg="#11111b", fg="#cdd6f4", insertbackground="#cdd6f4", relief=tk.FLAT)
            entry.insert(0, default)
            entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
            return entry

        id_entry = _entry_row("ID:", "scout-1")
        name_entry = _entry_row("Name:", "Scout")
        role_var = tk.StringVar(value="scout")
        role_row = tk.Frame(dialog, bg="#1e1e2e")
        role_row.pack(fill=tk.X, padx=10, pady=(8, 0))
        tk.Label(role_row, text="Role:", fg="#cdd6f4", bg="#1e1e2e", width=10, anchor=tk.W).pack(side=tk.LEFT)
        role_combo = ttk.Combobox(
            role_row,
            textvariable=role_var,
            values=["scout", "coordinator", "lead", "worker"],
            state="readonly",
            width=18,
        )
        role_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)

        def _save() -> None:
            employee_id = id_entry.get().strip()
            name = name_entry.get().strip() or employee_id
            role = role_var.get().strip() or "worker"
            if not employee_id:
                status_label.config(text=_msg("staff_id_required"))
                return
            created = widget._team_state.register_employee(employee_id, name, role=role)
            _refresh()
            status_label.config(text=_msg("staff_added") if created else _msg("staff_exists"))
            dialog.destroy()

        tk.Button(dialog, text="Add", command=_save).pack(pady=(10, 8))
        id_entry.focus_set()

    buttons = tk.Frame(parent, bg="#1e1e2e")
    buttons.pack(fill=tk.X, padx=4, pady=(0, 4))
    tk.Button(buttons, text="Approve", command=lambda: _resolve_selected(True)).pack(side=tk.LEFT, padx=(0, 4))
    tk.Button(buttons, text="Reject", command=lambda: _resolve_selected(False)).pack(side=tk.LEFT, padx=(0, 12))
    tk.Button(buttons, text="+ Staff", command=_add_staff_dialog).pack(side=tk.LEFT, padx=(0, 12))
    tk.Button(buttons, text="Route to tasks", command=_route_selected_queue_item).pack(side=tk.LEFT, padx=(0, 4))
    tk.Button(buttons, text="Dequeue next", command=_dequeue_next).pack(side=tk.LEFT, padx=(0, 4))
    tk.Button(buttons, text="Drop selected", command=_drop_selected_queue_item).pack(side=tk.LEFT)

    refresh_btn.bind("<Button-1>", lambda _event: _refresh())
    parent.after(100, _refresh)


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
        refresh_summary = getattr(widget, "_refresh_project_hub_summary", None)
        if callable(refresh_summary):
            refresh_summary()
        status_label.config(text=_msg("switched"))
        if not getattr(widget, "_workroom_mode", False):
            hub.after(500, lambda: _close_hub(widget, hub))
    except Exception as e:
        status_label.config(text=_friendly_error(e))


def _build_endpoints_tab(
    tab: tk.Frame,
    widget: Any,
    hub: tk.Toplevel,
    status_label: tk.Label,
) -> None:
    """Build the Endpoints tab - read-only dashboard + override.

    Default: system auto-selects the right endpoint per role.
    User can override per-role if needed.
    """
    from roost.state import TeamState

    team_state = widget._team_state if getattr(widget, "_team_state", None) is not None else TeamState()
    project_id = getattr(widget, "project_id", None)

    # --- Auto-select banner ---
    auto_frame = tk.Frame(tab, bg="#181825", height=28)
    auto_frame.pack(fill=tk.X, padx=8, pady=(8, 4))
    auto_frame.pack_propagate(False)

    auto_labels = {}
    for role_name in ("scout", "coordinator", "lead"):
        auto_alias = team_state.auto_select_endpoint(role_name)
        auto_backend = team_state.resolve_endpoint_backend(auto_alias)
        lbl = tk.Label(
            auto_frame,
            text=f"{role_name.capitalize()}: {auto_alias} -> {auto_backend}",
            fg="#a6e3a1", bg="#181825", font=("Segoe UI", 8),
        )
        lbl.pack(side=tk.LEFT, padx=8, pady=4)
        auto_labels[role_name] = lbl

    # --- Credit Plan ---
    plan_frame = tk.LabelFrame(
        tab,
        text="Credit Plan",
        fg="#cdd6f4",
        bg="#1e1e2e",
        font=("Segoe UI", 9, "bold"),
    )
    plan_frame.pack(fill=tk.X, padx=8, pady=(8, 4))

    plan_columns = ("role", "tier", "profile", "endpoint", "backend")
    plan_tree = ttk.Treeview(plan_frame, columns=plan_columns, show="headings", height=3)
    plan_tree.heading("role", text="Role")
    plan_tree.heading("tier", text="Tier")
    plan_tree.heading("profile", text="Model Profile")
    plan_tree.heading("endpoint", text="Route")
    plan_tree.heading("backend", text="Backend")
    plan_tree.column("role", width=100)
    plan_tree.column("tier", width=90)
    plan_tree.column("profile", width=180)
    plan_tree.column("endpoint", width=120)
    plan_tree.column("backend", width=90)
    plan_tree.pack(fill=tk.X, padx=4, pady=4)
    savings_label = tk.Label(
        plan_frame,
        text="Lead-only estimate: n/a",
        fg="#a6e3a1",
        bg="#1e1e2e",
        anchor=tk.W,
    )
    savings_label.pack(fill=tk.X, padx=4, pady=(0, 4))

    role_model_controls = tk.Frame(plan_frame, bg="#1e1e2e")
    role_model_controls.pack(fill=tk.X, padx=4, pady=(0, 4))
    role_model_vars: dict[str, tk.StringVar] = {}
    role_model_combos: dict[str, ttk.Combobox] = {}

    preset_frame = tk.Frame(role_model_controls, bg="#1e1e2e")
    preset_frame.pack(fill=tk.X, pady=(0, 4))
    preset_label = tk.Label(
        preset_frame,
        text="Preset: custom",
        fg="#cdd6f4",
        bg="#1e1e2e",
        width=20,
        anchor=tk.W,
    )
    preset_label.pack(side=tk.LEFT, padx=(0, 6))

    def _apply_team_model_preset(preset_id: str) -> None:
        try:
            team_state.apply_team_model_preset(preset_id, project_id=project_id)
            _refresh_credit_plan()
            _refresh_header_model_profiles()
            status_label.config(text=_msg("preset_applied"))
        except Exception as e:
            status_label.config(text=_friendly_error(e))

    for label, preset_id in (
        ("Save credits", "save-credits"),
        ("All local", "all-local"),
        ("All value", "all-value"),
        ("Lead SOTA", "lead-sota"),
    ):
        tk.Button(
            preset_frame,
            text=label,
            command=lambda preset=preset_id: _apply_team_model_preset(preset),
            bg="#313244",
            fg="#cdd6f4",
            relief=tk.FLAT,
            padx=8,
        ).pack(side=tk.LEFT, padx=(0, 4))

    def _profile_ids() -> list[str]:
        return [profile["id"] for profile in team_state.list_model_profiles()]

    def _refresh_role_model_controls() -> None:
        profile_ids = _profile_ids()
        for role, combo in role_model_combos.items():
            combo.configure(values=profile_ids)
            current = team_state.get_role_model_profile_id(role)
            if current in profile_ids:
                role_model_vars[role].set(current)

    def _save_role_model(role: str) -> None:
        profile_id = role_model_vars[role].get()
        try:
            team_state.set_role_model_profile(role, profile_id, project_id=project_id)
            _refresh_credit_plan()
            _refresh_header_model_profiles()
            status_label.config(text=_msg("role_saved"))
        except Exception as e:
            status_label.config(text=_friendly_error(e))

    def _clear_role_model(role: str) -> None:
        try:
            team_state.clear_role_model_profile(role, project_id=project_id)
            _refresh_credit_plan()
            _refresh_header_model_profiles()
            status_label.config(text=f"Role model reset: {role}")
        except Exception as e:
            status_label.config(text=_friendly_error(e))

    for role_name in ("scout", "coordinator", "lead"):
        row = tk.Frame(role_model_controls, bg="#1e1e2e")
        row.pack(fill=tk.X, pady=1)
        tk.Label(
            row,
            text=f"{role_name.capitalize()} model:",
            fg="#cdd6f4",
            bg="#1e1e2e",
            width=16,
            anchor=tk.W,
        ).pack(side=tk.LEFT)
        var = tk.StringVar(value=team_state.get_role_model_profile_id(role_name))
        cb = ttk.Combobox(row, textvariable=var, values=_profile_ids(), state="readonly", width=28)
        cb.pack(side=tk.LEFT, padx=(0, 4))
        cb.bind("<<ComboboxSelected>>", lambda _event, role=role_name: _save_role_model(role))
        role_model_vars[role_name] = var
        role_model_combos[role_name] = cb
        tk.Button(
            row,
            text="Reset",
            command=lambda role=role_name: _clear_role_model(role),
            bg="#313244",
            fg="#cdd6f4",
            relief=tk.FLAT,
            width=8,
        ).pack(side=tk.LEFT)

    def _selected_role_plan_item() -> dict[str, Any] | None:
        sel = plan_tree.selection()
        if not sel:
            status_label.config(text="Select a role in Credit Plan")
            return None
        role = str(plan_tree.item(sel[0])["values"][0]).strip().lower()
        for item in team_state.list_role_model_plan():
            if item.get("role") == role:
                return item
        status_label.config(text=f"Missing role plan: {role}")
        return None

    def _copy_selected_role_env() -> None:
        item = _selected_role_plan_item()
        if item is None:
            return
        profile = item.get("profile", {}) if isinstance(item.get("profile"), dict) else {}
        lines = _powershell_env_lines_for_profile(profile)
        hub.clipboard_clear()
        hub.clipboard_append("\n".join(lines))
        status_label.config(text=f"Copied {item.get('role')} env: {profile.get('id', '')}")

    def _copy_team_env() -> None:
        lines = _powershell_env_lines_for_role_plan(team_state.list_role_model_plan())
        hub.clipboard_clear()
        hub.clipboard_append("\n".join(lines))
        status_label.config(text="Copied team env plan")

    def _refresh_credit_plan() -> None:
        plan_tree.delete(*plan_tree.get_children())
        if hasattr(team_state, "get_team_model_preset_id"):
            preset_label.config(text=f"Preset: {team_state.get_team_model_preset_id()}")
        if hasattr(team_state, "list_role_model_plan"):
            plan = team_state.list_role_model_plan()
        else:
            plan = []
        for item in plan:
            profile = item.get("profile", {}) if isinstance(item.get("profile"), dict) else {}
            plan_tree.insert(
                "",
                tk.END,
                values=(
                    str(item.get("role", "")).capitalize(),
                    profile.get("tier", ""),
                    profile.get("id", ""),
                    item.get("endpoint", ""),
                    item.get("backend", ""),
                ),
            )
        if hasattr(team_state, "estimate_team_model_savings"):
            savings = team_state.estimate_team_model_savings()
            saved_units = savings["savedUnits"]
            if saved_units < 0:
                savings_text = f"{abs(saved_units)} units over baseline"
            else:
                savings_text = f"{savings['savedPercent']}% saved"
            savings_label.config(
                text=(
                    "Lead-only estimate: "
                    f"{savings['planUnits']}/{savings['baselineUnits']} units, "
                    f"{savings_text}"
                )
            )
        _refresh_role_model_controls()
        _refresh_header_model_profiles()

    widget._refresh_project_hub_credit_plan = _refresh_credit_plan

    plan_btn_frame = tk.Frame(plan_frame, bg="#1e1e2e")
    plan_btn_frame.pack(fill=tk.X, padx=4, pady=(0, 4))
    tk.Button(
        plan_btn_frame,
        text="Copy selected env",
        command=_copy_selected_role_env,
        bg="#313244",
        fg="#cdd6f4",
        relief=tk.FLAT,
    ).pack(side=tk.LEFT, padx=(0, 4))
    tk.Button(
        plan_btn_frame,
        text="Copy team env plan",
        command=_copy_team_env,
        bg="#313244",
        fg="#cdd6f4",
        relief=tk.FLAT,
    ).pack(side=tk.LEFT, padx=(0, 4))

    # --- Model Profiles ---
    model_frame = tk.LabelFrame(
        tab,
        text="Model Profiles (closed -> open-sota -> local -> value -> free)",
        fg="#cdd6f4",
        bg="#1e1e2e",
        font=("Segoe UI", 9, "bold"),
    )
    model_frame.pack(fill=tk.X, padx=8, pady=(8, 4))

    model_columns = ("active", "tier", "id", "provider", "model", "backend", "cost")
    model_tree = ttk.Treeview(model_frame, columns=model_columns, show="headings", height=5)
    model_tree.heading("active", text="")
    model_tree.heading("tier", text="Tier")
    model_tree.heading("id", text="Profile")
    model_tree.heading("provider", text="Provider")
    model_tree.heading("model", text="Model")
    model_tree.heading("backend", text="Backend")
    model_tree.heading("cost", text="Cost")
    model_tree.column("active", width=26, stretch=False)
    model_tree.column("tier", width=86)
    model_tree.column("id", width=150)
    model_tree.column("provider", width=90)
    model_tree.column("model", width=220)
    model_tree.column("backend", width=80)
    model_tree.column("cost", width=60)
    model_tree.pack(fill=tk.X, padx=4, pady=4)

    def _refresh_header_model_profiles() -> None:
        refresh_model_profiles = getattr(widget, "_refresh_project_hub_model_profiles", None)
        if callable(refresh_model_profiles):
            refresh_model_profiles()

    def _refresh_model_profiles() -> None:
        model_tree.delete(*model_tree.get_children())
        active_id = team_state.get_active_model_profile_id()
        active_item = None
        for info in team_state.list_model_profiles():
            profile_id = info["id"]
            item_id = model_tree.insert(
                "",
                tk.END,
                values=(
                    "*" if profile_id == active_id else "",
                    info.get("tier", model_profile_tier(info)),
                    profile_id,
                    info.get("provider", ""),
                    info.get("model", ""),
                    info.get("backend", ""),
                    info.get("cost", ""),
                ),
            )
            if profile_id == active_id:
                active_item = item_id
        if active_item is not None:
            model_tree.selection_set(active_item)
            model_tree.focus(active_item)
        _refresh_credit_plan()
        _refresh_header_model_profiles()

    def _selected_model_profile_id() -> str | None:
        sel = model_tree.selection()
        if not sel:
            status_label.config(text="Select a model profile")
            return None
        return str(model_tree.item(sel[0])["values"][2])

    def _selected_model_profile() -> dict[str, Any] | None:
        profile_id = _selected_model_profile_id()
        if not profile_id:
            return None
        for info in team_state.list_model_profiles():
            if info["id"] == profile_id:
                return info
        status_label.config(text=f"Missing model profile: {profile_id}")
        return None

    def _use_model_profile() -> None:
        profile_id = _selected_model_profile_id()
        if not profile_id:
            return
        try:
            team_state.set_active_model_profile(project_id, profile_id)
            _refresh_model_profiles()
            status_label.config(text=f"Active model: {profile_id}")
        except Exception as e:
            status_label.config(text=_friendly_error(e))

    def _remove_model_profile() -> None:
        profile_id = _selected_model_profile_id()
        if not profile_id:
            return
        try:
            removed = team_state.remove_model_profile(project_id, profile_id)
        except Exception as e:
            status_label.config(text=_friendly_error(e))
            return
        if removed:
            _refresh_model_profiles()
            status_label.config(text=f"Removed model: {profile_id}")

    def _test_model_profile() -> None:
        profile = _selected_model_profile()
        if profile is None:
            return
        backend_name = profile.get("backend", "hermes")
        if backend_name == "script":
            status_label.config(text=f"[Test] {profile['id']}: OK local script")
            return
        if backend_name == "codex":
            status_label.config(text=f"[Test] {profile['id']}: Codex profile saved")
            return
        from roost.dispatcher import BackendRegistry

        try:
            cls = BackendRegistry().get(backend_name)
            inst = cls()
            if hasattr(inst, "set_model_profile"):
                inst.set_model_profile(profile)
            ok = inst.health_check()
            status_label.config(text=f"[Test] {profile['id']}: {'OK' if ok else 'FAIL'}")
        except Exception as e:
            status_label.config(text=f"[Test] {profile['id']}: ERROR - {e}")

    def _copy_model_profile_env() -> None:
        profile = _selected_model_profile()
        if profile is None:
            return
        lines = _powershell_env_lines_for_profile(profile)
        hub.clipboard_clear()
        hub.clipboard_append("\n".join(lines))
        status_label.config(text=f"Copied env: {profile['id']}")

    def _model_profile_dialog(edit: bool = False) -> None:
        existing = None
        if edit:
            profile_id = _selected_model_profile_id()
            if not profile_id:
                return
            existing = next((info for info in team_state.list_model_profiles() if info["id"] == profile_id), None)
            if existing is None:
                status_label.config(text=f"Missing model profile: {profile_id}")
                return

        dialog = tk.Toplevel(hub)
        dialog.title("Edit Model Profile" if edit else "Add Model Profile")
        dialog.geometry("420x320")
        dialog.configure(bg="#1e1e2e")
        dialog.resizable(False, False)

        def _entry_row(label: str, value: str = "") -> tk.Entry:
            tk.Label(dialog, text=label, fg="#cdd6f4", bg="#1e1e2e").pack(anchor=tk.W, padx=8, pady=(8, 0))
            entry = tk.Entry(dialog, bg="#313244", fg="#cdd6f4", insertbackground="#cdd6f4")
            entry.insert(0, value)
            entry.pack(fill=tk.X, padx=8, pady=2)
            return entry

        id_entry = _entry_row("Profile id:", existing["id"] if existing else "openrouter/custom")
        if edit:
            id_entry.config(state="disabled")

        tk.Label(dialog, text="Backend:", fg="#cdd6f4", bg="#1e1e2e").pack(anchor=tk.W, padx=8, pady=(8, 0))
        backend_var = tk.StringVar(value=(existing or {}).get("backend", "hermes"))
        backend_combo = ttk.Combobox(
            dialog,
            textvariable=backend_var,
            values=["hermes", "script", "codex"],
            state="readonly",
        )
        backend_combo.pack(fill=tk.X, padx=8, pady=2)

        provider_entry = _entry_row("Provider:", (existing or {}).get("provider", "openrouter"))
        model_entry = _entry_row("Model:", (existing or {}).get("model", ""))

        tk.Label(dialog, text="Tier:", fg="#cdd6f4", bg="#1e1e2e").pack(anchor=tk.W, padx=8, pady=(8, 0))
        tier_var = tk.StringVar(value=(existing or {}).get("tier", "open-sota"))
        tier_combo = ttk.Combobox(
            dialog,
            textvariable=tier_var,
            values=["closed", "open-sota", "local", "value", "free"],
            state="readonly",
        )
        tier_combo.pack(fill=tk.X, padx=8, pady=2)

        tk.Label(dialog, text="Cost:", fg="#cdd6f4", bg="#1e1e2e").pack(anchor=tk.W, padx=8, pady=(8, 0))
        cost_var = tk.StringVar(value=(existing or {}).get("cost", "high"))
        cost_combo = ttk.Combobox(dialog, textvariable=cost_var, values=["free", "low", "high"], state="readonly")
        cost_combo.pack(fill=tk.X, padx=8, pady=2)

        def _save() -> None:
            try:
                team_state.set_model_profile(
                    project_id,
                    id_entry.get(),
                    backend_var.get(),
                    provider_entry.get(),
                    model_entry.get(),
                    cost_var.get(),
                    tier_var.get(),
                )
                _refresh_model_profiles()
                status_label.config(text=f"Saved model: {id_entry.get().strip()}")
                dialog.destroy()
            except Exception as e:
                status_label.config(text=_friendly_error(e))

        tk.Button(dialog, text="Save", command=_save).pack(pady=(10, 8))

    model_btn_frame = tk.Frame(model_frame, bg="#1e1e2e")
    model_btn_frame.pack(fill=tk.X, padx=4, pady=(0, 4))
    tk.Button(model_btn_frame, text="+ Add", command=lambda: _model_profile_dialog(False)).pack(
        side=tk.LEFT, padx=(0, 4)
    )
    tk.Button(model_btn_frame, text="Edit", command=lambda: _model_profile_dialog(True)).pack(
        side=tk.LEFT, padx=(0, 4)
    )
    tk.Button(model_btn_frame, text="Use", command=_use_model_profile).pack(side=tk.LEFT, padx=(0, 4))
    tk.Button(model_btn_frame, text="Test model", command=_test_model_profile).pack(side=tk.LEFT, padx=(0, 4))
    tk.Button(model_btn_frame, text="Copy env", command=_copy_model_profile_env).pack(side=tk.LEFT, padx=(0, 4))
    tk.Button(model_btn_frame, text="Remove", command=_remove_model_profile).pack(side=tk.LEFT)

    _refresh_model_profiles()
    _refresh_credit_plan()

    # --- Endpoint Registry (read-only) ---
    ep_label_frame = tk.LabelFrame(
        tab,
        text="Endpoint Registry (auto-managed)",
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
        for info in team_state.list_endpoints():
            ep_tree.insert("", tk.END, values=(info["alias"], info.get("backend", ""), info.get("cost", "")))

    _refresh_endpoints()

    # Buttons
    btn_frame = tk.Frame(ep_label_frame, bg="#1e1e2e")
    btn_frame.pack(fill=tk.X, padx=4, pady=(0, 4))

    def _test_endpoint():
        sel = ep_tree.selection()
        if not sel:
            status_label.config(text="Select an endpoint")
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
            status_label.config(text=f"[Test] {alias}: ERROR - {e}")

    def _remove_endpoint():
        sel = ep_tree.selection()
        if not sel:
            return
        alias = ep_tree.item(sel[0])["values"][0]
        try:
            removed = team_state.remove_endpoint(project_id, alias)
        except Exception as e:
            status_label.config(text=_friendly_error(e))
            return
        if removed:
            _refresh_endpoints()
            status_label.config(text=f"Removed: {alias}")

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
            try:
                if alias:
                    team_state.set_endpoint(project_id, alias, backend_var.get(), cost_var.get())
                    _refresh_endpoints()
                    status_label.config(text=f"Added: {alias}")
                dialog.destroy()
            except Exception as e:
                status_label.config(text=_friendly_error(e))

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

    all_ep_aliases = [info["alias"] for info in team_state.list_endpoints()]

    for role_name, default_be in [("scout", "local/fast"), ("coordinator", "remote/sota"), ("lead", "remote/sota")]:
        row = tk.Frame(role_frame, bg="#1e1e2e")
        row.pack(fill=tk.X, padx=4, pady=2)
        tk.Label(row, text=f"{role_name.capitalize()}:", fg="#cdd6f4", bg="#1e1e2e", width=14, anchor=tk.W).pack(
            side=tk.LEFT
        )
        var = tk.StringVar(value=team_state.get_role_backend(role_name) or default_be)
        cb = ttk.Combobox(row, textvariable=var, values=all_ep_aliases, state="readonly", width=20)
        cb.pack(side=tk.LEFT, padx=(0, 4))

        def _save_role(rn=role_name, v=var):
            try:
                team_state.set_role_backend(rn, v.get(), project_id=project_id)
                _refresh_credit_plan()
                status_label.config(text=f"Role saved: {rn} -> {v.get()}")
            except Exception as e:
                status_label.config(text=_friendly_error(e))

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

    for skill_info in team_state.list_skills():
        skill_id = skill_info["id"]
        row = tk.Frame(skills_frame, bg="#1e1e2e")
        row.pack(fill=tk.X, padx=4, pady=1)
        var = tk.BooleanVar(value=skill_info.get("enabled", False))

        def _toggle(sid=skill_id, v=var):
            try:
                team_state.set_skill_enabled(sid, v.get(), project_id=project_id)
                status_label.config(text=f"Skill {'ON' if v.get() else 'OFF'}: {sid}")
            except Exception as e:
                status_label.config(text=_friendly_error(e))

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
        tk.Label(row, text=f"-> {ep_str}", fg="#6c7086", bg="#1e1e2e").pack(side=tk.RIGHT, padx=4)


def _close_hub(widget: Any, hub: tk.Toplevel) -> None:
    widget._hub_window = None
    try:
        hub.destroy()
    except tk.TclError:
        pass
