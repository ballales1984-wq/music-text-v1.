#!/bin/bash
# Script di avvio per il backend

echo "🚀 Avvio Music Text Generator Backend..."

# Attiva virtual environment se esiste
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Avvia il server
python main.py

