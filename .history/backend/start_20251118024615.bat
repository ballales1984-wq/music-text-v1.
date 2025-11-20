@echo off
REM Script di avvio per il backend (Windows)

echo 🚀 Avvio Music Text Generator Backend...

REM Attiva virtual environment se esiste
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Avvia il server con uvicorn
echo 📡 Avvio server su http://localhost:8000...
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

pause

