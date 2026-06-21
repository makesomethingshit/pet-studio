"""Tests for the Pet Studio memory CLI."""

from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from roost.team_memory import list_memory_candidates, load_memory_context
from tools.pet_studio_memory import main


class TestPetStudioMemoryCli(unittest.TestCase):
    def test_add_and_approve_project_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            with redirect_stdout(StringIO()):
                add_code = main(
                    [
                        "--root",
                        str(root),
                        "add",
                        "--scope",
                        "project",
                        "--project-id",
                        "pet-studio",
                        "--kind",
                        "rule",
                        "Use local workroom wording",
                    ]
                )
            candidate_id = list_memory_candidates(root)[0]["id"]
            with redirect_stdout(StringIO()):
                approve_code = main(["--root", str(root), "approve", candidate_id])

            context = load_memory_context(root, "pet-studio")

            self.assertEqual(add_code, 0)
            self.assertEqual(approve_code, 0)
            self.assertEqual(context["project_culture"][0]["summary"], "Use local workroom wording")


if __name__ == "__main__":
    unittest.main()
