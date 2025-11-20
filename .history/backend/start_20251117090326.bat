@echo off
REM Script di avvio per il backend (Windows)

echo 🚀 Avvio Music Text Generator Backend...

REM Attiva virtual environment se esiste
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Avvia il server
python main.py

pause

