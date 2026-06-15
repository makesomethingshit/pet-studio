# Pet Studio Agent Guide

This file is a short operating guide for agents working on Pet Studio.
Use it to avoid re-reading every document while still respecting the project scope and release workflow.

## Current Focus

Pet Studio is preparing for the `v0.2.0` release candidate.

Current next feature:

- Add `tools/pet_studio_demo_states.py`
- Implement a project state demo cycler for widget state changes
- Reuse the existing state bridge instead of creating new runtime files

## Required Reading

Before feature work, read the relevant guide first:

| Task | Read first |
| --- | --- |
| New feature or CLI command | `docs/PET_STUDIO_ROADMAP.md`, `docs/DEVELOPMENT.md` |
| Install/launcher/widget behavior | `docs/INSTALL.md`, `pet-studio-widget/README.md` |
| Demo or state bridge work | `docs/DEMO_SCRIPT.md`, `docs/CODEX_INTEGRATION.md` |
| Release closure / QA focus | `docs/CODER_TO_QA_020_RELEASE_CLOSURE.md`, `PROJECT_HANDOFF.md` |
| Skill behavior | `pet-studio-kit/SKILL.md` |

Do not edit public docs based only on memory. Confirm wording against the existing files.

## Scope Rules

Stay within Pet Studio `v0.2.0` scope.

Do not add these as current features:

- Team Room
- Project Hub
- cloud sync
- hosted dashboard
- full simulation/game behavior
- automatic helper/sub-pet selection without user confirmation

Long-term concepts may be mentioned in vision docs, but they must not be implemented as current functionality.

## Working Style

- Prefer small, testable changes.
- Reuse existing modules and CLI patterns.
- Keep machine-readable output stable.
- Keep user-facing repair hints short and actionable.
- Do not install Codex hooks unless the command explicitly asks for hook installation.
- Do not modify `.codex/config.toml` or `.codex/hooks.json` during ordinary feature work.

## Testing Before Finishing

Run the relevant checks before reporting completion.

Minimum for code/CLI work:

```powershell
.\tools\pet_studio_python.cmd -m unittest discover -s pet-studio-widget\tests
.\tools\pet_studio_python.cmd -m unittest discover -s pet-studio-kit\tests
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --project-id gakju-archive-demo --skip-hooks
git diff --check
```

For Python entrypoints:

```powershell
.\tools\pet_studio_python.cmd -m py_compile <changed-python-files>
```

For the demo state cycler, also verify:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_demo_states.py --project-id gakju-archive-demo --dry-run
.\tools\pet_studio_python.cmd tools\pet_studio_demo_states.py --project-id gakju-archive-demo --once --delay-seconds 0
```

## Local Runtime Files

Do not commit local runtime state or QA output.

Ignored/local-only paths include:

```text
pet-studio-widget/project-room-active.json
pet-studio-widget/project-room-window.json
pet-studio-widget/project-room-session.json
pet-studio-widget/project-room-state.json
pet-studio-widget/project-room-hook-events.jsonl
runs/*/qa-pack/
tester/
```

`PROJECT_HANDOFF.md` says to keep local QA output under `tester/` and generated QA packs under `runs/<project-id>/qa-pack/`.

## Useful Commands

Install or refresh the local Pet Studio skill:

```powershell
.\tools\pet_studio_python.cmd tools\install_pet_studio_skill.py --force
```

Launch the demo widget:

```powershell
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25
```

Debug the widget with visible console output:

```powershell
.\tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25 --foreground
```

Generate QA evidence for the demo project:

```powershell
.\tools\pet_studio_python.cmd tools\pet_studio_create_qa_pack.py --project-id gakju-archive-demo
```

## Release Mindset

Pet Studio should remain:

- local-first
- lightweight
- Windows-focused for now
- understandable to first-time users
- safe for local file bridges and hooks
- clear about what is current functionality versus long-term vision
