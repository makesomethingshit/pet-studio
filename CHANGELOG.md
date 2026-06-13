# Changelog

All notable changes to Pet Studio are documented here.

## 0.1.0 - 2026-06-13

Initial public release.

- Added the `$pet-studio` Codex skill for generating and maintaining style-matched pet room kits.
- Added layered Pet Studio kit generation, validation, preview rendering, and optional hatch-pet fallback baking.
- Added the frameless Pet Studio widget runtime with draggable room entities, helper pets, speech bubbles, layout persistence, and registered project selection.
- Added Codex event bridge commands plus a local installer for project-scoped `hooks.json` lifecycle integration that updates widget bubble state from Codex task activity.
- Added the public Gakju archive room example and README screenshot.
- Fixed low-alpha chroma fringe cleanup so transparent widget edges do not show magenta residue.
- Kept `project-room.json` and `project-room-*` runtime files as the v1 compatibility format while exposing Pet Studio naming in public commands.
