# CODER_TO_QA: 0.2.0 Release Closure

## Summary

This pass keeps 0.2.0 focused on first-room creation, QA/preflight, asset guardrails, and local security hardening. It does not add Team Room, Project Hub, Core package extraction, or Codex Adapter architecture work.

## What Changed

- Long-term vision is preserved in `docs/PET_STUDIO_WORKROOM_VISION.md`.
- v0.3 architecture boundary docs are intentionally out of the 0.2.0 scope.
- Kit manifest asset paths are now constrained to relative paths inside the kit directory before validator, preview, bake, or widget bubble-style lookup opens them.
- Direct preview/bake paths reject oversized layer images according to room/pet/prop role bounds.
- Existing M3 preflight repair hints and M4 guardrail formatting are covered by regression tests.

## QA Focus

Please verify:

- `tools\pet_studio_preflight.py` gives repair hints for unknown project, invalid registry shape, missing `kitPath`, and missing manifest.
- M4 guardrail failure messages have a single sentence boundary before `Fix:`.
- Validator rejects manifest layer paths such as `../outside.png`.
- Preview and bake reject escaped layer paths.
- Widget bubble style does not read a main-pet sidecar outside the kit directory.
- Oversized manifest prop images fail before render/bake output is produced.

## Suggested Commands

```powershell
.\tools\pet_studio_python.cmd -m unittest discover -s pet-studio-kit\tests
.\tools\pet_studio_python.cmd -m unittest discover -s pet-studio-widget\tests
.\tools\pet_studio_python.cmd tools\pet_studio_preflight.py --project-id gakju-archive-demo --skip-hooks
.\tools\pet_studio_python.cmd tools\pet_studio_create_qa_pack.py --project-id gakju-archive-demo
git diff --check
```

## Out Of Scope

- Do not test Team Room or Project Hub behavior as current functionality.
- Do not edit `tester/` or any `QA_REPORT.md` from this handoff.
- Treat generated `runs/*/qa-pack/` output as local evidence, not public git content.
