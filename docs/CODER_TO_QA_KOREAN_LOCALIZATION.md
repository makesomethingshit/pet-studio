# CODER_TO_QA: Korean Localization

## Summary

Implemented the 0.2.0 Korean localization pass from `tester/gakju-archive-demo/KOREAN_LOCALIZATION_REPORT.md`.

This is intentionally limited to public Korean onboarding docs and repair-oriented CLI prose. English remains the default language, and JSON output keeps the existing English keys and structure.

## Changed

- Added `README.ko.md` and linked it from `README.md`.
- Added `docs/PET_STUDIO_WORKROOM_VISION.ko.md` with a top-of-page warning that the Workroom/Team Room language is long-term direction, not current functionality.
- Added minimal localization helpers in `pet-studio-kit/scripts/localized_messages.py`.
- Added `--lang en|ko` and `PET_STUDIO_LANG=ko` support to:
  - `tools/pet_studio_create_room.py`
  - `tools/pet_studio_preflight.py`
- Localized user-facing guardrail and preflight repair hints for Korean CLI mode.
- Kept JSON output stable and English-keyed.

## QA Focus

- Copy/paste commands in `README.ko.md` on Windows PowerShell.
- Confirm `README.md` and `README.ko.md` link to each other.
- Confirm `docs/PET_STUDIO_WORKROOM_VISION.ko.md` does not read like current feature documentation.
- Run representative Korean failure output:
  - unsafe `--project-id`
  - duplicate prop id
  - wrong room size
  - unknown prop placement
  - unknown preflight project
  - missing `kitPath`
  - missing manifest
- Confirm `PET_STUDIO_LANG=ko` behaves like `--lang ko`.
- Confirm `--json --lang ko` preserves the existing JSON keys and schema.
- Confirm PowerShell displays Korean correctly when the terminal uses UTF-8.

## Known Limits

- This is not full application-wide i18n.
- Only first-room creation, asset guardrail failure text, and preflight setup failure prose are localized.
- Command flags, paths, JSON keys, registry keys, error codes, and file names stay English by design.
- Any missing Korean string should fall back to English rather than block the command.

## Verification Run By Coder

```powershell
.\tools\pet_studio_python.cmd -m py_compile pet-studio-kit\scripts\localized_messages.py pet-studio-kit\scripts\asset_guardrails.py tools\pet_studio_create_room.py tools\pet_studio_preflight.py
.\tools\pet_studio_python.cmd -m unittest pet-studio-kit.tests.test_project_room_pipeline.ProjectRoomPipelineTests.test_guardrail_failure_format_supports_korean_output pet-studio-kit.tests.test_project_room_pipeline.ProjectRoomPipelineTests.test_guided_create_room_korean_lang_reports_guardrail_failures pet-studio-kit.tests.test_project_room_pipeline.ProjectRoomPipelineTests.test_guided_create_room_korean_lang_reports_unsafe_project_id pet-studio-kit.tests.test_project_room_pipeline.ProjectRoomPipelineTests.test_guided_create_room_uses_korean_env_language
.\tools\pet_studio_python.cmd -m unittest pet-studio-widget.tests.test_project_room_registry.PetStudioPreflightTests.test_preflight_cli_korean_lang_reports_unknown_project_hint pet-studio-widget.tests.test_project_room_registry.PetStudioPreflightTests.test_preflight_cli_korean_lang_reports_missing_kitpath_hint pet-studio-widget.tests.test_project_room_registry.PetStudioPreflightTests.test_preflight_json_output_remains_english_keyed_with_korean_lang
```

Full regression should still be run before release tagging.
