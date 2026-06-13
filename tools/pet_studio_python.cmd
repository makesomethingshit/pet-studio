@echo off
setlocal

if "%~1"=="" goto no_args

if defined PET_STUDIO_PYTHON (
    "%PET_STUDIO_PYTHON%" --version >nul 2>nul
    if not errorlevel 1 (
        "%PET_STUDIO_PYTHON%" %*
        exit /b %ERRORLEVEL%
    )
)

set "PET_STUDIO_CODEX_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if exist "%PET_STUDIO_CODEX_PYTHON%" (
    "%PET_STUDIO_CODEX_PYTHON%" --version >nul 2>nul
    if not errorlevel 1 (
        "%PET_STUDIO_CODEX_PYTHON%" %*
        exit /b %ERRORLEVEL%
    )
)

py -3 --version >nul 2>nul
if not errorlevel 1 (
    py -3 %*
    exit /b %ERRORLEVEL%
)

python --version >nul 2>nul
if not errorlevel 1 (
    python %*
    exit /b %ERRORLEVEL%
)

python3 --version >nul 2>nul
if not errorlevel 1 (
    python3 %*
    exit /b %ERRORLEVEL%
)

echo No working Python 3 runtime was found. Set PET_STUDIO_PYTHON to a Python 3.11+ executable and try again. 1>&2
exit /b 1

:no_args
echo Usage: tools\pet_studio_python.cmd SCRIPT.py [args...] 1>&2
exit /b 2
