<#
PowerShell helper: create a Windows shortcut on the current user's Desktop
that launches `main.py` using `pythonw` (preferred) or `python` as fallback.

Usage (from repo root):
  PowerShell -ExecutionPolicy Bypass -File .\scripts\create_shortcut.ps1
#>

$projectRoot = Split-Path -Parent $PSScriptRoot
$desktop = [Environment]::GetFolderPath('Desktop')
$shortcutPath = Join-Path $desktop 'PromptBuilder.lnk'

# Find pythonw or python on PATH
$pywCmd = Get-Command pythonw -ErrorAction SilentlyContinue
if ($pywCmd) { $pythonExe = $pywCmd.Source } else {
    $pyCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pyCmd) { $pythonExe = $pyCmd.Source } else { $pythonExe = $null }
}

if (-not $pythonExe) {
    Write-Host "Error: neither 'pythonw' nor 'python' was found on PATH. Please install Python or update PATH." -ForegroundColor Red
    exit 2
}

$target = $pythonExe
$arguments = "`"$projectRoot\main.py`""

try {
    $w = New-Object -ComObject WScript.Shell
    $sc = $w.CreateShortcut($shortcutPath)
    $sc.TargetPath = $target
    $sc.Arguments = $arguments
    $sc.WorkingDirectory = $projectRoot
    # Use python executable as icon if available
    $sc.IconLocation = "$pythonExe,0"
    $sc.Save()
    Write-Host "Created shortcut: $shortcutPath"
} catch {
    Write-Host "Failed to create shortcut: $_" -ForegroundColor Red
    exit 1
}
