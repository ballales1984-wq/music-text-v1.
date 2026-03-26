# Script per avviare Backend + Frontend in parallelo
# Music Text Generator v3.1.0

$ErrorActionPreference = "Stop"

Write-Host "🚀 Music Text Generator - Avvio Completo" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Funzione per avviare processo in background
function Start-BackgroundProcess {
    param(
        [string]$Title,
        [string]$WorkingDirectory,
        [string]$Command
    )
    
    Write-Host "▶️  Avvio $Title..." -ForegroundColor Yellow
    
    $process = Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "cd '$WorkingDirectory'; $Command"
    ) -PassThru -WindowStyle Normal
    
    Write-Host "   ✅ $Title avviato (PID: $($process.Id))" -ForegroundColor Green
    return $process
}

# 1. Avvia Backend
Write-Host ""
Write-Host "1️⃣ BACKEND (Python/FastAPI)" -ForegroundColor Magenta
Write-Host "   Porta: 8001" -ForegroundColor Gray
Write-Host "   URL: http://localhost:8001" -ForegroundColor Gray

$backendProcess = Start-BackgroundProcess `
    -Title "Backend" `
    -WorkingDirectory "d:/music text/backend" `
    -Command ".\venv\Scripts\Activate.ps1; Write-Host '🔧 Backend - Music Text Generator' -ForegroundColor Cyan; Write-Host '=================================' -ForegroundColor Cyan; Write-Host ''; uvicorn main:app --host 0.0.0.0 --port 8001 --reload"

Start-Sleep -Seconds 2

# 2. Avvia Frontend
Write-Host ""
Write-Host "2️⃣ FRONTEND (Next.js/React)" -ForegroundColor Magenta
Write-Host "   Porta: 3000" -ForegroundColor Gray
Write-Host "   URL: http://localhost:3000" -ForegroundColor Gray

$frontendProcess = Start-BackgroundProcess `
    -Title "Frontend" `
    -WorkingDirectory "d:/music text/frontend" `
    -Command "Write-Host '🎨 Frontend - Music Text Generator' -ForegroundColor Cyan; Write-Host '==================================' -ForegroundColor Cyan; Write-Host ''; npm run dev"

# 3. Riepilogo
Write-Host ""
Write-Host "✅ APPLICAZIONE AVVIATA!" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Processi Attivi:" -ForegroundColor Cyan
Write-Host "   • Backend  (PID: $($backendProcess.Id))" -ForegroundColor White
Write-Host "   • Frontend (PID: $($frontendProcess.Id))" -ForegroundColor White
Write-Host ""
Write-Host "🌐 URL Applicazione:" -ForegroundColor Cyan
Write-Host "   • Frontend:  http://localhost:3000" -ForegroundColor White
Write-Host "   • Backend:   http://localhost:8001" -ForegroundColor White
Write-Host "   • API Docs:  http://localhost:8001/docs" -ForegroundColor White
Write-Host ""
Write-Host "⏱️  Attendi 10-30 secondi per il caricamento completo..." -ForegroundColor Yellow
Write-Host ""
Write-Host "🛑 Per fermare tutto:" -ForegroundColor Red
Write-Host "   1. Chiudi le finestre del Backend e Frontend" -ForegroundColor Gray
Write-Host "   2. Oppure premi Ctrl+C in questo terminale" -ForegroundColor Gray
Write-Host ""

# Attendi input utente
Write-Host "Premi un tasto per aprire il browser..." -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Apri browser
Write-Host ""
Write-Host "🌐 Apertura browser..." -ForegroundColor Yellow
Start-Sleep -Seconds 3
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "✅ Browser aperto!" -ForegroundColor Green
Write-Host ""
Write-Host "💡 Suggerimenti:" -ForegroundColor Cyan
Write-Host "   • Carica un file audio (MP3, WAV, M4A, FLAC)" -ForegroundColor Gray
Write-Host "   • Max 100MB per file" -ForegroundColor Gray
Write-Host "   • Tempo elaborazione: 30-120 secondi" -ForegroundColor Gray
Write-Host ""
Write-Host "📝 Log disponibili nelle finestre Backend/Frontend" -ForegroundColor Yellow
Write-Host ""
Write-Host "Premi un tasto per terminare tutti i processi..." -ForegroundColor Red
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Cleanup
Write-Host ""
Write-Host "🛑 Terminazione processi..." -ForegroundColor Yellow

try {
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Host "   ✅ Backend terminato" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Backend già terminato" -ForegroundColor Yellow
}

try {
    Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Host "   ✅ Frontend terminato" -ForegroundColor Green
} catch {
    Write-Host "   ⚠️  Frontend già terminato" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "👋 Applicazione chiusa!" -ForegroundColor Cyan
Write-Host ""

# Made with Bob
