# Create A Room

Pet Studio can create a project room from a hatch-pet style source plus a room image and optional prop/helper assets.

New room quality depends on the provided or generated art. Visual QA is still required.

## Create A Room With Codex

After installing the skill, talk to Codex normally. Useful prompts:

```text
Create a Pet Studio room for my current Codex pet.
```

```text
Use my Gakju pet as the style source and make a cozy archive room.
```

```text
Register this room to the current workspace and launch the widget.
```

Codex should ask for missing art inputs, keep the style source locked, run validation, and report generated files. Helper/sub-pet art should be confirmed before generation because mismatched helper style is hard to repair later.

## Create A Room From The Command Line

Use the guided wrapper for a direct command-line first room:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_create_room.py `
  --project-id my-room `
  --pet-package "$env:USERPROFILE\.codex\pets\my-pet" `
  --room-image runs\my-assets\room.png `
  --prop desk=runs\my-assets\desk.png `
  --prop-placement desk=behind-pet `
  --theme "quiet archive nook"
```

The wrapper validates the pet and room inputs, creates `runs\my-room\kit`, renders preview/contact images, registers the project, links the current workspace, and prints preflight/launch/render/QA pack commands.

Useful options:

- `--dry-run` prints the planned low-level command without writing files.
- `--force` replaces an existing output directory. Use this only when the old `runs\<project-id>` output can be discarded.
- `--verbose` prints the underlying generator output; the default output is a concise JSON summary with created artifacts and next commands.

Create local QA evidence after generation:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_create_qa_pack.py --project-id my-room
```

The QA pack writes validation JSON, an idle render, an all-state contact sheet, a widget render, `CODER_TO_QA.md`, and `qa-pack-summary.json` under `runs\my-room\qa-pack\`. These files are local evidence and are ignored by git.

## What Gets Created

Typical generated output includes:

```text
runs/my-pet-studio-room/
  kit/
    project-room.json
    style-lock.json
    rooms/
    props/
    pets/
  generation-brief.json
  kit-validation.json
  production-report.json
  room-preview.png
  room-contact.png
  qa-pack/
    validation.json
    idle-render.png
    all-states-contact.png
    widget-render.png
    CODER_TO_QA.md
    qa-pack-summary.json
```

Local QA evidence and experimental run folders are intentionally ignored by git unless you choose to preserve them.

## Notes

- The real room format is layered.
- The fallback baked pet package is only for compatibility.
- Helper pets are optional.
- Kits can show helper pets in collaboration/problem-solving states such as review, handoff, blocked, or failed without turning them into a second main pet.
