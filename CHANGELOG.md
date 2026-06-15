# Changelog

All notable changes to Pet Studio are documented here.

## Unreleased

## 0.2.0 - 2026-06-15

- Started the first-room creation UX with a guided public wrapper for kit creation, validation, rendering, and registry linking.
- Added a local QA pack generator for validation evidence, renders, and `CODER_TO_QA.md` handoff files.
- Added project-centered preflight checks for generated rooms, including repair hints for registry, kit, hook, dependency, and render issues.
- Added asset guardrails for room size, transparent props, oversized props, duplicate ids, prop/helper collisions, invalid placements, and helper package validation.
- Added registered-project session restore so reopened widgets can restore the last state, bubble visibility, window position, and scale while ignoring stale bridge states.
- Hardened force-replace, hook passthrough, hook command quoting, id validation, manifest path containment, and direct render/bake image bounds.
- Added Korean public documentation and minimal Korean CLI repair hints for first-room creation and preflight failures.
- Fixed the Windows widget launcher path so normal launches focus an existing widget, avoid stacked detached `pythonw.exe` instances, and write detached output to local log files.
- Added a project state demo cycler for README GIF capture and manual QA that reuses the existing state bridge.
- Added `docs/PET_STUDIO_WORKROOM_VISION.md` as a long-term direction document without making workroom features part of the current release.

## 0.1.2 - 2026-06-14

Public stability hardening.

- Added a release preflight command that checks the public demo, local install, Codex hooks, ignored runtime files, and one-frame rendering.
- Documented the first-run demo flow, hook bubble policy, hook log debugging, and known limitations.
- Kept post-tool Codex hook bubbles in `Working` instead of premature review wording.

## 0.1.1 - 2026-06-14

License update.

- Changed the project license from Apache-2.0 to MIT for simpler public reuse.
- Updated package metadata and README badges to report the MIT license.
- Previous `v0.1.0` release remains available under its original Apache-2.0 terms.

## 0.1.0 - 2026-06-13

Initial public release.

- Added the `$pet-studio` Codex skill for generating and maintaining style-matched pet room kits.
- Added layered Pet Studio kit generation, validation, preview rendering, and optional hatch-pet fallback baking.
- Added the frameless Pet Studio widget runtime with draggable room entities, helper pets, speech bubbles, layout persistence, and registered project selection.
- Added Codex event bridge commands plus a local installer for project-scoped `hooks.json` lifecycle integration that updates widget bubble state from Codex task activity.
- Added the public Gakju archive room example and README screenshot.
- Kept `project-room.json` and `project-room-*` runtime files as the v1 compatibility format while exposing Pet Studio naming in public commands.
