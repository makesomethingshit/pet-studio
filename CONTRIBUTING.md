# Contributing

Pet Studio is early, Windows-focused, and local-first. Contributions are welcome when they keep the current implementation honest: a tiny desktop status widget for Codex projects, not a hosted dashboard or full game.

## Good First Areas

- Add more room props or room themes.
- Add more pet idle/state rows.
- Improve speech bubble templates and layout.
- Improve preview/contact sheet readability.
- Improve install and troubleshooting docs.
- Add small tests around room state, registry, or asset validation behavior.

More ideas are listed in [docs/CONTRIBUTING_IDEAS.md](docs/CONTRIBUTING_IDEAS.md).

## Development Checks

Run these before opening a pull request:

```powershell
.\tools\pet_studio_python.cmd -m unittest discover -s pet-studio-widget\tests
.\tools\pet_studio_python.cmd -m unittest discover -s pet-studio-kit\tests
.\tools\pet_studio_python.cmd -m py_compile pet-studio-widget\pet_studio_event_adapter.py pet-studio-widget\set_pet_studio_state.py pet-studio-widget\set_active_pet_studio.py pet-studio-widget\pet_studio_widget.py pet-studio-widget\project_room_registry.py pet-studio-kit\scripts\create_project_room_kit.py tools\pet_studio_preflight.py tools\pet_studio_create_room.py tools\pet_studio_create_qa_pack.py
```

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for release preflight commands and known limitations.

## Visual QA

Room changes should include visual evidence when they affect layout, assets, bubbles, helper pets, or state rendering.

- Prefer checked-in docs screenshots only when they are intentionally part of the public README or docs.
- Keep generated QA packs local unless they are needed for a review.
- Do not include private project names, paths, prompts, tokens, or chat content in screenshots.

## Pull Request Notes

- Keep feature claims tied to behavior that exists in the repo.
- Mark planned behavior as roadmap, not current functionality.
- Do not hide the current Windows-focused widget host limitation.
- Keep runtime changes separate from packaging/docs polish when possible.
