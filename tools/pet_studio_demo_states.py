"""Cycle Pet Studio project states for demos and manual QA."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
WIDGET_DIR = ROOT / "pet-studio-widget"
if str(WIDGET_DIR) not in sys.path:
    sys.path.insert(0, str(WIDGET_DIR))

from project_room_registry import DEFAULT_STATE_FILE  # noqa: E402
from set_project_state import utc_now, write_project_state  # noqa: E402


@dataclass(frozen=True)
class DemoStep:
    state: str
    message: str

    def to_dict(self) -> dict[str, str]:
        return {"state": self.state, "message": self.message}


DEMO_SEQUENCE = (
    DemoStep("idle", ""),
    DemoStep("running", "Working..."),
    DemoStep("waiting", "Compacting context..."),
    DemoStep("blocked", "Needs input"),
    DemoStep("review", "Ready for review"),
    DemoStep("done", "Done"),
    DemoStep("idle", ""),
)


def build_demo_sequence() -> list[DemoStep]:
    return list(DEMO_SEQUENCE)


def payload_for_step(project_id: str, step: DemoStep, updated_at: str | None, delay_seconds: float) -> dict[str, Any]:
    payload = {
        "projectId": project_id,
        "state": step.state,
        "message": step.message,
        "updatedAt": updated_at or utc_now(),
    }
    return payload


def write_step(state_file: Path, project_id: str, step: DemoStep) -> dict[str, Any]:
    return write_project_state(
        state_file=state_file,
        project_id=project_id,
        state=step.state,
        message=step.message,
        reset_to_state="idle",
    )


def sequence_summary(project_id: str, state_file: Path, delay_seconds: float, once: bool, dry_run: bool) -> dict[str, Any]:
    steps = build_demo_sequence()
    return {
        "ok": True,
        "dryRun": dry_run,
        "projectId": project_id,
        "stateFile": str(state_file),
        "delaySeconds": delay_seconds,
        "once": once,
        "sequence": [step.to_dict() for step in steps],
        "payloads": [payload_for_step(project_id, step, updated_at=None, delay_seconds=delay_seconds) for step in steps],
    }


def run_cycler(project_id: str, state_file: Path, delay_seconds: float, once: bool, dry_run: bool) -> dict[str, Any]:
    summary = sequence_summary(project_id, state_file, delay_seconds, once, dry_run)
    if dry_run:
        summary["cyclesCompleted"] = 0
        summary["writes"] = 0
        return summary

    writes = 0
    cycles = 0
    steps = build_demo_sequence()
    try:
        while True:
            for index, step in enumerate(steps):
                write_step(state_file, project_id, step)
                writes += 1
                if delay_seconds > 0 and not (once and index == len(steps) - 1):
                    time.sleep(delay_seconds)
            cycles += 1
            if once:
                break
    except KeyboardInterrupt:
        summary["interrupted"] = True
    summary["cyclesCompleted"] = cycles
    summary["writes"] = writes
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Cycle Pet Studio project states for README GIFs and manual QA.")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_FILE), help="Pet Studio state bridge JSON path")
    parser.add_argument("--delay", "--delay-seconds", dest="delay_seconds", type=float, default=2.0)
    parser.add_argument("--once", action="store_true", help="Run one full demo sequence and exit")
    parser.add_argument("--dry-run", action="store_true", help="Print the sequence without writing the state bridge")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if args.delay_seconds < 0:
        parser.error("--delay-seconds must be zero or greater")
    summary = run_cycler(
        project_id=args.project_id,
        state_file=Path(args.state_file).expanduser(),
        delay_seconds=args.delay_seconds,
        once=args.once,
        dry_run=args.dry_run,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
