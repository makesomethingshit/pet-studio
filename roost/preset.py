"""Room preset manager — export/import room presets as zip files.

A room preset bundles:
  - kit/           → project-room.json + image assets (pet spritesheet, room PNG, props)
  - layout.json    → anchor positions + z-order
  - session.json   → window position, scale, state
  - preset.json    → metadata (name, version, created at)
"""

from __future__ import annotations

import json
import logging
import shutil
import zipfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

PRESET_META_FILE = "preset.json"
PRESET_VERSION = "0.5.0"


class PresetError(Exception):
    """Raised when preset operations fail."""

    pass


def _preset_meta(name: str, source_dir: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    meta: dict[str, Any] = {
        "version": PRESET_VERSION,
        "name": name,
        "createdAt": datetime.now(UTC).isoformat(),
        "sourceDir": source_dir,
    }
    if extra:
        meta.update(extra)
    return meta


def export_preset(
    room_dir: Path,
    output: Path,
    name: str,
    *,
    include_session: bool = True,
    include_layout: bool = True,
) -> None:
    """Export a room directory as a preset zip.

    Args:
        room_dir: Path to the room directory (contains kit/, layout.json, session.json).
        output: Output zip file path.
        name: Human-readable preset name.
        include_session: Include session.json (window position/scale/state).
        include_layout: Include layout.json (anchor positions/z-order).
    """
    room_dir = room_dir.resolve()
    if not room_dir.is_dir():
        raise PresetError(f"Room directory not found: {room_dir}")

    kit_dir = room_dir / "kit"
    if not kit_dir.is_dir():
        raise PresetError(f"Kit directory not found: {kit_dir}")

    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    meta = _preset_meta(name, str(room_dir))

    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        # 1. Metadata
        zf.writestr(PRESET_META_FILE, json.dumps(meta, indent=2, ensure_ascii=False))

        # 2. Kit directory (project-room.json + all assets)
        for item in kit_dir.rglob("*"):
            if item.is_file():
                arcname = f"kit/{item.relative_to(kit_dir)}"
                zf.write(item, arcname)

        # 3. Layout
        if include_layout:
            layout_file = room_dir / "layout.json"
            if layout_file.exists():
                zf.write(layout_file, "layout.json")

        # 4. Session
        if include_session:
            session_file = room_dir / "session.json"
            if session_file.exists():
                zf.write(session_file, "session.json")

    logger.info("Preset exported: %s → %s", name, output)


def import_preset(
    zip_path: Path,
    target_dir: Path,
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Import a preset zip into a target directory.

    Args:
        zip_path: Path to the preset zip file.
        target_dir: Target room directory to extract into.
        overwrite: Overwrite existing files.

    Returns:
        Preset metadata dict.
    """
    zip_path = zip_path.resolve()
    if not zip_path.is_file():
        raise PresetError(f"Preset file not found: {zip_path}")

    target_dir = target_dir.resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # 1. Read metadata
            if PRESET_META_FILE not in zf.namelist():
                raise PresetError(f"Invalid preset: missing {PRESET_META_FILE}")
            meta = json.loads(zf.read(PRESET_META_FILE))

            # 2. Extract kit/
            for name in zf.namelist():
                if name.startswith("kit/"):
                    rel = name[len("kit/") :]
                    if not rel:
                        continue
                    dest = (target_dir / "kit" / rel).resolve()
                    if not dest.is_relative_to(target_dir.resolve()):
                        raise PresetError(f"Zip slip detected: {name}")
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    if dest.exists() and not overwrite:
                        logger.debug("Skipping existing: %s", dest)
                        continue
                    with zf.open(name) as src, dest.open("wb") as dst:
                        shutil.copyfileobj(src, dst)

            # 3. Extract layout.json
            if "layout.json" in zf.namelist():
                dest = (target_dir / "layout.json").resolve()
                if not dest.is_relative_to(target_dir.resolve()):
                    raise PresetError("Zip slip detected: layout.json")
                if not dest.exists() or overwrite:
                    with zf.open("layout.json") as src, dest.open("wb") as dst:
                        shutil.copyfileobj(src, dst)

            # 4. Extract session.json
            if "session.json" in zf.namelist():
                dest = (target_dir / "session.json").resolve()
                if not dest.is_relative_to(target_dir.resolve()):
                    raise PresetError("Zip slip detected: session.json")
                if not dest.exists() or overwrite:
                    with zf.open("session.json") as src, dest.open("wb") as dst:
                        shutil.copyfileobj(src, dst)
    except zipfile.BadZipFile as e:
        raise PresetError(f"Invalid preset zip: {e}") from e

    logger.info("Preset imported: %s → %s", meta.get("name", "?"), target_dir)
    return meta


def list_presets(presets_dir: Path) -> list[dict[str, Any]]:
    """List all preset zips in a directory.

    Returns:
        List of metadata dicts sorted by createdAt descending.
    """
    if not presets_dir.is_dir():
        return []

    results: list[dict[str, Any]] = []
    for zf_path in sorted(presets_dir.glob("*.zip"), reverse=True):
        try:
            with zipfile.ZipFile(zf_path, "r") as zf:
                if PRESET_META_FILE in zf.namelist():
                    meta = json.loads(zf.read(PRESET_META_FILE))
                    meta["_file"] = str(zf_path)
                    results.append(meta)
        except (zipfile.BadZipFile, json.JSONDecodeError) as e:
            logger.warning("Skipping invalid preset %s: %s", zf_path.name, e)

    results.sort(key=lambda m: m.get("createdAt", ""), reverse=True)
    return results
