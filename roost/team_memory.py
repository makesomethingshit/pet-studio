"""Approved team memory and project culture for Roost."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CANDIDATES_FILE = "team_memory_candidates.jsonl"
MEMORY_FILE = "team_memory.json"


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _candidate_path(root: str | Path) -> Path:
    return Path(root) / CANDIDATES_FILE


def _memory_path(root: str | Path) -> Path:
    return Path(root) / MEMORY_FILE


def _append_candidate_event(root: str | Path, event: dict[str, Any]) -> None:
    path = _candidate_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _load_memory(root: str | Path) -> dict[str, Any]:
    path = _memory_path(root)
    if not path.exists():
        return {"version": "v1", "team_memory": [], "project_culture": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"version": "v1", "team_memory": [], "project_culture": {}}
    data.setdefault("version", "v1")
    data.setdefault("team_memory", [])
    data.setdefault("project_culture", {})
    return data


def _save_memory(root: str | Path, memory: dict[str, Any]) -> None:
    path = _memory_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(memory, indent=2, ensure_ascii=False), encoding="utf-8")


def add_memory_candidate(
    root: str | Path,
    summary: str,
    *,
    scope: str = "team",
    project_id: str | None = None,
    kind: str = "lesson",
    evidence: list[str] | None = None,
    source: str = "manual",
) -> dict[str, Any]:
    """Append a pending memory candidate."""
    candidate = {
        "id": f"mem-{uuid.uuid4().hex[:12]}",
        "scope": scope,
        "projectId": project_id,
        "kind": kind,
        "summary": summary,
        "evidence": evidence or [],
        "source": source,
        "status": "pending",
        "createdAt": _now(),
    }
    _append_candidate_event(root, candidate)
    return candidate


def list_memory_candidates(root: str | Path, status: str | None = None) -> list[dict[str, Any]]:
    """Return candidates folded with append-only approval/rejection events."""
    path = _candidate_path(root)
    candidates: dict[str, dict[str, Any]] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            event = json.loads(line)
            candidate_id = str(event.get("id", ""))
            if not candidate_id:
                continue
            if event.get("event") == "decision":
                if candidate_id in candidates:
                    candidates[candidate_id]["status"] = event.get("status", candidates[candidate_id]["status"])
                    candidates[candidate_id]["decidedAt"] = event.get("decidedAt")
                continue
            candidates[candidate_id] = event
    result = list(candidates.values())
    if status:
        return [candidate for candidate in result if candidate.get("status") == status]
    return result


def _candidate_to_memory(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": candidate["id"],
        "kind": candidate.get("kind", "lesson"),
        "summary": candidate.get("summary", ""),
        "evidence": candidate.get("evidence", []),
        "source": candidate.get("source", ""),
        "approvedAt": _now(),
    }


def approve_memory_candidate(root: str | Path, candidate_id: str) -> dict[str, Any]:
    """Approve a pending candidate and promote it into memory."""
    candidates = {candidate["id"]: candidate for candidate in list_memory_candidates(root)}
    if candidate_id not in candidates:
        raise ValueError(f"Unknown memory candidate: {candidate_id}")
    candidate = dict(candidates[candidate_id])
    candidate["status"] = "approved"
    _append_candidate_event(
        root,
        {"event": "decision", "id": candidate_id, "status": "approved", "decidedAt": _now()},
    )

    memory = _load_memory(root)
    entry = _candidate_to_memory(candidate)
    if candidate.get("scope") == "project":
        project_id = candidate.get("projectId")
        if not project_id:
            raise ValueError("Project memory candidate requires projectId")
        memory.setdefault("project_culture", {}).setdefault(project_id, []).append(entry)
    else:
        memory.setdefault("team_memory", []).append(entry)
    _save_memory(root, memory)
    return candidate


def reject_memory_candidate(root: str | Path, candidate_id: str) -> dict[str, Any]:
    """Reject a pending candidate without deleting evidence."""
    candidates = {candidate["id"]: candidate for candidate in list_memory_candidates(root)}
    if candidate_id not in candidates:
        raise ValueError(f"Unknown memory candidate: {candidate_id}")
    candidate = dict(candidates[candidate_id])
    candidate["status"] = "rejected"
    _append_candidate_event(
        root,
        {"event": "decision", "id": candidate_id, "status": "rejected", "decidedAt": _now()},
    )
    return candidate


def load_memory_context(root: str | Path, project_id: str) -> dict[str, list[dict[str, Any]]]:
    """Return approved memory sections safe to inject into a work packet."""
    memory = _load_memory(root)
    return {
        "team_memory": list(memory.get("team_memory", [])),
        "project_culture": list(memory.get("project_culture", {}).get(project_id, [])),
    }
