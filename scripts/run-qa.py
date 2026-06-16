#!/usr/bin/env python3
"""Pet Studio QA Gate — single entry point for all quality checks.

Runs in order:
  1. Preflight  (tools/pet_studio_preflight.py)
  2. Widget tests (unittest)
  3. Kit tests (unittest)
  4. Compile check (py_compile)
  5. Core boundary check (import + forbidden patterns)

Fails fast on the first red check.
"""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def banner(label: str) -> None:
    print(f"\n{Colors.BOLD}{'=' * 60}")
    print(f"  QA Gate: {label}")
    print(f"{'=' * 60}{Colors.RESET}\n")


def pass_msg(label: str) -> None:
    print(f"  {Colors.GREEN}[OK]{Colors.RESET}  {label}")


def fail_msg(label: str) -> None:
    print(f"  {Colors.RED}[FAIL]{Colors.RESET} {label}")


def warn_msg(label: str) -> None:
    print(f"  {Colors.YELLOW}[WARN]{Colors.RESET} {label}")


def run_command(command: list[str], *, cwd: Path = ROOT, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        cwd=str(cwd),
        check=False,
        text=True,
        capture_output=capture,
    )


# ---------------------------------------------------------------------------
# Check 1: Preflight
# ---------------------------------------------------------------------------


def check_preflight() -> bool:
    banner("1. Preflight")
    result = run_command(
        [
            sys.executable,
            str(ROOT / "tools" / "pet_studio_preflight.py"),
            "--project-id",
            "gakju-archive-demo",
            "--skip-hooks",
        ]
    )
    output = result.stdout or ""
    lines = [l for l in output.splitlines() if l.strip()]
    all_ok = True
    for line in lines:
        if line.startswith("[OK]"):
            pass_msg(line[5:].strip())
        elif line.startswith("[FAIL]"):
            fail_msg(line[7:].strip())
            all_ok = False
        elif line.startswith("[WARN]"):
            warn_msg(line[7:].strip())
        else:
            print(f"  {line}")
    if result.returncode != 0:
        all_ok = False
    return all_ok


# ---------------------------------------------------------------------------
# Check 2: Widget Tests
# ---------------------------------------------------------------------------


def check_widget_tests() -> bool:
    banner("2. Widget Tests")
    loader = unittest.TestLoader()
    suite = loader.discover(
        str(ROOT / "pet-studio-widget" / "tests"),
        pattern="test_*.py",
    )
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=0)
    result = runner.run(suite)
    if result.wasSuccessful():
        pass_msg(f"All {result.testsRun} widget tests passed")
        return True
    else:
        fail_msg(f"{len(result.failures)} failure(s), {len(result.errors)} error(s)")
        return False


# ---------------------------------------------------------------------------
# Check 3: Kit Tests
# ---------------------------------------------------------------------------


def check_kit_tests() -> bool:
    banner("3. Kit Tests")
    loader = unittest.TestLoader()
    suite = loader.discover(
        str(ROOT / "pet-studio-kit" / "tests"),
        pattern="test_*.py",
    )
    runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=0)
    result = runner.run(suite)
    if result.wasSuccessful():
        pass_msg(f"All {result.testsRun} kit tests passed")
        return True
    else:
        fail_msg(f"{len(result.failures)} failure(s), {len(result.errors)} error(s)")
        return False


# ---------------------------------------------------------------------------
# Check 4: Compile Check
# ---------------------------------------------------------------------------

COMPILE_TARGETS = [
    "pet_studio_core/__init__.py",
    "pet_studio_core/registry.py",
    "pet_studio_core/state.py",
    "pet-studio-widget/project_room_registry.py",
    "pet-studio-widget/pet_studio_event_adapter.py",
    "pet-studio-widget/set_pet_studio_state.py",
    "pet-studio-widget/set_active_pet_studio.py",
    "pet-studio-widget/pet_studio_widget.py",
    "pet-studio-widget/project_room_scene.py",
    "tools/pet_studio_preflight.py",
    "tools/pet_studio_create_room.py",
    "tools/pet_studio_create_qa_pack.py",
]


def check_compile() -> bool:
    banner("4. Compile Check")
    all_ok = True
    for target in COMPILE_TARGETS:
        result = run_command(
            [sys.executable, "-m", "py_compile", target],
            capture=True,
        )
        if result.returncode == 0:
            pass_msg(target)
        else:
            fail_msg(f"{target}: {result.stderr.strip()}")
            all_ok = False
    return all_ok


# ---------------------------------------------------------------------------
# Check 5: Core Boundary Check
# ---------------------------------------------------------------------------


def check_core_boundary() -> bool:
    banner("5. Core Boundary Check")
    all_ok = True

    # 5a. Import check
    result = run_command(
        [
            sys.executable,
            "-c",
            "from pet_studio_core import init_core, write_project_state, EXTERNAL_STATES; print('core OK')",
        ]
    )
    if result.returncode == 0 and "core OK" in (result.stdout or ""):
        pass_msg("pet_studio_core imports cleanly")
    else:
        fail_msg(f"pet_studio_core import failed: {(result.stderr or result.stdout).strip()}")
        all_ok = False

    # 5b. Forbidden import check
    forbidden = ["codex_", "tkinter", "codex_pet_hook", "install_pet_studio_codex_integration", "pet_studio_widget"]
    core_files = list((ROOT / "pet_studio_core").rglob("*.py"))
    combined = "\n".join(f.read_text(encoding="utf-8") for f in core_files)
    for pattern in forbidden:
        if pattern in combined:
            fail_msg(f"Forbidden pattern '{pattern}' found in pet_studio_core/")
            all_ok = False
        else:
            pass_msg(f"No '{pattern}' in core")

    return all_ok


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    print(f"\n{Colors.BOLD}Pet Studio QA Gate{Colors.RESET}")
    print(f"Workspace: {ROOT}")
    print(f"Python:    {sys.version.split()[0]}")

    checks = [
        ("Preflight", check_preflight),
        ("Widget Tests", check_widget_tests),
        ("Kit Tests", check_kit_tests),
        ("Compile", check_compile),
        ("Core Boundary", check_core_boundary),
    ]

    results: list[tuple[str, bool]] = []
    for name, fn in checks:
        ok = fn()
        results.append((name, ok))
        if not ok:
            print(f"\n{Colors.RED}{Colors.BOLD}QA Gate FAILED at: {name}{Colors.RESET}")
            print("Fix the failing check and re-run.\n")
            raise SystemExit(1)

    print(f"\n{Colors.GREEN}{Colors.BOLD}QA Gate PASSED — all {len(results)} checks green{Colors.RESET}")
    print("Safe to push / merge / release.\n")
    raise SystemExit(0)


if __name__ == "__main__":
    main()
