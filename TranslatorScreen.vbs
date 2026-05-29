Dim pythonw, script, dir
dir    = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
pythonw = dir & "\.venv\Scripts\pythonw.exe"
script  = dir & "\main.py"

CreateObject("WScript.Shell").Run """" & pythonw & """ """ & script & """", 0, False
