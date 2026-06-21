"""Tests for lightweight research helper primitives."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from roost.packet import build_work_packet
from roost.research import (
    build_context_budget,
    build_trend_scout_sources,
    load_workflow_pack,
    record_long_task_iteration,
)
from roost.state import TeamState


class TestLongTaskState(unittest.TestCase):
    def test_stale_iterations_pivot_after_two_misses(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            task_dir = Path(tmp) / "trend-scan"

            first = record_long_task_iteration(task_dir, new_findings=0)
            second = record_long_task_iteration(task_dir, new_findings=0)

            self.assertEqual(first["stale_count"], 1)
            self.assertEqual(second["stale_count"], 2)
            self.assertEqual(second["recommendation"], "pivot")
            progress = json.loads((task_dir / "state" / "progress.json").read_text(encoding="utf-8"))
            self.assertEqual(progress["stale_count"], 2)


class TestWorkflowPack(unittest.TestCase):
    def test_manifest_reads_known_fields_and_ignores_unknown(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "trend-scout.json"
            manifest.write_text(
                json.dumps(
                    {
                        "id": "trend-scout",
                        "role": "scout",
                        "command": "scan",
                        "allowed_adapters": ["github-readme", "rss"],
                        "future_marketplace": True,
                    }
                ),
                encoding="utf-8",
            )

            pack = load_workflow_pack(manifest)

            self.assertEqual(pack["id"], "trend-scout")
            self.assertEqual(pack["role"], "scout")
            self.assertEqual(pack["command"], "scan")
            self.assertEqual(pack["allowed_adapters"], ["github-readme", "rss"])
            self.assertNotIn("future_marketplace", pack)


class TestContextBudget(unittest.TestCase):
    def test_context_budget_keeps_source_pointer_and_packet_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raw_log = Path(tmp) / "raw.log"
            raw_log.write_text("A" * 200, encoding="utf-8")
            budget = build_context_budget(
                [{"path": raw_log, "text": raw_log.read_text(encoding="utf-8")}],
                max_chars=20,
            )
            state = TeamState(Path(tmp) / "team_state.json")
            state.register_project("demo")

            packet = build_work_packet("demo", state, context_budget=budget)

            self.assertEqual(packet["context_budget"]["items"][0]["source"], str(raw_log))
            self.assertEqual(packet["context_budget"]["items"][0]["summary"], "A" * 20)
            self.assertNotIn("text", packet["context_budget"]["items"][0])


class TestTrendScoutSources(unittest.TestCase):
    def test_trend_scout_keeps_public_github_and_rss_sources_only(self) -> None:
        sources = build_trend_scout_sources(
            [
                "https://github.com/Panniantong/agent-reach",
                "https://example.com/feed.xml",
                "https://x.com/someone/status/1",
            ]
        )

        self.assertEqual([source["adapter"] for source in sources], ["github-readme", "rss"])
        self.assertEqual(sources[0]["url"], "https://github.com/Panniantong/agent-reach")
        self.assertEqual(sources[1]["url"], "https://example.com/feed.xml")


if __name__ == "__main__":
    unittest.main()
