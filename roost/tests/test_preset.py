"""Tests for roost preset manager."""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from roost.preset import PresetError, export_preset, import_preset, list_presets


class TestPresetManager(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.room_dir = Path(self.tmp) / "test-room"
        self.kit_dir = self.room_dir / "kit"
        self.kit_dir.mkdir(parents=True)

        (self.kit_dir / "project-room.json").write_text(
            json.dumps({"schemaVersion": 1, "id": "test", "displayName": "Test Room"}),
            encoding="utf-8",
        )
        (self.kit_dir / "spritesheet.webp").write_text("fake-webp", encoding="utf-8")
        (self.kit_dir / "room.png").write_text("fake-png", encoding="utf-8")

        (self.room_dir / "layout.json").write_text(
            json.dumps({"anchors": {}, "zOrder": {}}),
            encoding="utf-8",
        )
        (self.room_dir / "session.json").write_text(
            json.dumps({"x": 100, "y": 200, "scale": 1.0, "state": "idle"}),
            encoding="utf-8",
        )

    def _preset_path(self) -> Path:
        return Path(self.tmp) / "test-preset.zip"

    def test_export_creates_zip(self):
        out = self._preset_path()
        export_preset(self.room_dir, out, "Test Preset")
        self.assertTrue(out.exists())

    def test_export_zip_contains_kit(self):
        out = self._preset_path()
        export_preset(self.room_dir, out, "Test Preset")
        with zipfile.ZipFile(out, "r") as zf:
            names = zf.namelist()
            self.assertIn("preset.json", names)
            self.assertIn("kit/project-room.json", names)
            self.assertIn("kit/spritesheet.webp", names)
            self.assertIn("kit/room.png", names)
            self.assertIn("layout.json", names)
            self.assertIn("session.json", names)

    def test_export_metadata(self):
        out = self._preset_path()
        export_preset(self.room_dir, out, "My Room")
        with zipfile.ZipFile(out, "r") as zf:
            meta = json.loads(zf.read("preset.json"))
            self.assertEqual(meta["name"], "My Room")
            self.assertEqual(meta["version"], "0.5.0")
            self.assertIn("createdAt", meta)

    def test_export_without_session(self):
        out = self._preset_path()
        export_preset(self.room_dir, out, "No Session", include_session=False)
        with zipfile.ZipFile(out, "r") as zf:
            self.assertNotIn("session.json", zf.namelist())

    def test_export_without_layout(self):
        out = self._preset_path()
        export_preset(self.room_dir, out, "No Layout", include_layout=False)
        with zipfile.ZipFile(out, "r") as zf:
            self.assertNotIn("layout.json", zf.namelist())

    def test_export_missing_room_dir(self):
        with self.assertRaises(PresetError):
            export_preset(Path("/nonexistent"), self._preset_path(), "Bad")

    def test_export_missing_kit_dir(self):
        empty = Path(self.tmp) / "empty-room"
        empty.mkdir()
        with self.assertRaises(PresetError):
            export_preset(empty, self._preset_path(), "Bad")

    def test_import_roundtrip(self):
        out = self._preset_path()
        export_preset(self.room_dir, out, "Roundtrip")

        target = Path(self.tmp) / "imported-room"
        meta = import_preset(out, target)
        self.assertEqual(meta["name"], "Roundtrip")
        self.assertTrue((target / "kit" / "project-room.json").exists())
        self.assertTrue((target / "kit" / "spritesheet.webp").exists())
        self.assertTrue((target / "layout.json").exists())
        self.assertTrue((target / "session.json").exists())

    def test_import_missing_zip(self):
        with self.assertRaises(PresetError):
            import_preset(Path("/nonexistent.zip"), Path(self.tmp) / "fail")

    def test_import_invalid_zip(self):
        bad = Path(self.tmp) / "bad.zip"
        bad.write_text("not a zip", encoding="utf-8")
        with self.assertRaises(PresetError):
            import_preset(bad, Path(self.tmp) / "fail")

    def test_import_no_overwrite(self):
        out = self._preset_path()
        export_preset(self.room_dir, out, "No Overwrite")

        target = Path(self.tmp) / "no-overwrite"
        target.mkdir()
        (target / "kit").mkdir()
        (target / "kit" / "project-room.json").write_text("original", encoding="utf-8")

        import_preset(out, target, overwrite=False)
        content = (target / "kit" / "project-room.json").read_text(encoding="utf-8")
        self.assertEqual(content, "original")

    def test_import_overwrite(self):
        out = self._preset_path()
        export_preset(self.room_dir, out, "Overwrite")

        target = Path(self.tmp) / "overwrite"
        target.mkdir()
        (target / "kit").mkdir()
        (target / "kit" / "project-room.json").write_text("original", encoding="utf-8")

        import_preset(out, target, overwrite=True)
        content = (target / "kit" / "project-room.json").read_text(encoding="utf-8")
        self.assertNotEqual(content, "original")

    def test_list_presets(self):
        out1 = Path(self.tmp) / "preset-a.zip"
        out2 = Path(self.tmp) / "preset-b.zip"
        export_preset(self.room_dir, out1, "Preset A")
        export_preset(self.room_dir, out2, "Preset B")

        presets_dir = Path(self.tmp)
        results = list_presets(presets_dir)
        self.assertEqual(len(results), 2)
        names = [r["name"] for r in results]
        self.assertIn("Preset A", names)
        self.assertIn("Preset B", names)

    def test_list_presets_empty(self):
        results = list_presets(Path(self.tmp) / "nonexistent")
        self.assertEqual(results, [])

    def test_list_presets_skips_invalid(self):
        bad = Path(self.tmp) / "bad.zip"
        bad.write_text("not a zip", encoding="utf-8")
        results = list_presets(Path(self.tmp))
        self.assertEqual(results, [])

    def test_import_zip_slip_kit_blocked(self):
        """Zip with path traversal inside kit/ should be rejected."""
        out = self._preset_path()
        export_preset(self.room_dir, out, "Legit")
        import zipfile

        malicious = Path(self.tmp) / "malicious.zip"
        with zipfile.ZipFile(out, "r") as src, zipfile.ZipFile(malicious, "w") as dst:
            for item in src.infolist():
                dst.writestr(item, src.read(item.filename))
            # kit/ prefix but traverses upward
            dst.writestr("kit/../../etc/cron.d/evil", "* * * * * root pwned")
        target = Path(self.tmp) / "zip-slip-target"
        with self.assertRaises(PresetError) as ctx:
            import_preset(malicious, target)
        self.assertIn("Zip slip", str(ctx.exception))

    def test_import_legit_kit_nested_subdir(self):
        """Legitimate kit/ with nested subdirs should work fine."""
        out = self._preset_path()
        export_preset(self.room_dir, out, "Legit")
        target = Path(self.tmp) / "legit-nested"
        meta = import_preset(out, target)
        self.assertEqual(meta["name"], "Legit")
        self.assertTrue((target / "kit" / "project-room.json").exists())


if __name__ == "__main__":
    unittest.main()
