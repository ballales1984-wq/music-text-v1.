#!/bin/bash
# Script di avvio per il backend

echo "🚀 Avvio Music Text Generator Backend..."

# Attiva virtual environment se esiste
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Avvia il server
python -m uvicorn main_simple:app --host 0.0.0.0 --port 8001 --reload

