"""Interactive room creator — guided wizard for first-time users.

Usage:
    python tools/create_room_interactive.py

Walks through:
    1. Project ID
    2. Pet package (or use default)
    3. Room image (or generate)
    4. Props (optional)
    5. Theme
    6. Create + register + preflight
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "pet-studio-widget" / "project-room-projects.json"
CREATE_KIT_SCRIPT = ROOT / "pet-studio-kit" / "scripts" / "create_project_room_kit.py"
KIT_SCRIPTS = ROOT / "pet-studio-kit" / "scripts"

if str(KIT_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(KIT_SCRIPTS))

from asset_guardrails import is_safe_id  # noqa: E402


def ask(prompt: str, default: str | None = None) -> str:
    """Ask user for input with optional default."""
    if default:
        full = f"  {prompt} [{default}]: "
    else:
        full = f"  {prompt}: "
    value = input(full).strip()
    return value if value else (default or "")


def ask_path(prompt: str, must_exist: bool = True) -> Path | None:
    """Ask for a file path."""
    raw = ask(prompt)
    if not raw:
        return None
    path = Path(raw).expanduser()
    if must_exist and not path.exists():
        print(f"    [WARN] Not found: {path}")
        retry = ask("  Try again (or Enter to skip)", "")
        if retry:
            return ask_path(prompt, must_exist)
        return None
    return path


def ask_yes_no(prompt: str, default: bool = True) -> bool:
    suffix = " [Y/n]: " if default else " [y/N]: "
    value = input(f"  {prompt}{suffix}").strip().lower()
    if not value:
        return default
    return value in ("y", "yes")


def slug_to_title(value: str) -> str:
    words = [w for w in value.replace("_", "-").split("-") if w]
    return " ".join(w[:1].upper() + w[1:] for w in words) or "Pet Studio Room"


def validate_project_id(project_id: str) -> bool:
    if not is_safe_id(project_id):
        print(
            f"    [ERROR] Invalid ID '{project_id}'. Use letters, numbers, hyphens, underscores. Must start with letter/number."
        )
        return False
    return True


def check_registry(project_id: str) -> bool:
    """Check if project ID already exists in registry."""
    if not DEFAULT_REGISTRY.exists():
        return False
    try:
        data = json.loads(DEFAULT_REGISTRY.read_text(encoding="utf-8-sig"))
        for p in data.get("projects", []):
            if p.get("projectId") == project_id:
                return True
    except Exception:
        pass
    return False


def find_codex() -> str | None:
    """Find Codex CLI binary."""
    # Check PATH first
    for name in ("codex", "codex.exe"):
        try:
            result = subprocess.run([name, "--version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return name
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    # Check common install paths
    candidates = [
        Path.home() / ".codex" / "bin" / "codex.exe",
        Path.home() / ".codex" / "bin" / "codex",
        Path.home() / ".local" / "bin" / "codex",
        Path.home() / ".local" / "bin" / "codex.exe",
        Path(os.environ.get("APPDATA", "")) / "codex" / "codex.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "codex" / "codex.exe",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return None


def run_create_kit(
    out_dir: Path,
    pet_package: Path,
    room_image: Path,
    project_id: str,
    display_name: str,
    theme: str,
    props: list[tuple[str, Path]],
    prop_placements: dict[str, str],
    workspace_path: Path | None,
) -> bool:
    """Run the kit creation script."""
    cmd = [
        sys.executable,
        str(CREATE_KIT_SCRIPT),
        "--out-dir",
        str(out_dir),
        "--pet-package",
        str(pet_package),
        "--room-image",
        str(room_image),
        "--project-id",
        project_id,
        "--display-name",
        display_name,
        "--theme",
        theme,
        "--register-project",
        "--registry",
        str(DEFAULT_REGISTRY),
    ]
    for prop_id, prop_path in props:
        cmd.extend(["--prop", f"{prop_id}={prop_path}"])
        placement = prop_placements.get(prop_id, "behind-pet")
        cmd.extend(["--prop-placement", f"{prop_id}={placement}"])
    if workspace_path:
        cmd.extend(["--workspace-path", str(workspace_path)])

    print("\n  Creating room kit...")
    result = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if result.returncode != 0:
        print("    [ERROR] Kit creation failed:")
        print(result.stderr or result.stdout)
        return False
    print(f"    OK — kit created at {out_dir}")
    return True


def main() -> None:
    print()
    print("=" * 50)
    print("  Pet Studio — Interactive Room Creator")
    print("=" * 50)
    print()
    print("  This wizard creates a new pet room for your project.")
    print("  You'll need: a pet package, a room image, and a project ID.")
    print()

    # Step 1: Project ID
    print("─" * 50)
    print("  Step 1: Project ID")
    print("  (a unique name for this room, e.g. 'my-project')")
    print()
    while True:
        project_id = ask("Project ID")
        if not project_id:
            print("    [ERROR] Project ID is required.")
            continue
        if not validate_project_id(project_id):
            continue
        if check_registry(project_id):
            overwrite = ask_yes_no(f"  '{project_id}' already exists. Overwrite?", default=False)
            if not overwrite:
                continue
        break

    display_name = ask("Display name (or Enter to use project ID)", project_id)
    if not display_name:
        display_name = slug_to_title(project_id)

    # Step 2: Pet package
    print()
    print("─" * 50)
    print("  Step 2: Pet Package")
    print("  (folder containing pet.json + spritesheet.webp)")
    print()

    # Check for installed pets
    pets_dir = Path.home() / ".codex" / "pets"
    default_pet = None
    if pets_dir.exists():
        pet_dirs = [d for d in pets_dir.iterdir() if d.is_dir() and (d / "pet.json").exists()]
        if pet_dirs:
            print(f"  Found {len(pet_dirs)} installed pet(s):")
            for i, pd in enumerate(pet_dirs, 1):
                print(f"    {i}. {pd.name}")
            print(f"    {len(pet_dirs) + 1}. [새 펫 생성]")
            print()
            choice = ask("Select pet number (or Enter to specify path)", "")
            if choice.isdigit():
                choice_idx = int(choice)
                if 1 <= choice_idx <= len(pet_dirs):
                    default_pet = pet_dirs[choice_idx - 1]
                elif choice_idx == len(pet_dirs) + 1:
                    # New pet generation via Codex
                    print()
                    print("  [새 펫 생성]")
                    codex_cmd = find_codex()
                    if not codex_cmd:
                        print("  [ERROR] Codex CLI를 찾을 수 없습니다.")
                        print("  Codex를 설치하거나 PATH에 추가하세요.")
                        print("  https://github.com/openai/codex")
                        sys.exit(1)

                    theme_hint = ask("  펫 테마/스타일 (예: cute cat, robot dog, pixel dragon)", "cute pet")
                    prompt_hint = ask("  추가 프롬프트 (선택)", "")
                    print()
                    print("  Codex로 펫 생성 중...")

                    codex_prompt = f"Use $hatch-pet to create a new pet package. Theme: {theme_hint}"
                    if prompt_hint:
                        codex_prompt += f". Additional: {prompt_hint}"
                    codex_prompt += ". Output to ~/.codex/pets/<name>/ with pet.json and spritesheet.webp. Return the output path when done."

                    try:
                        result = subprocess.run(
                            [codex_cmd, "--prompt", codex_prompt], capture_output=True, text=True, timeout=120
                        )
                        output = result.stdout.strip()
                        # Parse pet package path from output
                        pet_package = None
                        for line in output.splitlines():
                            line = line.strip()
                            if line and (line.endswith("/") or line.endswith("\\")):
                                p = Path(line)
                                if (p / "pet.json").exists():
                                    pet_package = p
                                    break
                        if not pet_package:
                            # Fallback: check latest pet in ~/.codex/pets
                            pets_dir = Path.home() / ".codex" / "pets"
                            if pets_dir.exists():
                                pet_dirs = sorted(
                                    [d for d in pets_dir.iterdir() if d.is_dir() and (d / "pet.json").exists()],
                                    key=lambda d: d.stat().st_mtime,
                                    reverse=True,
                                )
                                if pet_dirs:
                                    pet_package = pet_dirs[0]
                        if pet_package:
                            print(f"    OK — 펫 생성됨: {pet_package}")
                        else:
                            print("    [WARN] 펫 생성 결과를 찾을 수 없습니다.")
                            print("    Codex 출력:")
                            print(output[:500])
                            pet_package = ask_path("Pet package folder path")
                            if not pet_package:
                                sys.exit(1)
                    except subprocess.TimeoutExpired:
                        print("    [ERROR] Codex 호출 타임아웃 (120초)")
                        sys.exit(1)
                    except Exception as e:
                        print(f"    [ERROR] Codex 호출 실패: {e}")
                        sys.exit(1)

    if default_pet:
        pet_package = default_pet
        print(f"    Using: {pet_package}")
    else:
        pet_package = ask_path("Pet package folder path")
        if not pet_package:
            print("    [ERROR] Pet package is required.")
            sys.exit(1)

    # Step 3: Room image
    print()
    print("─" * 50)
    print("  Step 3: Room Image")
    print("  (384x240 PNG with transparent background)")
    print()
    room_image = ask_path("Room image path (or Enter to skip — will use default)")
    if not room_image:
        # Use default room from kit
        default_room = ROOT / "pet-studio-kit" / "kit" / "rooms" / "default-room.png"
        if default_room.exists():
            room_image = default_room
            print(f"    Using default: {room_image}")
        else:
            print("    [ERROR] No default room image found. Please provide one.")
            sys.exit(1)

    # Step 4: Props (optional)
    print()
    print("─" * 50)
    print("  Step 4: Props (optional)")
    print("  (PNG images that appear in the room)")
    print()
    props: list[tuple[str, Path]] = []
    prop_placements: dict[str, str] = {}
    while ask_yes_no("Add a prop?", default=False):
        prop_id = ask("  Prop ID (e.g. 'desk', 'lamp')")
        if not prop_id:
            break
        prop_path = ask_path(f"  Prop image path for '{prop_id}'")
        if not prop_path:
            continue
        placement = ask("  Placement (background/behind-pet/front-of-pet/foreground)", "behind-pet")
        props.append((prop_id, prop_path))
        prop_placements[prop_id] = placement
        print(f"    Added: {prop_id} ({placement})")

    # Step 5: Theme
    print()
    print("─" * 50)
    print("  Step 5: Theme")
    print()
    theme = ask("Theme description (or Enter for default)", "pet studio room")

    # Step 6: Workspace path
    print()
    print("─" * 50)
    print("  Step 6: Workspace (optional)")
    print("  (link this room to a project folder for auto-detection)")
    print()
    workspace_path = None
    if ask_yes_no("Link to a workspace folder?", default=False):
        workspace_path = ask_path("Workspace folder path")
        if workspace_path and not workspace_path.is_dir():
            print(f"    [WARN] Not a directory: {workspace_path}")
            workspace_path = None

    # Summary
    print()
    print("=" * 50)
    print("  Summary")
    print("=" * 50)
    print(f"  Project ID:    {project_id}")
    print(f"  Display name:  {display_name}")
    print(f"  Pet package:   {pet_package}")
    print(f"  Room image:    {room_image}")
    print(f"  Props:         {len(props)}")
    print(f"  Theme:         {theme}")
    print(f"  Workspace:     {workspace_path or '(none)'}")
    print()

    if not ask_yes_no("Create this room?", default=True):
        print("  Cancelled.")
        sys.exit(0)

    # Create
    out_dir = ROOT / "runs" / f"{project_id}-room"
    success = run_create_kit(
        out_dir=out_dir,
        pet_package=pet_package,
        room_image=room_image,
        project_id=project_id,
        display_name=display_name,
        theme=theme,
        props=props,
        prop_placements=prop_placements,
        workspace_path=workspace_path,
    )

    if not success:
        sys.exit(1)

    # Preflight
    print()
    print("─" * 50)
    print("  Running preflight...")
    preflight_cmd = [
        sys.executable,
        str(ROOT / "tools" / "pet_studio_preflight.py"),
        "--project-id",
        project_id,
        "--skip-hooks",
    ]
    subprocess.run(preflight_cmd, cwd=str(ROOT))

    # Done
    print()
    print("=" * 50)
    print("  Room created!")
    print("=" * 50)
    print()
    print("  Launch it:")
    print(f"    .\\tools\\pet_studio_widget.cmd --project-id {project_id} --scale 1.25")
    print()
    print("  Create QA evidence:")
    print(f"    python tools\\pet_studio_create_qa_pack.py --project-id {project_id}")
    print()


if __name__ == "__main__":
    main()
