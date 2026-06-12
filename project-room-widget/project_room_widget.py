"""Frameless desktop widget runtime for Project Room Kit packages."""

from __future__ import annotations

import argparse
import json
import sys
import tkinter as tk
from pathlib import Path

from PIL import Image, ImageTk


ROOT = Path(__file__).resolve().parents[1]
LOCAL_TOOLS = ROOT / "project-room-kit" / "scripts"
INSTALLED_TOOLS = Path.home() / ".codex" / "skills" / "project-room-kit" / "scripts"
for tools_dir in (LOCAL_TOOLS, INSTALLED_TOOLS):
    if tools_dir.exists() and str(tools_dir) not in sys.path:
        sys.path.insert(0, str(tools_dir))

from bake_project_room_pet import (  # noqa: E402
    STATE_ROWS,
    build_source_frame,
    clear_transparent_rgb,
    load_layer_assets,
)
from project_room_registry import (  # noqa: E402
    DEFAULT_REGISTRY,
    DEFAULT_STATE_FILE,
    ProjectRegistryError,
    list_projects,
    normalize_state,
    project_to_summary,
    read_project_state,
    select_project,
)


CHROMA = "#ff00ff"


def resolve_kit_path(value: str) -> Path:
    path = Path(value).expanduser()
    if path.is_dir():
        path = path / "project-room.json"
    if not path.exists():
        raise FileNotFoundError(f"Project Room Kit manifest not found: {path}")
    return path


def load_kit(kit_path: Path) -> dict:
    return json.loads(kit_path.read_text(encoding="utf-8"))


def render_frames(kit_path: Path, state: str) -> list[Image.Image]:
    kit_dir = kit_path.parent
    kit = load_kit(kit_path)
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
        state_refresh_ms: int = 1000,
    ) -> None:
        self.kit_path = kit_path
        self.state = normalize_state(state, "idle")
        self.fps = fps
        self.scale = scale
        self.project_id = project_id
        self.state_file = state_file
        self.state_refresh_ms = max(250, state_refresh_ms)
        self.frames = [composite_for_tk(scaled_frame(frame, scale)) for frame in render_frames(kit_path, self.state)]
        self.index = 0
        self.drag_start: tuple[int, int] | None = None

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.configure(bg=CHROMA)
        self.root.wm_attributes("-transparentcolor", CHROMA)
        self.root.wm_attributes("-topmost", bool(topmost))
        self.root.title("Project Room Widget")

        if x is not None and y is not None:
            self.root.geometry(f"+{x}+{y}")

        self.image = ImageTk.PhotoImage(self.frames[0])
        self.label = tk.Label(self.root, image=self.image, bg=CHROMA, borderwidth=0, highlightthickness=0)
        self.label.pack()

        self.label.bind("<ButtonPress-1>", self.start_drag)
        self.label.bind("<B1-Motion>", self.drag)
        self.label.bind("<Double-Button-1>", self.cycle_state)
        self.label.bind("<Button-3>", lambda _event: self.root.destroy())
        self.root.bind("<Escape>", lambda _event: self.root.destroy())

        if click_through:
            self.root.after(250, self.enable_click_through)

        if self.state_file is not None:
            self.root.after(self.state_refresh_ms, self.refresh_external_state)

    def start_drag(self, event: tk.Event) -> None:
        self.drag_start = (event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y())

    def drag(self, event: tk.Event) -> None:
        if self.drag_start is None:
            return
        dx, dy = self.drag_start
        self.root.geometry(f"+{event.x_root - dx}+{event.y_root - dy}")

    def cycle_state(self, _event: tk.Event) -> None:
        states = list(STATE_ROWS)
        next_index = (states.index(self.state) + 1) % len(states)
        self.state = states[next_index]
        self.frames = [
            composite_for_tk(scaled_frame(frame, self.scale))
            for frame in render_frames(self.kit_path, self.state)
        ]
        self.index = 0

    def set_state(self, state: str) -> None:
        next_state = normalize_state(state, self.state)
        if next_state == self.state:
            return
        self.state = next_state
        self.frames = [
            composite_for_tk(scaled_frame(frame, self.scale))
            for frame in render_frames(self.kit_path, self.state)
        ]
        self.index = 0

    def refresh_external_state(self) -> None:
        if self.state_file is not None:
            self.set_state(read_project_state(self.state_file, self.project_id, self.state))
        self.root.after(self.state_refresh_ms, self.refresh_external_state)

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
        self.index = (self.index + 1) % len(self.frames)
        self.image = ImageTk.PhotoImage(self.frames[self.index])
        self.label.configure(image=self.image)
        delay = max(16, int(1000 / self.fps))
        self.root.after(delay, self.animate)

    def run(self) -> None:
        self.animate()
        self.root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kit", help="Path to project-room.json or a kit directory")
    parser.add_argument("--config", default=str(DEFAULT_REGISTRY), help="Project assignment registry path")
    parser.add_argument("--project-id", help="Project id from the registry")
    parser.add_argument("--list-projects", action="store_true", help="List registered projects and exit")
    parser.add_argument("--state-file", default=None, help="Optional external project state JSON file")
    parser.add_argument("--state-refresh-ms", type=int, default=1000)
    parser.add_argument("--state", default=None)
    parser.add_argument("--fps", type=float, default=6.0)
    parser.add_argument("--scale", type=float, default=1.0, help="Window display scale for the whole room")
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
    state = args.state or "idle"
    if args.project_id:
        try:
            project = select_project(args.config, args.project_id)
        except ProjectRegistryError as error:
            parser.error(str(error))
        kit_path = project.kit_manifest
        project_id = project.project_id
        state = args.state or project.default_state
    elif args.kit:
        kit_path = resolve_kit_path(args.kit)
    else:
        parser.error("Provide --kit or --project-id.")

    state_file = Path(args.state_file).expanduser() if args.state_file else (DEFAULT_STATE_FILE if project_id and args.state is None else None)
    if state_file is not None:
        state = read_project_state(state_file, project_id, state)

    render_once = args.render_project_once or args.render_once
    if render_once:
        frame = scaled_frame(render_frames(kit_path, state)[0], args.scale)
        output = Path(render_once)
        output.parent.mkdir(parents=True, exist_ok=True)
        clear_transparent_rgb(frame).save(output)
        print(json.dumps({"ok": True, "output": str(output), "state": normalize_state(state, "idle"), "projectId": project_id}, indent=2))
        return

    widget = ProjectRoomWidget(
        kit_path=kit_path,
        state=state,
        fps=args.fps,
        scale=args.scale,
        x=args.x,
        y=args.y,
        topmost=not args.no_topmost,
        click_through=args.click_through,
        project_id=project_id,
        state_file=state_file,
        state_refresh_ms=args.state_refresh_ms,
    )
    widget.run()


if __name__ == "__main__":
    main()
