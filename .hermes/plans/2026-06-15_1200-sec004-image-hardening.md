# Pet Studio Security Report SEC-004 Hardening Plan

> **For Hermes:** Execute task-by-task; keep changes minimal and verify with targeted tests.

**Goal:** Apply the remaining actionable item from `D:\pet-studio\security_best_practices_report.md`: harden image loading against malformed or oversized user-provided assets before full decode/render work.

**Architecture:** Add one shared image resource guard module under `pet-studio-kit/scripts`, then route existing image opens through it. SEC-001/002/003 are already addressed in the current worktree.

**Tech Stack:** Python 3, PIL/Pillow, unittest subprocess regression tests.

---

## Current Context / Assumptions

- Workspace: `D:\pet-studio`
- Report says:
  - SEC-001 path containment: addressed.
  - SEC-002 ID validation: addressed.
  - SEC-003 `--force` deletion safety: addressed.
  - SEC-004 image resource limits: partially addressed; remaining work is malformed-image/file-size hardening.
- Existing relevant files already contain path/ID guards and security regression tests.
- There are pre-existing uncommitted changes in docs/tests, so edits must be limited to security hardening files/tests/report only.

## Proposed Approach

1. Create `pet-studio-kit/scripts/image_guardrails.py` with:
   - `MAX_IMAGE_FILE_BYTES`
   - `MAX_IMAGE_PIXEL_COUNT`
   - `ImageResourceError`
   - `image_resource_info(path)`
   - `safe_image_size(path)`
   - `safe_rgba_image(path)`
2. Replace unsafe `Image.open(...).size` and direct decode paths in:
   - `bake_project_room_pet.py`
   - `validate_project_room_kit.py`
   - `asset_guardrails.py`
   - `project_room_assets.py`
   - `create_project_room_kit.py`
   - `register_pet_package.py`
   - `project_room_scene.py`
3. Keep behavior unchanged for valid assets.
4. Add regression tests for malformed prop/manifest images and resource guard behavior.
5. Update `security_best_practices_report.md` fix status and verification lines if tests pass.

## Step-by-Step Plan

### Task 1: Add shared image guard helper

**Objective:** Centralize Pillow verification and resource limits.

**Files:**
- Create: `pet-studio-kit/scripts/image_guardrails.py`

**Implementation sketch:**
```python
from dataclasses import dataclass
from pathlib import Path
from PIL import Image

MAX_IMAGE_FILE_BYTES = 25 * 1024 * 1024
MAX_IMAGE_PIXEL_COUNT = 4_000_000

@dataclass(frozen=True)
class ImageResourceInfo:
    width: int
    height: int
    file_size: int

class ImageResourceError(ValueError):
    pass

def image_resource_info(path: Path) -> ImageResourceInfo:
    file_size = path.stat().st_size
    if file_size > MAX_IMAGE_FILE_BYTES:
        raise ImageResourceError(f"Image file is too large: {file_size} bytes")
    try:
        with Image.open(path) as image:
            image.verify()
            width, height = image.size
    except OSError as exc:
        raise ImageResourceError(f"Image cannot be read: {path}") from exc
    pixels = width * height
    if pixels > MAX_IMAGE_PIXEL_COUNT:
        raise ImageResourceError(f"Image is too large: {width}x{height} pixels")
    return ImageResourceInfo(width=width, height=height, file_size=file_size)

def safe_image_size(path: Path) -> tuple[int, int]:
    info = image_resource_info(path)
    return info.width, info.height

def safe_rgba_image(path: Path) -> Image.Image:
    image_resource_info(path)
    with Image.open(path) as image:
        return image.convert("RGBA")
```

**Verification:** Run `python -m py_compile pet-studio-kit/scripts/image_guardrails.py`.

### Task 2: Route kit/render/bake image loads through guards

**Objective:** Prevent preview/bake/widget from fully decoding unsafe manifest assets.

**Files:**
- Modify: `pet-studio-kit/scripts/bake_project_room_pet.py`
- Modify: `pet-studio-kit/scripts/validate_project_room_kit.py`
- Modify: `pet-studio-widget/project_room_scene.py`

**Key changes:**
- `image_size(path)` uses `safe_image_size`.
- `load_image(path)` uses `safe_rgba_image`.
- `transparent_rgb_residue_count(path)` uses `safe_rgba_image`.
- `average_opaque_rgb(path)` catches `ImageResourceError` and returns `None`.

**Verification:** Existing tests `test_preview_and_bake_reject_manifest_layer_paths_that_escape_kit_dir` and `test_preview_rejects_manifest_prop_larger_than_room_bounds` should still pass.

### Task 3: Route generation-time asset checks through guards

**Objective:** Reject malformed/oversized room/prop/helper assets before copying/rendering.

**Files:**
- Modify: `pet-studio-kit/scripts/asset_guardrails.py`
- Modify: `pet-studio-kit/scripts/project_room_assets.py`
- Modify: `pet-studio-kit/scripts/create_project_room_kit.py`
- Modify: `pet-studio-kit/scripts/register_pet_package.py`

**Key changes:**
- `asset_guardrails.image_size` and `image_has_opaque_pixels` use guard helpers.
- `cleanup_room_image` and `room_edge_margin_pixel_count` use guard helpers.
- `create_project_room_kit.validate_image_size` uses `safe_image_size`.
- `register_pet_package.validate_spritesheet` uses `safe_image_size`.

**Verification:** Existing prop/room/helper guardrail tests should still pass.

### Task 4: Add regression tests for malformed images

**Objective:** Prove malformed user-provided images are rejected before decode-heavy work.

**Files:**
- Modify: `pet-studio-kit/tests/test_project_room_pipeline.py`
- Optional: Modify: `pet-studio-widget/tests/test_project_room_registry.py`

**Tests to add:**
- `test_guardrails_reject_malformed_prop_image_before_generation`
- `test_validator_and_bake_reject_malformed_manifest_prop_image`

**Verification:** Run targeted unittest methods or full relevant test files.

### Task 5: Update report and verify

**Objective:** Mark SEC-004 addressed and record passing commands.

**Files:**
- Modify: `security_best_practices_report.md`

**Commands:**
```bash
git -C D:/pet-studio status --short
.\tools\pet_studio_python.cmd pet-studio-kit\tests\test_project_room_pipeline.py
.\tools\pet_studio_python.cmd pet-studio-widget\tests\test_project_room_registry.py
```

**Expected final report:**
- SEC-004: addressed.
- Include new evidence paths/line references after implementation.

## Risks / Tradeoffs

- File-size limit may reject unusually large but valid assets; choose conservative but realistic defaults.
- `Image.verify()` may not catch every malformed image, but it avoids most full decode paths before resource checks.
- Importing `image_guardrails` into widget scene must not break direct test imports; add sys.path insertion if needed.

## Remaining Work After Plan

- None for SEC-004 hardening.
- Optional next step: run the full repository test suite if release closure requires it.
