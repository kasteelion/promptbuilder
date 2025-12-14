"""VBScript launcher for Prompt Builder. Double-click to run without a console."""
Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Determine script folder and parent (project root)
scriptFile = WScript.ScriptFullName
scriptFolder = fso.GetParentFolderName(scriptFile)
projectRoot = fso.GetParentFolderName(scriptFolder)

' Build command using pythonw; fallback handled by OS if pythonw isn't available
cmd = Chr(34) & "pythonw" & Chr(34) & " " & Chr(34) & projectRoot & "\main.py" & Chr(34)

' 0 = hide window, False = don't wait
WshShell.Run cmd, 0, False
