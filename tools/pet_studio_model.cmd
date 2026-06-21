@echo off
setlocal EnableExtensions DisableDelayedExpansion

set "SCRIPT=%~dp0..\pet-studio-widget\pet_studio_widget.py"
set "CMD=%~1"

if /I "%CMD%"=="codex" goto model_codex
if /I "%CMD%"=="closed" goto model_closed
if /I "%CMD%"=="gpt" goto model_gpt
if /I "%CMD%"=="claude" goto model_claude
if /I "%CMD%"=="openrouter" goto model_openrouter
if /I "%CMD%"=="open" goto model_open
if /I "%CMD%"=="open-sota" goto model_open_sota
if /I "%CMD%"=="local" goto model_local
if /I "%CMD%"=="fast" goto model_fast
if /I "%CMD%"=="value" goto model_value
if /I "%CMD%"=="sota" goto model_sota
if /I "%CMD%"=="cheap" goto model_cheap
if /I "%CMD%"=="free" goto model_free
if /I "%CMD%"=="status" goto model_status
if /I "%CMD%"=="plan" goto model_status
if /I "%CMD%"=="team" goto model_status
if /I "%CMD%"=="save-credits" goto preset_save_credits
if /I "%CMD%"=="credits" goto preset_save_credits
if /I "%CMD%"=="all-local" goto preset_all_local
if /I "%CMD%"=="all-value" goto preset_all_value
if /I "%CMD%"=="lead-sota" goto preset_lead_sota
if /I "%CMD%"=="reset-role" goto reset_role
if /I "%CMD%"=="clear-role" goto reset_role
if /I "%CMD%"=="env" goto env
if /I "%CMD%"=="scout" goto role_scout
if /I "%CMD%"=="coordinator" goto role_coordinator
if /I "%CMD%"=="lead" goto role_lead
goto passthrough

:model_codex
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --model codex %REST%
call exit /b %%ERRORLEVEL%%

:model_closed
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --model closed %REST%
call exit /b %%ERRORLEVEL%%

:model_gpt
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --model gpt %REST%
call exit /b %%ERRORLEVEL%%

:model_claude
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --model claude %REST%
call exit /b %%ERRORLEVEL%%

:model_openrouter
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --model openrouter %REST%
call exit /b %%ERRORLEVEL%%

:model_open
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --model open %REST%
call exit /b %%ERRORLEVEL%%

:model_open_sota
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --model open-sota %REST%
call exit /b %%ERRORLEVEL%%

:model_local
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --model local %REST%
call exit /b %%ERRORLEVEL%%

:model_fast
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --model fast %REST%
call exit /b %%ERRORLEVEL%%

:model_value
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --model value %REST%
call exit /b %%ERRORLEVEL%%

:model_sota
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --model sota %REST%
call exit /b %%ERRORLEVEL%%

:model_cheap
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --model cheap %REST%
call exit /b %%ERRORLEVEL%%

:model_free
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --model free %REST%
call exit /b %%ERRORLEVEL%%

:model_status
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --model-status %REST%
call exit /b %%ERRORLEVEL%%

:preset_save_credits
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --team-model-preset save-credits %REST%
call exit /b %%ERRORLEVEL%%

:preset_all_local
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --team-model-preset all-local %REST%
call exit /b %%ERRORLEVEL%%

:preset_all_value
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --team-model-preset all-value %REST%
call exit /b %%ERRORLEVEL%%

:preset_lead_sota
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --team-model-preset lead-sota %REST%
call exit /b %%ERRORLEVEL%%

:reset_role
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --clear-role-model %REST%
call exit /b %%ERRORLEVEL%%

:env
set "REST2=%*"
call set "REST2=%%REST2:* =%%"
call set "REST2=%%REST2:* =%%"
if /I "%~2"=="team" goto env_team
if /I "%~2"=="scout" goto env_scout
if /I "%~2"=="coordinator" goto env_coordinator
if /I "%~2"=="lead" goto env_lead
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --print-model-env %REST%
call exit /b %%ERRORLEVEL%%

:env_team
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --print-team-model-env %REST2%
call exit /b %%ERRORLEVEL%%

:env_scout
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --print-role-model-env scout %REST2%
call exit /b %%ERRORLEVEL%%

:env_coordinator
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --print-role-model-env coordinator %REST2%
call exit /b %%ERRORLEVEL%%

:env_lead
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --print-role-model-env lead %REST2%
call exit /b %%ERRORLEVEL%%

:role_scout
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --set-role-model scout %REST%
call exit /b %%ERRORLEVEL%%

:role_coordinator
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --set-role-model coordinator %REST%
call exit /b %%ERRORLEVEL%%

:role_lead
call :set_rest %*
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" --set-role-model lead %REST%
call exit /b %%ERRORLEVEL%%

:passthrough
call "%~dp0pet_studio_python.cmd" "%SCRIPT%" %*
call exit /b %%ERRORLEVEL%%

:set_rest
set "REST="
if not "%~2"=="" set "REST=%*"
if defined REST call set "REST=%%REST:* =%%"
exit /b 0
