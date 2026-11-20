Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

scriptFile = WScript.ScriptFullName
scriptFolder = fso.GetParentFolderName(scriptFile)
projectRoot = fso.GetParentFolderName(scriptFolder)

cmd = Chr(34) & "pythonw" & Chr(34) & " " & Chr(34) & projectRoot & "\main.py" & Chr(34)
WshShell.Run cmd, 0, False
