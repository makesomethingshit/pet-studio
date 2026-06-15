# Pet Studio Security Best Practices Review

Date: 2026-06-15

## Fix Status

This report is retained as a security review record and was rechecked against the current worktree on 2026-06-15. Several findings have been addressed during the 0.2.0 release-closure work:

- SEC-001: addressed. Kit manifest asset paths are constrained to relative paths inside the kit directory before validation, preview, bake, or widget bubble-style lookup opens them. Current evidence: `pet-studio-kit/scripts/bake_project_room_pet.py:25`, `pet-studio-kit/scripts/bake_project_room_pet.py:196`, `pet-studio-kit/scripts/validate_project_room_kit.py:14`, and `pet-studio-widget/project_room_scene.py:311`.
- SEC-002: addressed for the guided room workflow and generator paths covered by guardrails. Project, prop, and helper ids are restricted to slug-like values. Current evidence: `pet-studio-kit/scripts/asset_guardrails.py:21`, `pet-studio-kit/scripts/asset_guardrails.py:217`, `tools/pet_studio_create_room.py:29`, and `pet-studio-kit/scripts/create_project_room_kit.py:116`.
- SEC-003: addressed for the guided room wrapper. `--force` refuses unsafe replacement targets such as the repository root, code directories, home/root directories, and directories containing `.git` or `.codex`. Current evidence: `tools/pet_studio_create_room.py:49`.
- SEC-004: addressed. Shared image guards now enforce a 25 MiB file-size cap, 4M-pixel cap, and `Image.verify()` before room/prop/pet assets are decoded or loaded by validation, preview, bake, registration, or widget color sampling. Current evidence: `pet-studio-kit/scripts/image_guardrails.py:26`, `pet-studio-kit/scripts/bake_project_room_pet.py:54`, `pet-studio-kit/scripts/validate_project_room_kit.py:99`, `pet-studio-kit/scripts/asset_guardrails.py:54`, `pet-studio-kit/scripts/create_project_room_kit.py:81`, `pet-studio-kit/scripts/register_pet_package.py:21`, and `pet-studio-widget/project_room_scene.py:340`.

Current verification:

- `python -m unittest pet-studio-kit.tests.test_project_room_pipeline` passed: 48 tests.
- `python -m unittest pet-studio-widget.tests.test_project_room_registry` passed: 104 tests.
- Targeted security regression evidence includes `pet-studio-kit/tests/test_project_room_pipeline.py:810`, `pet-studio-kit/tests/test_project_room_pipeline.py:1100`, `pet-studio-kit/tests/test_project_room_pipeline.py:1126`, `pet-studio-kit/tests/test_project_room_pipeline.py:1187`, `pet-studio-kit/tests/test_project_room_pipeline.py:1211`, `pet-studio-kit/tests/test_project_room_pipeline.py:1250`, `pet-studio-kit/tests/test_project_room_pipeline.py:1295`, `pet-studio-kit/tests/test_project_room_pipeline.py:1326`, `pet-studio-kit/tests/test_project_room_pipeline.py:1353`, `pet-studio-widget/tests/test_project_room_registry.py:99`, and `pet-studio-widget/tests/test_project_room_registry.py:2365`.

The affected-code line numbers in the historical finding sections below are from the original review snapshot and may no longer match exactly after fixes.

## Executive Summary

Reviewed the local Pet Studio Python CLI/widget code using the `security-best-practices` skill. The project is local-first and does not expose a web server or remote API in the reviewed scope, so the main risks are local file-system safety, untrusted kit/package input handling, and image processing resource limits.

No critical remote-code-execution or credential exposure issue was found. The highest-priority findings are path traversal/write issues in user-controlled IDs and manifest paths, plus an overly broad destructive `--force` path.

## High Severity

No high-severity findings were identified in the reviewed local-only scope.

## Medium Severity

### SEC-001: Kit manifest layer paths can escape the kit directory

Affected code:

- `pet-studio-kit/scripts/bake_project_room_pet.py:151-152`
- `pet-studio-kit/scripts/bake_project_room_pet.py:216-225`
- `pet-studio-kit/scripts/validate_project_room_kit.py:58`
- `pet-studio-widget/project_room_scene.py:241-244`

`layer["path"]` from `project-room.json` is joined directly with `kit_dir`. A manifest can use absolute paths or `..` segments to reference files outside the kit directory. The validator, preview renderer, baker, and widget then open those resolved paths.

Impact: a malicious or copied kit can make Pet Studio read and render local image files outside the kit, or trigger image decoding work on attacker-chosen files.

Recommended fix:

- Resolve each asset path and require it to remain under the kit directory.
- Reject absolute layer paths and any resolved path that is not contained by `kit_dir`.
- Apply the same helper in validator, baker, preview renderer, widget, and bubble-style sidecar lookup.

### SEC-002: User-controlled prop/helper/layer IDs are used in output paths without filename validation

Affected code:

- `pet-studio-kit/scripts/create_project_room_kit.py:142`
- `pet-studio-kit/scripts/create_project_room_kit.py:259-273`
- `pet-studio-kit/scripts/create_project_room_kit.py:368-370`
- `pet-studio-kit/scripts/create_project_room_kit.py:500-505`
- `pet-studio-kit/scripts/register_pet_package.py:49`
- `tools/pet_studio_create_room.py:78-79`

Values such as `prop_id`, `helper_id`, and `--layer-id` are accepted as arbitrary strings and then interpolated into filesystem paths. Inputs containing path separators or traversal segments can write files outside the intended `props/`, `pets/`, or `prompts/` subdirectories.

Impact: a malicious command argument can overwrite files within or near the selected output tree, depending on the chosen `--out-dir`.

Recommended fix:

- Add a strict ID validator, for example `^[a-z0-9][a-z0-9-]{0,63}$`.
- Run it for `--prop` IDs, `--helper-package` IDs, `--layer-id`, and `--project-id` where IDs become filenames or registry keys.
- Keep display names separate from filesystem IDs.

### SEC-003: `--force` can recursively delete any user-supplied output directory

Affected code:

- `tools/pet_studio_create_room.py:34-42`
- `tools/pet_studio_create_room.py:172`
- `tools/pet_studio_create_room.py:187`

The guided wrapper accepts `--out-dir` and, when `--force` is present, calls `shutil.rmtree(out_dir)` without constraining the path to a safe generated-output root.

Impact: accidental or malicious invocation can delete an arbitrary directory accessible to the current user.

Recommended fix:

- Only allow forced deletion for paths under the default generated-output root, such as `ROOT / "runs"`, unless an additional explicit confirmation flag is provided.
- Reject root directories, home directories, repository root, and paths outside an allowlisted output directory.
- Print the resolved absolute path before deletion.

## Low Severity

### SEC-004: Image processing has limited resource guards for copied props and manifest-loaded assets

Affected code:

- `pet-studio-kit/scripts/bake_project_room_pet.py:25-26`
- `pet-studio-kit/scripts/bake_project_room_pet.py:216-225`
- `pet-studio-kit/scripts/validate_project_room_kit.py:35-41`
- `pet-studio-kit/scripts/validate_project_room_kit.py:94-120`
- `pet-studio-widget/project_room_scene.py:263`

Several paths open images from user-provided packages or kit manifests. The current hardening centralizes image resource checks and verifies files before full decode or pixel-heavy routines.

Impact: a malformed or oversized image can cause excessive CPU/memory use during validation, rendering, or widget startup.

Recommended fix:

- Set a project-level maximum pixel count and file size for user-provided images.
- Call `Image.verify()` or open in a helper that checks dimensions before conversion/loading.
- Stop validation early for static assets whose dimensions exceed allowed bounds before calling full-pixel routines such as transparent residue checks.

## Positive Observations

- No hardcoded API keys, tokens, passwords, or private keys were found by keyword search.
- Command execution generally uses `subprocess.run([...], shell=False)`, which avoids shell injection for the reviewed subprocess calls.
- Codex hook installation writes project-local hooks by default and wraps global notify only when explicitly requested.
- Runtime state files and hook logs are ignored in `.gitignore`.

## Suggested Fix Order

1. Add shared path containment helpers and apply them to kit asset loading.
2. Add strict ID validation for prop/helper/layer/project IDs used in paths.
3. Constrain `--force` deletion to safe generated-output directories.
4. Add image loading guards and regression tests for oversized/malformed assets.
