# Fix installazione - Chiude processi e reinstalla
Write-Host "🔧 Fix Installazione Backend" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan
Write-Host ""

# 1. Chiudi tutti i processi Python/Uvicorn
Write-Host "1️⃣ Chiusura processi Python..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*uvicorn*"} | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Write-Host "   ✅ Processi chiusi" -ForegroundColor Green

# 2. Rimuovi venv
Write-Host ""
Write-Host "2️⃣ Rimozione venv..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Remove-Item -Recurse -Force "venv" -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}
Write-Host "   ✅ Venv rimosso" -ForegroundColor Green

# 3. Crea nuovo venv
Write-Host ""
Write-Host "3️⃣ Creazione nuovo venv..." -ForegroundColor Yellow
python -m venv venv
Write-Host "   ✅ Venv creato" -ForegroundColor Green

# 4. Attiva e installa
Write-Host ""
Write-Host "4️⃣ Installazione dipendenze..." -ForegroundColor Yellow
Write-Host "   (Questo richiederà 5-10 minuti)" -ForegroundColor Gray
Write-Host ""

& ".\venv\Scripts\Activate.ps1"
python -m pip install --upgrade pip
pip install -r requirements.txt

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ INSTALLAZIONE COMPLETATA!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Ora puoi avviare il backend con:" -ForegroundColor Cyan
    Write-Host "   uvicorn main:app --host 0.0.0.0 --port 8001 --reload" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "❌ Errore durante l'installazione" -ForegroundColor Red
}

Write-Host ""

# Made with Bob
