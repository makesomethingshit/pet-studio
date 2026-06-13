# Bubble Style and Alpha Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make runtime bubbles match kit/pet style and improve room alpha cleanup without editing QA reports.

**Architecture:** Bubble style resolution lives in `project_room_scene.py` and is consumed by `project_room_widget.py`. Room alpha cleanup modes live in `project_room_assets.py` and are wired through `create_project_room_kit.py`.

**Tech Stack:** Python, Pillow, unittest, Project Room Kit JSON manifests.

---

### Task 1: Bubble Style Resolution

**Files:**
- Modify: `pet-studio-widget/project_room_scene.py`
- Modify: `pet-studio-widget/project_room_widget.py`
- Test: `pet-studio-widget/tests/test_project_room_registry.py`

- [ ] Add failing tests for kit-level `bubbleStyle`, pet sidecar `bubbleStyle`, and pet-color fallback.
- [ ] Implement `resolve_bubble_style(kit, kit_dir)` with priority: kit manifest, main pet sidecar, pet image extraction, default compact style.
- [ ] Update widget drawing to use `self.bubble_style`.
- [ ] Run widget tests.

### Task 2: Room Alpha Cleanup Modes

**Files:**
- Modify: `pet-studio-kit/scripts/project_room_assets.py`
- Modify: `pet-studio-kit/scripts/create_project_room_kit.py`
- Test: `pet-studio-kit/tests/test_project_room_pipeline.py`

- [ ] Add failing tests for `safe`, `balanced`, and `aggressive` cleanup behavior.
- [ ] Implement mode-aware edge-connected cleanup while preserving interior bright pixels.
- [ ] Add `--room-alpha-mode safe|balanced|aggressive` to kit creation; default `balanced`.
- [ ] Run kit tests.

### Task 3: QA Handoff

**Files:**
- Modify: `tester/fresh-custom-pet-room/CODER_TO_QA.md`

- [ ] Add a short note that `QA_REPORT.md` was not edited.
- [ ] List manual retest points for style-matched bubbles and room fringe cleanup.
- [ ] Run full widget and kit test suites.
