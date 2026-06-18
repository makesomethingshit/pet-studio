"""Preset export/import dialogs for Project Room Widget.

Provides file dialog-based preset zip export and import.
"""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog


def _import_widget_helpers():
    """Lazy import to avoid circular dependency."""
    from project_room_widget import (
        load_kit,
        load_layer_assets,
        load_project_layout,
        scene_entities_from_kit,
    )

    return load_kit, load_layer_assets, load_project_layout, scene_entities_from_kit


def export_preset_dialog(widget) -> None:
    """Export current room as a preset zip via file dialog."""
    try:
        from roost.preset import export_preset

        presets_dir = Path.cwd() / "presets"
        presets_dir.mkdir(exist_ok=True)
        default_name = f"{widget.project_id}-preset.zip"
        out = filedialog.asksaveasfilename(
            title="Export preset",
            initialdir=str(presets_dir),
            initialfile=default_name,
            defaultextension=".zip",
            filetypes=[("Preset zip", "*.zip")],
        )
        if not out:
            return
        room_dir = widget.kit_path.parent
        export_preset(room_dir, Path(out), widget.project_id or "room")
    except Exception as e:
        from ui.toast import show_toast

        show_toast(widget, f"Export preset failed: {e}", level="error")


def import_preset_dialog(widget) -> None:
    """Import a preset zip and reload the room."""
    try:
        from roost.preset import import_preset

        load_kit, load_layer_assets, load_project_layout, scene_entities_from_kit = (
            _import_widget_helpers()
        )

        presets_dir = Path.cwd() / "presets"
        zf = filedialog.askopenfilename(
            title="Import preset",
            initialdir=str(presets_dir) if presets_dir.exists() else str(Path.cwd()),
            filetypes=[("Preset zip", "*.zip")],
        )
        if not zf:
            return
        room_dir = widget.kit_path.parent
        import_preset(Path(zf), room_dir, overwrite=True)
        widget.kit = load_kit(widget.kit_path)
        # Reload layout from the imported layout.json
        if widget.layout_file and widget.project_id:
            widget.layout = load_project_layout(widget.layout_file, widget.project_id)
        widget.entities = scene_entities_from_kit(widget.kit, widget.layout)
        widget.entities_by_id = {entity.id: entity for entity in widget.entities}
        widget.layer_assets = load_layer_assets(widget.kit_dir, widget.kit, widget.warnings)
        from ui.toast import show_toast

        show_toast(widget, "Preset imported", level="info")
        widget.redraw_scene()
    except Exception as e:
        from ui.toast import show_toast

        show_toast(widget, f"Import preset failed: {e}", level="error")
