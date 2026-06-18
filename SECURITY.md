# Security Policy

Pet Studio is a local-first desktop widget and Codex hook bridge. It does not run a hosted service, but it can install local hook commands, read local project state files, and render generated assets. Treat those boundaries carefully.

## Supported Versions

The current public version is documented in [VERSION](VERSION) and [CHANGELOG.md](CHANGELOG.md). Security reports should target the current `main` branch unless a maintained release branch is explicitly announced.

## Reporting a Vulnerability

Open a private security advisory on GitHub if available. If private advisories are not enabled, open a minimal public issue that says a security report exists without sharing exploit details.

Please include:

- affected commit or version
- operating system
- whether Codex hooks were installed
- reproduction steps
- expected and actual behavior
- any generated asset or room kit involved, if relevant

## Areas Of Interest

- Hook installation and command construction.
- Workspace/project path resolution.
- Local file bridge reads and writes.
- Generated asset handling and validation.
- Widget launch commands.
- Any behavior that could expose private prompts, paths, tokens, or project data.

## Current Boundaries

- Pet Studio is local-first and does not intentionally upload project data.
- Codex integration is a local hook/file bridge, not an official Codex dashboard API.
- Windows is the primary tested widget host.
- Generated rooms and helper pets should be visually QA'd before publishing screenshots.
- Preset imports are protected against Zip Slip attacks (path traversal blocked).
- Approval queue uses full UUIDs to prevent ID collisions.
- L2 ASK actions require explicit user approval through the Team Room panel.
