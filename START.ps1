# Music Text Generator - Sistema Completo
# Verifica, installa e avvia tutto automaticamente
# Versione 3.1.0

$ErrorActionPreference = "Stop"

# Colori
function Write-Title { param($text) Write-Host "`n$text" -ForegroundColor Cyan }
function Write-Success { param($text) Write-Host "✅ $text" -ForegroundColor Green }
function Write-Error { param($text) Write-Host "❌ $text" -ForegroundColor Red }
function Write-Warning { param($text) Write-Host "⚠️  $text" -ForegroundColor Yellow }
function Write-Info { param($text) Write-Host "ℹ️  $text" -ForegroundColor Gray }

Clear-Host
Write-Host @"
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║     🎵 MUSIC TEXT GENERATOR v3.1.0 🎵                ║
║                                                       ║
║     Sistema Completo di Avvio Automatico             ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
"@ -ForegroundColor Cyan

Write-Host ""

# ============================================
# FASE 1: VERIFICA PREREQUISITI
# ============================================
Write-Title "📋 FASE 1: Verifica Prerequisiti"

# Python
Write-Host "Verifica Python..." -NoNewline
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+\.\d+)") {
        Write-Success "Python $($matches[1]) trovato"
    } else {
        throw "Python non trovato"
    }
} catch {
    Write-Error "Python non installato!"
    Write-Info "Scarica Python da: https://www.python.org/downloads/"
    exit 1
}

# Node.js
Write-Host "Verifica Node.js..." -NoNewline
try {
    $nodeVersion = node --version 2>&1
    Write-Success "Node.js $nodeVersion trovato"
} catch {
    Write-Error "Node.js non installato!"
    Write-Info "Scarica Node.js da: https://nodejs.org/"
    exit 1
}

# NPM
Write-Host "Verifica NPM..." -NoNewline
try {
    $npmVersion = npm --version 2>&1
    Write-Success "NPM $npmVersion trovato"
} catch {
    Write-Error "NPM non installato!"
    exit 1
}

# ============================================
# FASE 2: SETUP BACKEND
# ============================================
Write-Title "🐍 FASE 2: Setup Backend (Python)"

Set-Location "backend"

# Virtual Environment
if (-not (Test-Path "venv")) {
    Write-Warning "Virtual environment non trovato. Creazione..."
    python -m venv venv
    Write-Success "Virtual environment creato"
} else {
    Write-Success "Virtual environment esistente"
}

# Attiva venv
Write-Host "Attivazione virtual environment..." -NoNewline
& ".\venv\Scripts\Activate.ps1"
Write-Success "Attivato"

# Verifica dipendenze
Write-Host "Verifica dipendenze Python..." -NoNewline
$needsInstall = $false

try {
    $fastapi = pip show fastapi 2>&1
    if (-not $fastapi) { $needsInstall = $true }
} catch {
    $needsInstall = $true
}

if ($needsInstall) {
    Write-Warning "Dipendenze mancanti"
    Write-Host ""
    Write-Host "Installazione dipendenze Python (può richiedere 5-10 minuti)..." -ForegroundColor Yellow
    Write-Host "Download: ~3.5GB (PyTorch, Whisper, ecc.)" -ForegroundColor Gray
    Write-Host ""
    
    pip install --upgrade pip
    pip install -r requirements.txt
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Dipendenze Python installate"
    } else {
        Write-Error "Errore installazione dipendenze Python"
        exit 1
    }
} else {
    Write-Success "Dipendenze Python OK"
}

Set-Location ".."

# ============================================
# FASE 3: SETUP FRONTEND
# ============================================
Write-Title "⚛️  FASE 3: Setup Frontend (Node.js)"

Set-Location "frontend"

# Verifica node_modules
if (-not (Test-Path "node_modules")) {
    Write-Warning "Dipendenze Node.js non trovate. Installazione..."
    npm install
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Dipendenze Node.js installate"
    } else {
        Write-Error "Errore installazione dipendenze Node.js"
        exit 1
    }
} else {
    Write-Success "Dipendenze Node.js OK"
}

Set-Location ".."

# ============================================
# FASE 4: VERIFICA PORTE
# ============================================
Write-Title "🔌 FASE 4: Verifica Porte"

# Porta 8001 (Backend)
$port8001 = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
if ($port8001) {
    Write-Warning "Porta 8001 già in uso"
    Write-Host "   Terminare il processo? (S/N): " -NoNewline -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq "S" -or $response -eq "s") {
        $pid = $port8001.OwningProcess
        Stop-Process -Id $pid -Force
        Write-Success "Processo terminato"
    }
} else {
    Write-Success "Porta 8001 disponibile"
}

# Porta 3000 (Frontend)
$port3000 = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($port3000) {
    Write-Warning "Porta 3000 già in uso"
    Write-Host "   Terminare il processo? (S/N): " -NoNewline -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq "S" -or $response -eq "s") {
        $pid = $port3000.OwningProcess
        Stop-Process -Id $pid -Force
        Write-Success "Processo terminato"
    }
} else {
    Write-Success "Porta 3000 disponibile"
}

# ============================================
# FASE 5: AVVIO SERVIZI
# ============================================
Write-Title "🚀 FASE 5: Avvio Servizi"

Write-Host ""
Write-Host "Avvio Backend..." -ForegroundColor Yellow
$backendProcess = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd 'd:\music text\backend'; .\venv\Scripts\Activate.ps1; Write-Host '🔧 Backend - Music Text Generator' -ForegroundColor Cyan; Write-Host '=================================' -ForegroundColor Cyan; Write-Host ''; Write-Host 'Porta: 8001' -ForegroundColor Gray; Write-Host 'URL: http://localhost:8001' -ForegroundColor Gray; Write-Host 'Docs: http://localhost:8001/docs' -ForegroundColor Gray; Write-Host ''; uvicorn main:app --host 0.0.0.0 --port 8001 --reload"
) -PassThru -WindowStyle Normal

Write-Success "Backend avviato (PID: $($backendProcess.Id))"
Start-Sleep -Seconds 3

Write-Host ""
Write-Host "Avvio Frontend..." -ForegroundColor Yellow
$frontendProcess = Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd 'd:\music text\frontend'; Write-Host '🎨 Frontend - Music Text Generator' -ForegroundColor Cyan; Write-Host '==================================' -ForegroundColor Cyan; Write-Host ''; Write-Host 'Porta: 3000' -ForegroundColor Gray; Write-Host 'URL: http://localhost:3000' -ForegroundColor Gray; Write-Host ''; npm run dev"
) -PassThru -WindowStyle Normal

Write-Success "Frontend avviato (PID: $($frontendProcess.Id))"

# ============================================
# FASE 6: RIEPILOGO E APERTURA BROWSER
# ============================================
Write-Title "✅ SISTEMA AVVIATO CON SUCCESSO!"

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                                                       ║" -ForegroundColor Green
Write-Host "║     🎉 Music Text Generator è ONLINE! 🎉             ║" -ForegroundColor Green
Write-Host "║                                                       ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

Write-Host "📊 Processi Attivi:" -ForegroundColor Cyan
Write-Host "   • Backend  (PID: $($backendProcess.Id)) - Porta 8001" -ForegroundColor White
Write-Host "   • Frontend (PID: $($frontendProcess.Id)) - Porta 3000" -ForegroundColor White
Write-Host ""

Write-Host "🌐 URL Applicazione:" -ForegroundColor Cyan
Write-Host "   • App:       http://localhost:3000" -ForegroundColor White
Write-Host "   • Backend:   http://localhost:8001" -ForegroundColor White
Write-Host "   • API Docs:  http://localhost:8001/docs" -ForegroundColor White
Write-Host ""

Write-Host "⏱️  Attendi 10-30 secondi per il caricamento completo..." -ForegroundColor Yellow
Write-Host ""

# Attendi caricamento
Write-Host "Apertura browser tra: " -NoNewline -ForegroundColor Cyan
for ($i = 5; $i -gt 0; $i--) {
    Write-Host "$i..." -NoNewline -ForegroundColor Yellow
    Start-Sleep -Seconds 1
}
Write-Host ""

# Apri browser
Write-Host ""
Write-Host "🌐 Apertura browser..." -ForegroundColor Yellow
Start-Process "http://localhost:3000"
Write-Success "Browser aperto!"

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                       ║" -ForegroundColor Cyan
Write-Host "║     💡 SUGGERIMENTI                                   ║" -ForegroundColor Cyan
Write-Host "║                                                       ║" -ForegroundColor Cyan
Write-Host "║  • Carica file audio (MP3, WAV, M4A, FLAC)           ║" -ForegroundColor White
Write-Host "║  • Dimensione max: 100MB                             ║" -ForegroundColor White
Write-Host "║  • Tempo elaborazione: 30-120 secondi                ║" -ForegroundColor White
Write-Host "║  • Log disponibili nelle finestre Backend/Frontend   ║" -ForegroundColor White
Write-Host "║                                                       ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════════════╝" -ForegroundColor Cyan

Write-Host ""
Write-Host "🛑 Per fermare tutto:" -ForegroundColor Red
Write-Host "   1. Chiudi le finestre Backend e Frontend" -ForegroundColor Gray
Write-Host "   2. Oppure premi un tasto in questo terminale" -ForegroundColor Gray
Write-Host ""

# Attendi input per terminare
Write-Host "Premi un tasto per terminare tutti i processi..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# ============================================
# FASE 7: TERMINAZIONE
# ============================================
Write-Title "🛑 Terminazione Processi"

try {
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Success "Backend terminato"
} catch {
    Write-Warning "Backend già terminato"
}

try {
    Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Success "Frontend terminato"
} catch {
    Write-Warning "Frontend già terminato"
}

Write-Host ""
Write-Host "👋 Applicazione chiusa. Arrivederci!" -ForegroundColor Cyan
Write-Host ""

# Made with Bob
