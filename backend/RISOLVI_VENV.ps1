# Script per ricreare virtual environment
# Risolve il problema del percorso errato

Write-Host "🔧 Risoluzione Virtual Environment" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# 1. Rimuovi vecchio venv
Write-Host "1️⃣ Rimozione vecchio venv..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Remove-Item -Recurse -Force "venv"
    Write-Host "   ✅ Vecchio venv rimosso" -ForegroundColor Green
} else {
    Write-Host "   ℹ️ Nessun venv da rimuovere" -ForegroundColor Gray
}

# 2. Crea nuovo venv
Write-Host ""
Write-Host "2️⃣ Creazione nuovo venv..." -ForegroundColor Yellow
python -m venv venv
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Nuovo venv creato" -ForegroundColor Green
} else {
    Write-Host "   ❌ Errore creazione venv" -ForegroundColor Red
    exit 1
}

# 3. Attiva venv
Write-Host ""
Write-Host "3️⃣ Attivazione venv..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"
Write-Host "   ✅ Venv attivato" -ForegroundColor Green

# 4. Aggiorna pip
Write-Host ""
Write-Host "4️⃣ Aggiornamento pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip
Write-Host "   ✅ Pip aggiornato" -ForegroundColor Green

# 5. Installa dipendenze
Write-Host ""
Write-Host "5️⃣ Installazione dipendenze..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Dipendenze installate" -ForegroundColor Green
} else {
    Write-Host "   ❌ Errore installazione dipendenze" -ForegroundColor Red
    exit 1
}

# 6. Verifica installazione
Write-Host ""
Write-Host "6️⃣ Verifica installazione..." -ForegroundColor Yellow
$packages = @("fastapi", "uvicorn", "whisper", "torch")
foreach ($pkg in $packages) {
    $installed = pip show $pkg 2>$null
    if ($installed) {
        Write-Host "   ✅ $pkg installato" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️ $pkg non trovato" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "🎉 Setup completato!" -ForegroundColor Green
Write-Host ""
Write-Host "Ora puoi avviare il server con:" -ForegroundColor Cyan
Write-Host "   uvicorn main:app --host 0.0.0.0 --port 8001 --reload" -ForegroundColor White
Write-Host ""

# Made with Bob
