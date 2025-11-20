# Script completo: Installa Python 3.10 + Spleeter
# Esegue tutti i passaggi automaticamente

Write-Host "🎵 Installazione completa Python 3.10 + Spleeter" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Passo 1: Installa Python 3.10
Write-Host "📋 PASSO 1: Installazione Python 3.10" -ForegroundColor Yellow
Write-Host ""

$python310 = py -3.10 --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  Python 3.10 non trovato. Avvio installazione..." -ForegroundColor Yellow
    Write-Host ""
    
    # Esegui script installazione
    & "$PSScriptRoot\installa_python310.ps1"
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "❌ Installazione Python 3.10 fallita. Interrompo." -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "⚠️  RIAVVIA IL TERMINALE dopo l'installazione di Python 3.10" -ForegroundColor Yellow
    Write-Host "   Poi esegui di nuovo questo script." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "✅ Python 3.10 già installato: $python310" -ForegroundColor Green
}

Write-Host ""
Write-Host "📋 PASSO 2: Creazione venv con Python 3.10" -ForegroundColor Yellow
Write-Host ""

# Crea venv
if (Test-Path "venv_spleeter") {
    Write-Host "⚠️  venv_spleeter già esistente. Vuoi ricrearlo? (S/N)" -ForegroundColor Yellow
    $risposta = Read-Host
    if ($risposta -eq "S" -or $risposta -eq "s") {
        Remove-Item -Recurse -Force "venv_spleeter"
        Write-Host "🗑️  Venv rimosso" -ForegroundColor Gray
    } else {
        Write-Host "⏭️  Uso venv esistente" -ForegroundColor Gray
    }
}

if (-not (Test-Path "venv_spleeter")) {
    Write-Host "🔨 Creazione venv_spleeter con Python 3.10..." -ForegroundColor Cyan
    py -3.10 -m venv venv_spleeter
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Errore creazione venv" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Venv creato" -ForegroundColor Green
} else {
    Write-Host "✅ Venv già esistente" -ForegroundColor Green
}

Write-Host ""
Write-Host "📋 PASSO 3: Installazione Spleeter e dipendenze" -ForegroundColor Yellow
Write-Host ""

# Attiva venv e installa
$activateScript = ".\venv_spleeter\Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    Write-Host "🔧 Attivazione venv..." -ForegroundColor Cyan
    & $activateScript
    
    Write-Host "📦 Aggiornamento pip..." -ForegroundColor Cyan
    python -m pip install --upgrade pip
    
    Write-Host "📦 Installazione numpy compatibile..." -ForegroundColor Cyan
    pip install "numpy<1.24.0"
    
    Write-Host "📦 Installazione TensorFlow..." -ForegroundColor Cyan
    pip install tensorflow==2.12.1
    
    Write-Host "📦 Installazione Spleeter..." -ForegroundColor Cyan
    Write-Host "   Questo può richiedere alcuni minuti..." -ForegroundColor Gray
    pip install spleeter
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Spleeter installato!" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "🔍 Verifica installazione..." -ForegroundColor Cyan
        python -c "from spleeter.separator import Separator; print('✅ Spleeter funziona correttamente!')"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "=" * 60 -ForegroundColor Green
            Write-Host "✅ INSTALLAZIONE COMPLETA!" -ForegroundColor Green
            Write-Host "=" * 60 -ForegroundColor Green
            Write-Host ""
            Write-Host "🎯 Per usare Spleeter:" -ForegroundColor Cyan
            Write-Host "1. Attiva venv: .\venv_spleeter\Scripts\Activate.ps1"
            Write-Host "2. Avvia backend: python main.py"
            Write-Host ""
            Write-Host "💡 Oppure modifica start.bat per usare venv_spleeter automaticamente"
        } else {
            Write-Host "⚠️  Spleeter installato ma verifica fallita" -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Errore installazione Spleeter" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "❌ Script di attivazione non trovato" -ForegroundColor Red
    exit 1
}

