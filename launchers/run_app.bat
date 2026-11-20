@echo off
REM Launch Prompt Builder Desktop App
cd /d "%~dp0\.."
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with code %ERRORLEVEL%. Press any key to close...
    pause >nul
)
