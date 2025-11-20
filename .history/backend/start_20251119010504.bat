@echo off
REM Script di avvio per il backend (Windows)

echo 🚀 Avvio Music Text Generator Backend...

REM Usa Python dal venv direttamente
if exist venv\Scripts\python.exe (
    echo ✅ Usando Python dal venv
    venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
) else (
    echo ⚠️  Venv non trovato, uso Python di sistema
    python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
)

pause

