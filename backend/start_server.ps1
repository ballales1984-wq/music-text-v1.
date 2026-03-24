# Script PowerShell per avviare il backend
Set-Location $PSScriptRoot

# FIX: Forza encoding UTF-8 per evitare errori con emoji nei log
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "🚀 Avvio Music Text Generator Backend..." -ForegroundColor Green

# Attiva virtual environment
if (Test-Path "venv\Scripts\Activate.ps1") {
    .\venv\Scripts\Activate.ps1
    Write-Host "✅ Virtual environment attivato" -ForegroundColor Green
}
else {
    Write-Host "⚠️  Virtual environment non trovato" -ForegroundColor Yellow
}

# Avvia il server
Write-Host "📡 Avvio server su http://localhost:8001..." -ForegroundColor Cyan
python -m uvicorn main_simple:app --host 0.0.0.0 --port 8001 --reload

