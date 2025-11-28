#!/bin/bash
# Lethe.TXT - Script de execução (Unix/Mac)
# Autor: Matheus C. Pestana

# Diretório do script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Ativa o ambiente virtual
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Ambiente virtual ativado"
else
    echo "❌ Ambiente virtual não encontrado. Execute:"
    echo "   uv venv .venv"
    echo "   source .venv/bin/activate"
    echo "   uv pip install -r requirements.txt"
    exit 1
fi

# Executa o Streamlit
echo "🚀 Iniciando Lethe.TXT..."
streamlit run app.py

