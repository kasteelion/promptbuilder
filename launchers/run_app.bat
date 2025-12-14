@echo off
REM Launch Prompt Builder without opening a console (uses pythonw when available)
set SCRIPT_DIR=%~dp0
where pythonw >nul 2>nul
if %ERRORLEVEL%==0 (
  pythonw "%SCRIPT_DIR%..\main.py"
) else (
  python "%SCRIPT_DIR%..\main.py"
)
