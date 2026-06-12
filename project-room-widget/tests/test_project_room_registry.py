from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WIDGET_DIR = ROOT / "project-room-widget"
WIDGET_SCRIPT = WIDGET_DIR / "project_room_widget.py"
STATE_SCRIPT = WIDGET_DIR / "set_project_state.py"
ADAPTER_SCRIPT = WIDGET_DIR / "codex_state_adapter.py"
if str(WIDGET_DIR) not in sys.path:
    sys.path.insert(0, str(WIDGET_DIR))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


class ProjectRoomRegistryTests(unittest.TestCase):
    def make_config(self, path: Path, **overrides: object) -> Path:
        project = {
            "projectId": "gakju-demo",
            "displayName": "Gakju Demo",
            "kitPath": str(ROOT / "runs" / "gakju-imagegen-room-v1" / "kit"),
            "petPackagePath": str(ROOT / "runs" / "gakju-imagegen-room-v1" / "kit" / "pets" / "main-owner"),
            "defaultState": "idle",
            "theme": "quiet archive nook",
            "enabled": True,
        }
        project.update(overrides)
        write_json(path, {"schemaVersion": 1, "projects": [project]})
        return path

    def test_selects_enabled_project_and_resolves_kit_path(self) -> None:
        from project_room_registry import select_project

        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp) / "projects.json")

            project = select_project(config, "gakju-demo")

            self.assertEqual(project.project_id, "gakju-demo")
            self.assertEqual(project.display_name, "Gakju Demo")
            self.assertTrue(project.kit_manifest.exists())
            self.assertEqual(project.default_state, "idle")

    def test_rejects_disabled_unknown_and_missing_kit_projects(self) -> None:
        from project_room_registry import ProjectRegistryError, select_project

        with tempfile.TemporaryDirectory() as tmp:
            config = self.make_config(Path(tmp) / "projects.json", enabled=False)
            with self.assertRaisesRegex(ProjectRegistryError, "disabled"):
                select_project(config, "gakju-demo")

            missing_config = self.make_config(Path(tmp) / "missing.json", kitPath="missing-kit")
            with self.assertRaisesRegex(ProjectRegistryError, "Project Room Kit manifest not found"):
                select_project(missing_config, "gakju-demo")

            with self.assertRaisesRegex(ProjectRegistryError, "Unknown project id"):
                select_project(config, "nope")

    def test_state_file_maps_external_states_to_widget_rows(self) -> None:
        from project_room_registry import read_project_state

        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"
            write_json(
                state_file,
                {
                    "projectId": "gakju-demo",
                    "state": "done",
                    "message": "done",
                    "updatedAt": "2026-06-12T00:00:00Z",
                },
            )

            self.assertEqual(read_project_state(state_file, "gakju-demo", "idle"), "jumping")

            write_json(state_file, {"projectId": "other", "state": "failed"})
            self.assertEqual(read_project_state(state_file, "gakju-demo", "idle"), "idle")

            write_json(state_file, {"projectId": "gakju-demo", "state": "blocked"})
            self.assertEqual(read_project_state(state_file, "gakju-demo", "idle"), "failed")

            write_json(state_file, {"projectId": "gakju-demo", "state": "handoff"})
            self.assertEqual(read_project_state(state_file, "gakju-demo", "idle"), "review")

    def test_widget_cli_lists_and_renders_project_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            config = self.make_config(work / "projects.json")
            output = work / "render.png"

            listed = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--config",
                    str(config),
                    "--list-projects",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(listed.returncode, 0, listed.stderr + listed.stdout)
            self.assertIn("gakju-demo", listed.stdout)

            rendered = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--config",
                    str(config),
                    "--project-id",
                    "gakju-demo",
                    "--render-project-once",
                    str(output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(rendered.returncode, 0, rendered.stderr + rendered.stdout)
            self.assertTrue(output.exists())

            state_output = work / "render-done.png"
            rendered_done = subprocess.run(
                [
                    sys.executable,
                    str(WIDGET_SCRIPT),
                    "--config",
                    str(config),
                    "--project-id",
                    "gakju-demo",
                    "--state",
                    "done",
                    "--render-project-once",
                    str(state_output),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(rendered_done.returncode, 0, rendered_done.stderr + rendered_done.stdout)
            self.assertIn('"state": "jumping"', rendered_done.stdout)

    def test_set_project_state_cli_writes_external_state_bridge_file(self) -> None:
        from project_room_registry import read_project_state

        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(STATE_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--project-id",
                    "gakju-demo",
                    "--state",
                    "blocked",
                    "--message",
                    "Waiting on review notes",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            data = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(data["projectId"], "gakju-demo")
            self.assertEqual(data["state"], "blocked")
            self.assertEqual(data["message"], "Waiting on review notes")
            self.assertIn("updatedAt", data)
            self.assertEqual(read_project_state(state_file, "gakju-demo", "idle"), "failed")

    def test_codex_state_adapter_maps_events_to_bridge_states(self) -> None:
        from project_room_registry import read_project_state

        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"

            cases = [
                ("start", "running", "running"),
                ("block", "blocked", "failed"),
                ("done", "done", "jumping"),
            ]
            for event, stored_state, widget_state in cases:
                result = subprocess.run(
                    [
                        sys.executable,
                        str(ADAPTER_SCRIPT),
                        "--state-file",
                        str(state_file),
                        "--project-id",
                        "gakju-demo",
                        "--event",
                        event,
                        "--message",
                        f"event {event}",
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )

                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                data = json.loads(state_file.read_text(encoding="utf-8"))
                self.assertEqual(data["projectId"], "gakju-demo")
                self.assertEqual(data["state"], stored_state)
                self.assertEqual(data["message"], f"event {event}")
                self.assertEqual(read_project_state(state_file, "gakju-demo", "idle"), widget_state)

    def test_codex_state_adapter_rejects_unknown_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            state_file = Path(tmp) / "project-room-state.json"

            result = subprocess.run(
                [
                    sys.executable,
                    str(ADAPTER_SCRIPT),
                    "--state-file",
                    str(state_file),
                    "--project-id",
                    "gakju-demo",
                    "--event",
                    "mystery",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Unsupported Codex event", result.stderr + result.stdout)
            self.assertFalse(state_file.exists())


if __name__ == "__main__":
    unittest.main()
