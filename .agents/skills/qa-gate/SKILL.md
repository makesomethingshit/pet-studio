---
name: qa-gate
description: >
  Pet Studio QA Gate — run before every PR or release.
  Checks: preflight, unittest, py_compile, core boundary.
  Fails fast on the first red check.
---

# QA Gate Skill

## When to Run

- Before every `git push` to a feature branch
- Before merging a PR to `main`
- Before tagging a release
- After any agent handoff (Codex → Hermes or Hermes → Codex)

## Gate Checks (in order)

Run these in sequence. **Stop on first failure.**

### 1. Preflight

```powershell
python tools/pet_studio_preflight.py --project-id gakju-archive-demo --skip-hooks
```

Expected: all lines start with `[OK]`.

What it checks:
- Python + Pillow available
- Codex skill installed
- Project registry valid
- Kit manifest valid
- Local-only paths are gitignored
- Render output written

### 2. Widget Tests

```powershell
python -m unittest discover -s pet-studio-widget/tests -v
```

Expected: `OK` (all tests pass).

### 3. Kit Tests

```powershell
python -m unittest discover -s pet-studio-kit/tests -v
```

Expected: `OK` (all tests pass).

### 4. Compile Check

```powershell
python -m py_compile pet_studio_core/__init__.py
python -m py_compile pet_studio_core/registry.py
python -m py_compile pet_studio_core/state.py
python -m py_compile pet-studio-widget/project_room_registry.py
python -m py_compile pet-studio-widget/pet_studio_event_adapter.py
python -m py_compile pet-studio-widget/set_pet_studio_state.py
python -m py_compile pet-studio-widget/set_active_pet_studio.py
python -m py_compile pet-studio-widget/pet_studio_widget.py
python -m py_compile pet-studio-widget/project_room_scene.py
python -m py_compile tools/pet_studio_preflight.py
python -m py_compile tools/pet_studio_create_room.py
python -m py_compile tools/pet_studio_create_qa_pack.py
```

Expected: no output (exit code 0).

### 5. Core Boundary Check

```powershell
python -c "from pet_studio_core import init_core, write_project_state, EXTERNAL_STATES; print('core OK')"
```

Expected: `core OK` printed.

What it verifies:
- `pet_studio_core` imports without pulling in Codex/Tkinter/widget
- `init_core` and `write_project_state` are accessible
- `EXTERNAL_STATES` is defined

## Failure Handling

If any check fails:

1. **Do not proceed** to the next check
2. Report the exact command that failed and its output
3. Suggest a repair hint (see below)

### Repair Hints

| Check | Common Failure | Repair |
|-------|---------------|--------|
| Preflight | Pillow missing | `pip install Pillow` |
| Preflight | Skill not installed | `python tools/install_pet_studio_skill.py` |
| Preflight | Kit validation fails | Check `kitPath` in registry JSON |
| Unittest | Import error | Check `sys.path` and local tools dir |
| Unittest | Assertion failure | Read the traceback, fix the test or code |
| py_compile | Syntax error | Fix the reported file/line |
| Core boundary | Import error | Check for forbidden imports in `pet_studio_core/` |

## Pass Criteria

All 5 checks green = **QA Gate passed** → safe to push / merge / release.

## Integration Notes

- This skill is for **agent use** (Hermes / Codex), not for CI.
- For CI, use `.github/workflows/ci.yml` (runs on GitHub Actions).
- For local developer use, see `scripts/run-qa.py` (coming in Phase 2).
