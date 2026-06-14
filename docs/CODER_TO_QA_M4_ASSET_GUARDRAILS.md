# Coder To QA: M4 Asset Guardrails

## Scope

M4 adds pre-generation asset guardrails for first-room creation. It does not change `tester/` reports or existing `QA_REPORT.md` files.

## What Changed

- Added common asset guardrail checks used by both the guided wrapper and lower-level kit generator.
- Added `--guardrail-mode basic|strict|off`, defaulting to `basic`.
- Structural errors fail before creating a misleading kit: wrong room size, duplicate ids, prop/helper id collision, invisible props, oversized props, unknown prop placements, and invalid helper package atlases.
- Subjective style risks remain warnings in `basic`, become failures in `strict`, and are suppressed in `off`.
- Generator production reports and guided wrapper JSON summaries include `guardrails`.

## Suggested QA Commands

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_create_room.py --project-id guardrail-dry-run --pet-package <pet-package> --room-image <room.png> --dry-run
.\tools\pet_studio_python.cmd tools\pet_studio_create_room.py --project-id guardrail-strict --pet-package <pet-package> --room-image <room.png> --guardrail-mode strict --dry-run
.\tools\pet_studio_python.cmd tools\pet_studio_create_room.py --project-id guardrail-off --pet-package <pet-package> --room-image <room.png> --guardrail-mode off --dry-run
```

## Verification Points

- Valid room creation still succeeds and includes a `guardrails` block.
- Duplicate prop/helper ids fail with a repair-oriented message.
- A non-`384x240` room fails before kit files are produced.
- Blank transparent props fail.
- Props larger than the room canvas fail.
- Unknown prop placement ids fail and explain how to fix them.
- Helper packages with missing or bad spritesheets fail before generation.
- `--guardrail-mode off` suppresses subjective warnings but still fails structural errors.

## Local-Only Note

Any generated guardrail test runs under `runs/` are local evidence unless explicitly selected for public samples.
