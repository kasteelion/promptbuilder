# PowerShell Launcher for Prompt Builder
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $ScriptDir "..")
python main.py
