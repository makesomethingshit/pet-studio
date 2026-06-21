"""CLI for Roost team memory approval."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from roost.team_memory import (
    add_memory_candidate,
    approve_memory_candidate,
    list_memory_candidates,
    reject_memory_candidate,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Pet Studio team memory.")
    parser.add_argument("--root", default=".", help="Directory containing team memory files.")
    sub = parser.add_subparsers(dest="command", required=True)

    list_parser = sub.add_parser("list", help="List memory candidates.")
    list_parser.add_argument("--status", choices=["pending", "approved", "rejected"])

    add_parser = sub.add_parser("add", help="Add a memory candidate.")
    add_parser.add_argument("--scope", choices=["team", "project"], default="team")
    add_parser.add_argument("--project-id")
    add_parser.add_argument("--kind", default="lesson")
    add_parser.add_argument("--evidence", action="append", default=[])
    add_parser.add_argument("summary")

    approve_parser = sub.add_parser("approve", help="Approve a candidate.")
    approve_parser.add_argument("id")

    reject_parser = sub.add_parser("reject", help="Reject a candidate.")
    reject_parser.add_argument("id")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root)
    if args.command == "add":
        candidate = add_memory_candidate(
            root,
            args.summary,
            scope=args.scope,
            project_id=args.project_id,
            kind=args.kind,
            evidence=args.evidence,
        )
        print(f"added {candidate['id']}")
        return 0
    if args.command == "list":
        for candidate in list_memory_candidates(root, status=args.status):
            project = f" project={candidate.get('projectId')}" if candidate.get("projectId") else ""
            print(
                f"{candidate['id']} {candidate.get('status', 'pending')} "
                f"{candidate.get('scope', 'team')}{project}: {candidate.get('summary', '')}"
            )
        return 0
    if args.command == "approve":
        candidate = approve_memory_candidate(root, args.id)
        print(f"approved {candidate['id']}")
        return 0
    if args.command == "reject":
        candidate = reject_memory_candidate(root, args.id)
        print(f"rejected {candidate['id']}")
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
