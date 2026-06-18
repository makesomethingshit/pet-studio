"""Team Room submenu for the Project Room widget context menu."""

from __future__ import annotations

import tkinter as tk
from typing import Any


def add_team_room_menu(parent: tk.Menu, widget: Any) -> bool:
    if widget._team_state is None:
        return False
    try:
        pending = widget._team_state.get_pending_approvals()
        employees = widget._team_state.get_employees()
        queue = widget._team_state.get_roost_queue()
    except Exception:  # noqa: BLE001
        return False

    label = "Team Room"
    if pending:
        label += f" ({len(pending)} approval{'s' if len(pending) != 1 else ''})"
    elif queue:
        label += f" ({len(queue)} queued)"

    menu = tk.Menu(parent, tearoff=False)
    _add_approvals(menu, widget, pending)
    menu.add_separator()
    _add_staff(menu, employees)
    menu.add_separator()
    _add_queue(menu, queue)
    parent.add_cascade(label=label, menu=menu)
    parent.add_separator()
    return True


def _add_approvals(menu: tk.Menu, widget: Any, pending: list[dict]) -> None:
    menu.add_command(label="Approvals", state=tk.DISABLED)
    if not pending:
        menu.add_command(label="No pending approvals", state=tk.DISABLED)
        return
    for item in pending[:5]:
        action = item.get("action", "?")
        project_id = item.get("projectId", "")
        approval_id = item.get("id", "")
        label = f"{action} ({project_id})" if project_id else action
        menu.add_command(label=f"Approve: {label}", command=lambda aid=approval_id: _resolve(widget, aid, True))
        menu.add_command(label=f"Reject: {label}", command=lambda aid=approval_id: _resolve(widget, aid, False))


def _add_staff(menu: tk.Menu, employees: list[dict]) -> None:
    menu.add_command(label="Staff", state=tk.DISABLED)
    if not employees:
        menu.add_command(label="No staff assigned", state=tk.DISABLED)
        return
    for emp in employees:
        name = emp.get("name", emp.get("id", "?"))
        status = emp.get("status", "idle")
        role = emp.get("role", "worker")
        menu.add_command(label=f"{name} [{role}, {status}]", state=tk.DISABLED)


def _add_queue(menu: tk.Menu, queue: list[dict]) -> None:
    menu.add_command(label=f"Queue ({len(queue)})", state=tk.DISABLED)
    if not queue:
        menu.add_command(label="Queue empty", state=tk.DISABLED)
        return
    for item in queue[:5]:
        menu.add_command(label=item.get("type", "unknown"), state=tk.DISABLED)
    if len(queue) > 5:
        menu.add_command(label=f"+{len(queue) - 5} more", state=tk.DISABLED)


def _resolve(widget: Any, approval_id: str, approved: bool) -> None:
    if widget._team_state is not None:
        widget._team_state.resolve_approval(approval_id, approved)
