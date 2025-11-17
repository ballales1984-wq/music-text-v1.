@echo off
REM Script per avviare automaticamente l'applicazione
echo ========================================
echo   Music Text Generator
echo ========================================
echo.

cd /d "%~dp0"

REM Avvia Backend
echo Avvio Backend...
start "Music Text Generator - Backend" cmd /k "cd backend && venv\Scripts\activate && python main.py"

timeout /t 3 /nobreak >nul

REM Avvia Frontend
echo Avvio Frontend...
start "Music Text Generator - Frontend" cmd /k "cd frontend && npm run dev"

timeout /t 5 /nobreak >nul

REM Apri browser
echo Apertura browser...
start http://localhost:3000

echo.
echo ========================================
echo   App avviata!
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8000
echo ========================================
echo.
pause

