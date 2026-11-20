@echo off
REM Launch Prompt Builder in Web Browser Mode
cd /d "%~dp0"
python main.py --web
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with code %ERRORLEVEL%. Press any key to close...
    pause >nul
)
