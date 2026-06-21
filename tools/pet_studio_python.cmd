@echo off
setlocal

if "%~1"=="" goto no_args

if defined PET_STUDIO_PYTHON goto try_env_python
goto try_codex_python

:try_env_python
"%PET_STUDIO_PYTHON%" --version >nul 2>nul
if errorlevel 1 goto try_codex_python
"%PET_STUDIO_PYTHON%" %*
call exit /b %%ERRORLEVEL%%

:try_codex_python
set "PET_STUDIO_CODEX_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
if not exist "%PET_STUDIO_CODEX_PYTHON%" goto try_py_launcher
"%PET_STUDIO_CODEX_PYTHON%" --version >nul 2>nul
if errorlevel 1 goto try_py_launcher
"%PET_STUDIO_CODEX_PYTHON%" %*
call exit /b %%ERRORLEVEL%%

:try_py_launcher
py -3 --version >nul 2>nul
if errorlevel 1 goto try_python
py -3 %*
call exit /b %%ERRORLEVEL%%

:try_python
python --version >nul 2>nul
if errorlevel 1 goto try_python3
python %*
call exit /b %%ERRORLEVEL%%

:try_python3
python3 --version >nul 2>nul
if errorlevel 1 goto no_python
python3 %*
call exit /b %%ERRORLEVEL%%

:no_python
echo No working Python 3 runtime was found. Set PET_STUDIO_PYTHON to a Python 3.11+ executable and try again. 1>&2
exit /b 1

:no_args
echo Usage: tools\pet_studio_python.cmd SCRIPT.py [args...] 1>&2
exit /b 2
