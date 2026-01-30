Set WshShell = CreateObject("WScript.Shell")
' O parametro 0 no final esconde a janela
' O script procura o .bat na mesma pasta onde este arquivo esta
WshShell.Run chr(34) & "inicializar_sistema.bat" & Chr(34), 0
Set WshShell = Nothing