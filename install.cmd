@echo off
REM Pet Studio — one-click install + launch
REM Double-click this file to get started.

echo ============================================
echo  Pet Studio — Quick Install
echo ============================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

echo [1/3] Checking dependencies...
python -c "from PIL import Image" 2>nul
if %errorlevel% neq 0 (
    echo         Installing Pillow...
    python -m pip install pillow
    if %errorlevel% neq 0 (
        echo [ERROR] Pillow install failed.
        pause
        exit /b 1
    )
)
echo         OK.

echo [2/3] Installing Pet Studio skill...
python tools\install_pet_studio_skill.py --force
if %errorlevel% neq 0 (
    echo [ERROR] Skill install failed.
    pause
    exit /b 1
)
echo         OK.

echo [3/3] Running preflight...
python tools\pet_studio_preflight.py --project-id gakju-archive-demo --skip-hooks
if %errorlevel% neq 0 (
    echo [WARN] Preflight had warnings. See above.
) else (
    echo         OK.
)

echo.
echo ============================================
echo  Install complete!
echo.
echo  Launching demo widget...
echo  (close the widget window to exit)
echo ============================================
echo.

start "" tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25

echo.
echo Not what you expected? Try:
echo   python tools\pet_studio_demo_states.py --project-id gakju-archive-demo --dry-run
echo.
pause
