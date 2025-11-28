@echo off
REM Lethe.TXT - Script de execução (Windows)
REM Autor: Matheus C. Pestana

REM Muda para o diretório do script
cd /d "%~dp0"

REM Ativa o ambiente virtual
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo [OK] Ambiente virtual ativado
) else (
    echo [ERRO] Ambiente virtual nao encontrado. Execute:
    echo    uv venv .venv
    echo    .venv\Scripts\activate.bat
    echo    uv pip install -r requirements.txt
    exit /b 1
)

REM Executa o Streamlit
echo [INFO] Iniciando Lethe.TXT...
streamlit run app.py

