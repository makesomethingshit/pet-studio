"""Lightweight research helper primitives for Roost.

These helpers keep research automation file-based and read-only by default.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


def _now() -> str:
    return datetime.now(UTC).isoformat()


def record_long_task_iteration(
    task_dir: str | Path,
    new_findings: int,
    metric_delta: int | float = 0,
    security_level: int = 1,
) -> dict[str, Any]:
    """Update a long-task progress file and return the new state."""
    task_path = Path(task_dir)
    state_dir = task_path / "state"
    logs_dir = task_path / "logs"
    state_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    progress_path = state_dir / "progress.json"
    if progress_path.exists():
        progress = json.loads(progress_path.read_text(encoding="utf-8"))
    else:
        progress = {"iteration": 0, "total_findings": 0, "stale_count": 0, "status": "running"}

    stale = new_findings <= 0 or metric_delta < 0
    progress["iteration"] = int(progress.get("iteration", 0)) + 1
    progress["total_findings"] = int(progress.get("total_findings", 0)) + max(0, int(new_findings))
    progress["stale_count"] = int(progress.get("stale_count", 0)) + 1 if stale else 0
    if progress["stale_count"] >= 2:
        progress["recommendation"] = "pivot" if security_level <= 1 else "approval-required"
    else:
        progress.pop("recommendation", None)
    progress["updatedAt"] = _now()
    progress_path.write_text(json.dumps(progress, indent=2, ensure_ascii=False), encoding="utf-8")

    with (logs_dir / "orchestrator.jsonl").open("a", encoding="utf-8") as log:
        log.write(json.dumps({"ts": progress["updatedAt"], "event": "iteration", "stale": stale}) + "\n")
    return progress


def load_workflow_pack(path: str | Path) -> dict[str, Any]:
    """Load the supported subset of a local workflow pack manifest."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        "id": str(data.get("id", "")),
        "role": str(data.get("role", "")),
        "command": str(data.get("command", "")),
        "allowed_adapters": [str(item) for item in data.get("allowed_adapters", [])],
        "output_template": str(data.get("output_template", "")),
    }


def build_context_budget(items: list[dict[str, Any]], max_chars: int = 1200) -> dict[str, Any]:
    """Build a packet-safe context budget with summaries and source pointers."""
    budget_items = []
    for item in items:
        source = str(item.get("path") or item.get("source") or "")
        text = str(item.get("text", ""))
        budget_items.append(
            {
                "source": source,
                "summary": text[:max_chars],
                "originalChars": len(text),
            }
        )
    return {"version": "v1", "items": budget_items}


def build_trend_scout_sources(urls: list[str]) -> list[dict[str, str]]:
    """Return read-only public sources Trend Scout can inspect without cookies."""
    sources: list[dict[str, str]] = []
    for url in urls:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            continue
        host = parsed.netloc.lower()
        path = parsed.path.rstrip("/")
        if host == "github.com" and len([part for part in path.split("/") if part]) >= 2:
            sources.append({"adapter": "github-readme", "url": url})
        elif path.endswith((".rss", ".xml", "/feed", "/rss", "/atom")):
            sources.append({"adapter": "rss", "url": url})
    return sources
