@echo off
REM Script di avvio per il backend (Windows)

REM Apri la cartella progetto
start explorer .

echo 🚀 Avvio Music Text Generator Backend...

REM Usa Python dal venv direttamente
if exist venv\Scripts\python.exe (
    echo ✅ Usando Python dal venv
    venv\Scripts\python.exe -m uvicorn main_simple:app --host 0.0.0.0 --port 8001 --reload
) else (
    echo ⚠️  Venv non trovato, uso Python di sistema
    python -m uvicorn main_simple:app --host 0.0.0.0 --port 8001 --reload
)

pause

