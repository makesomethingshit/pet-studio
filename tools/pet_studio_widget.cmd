@echo off
setlocal

if "%~1"=="" goto no_args

set "PET_STUDIO_WIDGET_PS1=%~dp0pet_studio_widget.ps1"
if exist "%PET_STUDIO_WIDGET_PS1%" (
    powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "%PET_STUDIO_WIDGET_PS1%" %*
    exit /b %ERRORLEVEL%
)

if defined PET_STUDIO_PYTHONW (
    "%PET_STUDIO_PYTHONW%" --version >nul 2>nul
    if not errorlevel 1 (
        start "Pet Studio Widget" /min "%PET_STUDIO_PYTHONW%" "%~dp0..\pet-studio-widget\pet_studio_widget.py" %*
        exit /b 0
    )
)

set "PET_STUDIO_CODEX_PYTHONW=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe"
if exist "%PET_STUDIO_CODEX_PYTHONW%" (
    "%PET_STUDIO_CODEX_PYTHONW%" --version >nul 2>nul
    if not errorlevel 1 (
        start "Pet Studio Widget" /min "%PET_STUDIO_CODEX_PYTHONW%" "%~dp0..\pet-studio-widget\pet_studio_widget.py" %*
        exit /b 0
    )
)

if defined PET_STUDIO_PYTHON (
    "%PET_STUDIO_PYTHON%" --version >nul 2>nul
    if not errorlevel 1 (
        start "Pet Studio Widget" /min "%PET_STUDIO_PYTHON%" "%~dp0..\pet-studio-widget\pet_studio_widget.py" %*
        exit /b 0
    )
)

set "PET_STUDIO_CODEX_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%PET_STUDIO_CODEX_PYTHON%" (
    "%PET_STUDIO_CODEX_PYTHON%" --version >nul 2>nul
    if not errorlevel 1 (
        start "Pet Studio Widget" /min "%PET_STUDIO_CODEX_PYTHON%" "%~dp0..\pet-studio-widget\pet_studio_widget.py" %*
        exit /b 0
    )
)

pythonw --version >nul 2>nul
if not errorlevel 1 (
    start "Pet Studio Widget" /min pythonw "%~dp0..\pet-studio-widget\pet_studio_widget.py" %*
    exit /b 0
)

echo No working Python GUI runtime was found. Set PET_STUDIO_PYTHONW to pythonw.exe and try again. 1>&2
exit /b 1

:no_args
echo Usage: tools\pet_studio_widget.cmd [pet_studio_widget.py args...] 1>&2
echo Example: tools\pet_studio_widget.cmd --project-id gakju-archive-demo --scale 1.25 1>&2
exit /b 2
