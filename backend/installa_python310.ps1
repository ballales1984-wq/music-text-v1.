# Script per installare Python 3.10 automaticamente
# Usa winget (Windows Package Manager)

Write-Host "🐍 Installazione Python 3.10 per Spleeter..." -ForegroundColor Cyan
Write-Host ""

# Verifica se Python 3.10 è già installato
Write-Host "🔍 Verifica Python 3.10..." -ForegroundColor Yellow
$python310 = py -3.10 --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Python 3.10 già installato: $python310" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎯 Prossimi passi:" -ForegroundColor Cyan
    Write-Host "1. Crea venv: py -3.10 -m venv venv_spleeter"
    Write-Host "2. Attiva: .\venv_spleeter\Scripts\Activate.ps1"
    Write-Host "3. Installa: pip install spleeter"
    exit 0
}

# Verifica winget
Write-Host "🔍 Verifica winget..." -ForegroundColor Yellow
$wingetVersion = winget --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ winget non disponibile. Installa manualmente Python 3.10 da:" -ForegroundColor Red
    Write-Host "   https://www.python.org/downloads/release/python-31011/" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ winget disponibile: $wingetVersion" -ForegroundColor Green
Write-Host ""

# Cerca Python 3.10 su winget
Write-Host "🔍 Cerca Python 3.10 su winget..." -ForegroundColor Yellow
$searchResult = winget search Python.Python.3.10 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Python 3.10 non trovato su winget. Provo ricerca alternativa..." -ForegroundColor Yellow
    $searchResult = winget search "Python 3.10" 2>&1
}

# Installa Python 3.10
Write-Host ""
Write-Host "📥 Installazione Python 3.10..." -ForegroundColor Cyan
Write-Host "   Questo può richiedere alcuni minuti..." -ForegroundColor Gray
Write-Host ""

# Prova installazione con ID esatto
$installCmd = "winget install --id Python.Python.3.10 --exact --silent --accept-package-agreements --accept-source-agreements"
Write-Host "Eseguo: $installCmd" -ForegroundColor Gray
Invoke-Expression $installCmd

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Python 3.10 installato con successo!" -ForegroundColor Green
    Write-Host ""
    
    # Verifica installazione
    Write-Host "🔍 Verifica installazione..." -ForegroundColor Yellow
    Start-Sleep -Seconds 2  # Aspetta che il PATH si aggiorni
    $python310 = py -3.10 --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Python 3.10 verificato: $python310" -ForegroundColor Green
        Write-Host ""
        Write-Host "🎯 Prossimi passi:" -ForegroundColor Cyan
        Write-Host "1. Crea venv: py -3.10 -m venv venv_spleeter"
        Write-Host "2. Attiva: .\venv_spleeter\Scripts\Activate.ps1"
        Write-Host "3. Installa: pip install spleeter"
    } else {
        Write-Host "⚠️  Python 3.10 installato ma non ancora nel PATH" -ForegroundColor Yellow
        Write-Host "   Riavvia il terminale o esegui: refreshenv" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "❌ Installazione fallita. Provo metodo alternativo..." -ForegroundColor Red
    Write-Host ""
    
    # Metodo alternativo: download diretto
    Write-Host "📥 Download Python 3.10.11..." -ForegroundColor Cyan
    $pythonUrl = "https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe"
    $installerPath = "$env:TEMP\python-3.10.11-amd64.exe"
    
    try {
        Invoke-WebRequest -Uri $pythonUrl -OutFile $installerPath -UseBasicParsing
        Write-Host "✅ Download completato" -ForegroundColor Green
        Write-Host ""
        Write-Host "🚀 Avvio installer..." -ForegroundColor Cyan
        Write-Host "   IMPORTANTE: Seleziona 'Add Python 3.10 to PATH' durante l'installazione!" -ForegroundColor Yellow
        Write-Host ""
        
        Start-Process -FilePath $installerPath -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1" -Wait
        
        Write-Host ""
        Write-Host "✅ Installazione completata!" -ForegroundColor Green
        Write-Host "   Riavvia il terminale per usare Python 3.10" -ForegroundColor Yellow
    } catch {
        Write-Host "❌ Errore durante download: $_" -ForegroundColor Red
        Write-Host ""
        Write-Host "💡 Installa manualmente da:" -ForegroundColor Yellow
        Write-Host "   https://www.python.org/downloads/release/python-31011/" -ForegroundColor Cyan
    }
}

