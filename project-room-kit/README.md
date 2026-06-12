# Project Room Kit

Project Room Kit is a modular pet-room asset format for a windowless Codex pet widget.

The idea is closer to room decorating than to a standalone app:

- pet assets
- helper pet assets
- room assets
- furniture and small props
- layout manifests
- optional baking into a normal hatch-pet package

## Why This Exists

The current hatch-pet package is a single `pet.json` plus `spritesheet.webp`. That is great for compatibility, but it is not enough for room decorating by itself.

Project Room Kit keeps the authoring model modular, then supports two output modes:

1. **Layered output** for a future runtime that can render room and prop layers.
2. **Baked output** for the current pet runtime, where the room, props, and pet frames are composed into one normal hatch-pet spritesheet.

## Folder Shape

```text
project-room-kit/
  generation-workflow.json
  kit/
    project-room.json
    rooms/
    props/
    pets/
  scripts/
    bake_project_room_pet.py
    create_project_room_kit.py
    create_sample_assets.py
    register_pet_package.py
    run_full_experiment.py
    validate_project_room_kit.py
```

## Asset Roles

- `room`: fixed-size side-view wall/floor/base layer. Every source room module is `384x240` and should include matching left/right doors.
- `prop`: furniture or decoration placed by anchors.
- `mainPet`: the project owner pet.
- `helperPet`: optional coworker used by review/handoff states.
- `overlay`: optional runtime-only bubble/status layer; not baked into sprites unless explicitly requested.

## Compatibility Rule

The kit should never require a separate visible app window. If the runtime cannot render layers, the kit is baked into a standard hatch-pet atlas.

## Room Module Contract

Every room background should use the same module size:

- `384x240` source canvas for the layered project-room widget.
- `192x208` hatch-pet cell only for compatibility preview/fallback baking.
- Eye-level side view.
- Left and right doors in consistent positions.
- A simple back wall and floor line.
- Quiet enough for pet and prop layers to stay readable.

This makes rooms feel like connected project nooks. Later, the runtime can swap room themes or decorate them without changing pet atlas geometry.

## Style Lock

The kit uses `kit/style-lock.json` as the art-direction contract. This exists to avoid the common solo-dev asset problem where individually nice assets look wrong together.

The room-decorating skill should start by asking which pet defines the style. Do not generate rooms, props, or helper pets before this is answered.

Good first prompt:

```text
Which pet should this room kit match?
1. Use an existing hatch-pet package as the style source.
2. Generate a new main pet with hatch-pet first, then match everything to it.
3. Use an existing style-lock.json directly.
```

The recommended path is option 2 for a new room kit, and option 1 when the user already likes a current pet.

Every asset should have a sidecar metadata file:

```text
rooms/default-room.png
rooms/default-room.asset.json
props/desk.png
props/desk.asset.json
pets/main-owner/spritesheet.webp
pets/main-owner/spritesheet.asset.json
```

The sidecar must match the kit `styleId` and perspective. The validator checks:

- asset file exists
- sidecar metadata exists
- `styleId` matches `style-lock.json`
- perspective matches
- room modules are exactly `384x240`
- room metadata includes left door, right door, floor line, and back wall
- pet atlases are exactly `1536x1872`
- props fit inside the `384x240` source room canvas
- static layers have no transparent RGB residue

This does not replace visual QA. It catches structural mismatch, while contact-sheet review catches taste mismatch.

Visual QA should reject an asset set when:

- one asset looks pixel-art, painterly, 3D, or photoreal while the others are sticker-like
- outline thickness or color obviously changes between pet, room, and props
- lighting direction or shadow treatment differs between assets
- room perspective drifts away from eye-level side view
- furniture scale makes the pet feel from a different world
- a prop has more rendering detail than the pet
- baked contact sheet feels like mixed asset packs instead of one tiny room set

## Current Workflow

## Production Generation Order

The intended production flow is:

1. Ask which pet or style source the room kit should match.
2. Lock the style in `kit/style-lock.json`.
3. Generate the main owner pet with `hatch-pet`, unless an existing pet was selected.
4. Register that hatch-pet package into `kit/pets/main-owner`.
5. Generate animated helper pets with `hatch-pet` when needed.
6. Register helper packages into `kit/pets/<helper-id>`.
7. Generate or author rooms and props under the same style-lock.
8. Validate the kit.
9. Bake the kit into a normal pet package.
10. Run hatch-pet atlas validation and contact sheet QA.

This is also captured in `generation-workflow.json`.

Create a production kit from an arbitrary hatch-pet package and generated or hand-authored room/prop PNGs:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe `
  D:\pet-studio\project-room-kit\scripts\create_project_room_kit.py `
  --out-dir D:\pet-studio\runs\my-project-room `
  --pet-package C:\Users\USER\.codex\pets\gakju `
  --room-image D:\pet-studio\runs\my-assets\room.png `
  --prop desk=D:\pet-studio\runs\my-assets\desk.png `
  --theme "quiet archive nook" `
  --display-name "Archive Nook" `
  --render-preview `
  --render-contact `
  --bake-fallback `
  --register-project `
  --project-id archive-nook `
  --registry D:\pet-studio\project-room-widget\project-room-projects.json
```

This writes `kit/project-room.json`, `kit/style-lock.json`, copied layer assets, sidecar `.asset.json` files, `generation-brief.json`, prompt text files, `kit-validation.json`, and `production-report.json`. The fallback package is optional and is only for runtimes that still need a normal hatch-pet package.

When `--register-project` is used, the new kit is also added to a project assignment registry so the widget can launch it with `--project-id`.

Register a hatch-pet package as a kit pet layer:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe `
  D:\pet-studio\project-room-kit\scripts\register_pet_package.py `
  --kit-dir D:\pet-studio\project-room-kit\kit `
  --package-dir D:\pet-studio\runs\some-hatch-pet-package `
  --layer-id main-owner
```

For a helper:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe `
  D:\pet-studio\project-room-kit\scripts\register_pet_package.py `
  --kit-dir D:\pet-studio\project-room-kit\kit `
  --package-dir D:\pet-studio\runs\some-helper-pet-package `
  --layer-id helper-reviewer `
  --feature review-helper
```

Run the whole compatibility experiment:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe `
  D:\pet-studio\project-room-kit\scripts\run_full_experiment.py `
  --source-kit-dir D:\pet-studio\project-room-kit\kit `
  --out-dir D:\pet-studio\runs\full-pipeline-experiment
```

This creates sample assets, validates style-lock metadata, bakes a normal pet package, validates the hatch-pet atlas, and writes a contact sheet.

Create sample assets for pipeline testing:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe `
  D:\pet-studio\project-room-kit\scripts\create_sample_assets.py `
  --kit-dir D:\pet-studio\project-room-kit\kit
```

Bake the kit into a standard pet package:

Validate style consistency first:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe `
  D:\pet-studio\project-room-kit\scripts\validate_project_room_kit.py `
  --kit D:\pet-studio\project-room-kit\kit\project-room.json `
  --json-out D:\pet-studio\runs\project-room-kit-sample\kit-style-validation.json
```

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe `
  D:\pet-studio\project-room-kit\scripts\bake_project_room_pet.py `
  --kit D:\pet-studio\project-room-kit\kit\project-room.json `
  --out-dir D:\pet-studio\runs\project-room-kit-sample `
  --pet-id project-room-kit-sample `
  --display-name "Project Room Kit Sample"
```

Validate the baked atlas:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe `
  C:\Users\USER\.codex\skills\hatch-pet\scripts\validate_atlas.py `
  D:\pet-studio\runs\project-room-kit-sample\spritesheet.webp `
  --json-out D:\pet-studio\runs\project-room-kit-sample\validation.json
```

Generate a contact sheet:

```powershell
C:\Users\USER\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe `
  C:\Users\USER\.codex\skills\hatch-pet\scripts\make_contact_sheet.py `
  D:\pet-studio\runs\project-room-kit-sample\spritesheet.webp `
  --output D:\pet-studio\runs\project-room-kit-sample\contact-sheet.png
```

## Next Real Art Step

Replace the sample assets with generated or hand-authored assets:

- `kit/rooms/default-room.png`
- `kit/props/desk.png`
- `kit/pets/main-owner/spritesheet.webp`
- `kit/pets/helper-reviewer/spritesheet.webp`

After replacement, run the same bake and validation commands. The output remains a normal pet package with `pet.json` and `spritesheet.webp`.
