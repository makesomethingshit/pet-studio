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
    ) -> None:
        self.kit_path = kit_path
        self.state = state
        self.fps = fps
        self.scale = scale
        self.frames = [composite_for_tk(scaled_frame(frame, scale)) for frame in render_frames(kit_path, state)]
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
    parser.add_argument("--kit", required=True, help="Path to project-room.json or a kit directory")
    parser.add_argument("--state", default="idle", choices=sorted(STATE_ROWS))
    parser.add_argument("--fps", type=float, default=6.0)
    parser.add_argument("--scale", type=float, default=1.0, help="Window display scale for the whole room")
    parser.add_argument("--x", type=int)
    parser.add_argument("--y", type=int)
    parser.add_argument("--no-topmost", action="store_true")
    parser.add_argument("--click-through", action="store_true")
    parser.add_argument("--render-once", help="Write one rendered full-size frame to PNG and exit")
    args = parser.parse_args()

    kit_path = resolve_kit_path(args.kit)
    if args.render_once:
        frame = scaled_frame(render_frames(kit_path, args.state)[0], args.scale)
        output = Path(args.render_once)
        output.parent.mkdir(parents=True, exist_ok=True)
        clear_transparent_rgb(frame).save(output)
        print(json.dumps({"ok": True, "output": str(output), "state": args.state}, indent=2))
        return

    widget = ProjectRoomWidget(
        kit_path=kit_path,
        state=args.state,
        fps=args.fps,
        scale=args.scale,
        x=args.x,
        y=args.y,
        topmost=not args.no_topmost,
        click_through=args.click_through,
    )
    widget.run()


if __name__ == "__main__":
    main()
