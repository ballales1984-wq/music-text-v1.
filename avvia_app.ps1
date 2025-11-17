# Script PowerShell per avviare automaticamente l'applicazione
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Music Text Generator" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

# Avvia Backend
Write-Host "Avvio Backend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath\backend'; .\venv\Scripts\Activate.ps1; python main.py" -WindowStyle Minimized

Start-Sleep -Seconds 3

# Avvia Frontend
Write-Host "Avvio Frontend..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$scriptPath\frontend'; npm run dev" -WindowStyle Minimized

Start-Sleep -Seconds 5

# Apri browser
Write-Host "Apertura browser..." -ForegroundColor Yellow
Start-Process "http://localhost:3000"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  App avviata!" -ForegroundColor Green
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

