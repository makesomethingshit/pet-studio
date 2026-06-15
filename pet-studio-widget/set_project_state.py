"""Write the Pet Studio widget file-based state bridge."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pet_studio_core.state import DEFAULT_STATE_FILE, EXTERNAL_STATES, utc_now, write_project_state  # noqa: E402,F401


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_FILE), help="Pet Studio state JSON path")
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--state", required=True, help="External Pet Studio state to publish")
    parser.add_argument("--message", default="")
    parser.add_argument("--updated-at", default=None, help="Override updatedAt; mainly useful for deterministic tests")
    parser.add_argument("--reset-after-ms", type=int, default=None, help="Optional auto-reset delay for transient states")
    parser.add_argument("--reset-to-state", default="idle", help="State to show after --reset-after-ms expires")
    args = parser.parse_args()

    state_file = Path(args.state_file).expanduser()
    payload = write_project_state(
        state_file,
        args.project_id,
        args.state,
        args.message,
        args.updated_at,
        args.reset_after_ms,
        args.reset_to_state,
    )
    print(json.dumps({"ok": True, "stateFile": str(state_file), "state": payload}, indent=2))


if __name__ == "__main__":
    main()
