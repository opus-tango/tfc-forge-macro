Set sh = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
sh.CurrentDirectory = fso.GetParentFolderName(WScript.ScriptFullName)

Function QuoteForCmd(s)
    QuoteForCmd = """" & Replace(s, """", """""") & """"
End Function

Dim extra, i
extra = ""
For i = 0 To WScript.Arguments.Count - 1
    If Len(extra) > 0 Then extra = extra & " "
    extra = extra & QuoteForCmd(WScript.Arguments(i))
Next

Dim cmdLine
cmdLine = "cmd /c uv run main.py"
If Len(extra) > 0 Then cmdLine = cmdLine & " " & extra
sh.Run cmdLine, 0, False
