<#
PowerShell launcher for Prompt Builder.
Double-clicking this file will start the app using `pythonw` (no console) when available.
#>
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$entry = Join-Path $scriptDir "..\main.py"
$python = "pythonw"
try {
    Start-Process -FilePath $python -ArgumentList "`"$entry`"" -WorkingDirectory $scriptDir -WindowStyle Hidden -PassThru | Out-Null
} catch {
    # Fallback to python if pythonw is missing
    Start-Process -FilePath "python" -ArgumentList "`"$entry`"" -WorkingDirectory $scriptDir
}
