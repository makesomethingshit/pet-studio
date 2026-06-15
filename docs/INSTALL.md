# Install

Pet Studio is currently Windows-focused and local-first.

## Requirements

- Windows as the primary tested desktop widget host.
- Python 3.11+ with Pillow.
- Codex Desktop or a local Codex skill folder for `$pet-studio`.
- A hatch-pet package to use as the style source when creating new rooms.

## Install The Skill

Clone the repo and install the skill:

```powershell
git clone https://github.com/makesomethingshit/codex-pet-studio-skill.git
cd codex-pet-studio-skill
.\tools\pet_studio_python.cmd tools\install_pet_studio_skill.py
```

To replace an older installed copy:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_skill.py --force
```

The installer copies the skill to:

```text
%USERPROFILE%\.codex\skills\pet-studio
```

The repository also keeps the older `project-room-*` file names as the v1 compatibility format. New public commands use Pet Studio names.

## Launch The Demo Widget

Run the preflight first. It checks Python/Pillow, the installed skill, the public demo registry, the sample kit, local-only ignore rules, and a one-frame render. It also reports whether Codex hook entries are installed:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py
```

Then launch the included Gakju archive room:

```powershell
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25
```

The normal widget launcher uses `pythonw`, so the command prompt does not stay attached. If the widget is already running, the launcher brings the existing `Pet Studio Widget` window forward instead of starting another copy. Close the widget from the right-click menu or press `Escape`.

For visible debug output:

```powershell
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25 --foreground
```

Detached launcher logs are local-only files under `pet-studio-widget\project-room-widget.log` and `pet-studio-widget\project-room-widget.err.log`.

Useful demo checks:

```powershell
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_widget.py --list-projects
.\tools\pet_studio_python.cmd pet-studio-widget\pet_studio_widget.py --project-id gakju-archive-demo --render-project-once runs\widget-render-test.png
```

The sample files under `runs/gakju-imagegen-room-v1/` are intended as public examples. Local QA reports, private test runs, preflight renders, and fresh project experiments stay ignored by git.

## Widget Controls

- Drag props or pets to reposition them.
- Drag the room background or empty space to move the widget window.
- Right-click for the context menu.
- Use `Larger`, `Smaller`, or `Reset size` from the context menu.
- Press `Ctrl` + `+`, `Ctrl` + `-`, or `Ctrl` + `0` for size controls.
- Press `Escape` to close.

Registered projects persist moved anchors and window scale locally.
