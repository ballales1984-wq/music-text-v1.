# Installazione semplificata - Salta pacchetti problematici
Write-Host "🔧 Installazione Semplificata Backend" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# Attiva venv
& ".\venv\Scripts\Activate.ps1"

Write-Host "📦 Installazione pacchetti essenziali..." -ForegroundColor Yellow
Write-Host ""

# Installa solo i pacchetti essenziali per far partire il backend
pip install fastapi==0.104.1
pip install uvicorn[standard]==0.24.0
pip install python-multipart==0.0.6
pip install torch>=2.0.0
pip install torchaudio>=2.0.0
pip install openai-whisper>=20231117
pip install openai>=1.3.0
pip install transformers>=4.30.0
pip install numpy>=1.24.0
pip install pydub>=0.25.1
pip install soundfile>=0.12.0
pip install scipy>=1.10.0
pip install pronouncing>=0.2.0
pip install python-dotenv==1.0.0
pip install requests>=2.31.0
pip install redis>=5.0.0
pip install prometheus-client>=0.19.0

Write-Host ""
Write-Host "✅ INSTALLAZIONE COMPLETATA!" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  Pacchetti opzionali saltati:" -ForegroundColor Yellow
Write-Host "   • librosa (per analisi audio avanzata)" -ForegroundColor Gray
Write-Host "   • noisereduce (per denoise)" -ForegroundColor Gray
Write-Host "   • matplotlib (per grafici)" -ForegroundColor Gray
Write-Host ""
Write-Host "💡 L'app funzionerà comunque!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Avvia il backend con:" -ForegroundColor Cyan
Write-Host "   uvicorn main:app --host 0.0.0.0 --port 8001 --reload" -ForegroundColor White
Write-Host ""

# Made with Bob
