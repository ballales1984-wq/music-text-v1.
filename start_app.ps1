# Music Text Generator - Avvio Automatico
# Versione 3.1.0

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🎵 Music Text Generator v3.1.0" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verifica prerequisiti
Write-Host "🔍 Verifica prerequisiti..." -ForegroundColor Yellow

# Verifica Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✅ Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Python non trovato! Installa Python 3.8+" -ForegroundColor Red
    exit 1
}

# Verifica Node
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  ✅ Node.js: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Node.js non trovato! Installa Node.js 18+" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Verifica dipendenze backend
Write-Host "📦 Verifica dipendenze backend..." -ForegroundColor Yellow
if (-not (Test-Path "backend/venv")) {
    Write-Host "  ⚠️  Virtual environment non trovato" -ForegroundColor Yellow
    Write-Host "  📥 Creazione virtual environment..." -ForegroundColor Cyan
    
    Set-Location backend
    python -m venv venv
    
    Write-Host "  📥 Installazione dipendenze..." -ForegroundColor Cyan
    .\venv\Scripts\activate
    pip install -r requirements.txt
    deactivate
    
    Set-Location ..
    Write-Host "  ✅ Dipendenze backend installate" -ForegroundColor Green
} else {
    Write-Host "  ✅ Virtual environment trovato" -ForegroundColor Green
}

# Verifica dipendenze frontend
Write-Host "📦 Verifica dipendenze frontend..." -ForegroundColor Yellow
if (-not (Test-Path "frontend/node_modules")) {
    Write-Host "  ⚠️  node_modules non trovato" -ForegroundColor Yellow
    Write-Host "  📥 Installazione dipendenze..." -ForegroundColor Cyan
    
    Set-Location frontend
    npm install
    Set-Location ..
    
    Write-Host "  ✅ Dipendenze frontend installate" -ForegroundColor Green
} else {
    Write-Host "  ✅ node_modules trovato" -ForegroundColor Green
}

Write-Host ""
Write-Host "🚀 Avvio applicazione..." -ForegroundColor Green
Write-Host ""

# Avvia backend in nuova finestra
Write-Host "  🔧 Avvio backend (porta 8001)..." -ForegroundColor Cyan
$backendScript = @"
Write-Host '🔧 Backend - Music Text Generator' -ForegroundColor Green
Write-Host '=================================' -ForegroundColor Green
Write-Host ''
cd backend
.\venv\Scripts\activate
python main.py
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendScript

# Aspetta che backend si avvii
Write-Host "  ⏳ Attendo avvio backend (5 secondi)..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Verifica backend
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8001/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "  ✅ Backend avviato correttamente" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Backend potrebbe richiedere più tempo..." -ForegroundColor Yellow
}

Write-Host ""

# Avvia frontend in nuova finestra
Write-Host "  ⚛️  Avvio frontend (porta 3000)..." -ForegroundColor Cyan
$frontendScript = @"
Write-Host '⚛️  Frontend - Music Text Generator' -ForegroundColor Green
Write-Host '==================================' -ForegroundColor Green
Write-Host ''
cd frontend
npm run dev
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendScript

# Aspetta che frontend si avvii
Write-Host "  ⏳ Attendo avvio frontend (8 secondi)..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ Applicazione avviata!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 URL Applicazione:" -ForegroundColor Yellow
Write-Host "   🌐 Frontend:  http://localhost:3000" -ForegroundColor Cyan
Write-Host "   🔧 Backend:   http://localhost:8001" -ForegroundColor Cyan
Write-Host "   📊 Metrics:   http://localhost:8001/metrics" -ForegroundColor Cyan
Write-Host "   📈 Stats:     http://localhost:8001/stats" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 Suggerimenti:" -ForegroundColor Yellow
Write-Host "   - Apri http://localhost:3000 nel browser" -ForegroundColor White
Write-Host "   - Carica un file audio (MP3, WAV, etc.)" -ForegroundColor White
Write-Host "   - Attendi il processamento (30-120 secondi)" -ForegroundColor White
Write-Host "   - Visualizza e scarica i risultati" -ForegroundColor White
Write-Host ""
Write-Host "🛑 Per fermare:" -ForegroundColor Yellow
Write-Host "   - Chiudi le finestre PowerShell di backend e frontend" -ForegroundColor White
Write-Host "   - Oppure premi Ctrl+C in ogni finestra" -ForegroundColor White
Write-Host ""

# Apri browser dopo 3 secondi
Write-Host "🌐 Apertura browser tra 3 secondi..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

try {
    Start-Process "http://localhost:3000"
    Write-Host "  ✅ Browser aperto" -ForegroundColor Green
} catch {
    Write-Host "  ⚠️  Apri manualmente: http://localhost:3000" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "🎉 Buon divertimento con Music Text Generator!" -ForegroundColor Green
Write-Host ""
Write-Host "Premi un tasto per chiudere questa finestra..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Made with Bob
