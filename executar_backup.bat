@echo off
echo --- INICIANDO BACKUP MANUAL ---

:: 1. Entra na pasta do projeto (AJUSTE ESTE CAMINHO)
cd /d "C:\Users\W11\Documents\GitHub\ERP_ELETROMASTER"

:: 2. Executa o backup usando o Python do ambiente virtual
:: (AJUSTE O CAMINHO DO PYTHON SE NECESSARIO)
venv\Scripts\python.exe -m flask --app src/app.py backup

:: 3. Pausa a tela para você ler o que aconteceu
echo.
echo ---------------------------------------------------
echo Se apareceu erro acima, leia. Se finalizou, feche.
echo ---------------------------------------------------
