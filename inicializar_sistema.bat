@echo off
title Servidor ERP Eletromaster

:: 1. Entra na pasta exata do projeto
cd /d "C:\Users\W11\Documents\GitHub\ERP_ELETROMASTER"

:: 2. Confirma se o arquivo app.py existe (Diagnóstico)
if not exist "src\app.py" (
    echo ERRO: Nao encontrei o arquivo src\app.py
    echo Verifique se a pasta src esta correta.
    pause
    exit
)

:: --- A CORREÇÃO MÁGICA ---
:: Define que a pasta raiz do projeto faz parte do caminho do Python.
:: Isso permite que o código encontre o modulo "src".
set PYTHONPATH=%CD%

:: 3. Inicia o sistema
echo Iniciando servidor...
venv\Scripts\python.exe src\app.py

:: 4. Se o servidor cair, o pause segura a tela
pause