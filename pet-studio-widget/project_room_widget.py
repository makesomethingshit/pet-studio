"""Frameless desktop widget runtime for Pet Studio kits."""

from __future__ import annotations

import argparse
import json
import logging
import os
import subprocess
import sys
import tkinter as tk
import tkinter.font as tkfont
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageTk

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parents[1]
LOCAL_TOOLS = ROOT / "pet-studio-kit" / "scripts"
INSTALLED_TOOLS = Path.home() / ".codex" / "skills" / "pet-studio" / "scripts"


def prefer_local_room_kit_tools() -> None:
    for tools_dir in (INSTALLED_TOOLS, LOCAL_TOOLS):
        tools_text = str(tools_dir)
        while tools_text in sys.path:
            sys.path.remove(tools_text)
        if tools_dir.exists():
            sys.path.insert(0, tools_text)


prefer_local_room_kit_tools()

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
from project_room_scene import (  # noqa: E402
    DEFAULT_LAYOUT_FILE,
    DEFAULT_SESSION_FILE,
    DEFAULT_WINDOW_FILE,
    SceneEntity,
    bubble_text_for_state,
    clamp_anchor_to_source_canvas,
    kit_with_layout,
    load_project_layout,
    load_project_session,
    load_project_window,
    reset_project_layout,
    resolve_bubble_style,
    rounded_rectangle_points,
    save_project_anchor,
    save_project_session,
    save_project_window,
    save_project_z_order,
    scene_entities_from_kit,
    visible_scene_entities,
)
from set_active_project import write_active_project  # noqa: E402

# UI submodules
from ui.preset_dialog import export_preset_dialog, import_preset_dialog  # noqa: E402
from ui.status_bar import draw_status_bar  # noqa: E402
from ui.team_room_popup import show_team_room  # noqa: E402

CHROMA = "#ff00ff"
WINDOW_TITLE = "Pet Studio Widget"
DEFAULT_BUBBLE_FONT = "Segoe UI"
TOPMOST_REFRESH_MS = 2000
BACKGROUND_CHILD_ENV = "PET_STUDIO_WIDGET_BACKGROUND_CHILD"
DEFAULT_WIDGET_LOG = ROOT / "pet-studio-widget" / "project-room-widget.log"
DEFAULT_WIDGET_LOCK = ROOT / "pet-studio-widget" / "project-room-widget.lock"
HIT_TEST_ALPHA_THRESHOLD = 16
DEFAULT_STATE_STALE_AFTER_MS = 300000
DEFAULT_DEMO_CYCLE_DELAY_SECONDS = 2.0
STATUS_BAR_HEIGHT = 20
STATUS_BAR_BG = "#1e1e2e"
STATUS_BAR_FG = "#cdd6f4"
STATUS_BAR_FONT = "Segoe UI"
STATUS_LABELS = {
    "idle": "대기",
    "running": "작업중",
    "waiting": "대기중",
    "review": "리뷰",
    "failed": "실패",
    "blocked": "차단됨",
    "handoff": "전환",
    "jumping": "완료",
    "done": "완료",
}
DEMO_CYCLE_STEPS = (
    ("idle", ""),
    ("running", "Working..."),
    ("waiting", "Compacting context..."),
    ("blocked", "Needs input"),
    ("review", "Ready for review"),
    ("done", "Done"),
    ("idle", ""),
)
STALE_BRIDGE_STATES = {"running", "waiting", "review", "failed", "blocked", "handoff"}
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


def parse_utc_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def reset_state_for_payload(data: dict, now: datetime | None = None) -> str | None:
    reset_after_ms = data.get("resetAfterMs")
    if not isinstance(reset_after_ms, (int, float)) or reset_after_ms < 0:
        return None
    updated_at = parse_utc_timestamp(data.get("updatedAt"))
    if updated_at is None:
        return None
    current = (now or datetime.now(UTC)).astimezone(UTC)
    elapsed_ms = (current - updated_at).total_seconds() * 1000
    if elapsed_ms < reset_after_ms:
        return None
    reset_to_state = data.get("resetToState")
    return reset_to_state if isinstance(reset_to_state, str) and reset_to_state.strip() else "idle"


def read_project_state_document(state_file: Path) -> dict | None:
    if not state_file.exists():
        return None
    try:
        data = json.loads(state_file.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def bridge_payload_is_stale(data: dict, stale_after_ms: int, now: datetime | None = None) -> bool:
    state = normalize_state(data.get("state"), "idle")
    reset_state = reset_state_for_payload(data, now)
    if reset_state is not None:
        return False
    if state not in STALE_BRIDGE_STATES:
        return False
    updated_at = parse_utc_timestamp(data.get("updatedAt"))
    if updated_at is None:
        return True
    current = (now or datetime.now(UTC)).astimezone(UTC)
    return (current - updated_at).total_seconds() * 1000 > stale_after_ms


def read_project_state_payload(
    state_file: Path,
    project_id: str | None,
    fallback: str,
    now: datetime | None = None,
) -> tuple[str, str | None]:
    data = read_project_state_document(state_file)
    if data is None:
        return normalize_state(fallback, "idle"), None
    if project_id and data.get("projectId") != project_id:
        return normalize_state(fallback, "idle"), None
    reset_state = reset_state_for_payload(data, now)
    if reset_state is not None:
        return normalize_state(reset_state, "idle"), None
    message = data.get("message")
    return normalize_state(data.get("state"), fallback), message if isinstance(message, str) else None


def read_fresh_project_state_payload(
    state_file: Path,
    project_id: str | None,
    fallback: str,
    stale_after_ms: int = DEFAULT_STATE_STALE_AFTER_MS,
    now: datetime | None = None,
) -> tuple[str, str | None, bool]:
    data = read_project_state_document(state_file)
    if data is None:
        return normalize_state(fallback, "idle"), None, False
    if project_id and data.get("projectId") != project_id:
        return normalize_state(fallback, "idle"), None, False
    if bridge_payload_is_stale(data, max(0, stale_after_ms), now):
        return normalize_state(fallback, "idle"), None, False
    state, message = read_project_state_payload(state_file, project_id, fallback, now)
    return state, message, True


def session_window_value(session: dict, key: str) -> int | float | None:
    window = session.get("window")
    if not isinstance(window, dict):
        return None
    value = window.get(key)
    if key == "scale":
        return float(value) if isinstance(value, (int, float)) and value > 0 else None
    return int(value) if isinstance(value, int) else None


def resolve_startup_window(
    saved_window: dict | None,
    session: dict,
    restore_session: bool,
    scale_arg: float | None,
    x_arg: int | None,
    y_arg: int | None,
) -> tuple[float, int | None, int | None]:
    session_scale = session_window_value(session, "scale") if restore_session else None
    session_x = session_window_value(session, "x") if restore_session else None
    session_y = session_window_value(session, "y") if restore_session else None
    scale = scale_arg if scale_arg is not None else float(session_scale or (saved_window or {}).get("scale", 1.0))
    x = x_arg if x_arg is not None else session_x if session_x is not None else (saved_window or {}).get("x")
    y = y_arg if y_arg is not None else session_y if session_y is not None else (saved_window or {}).get("y")
    return float(scale), x if isinstance(x, int) else None, y if isinstance(y, int) else None


def resolve_startup_state(
    default_state: str,
    explicit_state: str | None,
    state_file: Path | None,
    project_id: str | None,
    session: dict,
    restore_session: bool,
    stale_after_ms: int = DEFAULT_STATE_STALE_AFTER_MS,
    now: datetime | None = None,
) -> tuple[str, str | None, str]:
    if explicit_state is not None:
        return normalize_state(explicit_state, default_state), None, "cli"
    state = normalize_state(default_state, "idle")
    message: str | None = None
    state_source = "default"
    if restore_session and isinstance(session.get("state"), str):
        state = normalize_state(session["state"], state)
        message = session.get("message") if isinstance(session.get("message"), str) else None
        state_source = session.get("stateSource") if isinstance(session.get("stateSource"), str) else "session"
    if state_file is not None:
        bridge_state, bridge_message, applied = read_fresh_project_state_payload(
            state_file,
            project_id,
            state,
            stale_after_ms=stale_after_ms,
            now=now,
        )
        if applied:
            state = bridge_state
            message = bridge_message
            state_source = "bridge"
    return state, message, state_source


def restore_session_enabled(project_id: str | None, render_once: str | None, requested: bool | None) -> bool:
    if render_once or not project_id:
        return False
    return True if requested is None else bool(requested)


def render_frames(kit_path: Path, state: str, layout: dict | None = None) -> list[Image.Image]:
    kit_dir = kit_path.parent
    kit = kit_with_layout(load_kit(kit_path), layout)
    warnings: list[str] = []
    layer_assets = load_layer_assets(kit_dir, kit, warnings)
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


def is_gui_launch(args: argparse.Namespace) -> bool:
    return not bool(args.list_projects or args.render_once or args.render_project_once)


def pythonw_for(executable: str | Path) -> Path | None:
    current = Path(executable)
    if current.name.lower() == "pythonw.exe":
        return None
    sibling = current.with_name("pythonw.exe")
    if sibling.exists():
        return sibling
    bundled = (
        Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "python" / "pythonw.exe"
    )
    if bundled.exists():
        return bundled
    return None


def should_relaunch_background(
    args: argparse.Namespace, platform: str = sys.platform, env: dict[str, str] | None = None
) -> bool:
    if platform != "win32" or not is_gui_launch(args):
        return False
    if getattr(args, "foreground", False):
        return False
    return (env or os.environ).get(BACKGROUND_CHILD_ENV) != "1"


def focus_existing_widget_window(title: str = WINDOW_TITLE, platform: str = sys.platform) -> bool:
    if platform != "win32":
        return False
    try:
        import ctypes

        user32 = ctypes.windll.user32
        hwnd = user32.FindWindowW(None, title)
        if not hwnd:
            return False
        user32.ShowWindow(hwnd, 9)
        user32.SetForegroundWindow(hwnd)
    except (AttributeError, OSError):
        return False
    return True


def acquire_widget_lock(lock_file: Path = DEFAULT_WIDGET_LOCK, platform: str = sys.platform):
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    handle = lock_file.open("a+b")
    if platform == "win32":
        try:
            import msvcrt

            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            handle.seek(0)
            handle.truncate()
            handle.write(str(os.getpid()).encode("ascii", errors="ignore") or b"0")
            handle.flush()
            return handle
        except OSError:
            handle.close()
            return None
    try:
        import fcntl

        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return handle
    except (ImportError, OSError):
        handle.close()
        return None


def relaunch_background(argv: list[str], executable: str | Path = sys.executable, log_file: Path | None = None) -> bool:
    pythonw = pythonw_for(executable)
    if pythonw is None:
        return False
    env = dict(os.environ)
    env[BACKGROUND_CHILD_ENV] = "1"
    log_path = Path(env.get("PET_STUDIO_WIDGET_LOG", str(log_file or DEFAULT_WIDGET_LOG))).expanduser()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    creation_flags = 0
    if sys.platform == "win32":
        creation_flags = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
    try:
        with log_path.open("a", encoding="utf-8") as log_handle:
            log_handle.write(f"\n[{datetime.now(UTC).isoformat()}] launching Pet Studio widget\n")
            log_handle.flush()
            subprocess.Popen(
                [str(pythonw), str(Path(__file__).resolve()), *argv],
                cwd=str(ROOT),
                env=env,
                close_fds=True,
                creationflags=creation_flags,
                stdin=subprocess.DEVNULL,
                stdout=log_handle,
                stderr=log_handle,
            )
    except OSError:
        return False
    return True


def image_anchor_s_pixel_is_opaque(
    image: Image.Image,
    anchor_x: float,
    anchor_y: float,
    x: int,
    y: int,
    alpha_threshold: int = HIT_TEST_ALPHA_THRESHOLD,
) -> bool:
    left = int(round(anchor_x - image.width / 2))
    top = int(round(anchor_y - image.height))
    px = int(x - left)
    py = int(y - top)
    if px < 0 or py < 0 or px >= image.width or py >= image.height:
        return False
    return image.convert("RGBA").getpixel((px, py))[3] > alpha_threshold


def image_bounds_for_anchor(
    anchor: dict[str, int], image: Image.Image, widget_scale: float
) -> tuple[int, int, int, int]:
    x = int(round(anchor["x"] * widget_scale))
    y = int(round(anchor["y"] * widget_scale))
    left = int(round(x - image.width / 2))
    top = int(round(y - image.height))
    return (left, top, left + image.width, top + image.height)


def clamp_anchor_to_visible_image_bounds(
    kit: dict,
    anchor: dict[str, int],
    image: Image.Image,
    widget_scale: float,
) -> dict[str, int]:
    source_canvas = kit.get("sourceCanvas", kit.get("cell", {}))
    source_width = int(source_canvas.get("width", 0))
    source_height = int(source_canvas.get("height", 0))
    if source_width <= 0 or source_height <= 0 or widget_scale <= 0:
        return clamp_anchor_to_source_canvas(kit, anchor)
    image_width = image.width / widget_scale
    image_height = image.height / widget_scale
    if image_width >= source_width:
        x = source_width // 2
    else:
        min_x = image_width / 2
        max_x = source_width - image_width / 2
        x = int(round(max(min_x, min(max_x, int(anchor["x"])))))
    if image_height >= source_height:
        y = source_height
    else:
        min_y = image_height
        max_y = source_height
        y = int(round(max(min_y, min(max_y, int(anchor["y"])))))
    return {"x": x, "y": y}


def bounds_overlap(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    return a[0] < b[2] and a[2] > b[0] and a[1] < b[3] and a[3] > b[1]


def bubble_avoid_owner_shift(
    bubble_bounds: tuple[int, int, int, int],
    owner_bounds: tuple[int, int, int, int] | None,
    canvas_width: int,
    canvas_height: int,
    margin: int,
    gap: int,
) -> tuple[int, int]:
    if owner_bounds is None or not bounds_overlap(bubble_bounds, owner_bounds):
        return (0, 0)
    left, top, right, bottom = bubble_bounds
    width = right - left
    height = bottom - top
    candidates = [
        (0, owner_bounds[1] - gap - bottom),
        (owner_bounds[2] + gap - left, 0),
        (owner_bounds[0] - gap - right, 0),
    ]
    for dx, dy in candidates:
        shifted = (left + dx, top + dy, right + dx, bottom + dy)
        if (
            shifted[0] >= margin
            and shifted[1] >= margin
            and shifted[2] <= canvas_width - margin
            and shifted[3] <= canvas_height - margin
            and not bounds_overlap(shifted, owner_bounds)
        ):
            return (dx, dy)
    if owner_bounds[0] > canvas_width - owner_bounds[2]:
        target_left = max(margin, owner_bounds[0] - gap - width)
    else:
        target_left = min(canvas_width - margin - width, owner_bounds[2] + gap)
    target_top = min(max(margin, top), canvas_height - margin - height)
    return (target_left - left, target_top - top)


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
        session_file: Path | None = None,
        state_refresh_ms: int = 1000,
        state_stale_after_ms: int = DEFAULT_STATE_STALE_AFTER_MS,
        message: str | None = None,
        bubble_visible: bool = True,
        state_source: str = "default",
    ) -> None:
        self.kit_path = kit_path
        self.kit_dir = kit_path.parent
        self.kit = load_kit(kit_path)
        self.state = normalize_state(state, "idle")
        self.fps = fps
        self.scale = scale
        self.project_id = project_id
        self._project_display_name = None
        self._registry_path = None
        self.state_file = state_file
        self.layout_file = layout_file if project_id else None
        self.window_file = window_file if project_id else None
        self.session_file = session_file if project_id else None
        self.message = message
        self.bubble_visible = bool(bubble_visible)
        self.state_source = state_source
        self.bubble_style = resolve_bubble_style(self.kit, self.kit_dir)
        self.layout = (
            load_project_layout(layout_file, project_id)
            if layout_file and project_id
            else {"anchors": {}, "zOrder": {}}
        )
        self.entities = scene_entities_from_kit(self.kit, self.layout)
        self.entities_by_id = {entity.id: entity for entity in self.entities}
        self.warnings: list[str] = []
        self.layer_assets = load_layer_assets(self.kit_dir, self.kit, self.warnings)
        self.state_refresh_ms = max(250, state_refresh_ms)
        self.state_stale_after_ms = max(0, state_stale_after_ms)

        # --- Roost TeamState ---
        self._team_state: Any = None
        try:
            from roost.state import TeamState

            ts_path = self.state_file.parent / "team_state.json" if self.state_file else None
            self._team_state = TeamState(ts_path) if ts_path else TeamState()
        except Exception:  # noqa: BLE001
            self._toast_message = "TeamState init failed"
        self.demo_cycle_job_id: int | None = None
        self.index = 0
        self.drag_start: tuple[int, int] | None = None
        self.drag_entity_id: str | None = None
        self.drag_last: tuple[int, int] | None = None
        self.entity_items: dict[str, int] = {}
        self.entity_images: dict[str, Image.Image] = {}
        self.entity_photos: dict[str, ImageTk.PhotoImage] = {}
        self.bubble_items: list[int] = []
        self.topmost = bool(topmost)
        self._status_bar_items: list[int] = []
        self._toast_items: list[int] = []
        self._toast_job_id: int | None = None
        self._toast_message: str | None = None
        self._team_room_panel: tk.Toplevel | None = None
        self._context_menu_open = False

        # Feedback when no project detected
        if not self.project_id:
            self._toast_message = "No project detected — right-click to register"

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.configure(bg=CHROMA)
        self.root.wm_attributes("-transparentcolor", CHROMA)
        apply_topmost(self.root, self.topmost)
        self.root.title(WINDOW_TITLE)

        if x is not None and y is not None:
            self.root.geometry(f"+{x}+{y}")

        source_canvas = self.kit.get("sourceCanvas", self.kit["cell"])
        canvas_width = max(1, int(round(int(source_canvas["width"]) * scale)))
        canvas_height = max(1, int(round(int(source_canvas["height"]) * scale)))
        self._canvas_height = canvas_height
        self.canvas = tk.Canvas(
            self.root,
            width=canvas_width,
            height=canvas_height + STATUS_BAR_HEIGHT,
            bg=CHROMA,
            borderwidth=0,
            highlightthickness=0,
        )
        self.canvas.pack()

        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.drag)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)
        self.canvas.bind("<Double-Button-1>", lambda _event: self.run_demo_cycle())
        self.canvas.bind("<Button-3>", self.show_context_menu)
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<Escape>", lambda _event: self.close())
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
            image = crop_atlas_frame(
                source, row_state, frame_index, int(self.kit["cell"]["width"]), int(self.kit["cell"]["height"])
            )
        elif entity.role == "helperPet":
            row_state = self.kit["states"][self.state].get("helperPetRow", "review")
            image = crop_atlas_frame(
                source, row_state, frame_index, int(self.kit["cell"]["width"]), int(self.kit["cell"]["height"])
            )
        else:
            image = source
        scaled = scale_visible_layer(image, entity.scale * self.scale, entity.flip_x)
        return clear_transparent_rgb(scaled)

    def draw_entity(self, entity: SceneEntity, frame_index: int) -> None:
        image = self.entity_image(entity, frame_index)
        anchor = entity.anchor
        if entity.draggable and not entity.locked:
            anchor = clamp_anchor_to_visible_image_bounds(self.kit, entity.anchor, image, self.scale)
            if anchor != entity.anchor:
                self.replace_entity_anchor(entity.id, anchor)
                self.layout.setdefault("anchors", {})[entity.id] = anchor
                if self.project_id and self.layout_file:
                    save_project_anchor(self.layout_file, self.project_id, entity.id, anchor)
        photo = ImageTk.PhotoImage(image)
        self.entity_photos[entity.id] = photo
        x = int(round(anchor["x"] * self.scale))
        y = int(round(anchor["y"] * self.scale))
        item = self.canvas.create_image(
            x,
            y,
            image=photo,
            anchor=tk.S,
            tags=("entity", f"entity:{entity.id}", f"role:{entity.role}"),
        )
        self.entity_items[entity.id] = item
        self.entity_images[entity.id] = image

    def redraw_scene(self) -> None:
        self.canvas.delete("entity")
        self.canvas.delete("bubble")
        self.entity_items.clear()
        self.entity_images.clear()
        self.entity_photos.clear()
        self.bubble_items.clear()
        for entity in visible_scene_entities(self.kit, self.entities, self.state):
            if entity.id not in self.layer_assets:
                if entity.role == "mainPet":
                    raise FileNotFoundError(f"Required main pet layer is missing: {entity.id}")
                continue
            self.draw_entity(entity, self.index)
        self.draw_bubble()
        draw_status_bar(self)

    def _draw_status_bar(self) -> None:
        draw_status_bar(self)

    def _roost_status_icon(self) -> str:
        try:
            from roost.state import TeamState

            ts = TeamState()
            status = ts.roost_status
            return {"active": "\U0001f7e2", "idle": "\u26aa", "error": "\U0001f534"}.get(status, "\u26aa")
        except Exception:
            return ""

    def draw_bubble(self) -> None:
        text = bubble_text_for_state(self.state, self.message, self.bubble_visible)
        owner = self.entities_by_id.get("main-owner")
        if not text or owner is None:
            return
        canvas_width = max(1, int(self.canvas.cget("width")))
        canvas_height = self._canvas_height
        x = int(round(owner.anchor["x"] * self.scale))
        y = int(round((owner.anchor["y"] - 116) * self.scale))
        margin = max(10, int(round(12 * self.scale)))
        max_width = min(max(104, int(round(canvas_width * 0.8))), max(80, canvas_width - margin * 2))
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
        owner_item = self.entity_items.get(owner.id)
        owner_bbox = self.canvas.bbox(owner_item) if owner_item is not None else None
        gap = max(8, int(round(8 * self.scale)))
        dx, dy = bubble_avoid_owner_shift(
            (left, top, right, bottom),
            owner_bbox,
            canvas_width,
            canvas_height,
            margin,
            gap,
        )
        if dx or dy:
            self.canvas.move(text_item, dx, dy)
            bbox = self.canvas.bbox(text_item)
            if bbox is None:
                return
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
            self.entity_images[entity.id] = image
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
            if not entity:
                continue
            image = self.entity_images.get(entity.id)
            if image is not None:
                anchor_x, anchor_y = self.canvas.coords(item)
                if not image_anchor_s_pixel_is_opaque(image, anchor_x, anchor_y, x, y):
                    continue
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
            image = self.entity_images.get(entity.id)
            if image is not None:
                next_anchor = clamp_anchor_to_visible_image_bounds(self.kit, next_anchor, image, self.scale)
            else:
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

    def cancel_demo_cycle(self) -> None:
        if self.demo_cycle_job_id is None:
            return
        try:
            self.root.after_cancel(self.demo_cycle_job_id)
        except tk.TclError:
            pass
        self.demo_cycle_job_id = None

    def run_demo_cycle(self, delay_seconds: float = DEFAULT_DEMO_CYCLE_DELAY_SECONDS) -> None:
        self.cancel_demo_cycle()
        steps = list(DEMO_CYCLE_STEPS)
        delay_ms = max(0, int(round(delay_seconds * 1000)))

        def apply_step(index: int) -> None:
            if index >= len(steps):
                self.demo_cycle_job_id = None
                return
            state, message = steps[index]
            self.set_state(state, message, state_source="demo-cycle")
            if index < len(steps) - 1:
                self.demo_cycle_job_id = self.root.after(delay_ms, lambda: apply_step(index + 1))
            else:
                self.demo_cycle_job_id = None

        apply_step(0)

    def set_state(self, state: str, message: str | None = None, state_source: str | None = None) -> None:
        next_state = normalize_state(state, self.state)
        next_message = message if message is not None else self.message
        next_source = state_source or self.state_source
        if next_state == self.state and next_message == self.message:
            if state_source and next_source != self.state_source:
                self.state_source = next_source
                self.save_session(next_source)
            return

        self.state = next_state
        self.message = next_message
        self.state_source = next_source
        self.index = 0
        self.redraw_scene()
        if state_source:
            self.save_session(next_source)

    def refresh_external_state(self) -> None:
        if self.state_file is not None:
            state, message, applied = read_fresh_project_state_payload(
                self.state_file,
                self.project_id,
                self.state,
                stale_after_ms=self.state_stale_after_ms,
            )
            if applied:
                self.set_state(state, message, state_source="bridge")
        self.root.after(self.state_refresh_ms, self.refresh_external_state)

    def refresh_topmost(self) -> None:
        if self.topmost and not self._context_menu_open:
            apply_topmost(self.root, True)
        if self.topmost:
            self.root.after(TOPMOST_REFRESH_MS, self.refresh_topmost)

    def show_context_menu(self, event: tk.Event) -> None:
        entity = self.pick_draggable_entity(event.x, event.y)
        menu = tk.Menu(self.root, tearoff=False)
        menu.add_command(label="Cycle state", command=self.run_demo_cycle)

        # Switch to submenu
        if self._registry_path:
            try:
                projects = [project_to_summary(p) for p in list_projects(self._registry_path)]
                if len(projects) > 1:
                    switch_menu = tk.Menu(menu, tearoff=False)
                    for p in projects:
                        pid = p["projectId"]
                        name = p.get("displayName", pid)
                        if pid == self.project_id:
                            switch_menu.add_label(f"• {name} (current)")
                        else:
                            switch_menu.add_command(
                                label=name,
                                command=lambda pid=pid: self.switch_project(pid),
                            )
                    menu.add_cascade(label="Switch to", menu=switch_menu)
            except Exception:
                pass

        # Team Room
        if self._team_state is not None:
            try:
                pending = self._team_state.get_pending_approvals()
                queue = self._team_state.get_roost_queue()
                pending_count = len(pending)
                queue_count = len(queue)
                label = "Team Room"
                if pending_count:
                    label += f" ({pending_count} approval{'s' if pending_count != 1 else ''} pending)"
                elif queue_count:
                    label += f" ({queue_count} in queue)"
                menu.add_command(label=label, command=self._show_team_room)
                menu.add_separator()
            except Exception:  # noqa: BLE001
                pass

        # Preset submenu
        if self.project_id:
            preset_menu = tk.Menu(menu, tearoff=False)
            preset_menu.add_command(
                label="Export preset",
                command=self._export_preset_dialog,
            )
            preset_menu.add_command(
                label="Import preset",
                command=self._import_preset_dialog,
            )
            menu.add_cascade(label="Preset", menu=preset_menu)

        if self.project_id and self.layout_file:
            menu.add_command(label="Reset layout", command=self.reset_layout)
        if self.project_id and self.layout_file and entity is not None:
            menu.add_separator()
            menu.add_command(
                label="Bring forward", command=lambda entity_id=entity.id: self.adjust_entity_z(entity_id, 1)
            )
            menu.add_command(
                label="Send backward", command=lambda entity_id=entity.id: self.adjust_entity_z(entity_id, -1)
            )
            menu.add_command(
                label="Bring to front",
                command=lambda entity_id=entity.id: self.move_entity_z_to_edge(entity_id, "front"),
            )
            menu.add_command(
                label="Send to back", command=lambda entity_id=entity.id: self.move_entity_z_to_edge(entity_id, "back")
            )
        menu.add_separator()
        menu.add_command(label="Larger", command=lambda: self.adjust_scale(1.1))
        menu.add_command(label="Smaller", command=lambda: self.adjust_scale(1 / 1.1))
        menu.add_command(label="Reset size", command=self.reset_scale)
        menu.add_separator()
        menu.add_command(label="Hide bubble" if self.bubble_visible else "Show bubble", command=self.toggle_bubble)
        menu.add_separator()
        menu.add_command(label="Close", command=self.close)

        def restore_topmost(_event: tk.Event | None = None) -> None:
            if not self._context_menu_open:
                return
            self._context_menu_open = False
            if self.topmost:
                try:
                    apply_topmost(self.root, True)
                except tk.TclError:
                    pass

        if self.topmost:
            self._context_menu_open = True
            apply_topmost(self.root, False)
            menu.bind("<Unmap>", restore_topmost)
            menu.bind("<Destroy>", restore_topmost)
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _show_team_room(self) -> None:
        show_team_room(self)

    def _on_close_team_room(self) -> None:
        if self._team_room_panel is not None:
            try:
                self._team_room_panel.close()  # type: ignore[attr-defined]
            except tk.TclError:
                pass

    def _resolve_approval(self, approval_id: str, approved: bool) -> None:
        if self._team_state is not None:
            self._team_state.resolve_approval(approval_id, approved)
        if self._team_room_panel is not None:
            try:
                self._team_room_panel.destroy()
            except tk.TclError:
                pass
            self._team_room_panel = None
        show_team_room(self)

    def _export_preset_dialog(self) -> None:
        export_preset_dialog(self)

    def _import_preset_dialog(self) -> None:
        import_preset_dialog(self)

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
        self.save_session(self.state_source)

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
        if not self.project_id:
            return
        window = {"x": self.root.winfo_x(), "y": self.root.winfo_y(), "scale": self.scale}
        if self.window_file:
            save_project_window(self.window_file, self.project_id, window)
        self.save_session(self.state_source)

    def save_session(self, state_source: str | None = None) -> None:
        if not self.project_id or not self.session_file:
            return
        if state_source:
            self.state_source = state_source
        save_project_session(
            self.session_file,
            self.project_id,
            {
                "state": self.state,
                "message": self.message or "",
                "bubbleVisible": self.bubble_visible,
                "window": {"x": self.root.winfo_x(), "y": self.root.winfo_y(), "scale": self.scale},
                "stateSource": self.state_source,
                "updatedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            },
        )

    def switch_project(self, project_id: str) -> None:
        try:
            project = select_project(self._registry_path, project_id)
        except ProjectRegistryError:
            return
        self.project_id = project_id
        self._project_display_name = project.display_name
        self.kit_path = project.kit_manifest
        self.kit_dir = project.kit_manifest.parent
        self.kit = load_kit(project.kit_manifest)
        self.state = normalize_state(project.default_state, "idle")
        self.message = None
        self.state_source = "default"
        self.bubble_style = resolve_bubble_style(self.kit, self.kit_dir)
        self.layout = {"anchors": {}, "zOrder": {}}
        self.entities = scene_entities_from_kit(self.kit, self.layout)
        self.entities_by_id = {entity.id: entity for entity in self.entities}
        self.warnings = []
        self.layer_assets = load_layer_assets(self.kit_dir, self.kit, self.warnings)
        self.index = 0
        source_canvas = self.kit.get("sourceCanvas", self.kit["cell"])
        canvas_width = max(1, int(round(int(source_canvas["width"]) * self.scale)))
        canvas_height = max(1, int(round(int(source_canvas["height"]) * self.scale)))
        self._canvas_height = canvas_height
        self.canvas.configure(width=canvas_width, height=canvas_height + STATUS_BAR_HEIGHT)
        self.entity_items.clear()
        self.entity_images.clear()
        self.entity_photos.clear()
        self.bubble_items.clear()
        self._status_bar_items.clear()
        self.redraw_scene()

    def close(self) -> None:
        self.cancel_demo_cycle()
        self.save_session(self.state_source)
        self.root.destroy()

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
    parser.add_argument(
        "--layout-file", default=str(DEFAULT_LAYOUT_FILE), help="Optional project entity layout JSON file"
    )
    parser.add_argument(
        "--window-file", default=str(DEFAULT_WINDOW_FILE), help="Optional project window placement JSON file"
    )
    parser.add_argument(
        "--session-file", default=str(DEFAULT_SESSION_FILE), help="Optional project session snapshot JSON file"
    )
    parser.add_argument(
        "--restore-session",
        dest="restore_session",
        action="store_true",
        default=None,
        help="Restore the last registered project session",
    )
    parser.add_argument(
        "--no-restore-session",
        dest="restore_session",
        action="store_false",
        help="Ignore the saved project session for deterministic launches",
    )
    parser.add_argument("--state-refresh-ms", type=int, default=1000)
    parser.add_argument("--state-stale-after-ms", type=int, default=DEFAULT_STATE_STALE_AFTER_MS)
    parser.add_argument("--state", default=None)
    parser.add_argument("--fps", type=float, default=6.0)
    parser.add_argument("--scale", type=float, default=None, help="Window display scale for the whole room")
    parser.add_argument("--x", type=int)
    parser.add_argument("--y", type=int)
    parser.add_argument("--no-topmost", action="store_true")
    parser.add_argument("--click-through", action="store_true")
    parser.add_argument(
        "--foreground", action="store_true", help="Keep the widget attached to this console for debugging"
    )
    parser.add_argument("--render-once", help="Write one rendered full-size frame to PNG and exit")
    parser.add_argument("--render-project-once", help="Write one project-selected full-size frame to PNG and exit")
    args = parser.parse_args()

    # Auto-detect project from workspace if --project-id not given and not listing/rendering
    if not args.project_id and not args.list_projects and not args.render_once and not args.render_project_once:
        try:
            from registry import infer_project_for_workspace

            detected = infer_project_for_workspace(args.config, Path.cwd())
            args.project_id = detected.project_id
            print(f"  [auto-detect] Project: {args.project_id} (workspace: {Path.cwd()})")
        except Exception:
            pass  # Silently fall through; later checks will report "no project"

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

    gui_launch = is_gui_launch(args)
    if gui_launch and not args.foreground and focus_existing_widget_window():
        return

    if should_relaunch_background(args) and relaunch_background(sys.argv[1:]):
        return

    widget_lock = None
    if gui_launch and not args.foreground:
        widget_lock = acquire_widget_lock()
        if widget_lock is None:
            focus_existing_widget_window()
            return

    render_once = args.render_project_once or args.render_once
    restore_session = restore_session_enabled(project_id, render_once, args.restore_session)
    state_file = (
        Path(args.state_file).expanduser()
        if args.state_file
        else (DEFAULT_STATE_FILE if project_id and args.state is None else None)
    )
    layout_file = Path(args.layout_file).expanduser() if project_id and args.layout_file else None
    window_file = Path(args.window_file).expanduser() if project_id and args.window_file else None
    session_file = Path(args.session_file).expanduser() if project_id and args.session_file else None
    saved_window = load_project_window(window_file, project_id) if window_file and project_id else None
    session = load_project_session(session_file, project_id) if restore_session and session_file else {}
    scale, x, y = resolve_startup_window(saved_window, session, restore_session, args.scale, args.x, args.y)
    state, message, state_source = resolve_startup_state(
        state,
        args.state,
        state_file,
        project_id,
        session,
        restore_session,
        stale_after_ms=args.state_stale_after_ms,
    )
    bubble_visible = session.get("bubbleVisible", True) if restore_session else True

    if render_once:
        layout = load_project_layout(layout_file, project_id) if layout_file and project_id else None
        frame = scaled_frame(render_frames(kit_path, state, layout)[0], scale)
        output = Path(render_once)
        output.parent.mkdir(parents=True, exist_ok=True)
        clear_transparent_rgb(frame).save(output)
        print(
            json.dumps(
                {"ok": True, "output": str(output), "state": normalize_state(state, "idle"), "projectId": project_id},
                indent=2,
            )
        )
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
        session_file=session_file if restore_session else None,
        state_refresh_ms=args.state_refresh_ms,
        state_stale_after_ms=args.state_stale_after_ms,
        message=message,
        bubble_visible=bool(bubble_visible),
        state_source=state_source,
    )
    if selected_project is not None:
        widget._project_display_name = selected_project.display_name
    widget._registry_path = args.config
    try:
        widget.run()
    finally:
        if widget_lock is not None:
            widget_lock.close()


if __name__ == "__main__":
    main()
