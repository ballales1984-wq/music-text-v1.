@echo off
echo ========================================
echo  Push su GitHub - Music Text Generator
echo ========================================
echo.

REM Verifica se remote esiste
git remote get-url origin >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Remote GitHub non configurato.
    echo.
    echo 📝 Per configurare:
    echo    1. Crea repository su https://github.com/new
    echo    2. Esegui: git remote add origin https://github.com/TUO_USERNAME/music-text-generator.git
    echo.
    pause
    exit /b 1
)

echo ✅ Remote configurato
echo.
echo 🚀 Eseguo push...
echo.

git push -u origin master

if errorlevel 1 (
    echo.
    echo ❌ Errore nel push!
    echo.
    echo 💡 Possibili soluzioni:
    echo    - Verifica autenticazione GitHub
    echo    - Usa: gh auth login
    echo    - Oppure usa token: git remote set-url origin https://TOKEN@github.com/USERNAME/repo.git
    echo.
) else (
    echo.
    echo ✅ Push completato con successo!
    echo.
)

pause

