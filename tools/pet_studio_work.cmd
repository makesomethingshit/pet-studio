@echo off
setlocal EnableExtensions DisableDelayedExpansion

set "SCRIPT=%~dp0..\pet-studio-widget\pet_studio_widget.py"
set "CMD=%~1"
set "REST="
if not "%~2"=="" set "REST=%*"
if defined REST call set "REST=%%REST:* =%%"

if /I "%CMD%"=="goal" goto goal
if /I "%CMD%"=="mission" goto mission
if /I "%CMD%"=="task" goto task
if /I "%CMD%"=="staff" goto staff
if /I "%CMD%"=="assign-role" goto assign_role
if /I "%CMD%"=="assign-staff" goto assign_staff
if /I "%CMD%"=="start" goto start
if /I "%CMD%"=="done" goto done
if /I "%CMD%"=="status" goto status
if /I "%CMD%"=="clear" goto clear
if /I "%CMD%"=="clear-mission" goto clear_mission
if /I "%CMD%"=="open" goto open
goto passthrough

:goal
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --goal %REST%
call exit /b %%ERRORLEVEL%%

:mission
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --mission %REST%
call exit /b %%ERRORLEVEL%%

:task
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --add-task %REST%
call exit /b %%ERRORLEVEL%%

:staff
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --add-staff %REST%
call exit /b %%ERRORLEVEL%%

:assign_role
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --assign-task %REST%
call exit /b %%ERRORLEVEL%%

:assign_staff
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --assign-staff %REST%
call exit /b %%ERRORLEVEL%%

:start
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --task-start %REST%
call exit /b %%ERRORLEVEL%%

:done
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --task-done %REST%
call exit /b %%ERRORLEVEL%%

:status
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --work-status %REST%
call exit /b %%ERRORLEVEL%%

:clear
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --clear-tasks %REST%
call exit /b %%ERRORLEVEL%%

:clear_mission
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --clear-mission %REST%
call exit /b %%ERRORLEVEL%%

:open
call "%~dp0pet_studio_workroom.cmd" %REST%
call exit /b %%ERRORLEVEL%%

:passthrough
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" %*
call exit /b %%ERRORLEVEL%%
