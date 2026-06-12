# Pet Studio / Project Room Handoff

Last updated: 2026-06-13

## One-Line Summary

We built a modular Project Room system for Codex pets: `project-room-kit` creates and validates layered 384x240 room kits, and `project-room-widget` displays those kits as a frameless scene host with independent room, prop, and pet entities. The current best demo is Gakju in an SD/chibi archive room generated with GPT image generation.

## Current Workspace

- Main workspace: `D:\pet-studio`
- Roadmap: `D:\pet-studio\docs\PROJECT_ROOM_ROADMAP.md`
- Skill installed at: `C:\Users\USER\.codex\skills\project-room-kit`
- Gakju pet source: `C:\Users\USER\.codex\pets\gakju`
- Current best run: `D:\pet-studio\runs\gakju-imagegen-room-v1`
- Widget runtime: `D:\pet-studio\project-room-widget`

## What Exists Now

### 1. Project Room Kit

Folder: `D:\pet-studio\project-room-kit`

Purpose:

- Maintain a layered room-decorating source format.
- Keep room, props, main pet, and helper pets as separate layers.
- Validate style metadata and dimensions.
- Render full-size previews from the layered source.
- Optionally make hatch-pet fallback previews, but fallback is not the real output.

Important files:

- `kit/project-room.json`: layered room manifest.
- `kit/style-lock.json`: style contract.
- `scripts/validate_project_room_kit.py`: validates kit metadata, dimensions, style, perspective, room features, prop size, and pet atlas size.
- `scripts/project_room_assets.py`: clears edge-connected near-white room margins to transparent alpha while preserving `384x240` room size.
- `scripts/register_pet_package.py`: registers an existing hatch-pet package as a layer.
- `scripts/render_project_room_preview.py`: renders full-size room previews.
- `scripts/bake_project_room_pet.py`: optional diagnostic/fallback hatch-pet preview only.

Current format decisions:

- Source room canvas: `384x240`.
- Hatch-pet cell: `192x208`, used only for pet frames and optional fallback previews.
- Main pet remains a hatch-pet spritesheet layer.
- Props are separate PNG layers with alpha.
- Prop layers now declare semantic placement relative to the pet: `background`, `behindPet`, `frontOfPet`, or `foreground`. Renderers still execute by `z`, but the authoring intent is visible in `project-room.json`.
- Live scene-host layers can declare `draggable` and `locked`. Room/background layers are locked by default; props and pets are draggable by default.
- Every asset should have a sidecar `.asset.json`.
- Room intake clears edge-connected near-white borders at registration time; this fixes generated top/bottom fringe without cropping the source room.

### 2. Installed Codex Skill

Installed skill path:

```text
C:\Users\USER\.codex\skills\project-room-kit
```

The skill was validated with:

```powershell
$env:PYTHONPATH='C:\Users\USER\Documents\Codex\2026-06-11\pet-skill\work\pydeps'
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe C:\Users\USER\.codex\skills\.system\skill-creator\scripts\quick_validate.py C:\Users\USER\.codex\skills\project-room-kit
```

Expected result:

```text
Skill is valid!
```

Note:

- `PyYAML` was installed locally under `C:\Users\USER\Documents\Codex\2026-06-11\pet-skill\work\pydeps` only to run the skill validator.

### 3. Project Room Widget Runtime

Folder:

```text
D:\pet-studio\project-room-widget
```

Files:

- `project_room_widget.py`
- `project_room_scene.py`
- `codex_state_adapter.py`
- `set_project_state.py`
- `README.md`
- `project-room-projects.json`
- `project-room-layouts.json`
- `project-room-window.json`
- `project-room-state.json`
- `run-gakju-archive-room.bat`
- `run-gakju-imagegen-room-v1.bat`

Purpose:

- Load a `project-room.json` kit.
- Select a registered project by `projectId`.
- Poll a small state file for external project state.
- Write that state file manually or through a Codex-style task event adapter.
- Infer the active project from registry `workspacePaths` when adapter calls omit `--project-id`.
- Keep project assignment in `project-room-projects.json`; production reports also include a `projectLink` block for quick inspection.
- Render room, prop, main pet, and helper pet as independent Canvas entities in one transparent scene-host window.
- Persist project-specific dragged entity anchors in `project-room-layouts.json`.
- Persist registered project host window position and scale in `project-room-window.json`.
- Show state messages as a runtime-only speech bubble near the main pet.
- Open a right-click context menu instead of closing immediately.
- Animate pet states by cycling frames.

Controls:

- Drag a prop or pet with left mouse button.
- Drag locked room/background or empty space to move the host window.
- Double-click to cycle animation state.
- Right-click to open the context menu: cycle state, reset project layout, toggle bubble, or close.
- Escape closes the host.

Pet UX parity note:

- The original Codex pet runtime implementation is not bundled in this repo, so parity v1 covers confirmed behavior first: speech bubble, context menu instead of immediate right-click close, explicit close action, and window placement persistence.

Run current best widget:

```powershell
D:\pet-studio\project-room-widget\run-gakju-imagegen-room-v1.bat
```

Direct command:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe D:\pet-studio\project-room-widget\project_room_widget.py --kit D:\pet-studio\runs\gakju-imagegen-room-v1\kit --scale 1.25 --x 1200 --y 620
```

Registered project command:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe D:\pet-studio\project-room-widget\project_room_widget.py --project-id gakju-archive-demo --scale 1.25 --x 1200 --y 620
```

Render test:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe D:\pet-studio\project-room-widget\project_room_widget.py --kit D:\pet-studio\runs\gakju-imagegen-room-v1\kit --render-once D:\pet-studio\runs\widget-render-test.png
```

Publish a Codex-style state event:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe D:\pet-studio\project-room-widget\codex_state_adapter.py --event start --message "working"
```

## Current Best Run: `gakju-imagegen-room-v1`

Folder:

```text
D:\pet-studio\runs\gakju-imagegen-room-v1
```

Important outputs:

- `room-preview.png`: final full-size preview.
- `room-contact.png`: all-state preview sheet.
- `widget-render-test.png`: widget runtime render test.
- `kit/project-room.json`: final layered manifest.
- `kit/rooms/default-room.png`: GPT-generated SD/chibi room background.
- `kit/props/desk.png`: GPT-generated desk prop with alpha.
- `kit/props/book-stack.png`: GPT-generated book stack prop with alpha.
- `generated/`: preserved raw generated assets and processed alpha images.

Validation status:

- `validate_project_room_kit.py`: passed.
- `kit/rooms/default-room.png` edge-connected near-white room margin: cleaned from 19055 pixels to 0.
- `desk.png` transparent RGB residue: `0`.
- `book-stack.png` transparent RGB residue: `0`.
- `project-room-widget --render-once`: passed.
- Actual widget process was launched successfully with `pythonw.exe`.

## Image Generation Notes

The first GPT image generation attempt looked too much like a realistic/archive interior, not an SD character room. The prompt was revised after user feedback.

Correct visual direction:

- It should feel like an SD/chibi character dollhouse room.
- It should match Gakju's proportions and rendering density.
- It should not feel like a realistic interior background.
- Use big rounded furniture, fewer objects, thick soft outlines, warm parchment/gray colors, muted navy accents.
- Room should stay relatively open so Gakju does not get buried.

Important prompt constraints:

- No readable text.
- No letters.
- No numbers.
- No watermark.
- No UI frame.
- No character in the room background.
- For props, use flat chroma-key green background and remove it locally.

Chosen generation strategy:

- Room and props are separate.
- Room background should not include a desk/table that duplicates prop layers.
- Desk and book stack are transparent prop layers.

## Useful Commands

Validate current best kit:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe C:\Users\USER\.codex\skills\project-room-kit\scripts\validate_project_room_kit.py --kit D:\pet-studio\runs\gakju-imagegen-room-v1\kit\project-room.json --json-out D:\pet-studio\runs\gakju-imagegen-room-v1\kit-validation.json
```

Render full-size preview:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe C:\Users\USER\.codex\skills\project-room-kit\scripts\render_project_room_preview.py --kit D:\pet-studio\runs\gakju-imagegen-room-v1\kit\project-room.json --state idle --out D:\pet-studio\runs\gakju-imagegen-room-v1\room-preview.png
```

Render all-state preview:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe C:\Users\USER\.codex\skills\project-room-kit\scripts\render_project_room_preview.py --kit D:\pet-studio\runs\gakju-imagegen-room-v1\kit\project-room.json --state all --out D:\pet-studio\runs\gakju-imagegen-room-v1\room-contact.png
```

Launch widget:

```powershell
Start-Process -FilePath 'C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe' -ArgumentList @('D:\pet-studio\project-room-widget\project_room_widget.py','--kit','D:\pet-studio\runs\gakju-imagegen-room-v1\kit','--scale','1.25','--x','1180','--y','620')
```

## What To Do Next

Recommended next step:

1. Continue from `docs/PROJECT_ROOM_ROADMAP.md`.
2. Expand `codex_state_adapter.py` from workspace project detection toward hooks.
3. Add more pet runtime parity items as users identify them.
4. Generate additional room/prop variants and verify the intake cleanup.

Other good next steps:

- Generate one more SD room variant with even fewer built-in objects.
- Expand `project-room-kit/README.md` with more real production examples as the pipeline grows.
- Add a helper/sub-agent pet generation workflow.
- Add a project/chat-room identity layer so each project can own a different room kit.

## New Chat Starter Prompt

Paste this in a new Codex chat:

```text
We are continuing Pet Studio work from D:\pet-studio. Please read D:\pet-studio\PROJECT_HANDOFF.md first.

Current goal: continue the Project Room system for Codex pets. The best current demo is D:\pet-studio\runs\gakju-imagegen-room-v1, displayed by D:\pet-studio\project-room-widget\project_room_widget.py.

Important: the real output is a 384x240 scene-host kit, not a 192x208 hatch-pet spritesheet and not one precomposited widget image. Keep room, props, and pet entities separate. Use Gakju as the style source.
Roadmap: D:\pet-studio\docs\PROJECT_ROOM_ROADMAP.md
```
