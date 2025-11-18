@echo off
echo ========================================
echo  Music Text Generator - Build EXE
echo ========================================
echo.

REM Verifica Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python non trovato!
    pause
    exit /b 1
)

REM Verifica PyInstaller
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo 📦 Installazione PyInstaller...
    pip install pyinstaller
)

REM Crea directory necessarie
if not exist "uploads" mkdir uploads
if not exist "outputs" mkdir outputs

REM Build
echo 🔨 Creazione eseguibile...
python build_exe.py

if exist "dist\music-text-generator-backend.exe" (
    echo.
    echo ✅ SUCCESSO!
    echo 📁 Eseguibile: dist\music-text-generator-backend.exe
    echo.
    echo ⚠️  NOTA: L'eseguibile include tutte le dipendenze.
    echo    Dimensione: ~500MB-1GB (include PyTorch, Whisper, etc.)
    echo.
) else (
    echo.
    echo ❌ ERRORE nella creazione dell'eseguibile!
    echo    Controlla i log sopra per dettagli.
    echo.
)

pause

