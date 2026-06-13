@echo off
setlocal
set "PET_STUDIO_WIDGET_PYTHON=%PET_STUDIO_PYTHONW%"
if not defined PET_STUDIO_WIDGET_PYTHON set "PET_STUDIO_WIDGET_PYTHON=%PET_STUDIO_PYTHON%"
if not defined PET_STUDIO_WIDGET_PYTHON if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe" set "PET_STUDIO_WIDGET_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\pythonw.exe"
if not defined PET_STUDIO_WIDGET_PYTHON if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" set "PET_STUDIO_WIDGET_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not defined PET_STUDIO_WIDGET_PYTHON set "PET_STUDIO_WIDGET_PYTHON=pythonw"
start "Pet Studio Widget" /min "%PET_STUDIO_WIDGET_PYTHON%" "%~dp0pet_studio_widget.py" --kit "%~dp0..\runs\gakju-imagegen-room-v1\kit" --scale 1.25 --x 1200 --y 620
