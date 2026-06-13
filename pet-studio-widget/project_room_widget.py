"""Frameless desktop widget runtime for Pet Studio kits."""

from __future__ import annotations

import argparse
import json
import sys
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path

from PIL import Image, ImageTk


ROOT = Path(__file__).resolve().parents[1]
LOCAL_TOOLS = ROOT / "pet-studio-kit" / "scripts"
INSTALLED_TOOLS = Path.home() / ".codex" / "skills" / "pet-studio" / "scripts"
for tools_dir in (INSTALLED_TOOLS, LOCAL_TOOLS):
    if tools_dir.exists() and str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))

from bake_project_room_pet import (  # noqa: E402
    STATE_ROWS,
    build_source_frame,
    clear_transparent_rgb,
    crop_atlas_frame,
    load_layer_assets,
    scale_visible_layer,
)
from project_room_registry import (  # noqa: E402
    DEFAULT_ACTIVE_PROJECT_FILE,
    DEFAULT_REGISTRY,
    DEFAULT_STATE_FILE,
    ProjectRegistryError,
    list_projects,
    normalize_state,
    project_to_summary,
    select_project,
)
from set_active_project import write_active_project  # noqa: E402
from project_room_scene import (  # noqa: E402
    DEFAULT_LAYOUT_FILE,
    DEFAULT_WINDOW_FILE,
    SceneEntity,
    bubble_text_for_state,
    kit_with_layout,
    load_project_layout,
    load_project_window,
    reset_project_layout,
    save_project_anchor,
    save_project_window,
    save_project_z_order,
    scene_entities_from_kit,
    resolve_bubble_style,
    clamp_anchor_to_source_canvas,
    rounded_rectangle_points,
    visible_scene_entities,
)


CHROMA = "#ff00ff"
DEFAULT_BUBBLE_FONT = "Segoe UI"
TOPMOST_REFRESH_MS = 2000
FONT_CANDIDATES = {
    "base": ["Noto Sans", "Segoe UI", "Helvetica Neue", "DejaVu Sans", "Arial", "TkDefaultFont"],
    "cjk": [
        "Noto Sans CJK KR",
        "Noto Sans CJK SC",
        "Noto Sans CJK JP",
        "Noto Sans CJK TC",
        "Noto Sans KR",
        "Noto Sans SC",
        "Noto Sans JP",
        "Noto Sans TC",
        "Malgun Gothic",
        "Microsoft YaHei UI",
        "Yu Gothic UI",
        "Apple SD Gothic Neo",
        "PingFang SC",
        "Hiragino Sans",
    ],
    "arabic": ["Noto Sans Arabic", "Nirmala UI", "Segoe UI", "Arial"],
    "hebrew": ["Noto Sans Hebrew", "Segoe UI", "Arial"],
    "indic": [
        "Noto Sans Devanagari",
        "Noto Sans Bengali",
        "Noto Sans Tamil",
        "Noto Sans Telugu",
        "Noto Sans Gujarati",
        "Nirmala UI",
    ],
    "thai": ["Noto Sans Thai", "Leelawadee UI", "Nirmala UI"],
    "emoji": ["Noto Color Emoji", "Segoe UI Emoji", "Apple Color Emoji"],
}


def bubble_font_categories(text: str) -> list[str]:
    categories: list[str] = []
    for char in text:
        codepoint = ord(char)
        if (
            0x3040 <= codepoint <= 0x30FF
            or 0x3400 <= codepoint <= 0x4DBF
            or 0x4E00 <= codepoint <= 0x9FFF
            or 0xAC00 <= codepoint <= 0xD7AF
        ):
            categories.append("cjk")
        elif 0x0590 <= codepoint <= 0x05FF:
            categories.append("hebrew")
        elif 0x0600 <= codepoint <= 0x06FF or 0x0750 <= codepoint <= 0x077F or 0x08A0 <= codepoint <= 0x08FF:
            categories.append("arabic")
        elif 0x0900 <= codepoint <= 0x0DFF:
            categories.append("indic")
        elif 0x0E00 <= codepoint <= 0x0E7F:
            categories.append("thai")
        elif 0x1F300 <= codepoint <= 0x1FAFF:
            categories.append("emoji")
    return list(dict.fromkeys(categories))


def bubble_font_candidates(text: str) -> list[str]:
    candidates: list[str] = []
    for category in bubble_font_categories(text):
        candidates.extend(FONT_CANDIDATES[category])
    candidates.extend(FONT_CANDIDATES["base"])
    return list(dict.fromkeys(candidates))


def bubble_font_family(text: str, available_families: set[str] | None = None) -> str:
    if not available_families:
        return DEFAULT_BUBBLE_FONT
    normalized = {family.casefold(): family for family in available_families}
    for candidate in bubble_font_candidates(text):
        family = normalized.get(candidate.casefold())
        if family:
            return family
    return DEFAULT_BUBBLE_FONT


def resolve_kit_path(value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_dir():
        path = path / "project-room.json"
    if not path.exists():
        raise FileNotFoundError(f"Pet Studio kit manifest not found: {path}")
    return path


def load_kit(kit_path: Path) -> dict:
    return json.loads(kit_path.read_text(encoding="utf-8"))


def read_project_state_payload(state_file: Path, project_id: str | None, fallback: str) -> tuple[str, str | None]:
    if not state_file.exists():
        return normalize_state(fallback, "idle"), None
    try:
        data = json.loads(state_file.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return normalize_state(fallback, "idle"), None
    if project_id and data.get("projectId") != project_id:
        return normalize_state(fallback, "idle"), None
    message = data.get("message")
    return normalize_state(data.get("state"), fallback), message if isinstance(message, str) else None


def render_frames(kit_path: Path, state: str, layout: dict | None = None) -> list[Image.Image]:
    kit_dir = kit_path.parent
    kit = kit_with_layout(load_kit(kit_path), layout)
    warnings: list[str] = []
    layer_assets = load_layer_assets(kit_dir, kit["layers"], warnings)
    state = normalize_state(state, "idle")
    frame_count = STATE_ROWS[state]["frames"]
    return [
        clear_transparent_rgb(build_source_frame(kit_dir, kit, state, index, layer_assets, warnings))
        for index in range(frame_count)
    ]


def scaled_frame(frame: Image.Image, scale: float) -> Image.Image:
    if scale == 1:
        return frame
    width = max(1, int(round(frame.width * scale)))
    height = max(1, int(round(frame.height * scale)))
    return frame.resize((width, height), Image.Resampling.LANCZOS)


def composite_for_tk(frame: Image.Image) -> Image.Image:
    background = Image.new("RGBA", frame.size, CHROMA)
    background.alpha_composite(frame)
    return background.convert("RGB")


def apply_topmost(root: tk.Tk, enabled: bool) -> None:
    root.wm_attributes("-topmost", bool(enabled))
    if enabled:
        root.lift()


class ProjectRoomWidget:
    def __init__(
        self,
        kit_path: Path,
        state: str,
        fps: float,
        scale: float,
        x: int | None,
        y: int | None,
        topmost: bool,
        click_through: bool,
        project_id: str | None = None,
        state_file: Path | None = None,
        layout_file: Path | None = None,
        window_file: Path | None = None,
        state_refresh_ms: int = 1000,
        message: str | None = None,
    ) -> None:
        self.kit_path = kit_path
        self.kit_dir = kit_path.parent
        self.kit = load_kit(kit_path)
        self.state = normalize_state(state, "idle")
        self.fps = fps
        self.scale = scale
        self.project_id = project_id
        self.state_file = state_file
        self.layout_file = layout_file if project_id else None
        self.window_file = window_file if project_id else None
        self.message = message
        self.bubble_visible = True
        self.bubble_style = resolve_bubble_style(self.kit, self.kit_dir)
        self.layout = load_project_layout(layout_file, project_id) if layout_file and project_id else {"anchors": {}, "zOrder": {}}
        self.entities = scene_entities_from_kit(self.kit, self.layout)
        self.entities_by_id = {entity.id: entity for entity in self.entities}
        self.warnings: list[str] = []
        self.layer_assets = load_layer_assets(self.kit_dir, self.kit["layers"], self.warnings)
        self.state_refresh_ms = max(250, state_refresh_ms)
        self.index = 0
        self.drag_start: tuple[int, int] | None = None
        self.drag_entity_id: str | None = None
        self.drag_last: tuple[int, int] | None = None
        self.entity_items: dict[str, int] = {}
        self.entity_photos: dict[str, ImageTk.PhotoImage] = {}
        self.bubble_items: list[int] = []
        self.topmost = bool(topmost)

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.configure(bg=CHROMA)
        self.root.wm_attributes("-transparentcolor", CHROMA)
        apply_topmost(self.root, self.topmost)
        self.root.title("Pet Studio Widget")

        if x is not None and y is not None:
            self.root.geometry(f"+{x}+{y}")

        source_canvas = self.kit.get("sourceCanvas", self.kit["cell"])
        canvas_width = max(1, int(round(int(source_canvas["width"]) * scale)))
        canvas_height = max(1, int(round(int(source_canvas["height"]) * scale)))
        self.canvas = tk.Canvas(
            self.root,
            width=canvas_width,
            height=canvas_height,
            bg=CHROMA,
            borderwidth=0,
            highlightthickness=0,
        )
        self.canvas.pack()

        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)
        self.canvas.bind("<Double-Button-1>", self.cycle_state)
        self.canvas.bind("<Button-3>", self.show_context_menu)
        self.root.bind("<Escape>", lambda _event: self.root.destroy())
        self.root.bind("<Control-plus>", lambda _event: self.adjust_scale(1.1))
        self.root.bind("<Control-equal>", lambda _event: self.adjust_scale(1.1))
        self.root.bind("<Control-minus>", lambda _event: self.adjust_scale(1 / 1.1))
        self.root.bind("<Control-0>", lambda _event: self.reset_scale())
        self.redraw_scene()

        if click_through:
            self.root.after(250, self.enable_click_through)

        if self.state_file is not None:
            self.root.after(self.state_refresh_ms, self.refresh_external_state)
        if self.topmost:
            self.root.after(250, self.refresh_topmost)

    def entity_image(self, entity: SceneEntity, frame_index: int) -> Image.Image:
        source = self.layer_assets.get(entity.id)
        if source is None:
            raise FileNotFoundError(f"Required scene entity asset is missing: {entity.id}")
        if entity.role == "mainPet":
            row_state = self.kit["states"][self.state].get("mainPetRow", self.state)
            image = crop_atlas_frame(source, row_state, frame_index, int(self.kit["cell"]["width"]), int(self.kit["cell"]["height"]))
        elif entity.role == "helperPet":
            row_state = self.kit["states"][self.state].get("helperPetRow", self.state)
            image = crop_atlas_frame(source, row_state, frame_index, int(self.kit["cell"]["width"]), int(self.kit["cell"]["height"]))
        else:
            image = source
        scaled = scale_visible_layer(image, entity.scale * self.scale, entity.flip_x)
        return clear_transparent_rgb(scaled)

    def draw_entity(self, entity: SceneEntity, frame_index: int) -> None:
        image = self.entity_image(entity, frame_index)
        photo = ImageTk.PhotoImage(image)
        self.entity_photos[entity.id] = photo
        x = int(round(entity.anchor["x"] * self.scale))
        y = int(round(entity.anchor["y"] * self.scale))
        item = self.canvas.create_image(
            x,
            y,
            image=photo,
            anchor=tk.S,
            tags=("entity", f"entity:{entity.id}", f"role:{entity.role}"),
        )
        self.entity_items[entity.id] = item

    def redraw_scene(self) -> None:
        self.canvas.delete("entity")
        self.canvas.delete("bubble")
        self.entity_items.clear()
        self.entity_photos.clear()
        self.bubble_items.clear()
        for entity in visible_scene_entities(self.kit, self.entities, self.state):
            if entity.id not in self.layer_assets:
                if entity.role == "mainPet":
                    raise FileNotFoundError(f"Required main pet layer is missing: {entity.id}")
                continue
            self.draw_entity(entity, self.index)
        self.draw_bubble()

    def draw_bubble(self) -> None:
        text = bubble_text_for_state(self.state, self.message, self.bubble_visible)
        owner = self.entities_by_id.get("main-owner")
        if not text or owner is None:
            return
        canvas_width = max(1, int(self.canvas.cget("width")))
        canvas_height = max(1, int(self.canvas.cget("height")))
        x = int(round(owner.anchor["x"] * self.scale))
        y = int(round((owner.anchor["y"] - 116) * self.scale))
        margin = max(10, int(round(12 * self.scale)))
        max_width = min(max(104, int(round(142 * self.scale))), max(80, canvas_width - margin * 2))
        font_size = max(9, int(round(9.5 * self.scale)))
        text_item = self.canvas.create_text(
            x,
            y,
            text=text,
            width=max_width,
            fill=self.bubble_style["text"],
            font=(bubble_font_family(text, set(tkfont.families(self.root))), font_size, "normal"),
            anchor=tk.S,
            tags=("bubble",),
        )
        bbox = self.canvas.bbox(text_item)
        if bbox is None:
            return
        if bbox[0] < margin:
            self.canvas.move(text_item, margin - bbox[0], 0)
            bbox = self.canvas.bbox(text_item)
        if bbox and bbox[2] > canvas_width - margin:
            self.canvas.move(text_item, canvas_width - margin - bbox[2], 0)
            bbox = self.canvas.bbox(text_item)
        if bbox and bbox[1] < margin:
            self.canvas.move(text_item, 0, margin - bbox[1])
            bbox = self.canvas.bbox(text_item)
        if bbox is None:
            return
        pad_x = max(10, int(round(10 * self.scale)))
        pad_y = max(6, int(round(7 * self.scale)))
        radius = max(8, int(round(9 * self.scale)))
        left, top, right, bottom = bbox[0] - pad_x, bbox[1] - pad_y, bbox[2] + pad_x, bbox[3] + pad_y
        if bottom + max(8, int(round(9 * self.scale))) > canvas_height - margin:
            shift = canvas_height - margin - bottom - max(8, int(round(9 * self.scale)))
            self.canvas.move(text_item, 0, shift)
            bbox = self.canvas.bbox(text_item)
            if bbox is None:
                return
            left, top, right, bottom = bbox[0] - pad_x, bbox[1] - pad_y, bbox[2] + pad_x, bbox[3] + pad_y
        tail_anchor = max(left + radius + 6, min(x, right - radius - 6))
        shadow_offset = max(1, int(round(2 * self.scale)))
        tail_height = max(6, int(round(7 * self.scale)))
        tail_half = max(5, int(round(5.5 * self.scale)))
        rect_points = rounded_rectangle_points(left, top, right, bottom, radius, steps=5)
        shadow_rect = self.canvas.create_polygon(
            [coord + shadow_offset for coord in rect_points],
            fill=self.bubble_style["shadow"],
            outline="",
            tags=("bubble",),
        )
        shadow_tail = self.canvas.create_polygon(
            tail_anchor - tail_half + shadow_offset,
            bottom - 1 + shadow_offset,
            tail_anchor + tail_half + shadow_offset,
            bottom - 1 + shadow_offset,
            tail_anchor - int(round(2 * self.scale)) + shadow_offset,
            bottom + tail_height + shadow_offset,
            fill=self.bubble_style["shadow"],
            outline="",
            tags=("bubble",),
        )
        tail = self.canvas.create_polygon(
            tail_anchor - tail_half,
            bottom - 1,
            tail_anchor + tail_half,
            bottom - 1,
            tail_anchor - int(round(2 * self.scale)),
            bottom + tail_height,
            fill=self.bubble_style["fill"],
            outline=self.bubble_style["outline"],
            tags=("bubble",),
        )
        rect = self.canvas.create_polygon(
            rect_points,
            fill=self.bubble_style["fill"],
            outline=self.bubble_style["outline"],
            width=max(1, int(round(1.1 * self.scale))),
            tags=("bubble",),
        )
        self.canvas.tag_lower(rect, text_item)
        self.canvas.tag_lower(tail, rect)
        self.canvas.tag_lower(shadow_rect, tail)
        self.canvas.tag_lower(shadow_tail, shadow_rect)
        self.bubble_items.extend([shadow_rect, shadow_tail, rect, tail, text_item])

    def update_pet_frames(self) -> None:
        for entity in visible_scene_entities(self.kit, self.entities, self.state):
            if entity.role not in {"mainPet", "helperPet"} or entity.id not in self.entity_items:
                continue
            image = self.entity_image(entity, self.index)
            photo = ImageTk.PhotoImage(image)
            self.entity_photos[entity.id] = photo
            self.canvas.itemconfigure(self.entity_items[entity.id], image=photo)

    def item_entity(self, item: int) -> SceneEntity | None:
        for tag in self.canvas.gettags(item):
            if tag.startswith("entity:"):
                return self.entities_by_id.get(tag.split(":", 1)[1])
        return None

    def pick_draggable_entity(self, x: int, y: int) -> SceneEntity | None:
        items = self.canvas.find_overlapping(x, y, x, y)
        for item in reversed(items):
            entity = self.item_entity(item)
            if entity and entity.draggable and not entity.locked:
                return entity
            if entity and entity.locked:
                return None
        return None

    def replace_entity_anchor(self, entity_id: str, anchor: dict[str, int]) -> None:
        next_entities: list[SceneEntity] = []
        for entity in self.entities:
            if entity.id == entity_id:
                next_entities.append(
                    SceneEntity(
                        id=entity.id,
                        role=entity.role,
                        path=entity.path,
                        anchor_name=entity.anchor_name,
                        anchor=anchor,
                        scale=entity.scale,
                        flip_x=entity.flip_x,
                        z=entity.z,
                        placement=entity.placement,
                        visible_when=entity.visible_when,
                        draggable=entity.draggable,
                        locked=entity.locked,
                    )
                )
            else:
                next_entities.append(entity)
        self.entities = next_entities
        self.entities_by_id = {entity.id: entity for entity in self.entities}

    def replace_entity_z(self, entity_id: str, z: int) -> None:
        next_entities: list[SceneEntity] = []
        for entity in self.entities:
            next_entities.append(
                SceneEntity(
                    id=entity.id,
                    role=entity.role,
                    path=entity.path,
                    anchor_name=entity.anchor_name,
                    anchor=entity.anchor,
                    scale=entity.scale,
                    flip_x=entity.flip_x,
                    z=int(z) if entity.id == entity_id else entity.z,
                    placement=entity.placement,
                    visible_when=entity.visible_when,
                    draggable=entity.draggable,
                    locked=entity.locked,
                )
            )
        self.entities = sorted(next_entities, key=lambda entity: entity.z)
        self.entities_by_id = {entity.id: entity for entity in self.entities}

    def start_drag(self, event: tk.Event) -> None:
        entity = self.pick_draggable_entity(event.x, event.y)
        if entity is not None:
            self.drag_entity_id = entity.id
            self.drag_last = (event.x, event.y)
            self.drag_start = None
            return
        self.drag_entity_id = None
        self.drag_last = None
        self.drag_start = (event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y())

    def drag(self, event: tk.Event) -> None:
        if self.drag_entity_id is not None and self.drag_last is not None:
            last_x, last_y = self.drag_last
            dx = event.x - last_x
            dy = event.y - last_y
            item = self.entity_items.get(self.drag_entity_id)
            if item is not None:
                self.canvas.move(item, dx, dy)
            entity = self.entities_by_id[self.drag_entity_id]
            if entity.id == "main-owner":
                self.canvas.move("bubble", dx, dy)
            next_anchor = {
                "x": int(round(entity.anchor["x"] + dx / self.scale)),
                "y": int(round(entity.anchor["y"] + dy / self.scale)),
            }
            next_anchor = clamp_anchor_to_source_canvas(self.kit, next_anchor)
            self.replace_entity_anchor(self.drag_entity_id, next_anchor)
            self.drag_last = (event.x, event.y)
            return
        if self.drag_start is None:
            return
        dx, dy = self.drag_start
        self.root.geometry(f"+{event.x_root - dx}+{event.y_root - dy}")

    def end_drag(self, _event: tk.Event) -> None:
        if self.drag_entity_id and self.project_id and self.layout_file:
            entity = self.entities_by_id[self.drag_entity_id]
            save_project_anchor(self.layout_file, self.project_id, entity.id, entity.anchor)
        elif self.drag_start is not None:
            self.save_window_position()
        self.drag_entity_id = None
        self.drag_last = None
        self.drag_start = None

    def cycle_state(self, _event: tk.Event) -> None:
        states = list(STATE_ROWS)
        next_index = (states.index(self.state) + 1) % len(states)
        self.state = states[next_index]
        self.index = 0
        self.redraw_scene()

    def set_state(self, state: str, message: str | None = None) -> None:
        next_state = normalize_state(state, self.state)
        next_message = message if message is not None else self.message
        if next_state == self.state and next_message == self.message:
            return
        self.state = next_state
        self.message = next_message
        self.index = 0
        self.redraw_scene()

    def refresh_external_state(self) -> None:
        if self.state_file is not None:
            state, message = read_project_state_payload(self.state_file, self.project_id, self.state)
            self.set_state(state, message)
        self.root.after(self.state_refresh_ms, self.refresh_external_state)

    def refresh_topmost(self) -> None:
        if self.topmost:
            apply_topmost(self.root, True)
            self.root.after(TOPMOST_REFRESH_MS, self.refresh_topmost)

    def show_context_menu(self, event: tk.Event) -> None:
        entity = self.pick_draggable_entity(event.x, event.y)
        menu = tk.Menu(self.root, tearoff=False)
        menu.add_command(label="Cycle state", command=lambda: self.cycle_state(event))
        if self.project_id and self.layout_file:
            menu.add_command(label="Reset layout", command=self.reset_layout)
        if self.project_id and self.layout_file and entity is not None:
            menu.add_separator()
            menu.add_command(label="Bring forward", command=lambda entity_id=entity.id: self.adjust_entity_z(entity_id, 1))
            menu.add_command(label="Send backward", command=lambda entity_id=entity.id: self.adjust_entity_z(entity_id, -1))
            menu.add_command(label="Bring to front", command=lambda entity_id=entity.id: self.move_entity_z_to_edge(entity_id, "front"))
            menu.add_command(label="Send to back", command=lambda entity_id=entity.id: self.move_entity_z_to_edge(entity_id, "back"))
        menu.add_separator()
        menu.add_command(label="Larger", command=lambda: self.adjust_scale(1.1))
        menu.add_command(label="Smaller", command=lambda: self.adjust_scale(1 / 1.1))
        menu.add_command(label="Reset size", command=self.reset_scale)
        menu.add_separator()
        menu.add_command(label="Hide bubble" if self.bubble_visible else "Show bubble", command=self.toggle_bubble)
        menu.add_separator()
        menu.add_command(label="Close", command=self.root.destroy)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def reset_layout(self) -> None:
        if not self.project_id or not self.layout_file:
            return
        reset_project_layout(self.layout_file, self.project_id)
        self.layout = {"anchors": {}, "zOrder": {}}
        self.entities = scene_entities_from_kit(self.kit, self.layout)
        self.entities_by_id = {entity.id: entity for entity in self.entities}
        self.redraw_scene()

    def save_entity_z(self, entity_id: str, z: int) -> None:
        self.layout.setdefault("zOrder", {})[entity_id] = int(z)
        if self.project_id and self.layout_file:
            save_project_z_order(self.layout_file, self.project_id, entity_id, z)

    def set_entity_z(self, entity_id: str, z: int) -> None:
        if entity_id not in self.entities_by_id:
            return
        self.replace_entity_z(entity_id, z)
        self.save_entity_z(entity_id, z)
        self.redraw_scene()

    def adjust_entity_z(self, entity_id: str, delta: int) -> None:
        entity = self.entities_by_id.get(entity_id)
        if entity is None:
            return
        self.set_entity_z(entity_id, entity.z + delta)

    def move_entity_z_to_edge(self, entity_id: str, edge: str) -> None:
        if entity_id not in self.entities_by_id:
            return
        z_values = [entity.z for entity in self.entities]
        if not z_values:
            return
        next_z = max(z_values) + 1 if edge == "front" else min(z_values) - 1
        self.set_entity_z(entity_id, next_z)

    def toggle_bubble(self) -> None:
        self.bubble_visible = not self.bubble_visible
        self.redraw_scene()

    def set_scale(self, scale: float) -> None:
        next_scale = max(0.6, min(2.0, round(scale, 3)))
        if next_scale == self.scale:
            return
        self.scale = next_scale
        source_canvas = self.kit.get("sourceCanvas", self.kit["cell"])
        canvas_width = max(1, int(round(int(source_canvas["width"]) * self.scale)))
        canvas_height = max(1, int(round(int(source_canvas["height"]) * self.scale)))
        self.canvas.configure(width=canvas_width, height=canvas_height)
        self.redraw_scene()
        self.save_window_position()

    def adjust_scale(self, multiplier: float) -> None:
        self.set_scale(self.scale * multiplier)

    def reset_scale(self) -> None:
        self.set_scale(1.0)

    def save_window_position(self) -> None:
        if not self.project_id or not self.window_file:
            return
        save_project_window(
            self.window_file,
            self.project_id,
            {"x": self.root.winfo_x(), "y": self.root.winfo_y(), "scale": self.scale},
        )

    def enable_click_through(self) -> None:
        if sys.platform != "win32":
            return
        import ctypes

        hwnd = self.root.winfo_id()
        gwl_exstyle = -20
        ws_ex_layered = 0x00080000
        ws_ex_transparent = 0x00000020
        user32 = ctypes.windll.user32
        current = user32.GetWindowLongW(hwnd, gwl_exstyle)
        user32.SetWindowLongW(hwnd, gwl_exstyle, current | ws_ex_layered | ws_ex_transparent)

    def animate(self) -> None:
        frame_count = STATE_ROWS[self.state]["frames"]
        self.index = (self.index + 1) % frame_count
        self.update_pet_frames()
        delay = max(16, int(1000 / self.fps))
        self.root.after(delay, self.animate)

    def run(self) -> None:
        self.animate()
        self.root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kit", help="Path to a Pet Studio kit manifest (project-room.json) or kit directory")
    parser.add_argument("--config", default=str(DEFAULT_REGISTRY), help="Project assignment registry path")
    parser.add_argument("--project-id", help="Project id from the registry")
    parser.add_argument("--list-projects", action="store_true", help="List registered projects and exit")
    parser.add_argument("--state-file", default=None, help="Optional external project state JSON file")
    parser.add_argument("--layout-file", default=str(DEFAULT_LAYOUT_FILE), help="Optional project entity layout JSON file")
    parser.add_argument("--window-file", default=str(DEFAULT_WINDOW_FILE), help="Optional project window placement JSON file")
    parser.add_argument("--state-refresh-ms", type=int, default=1000)
    parser.add_argument("--state", default=None)
    parser.add_argument("--fps", type=float, default=6.0)
    parser.add_argument("--scale", type=float, default=None, help="Window display scale for the whole room")
    parser.add_argument("--x", type=int)
    parser.add_argument("--y", type=int)
    parser.add_argument("--no-topmost", action="store_true")
    parser.add_argument("--click-through", action="store_true")
    parser.add_argument("--render-once", help="Write one rendered full-size frame to PNG and exit")
    parser.add_argument("--render-project-once", help="Write one project-selected full-size frame to PNG and exit")
    args = parser.parse_args()

    if args.list_projects:
        try:
            projects = [project_to_summary(project) for project in list_projects(args.config)]
        except ProjectRegistryError as error:
            parser.error(str(error))
        print(json.dumps({"ok": True, "projects": projects}, indent=2))
        return

    project_id: str | None = None
    selected_project = None
    state = args.state or "idle"
    if args.project_id:
        try:
            project = select_project(args.config, args.project_id)
        except ProjectRegistryError as error:
            parser.error(str(error))
        selected_project = project
        kit_path = project.kit_manifest
        project_id = project.project_id
        state = args.state or project.default_state
    elif args.kit:
        kit_path = resolve_kit_path(args.kit)
    else:
        parser.error("Provide --kit or --project-id.")

    state_file = Path(args.state_file).expanduser() if args.state_file else (DEFAULT_STATE_FILE if project_id and args.state is None else None)
    layout_file = Path(args.layout_file).expanduser() if project_id and args.layout_file else None
    window_file = Path(args.window_file).expanduser() if project_id and args.window_file else None
    saved_window = load_project_window(window_file, project_id) if window_file and project_id else None
    scale = args.scale if args.scale is not None else float((saved_window or {}).get("scale", 1.0))
    x = args.x if args.x is not None else (saved_window or {}).get("x")
    y = args.y if args.y is not None else (saved_window or {}).get("y")
    message: str | None = None
    if state_file is not None:
        state, message = read_project_state_payload(state_file, project_id, state)

    render_once = args.render_project_once or args.render_once
    if render_once:
        layout = load_project_layout(layout_file, project_id) if layout_file and project_id else None
        frame = scaled_frame(render_frames(kit_path, state, layout)[0], scale)
        output = Path(render_once)
        output.parent.mkdir(parents=True, exist_ok=True)
        clear_transparent_rgb(frame).save(output)
        print(json.dumps({"ok": True, "output": str(output), "state": normalize_state(state, "idle"), "projectId": project_id}, indent=2))
        return

    if project_id and selected_project is not None:
        workspace_path = selected_project.workspace_paths[0] if selected_project.workspace_paths else Path.cwd()
        write_active_project(DEFAULT_ACTIVE_PROJECT_FILE, project_id, workspace_path)

    widget = ProjectRoomWidget(
        kit_path=kit_path,
        state=state,
        fps=args.fps,
        scale=scale,
        x=x,
        y=y,
        topmost=not args.no_topmost,
        click_through=args.click_through,
        project_id=project_id,
        state_file=state_file,
        layout_file=layout_file,
        window_file=window_file,
        state_refresh_ms=args.state_refresh_ms,
        message=message,
    )
    widget.run()


if __name__ == "__main__":
    main()
