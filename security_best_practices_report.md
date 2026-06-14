# Pet Studio Security Best Practices Review

Date: 2026-06-14

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

Several paths open images from user-provided packages or kit manifests. Some fixed-size checks exist for room images and pet atlases, but prop images and manifest-loaded layers can still be decoded before all practical resource bounds are enforced.

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
