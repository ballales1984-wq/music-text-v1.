# 🚀 Guida Avvio su Localhost

**Versione**: 3.1.0  
**Sistema**: Windows 11  
**Tempo stimato**: 5-10 minuti

---

## 📋 PREREQUISITI

Prima di iniziare, verifica di avere:

- ✅ Python 3.8+ installato
- ✅ Node.js 18+ installato
- ⚠️ Redis (opzionale - l'app funziona anche senza)

### Verifica Installazioni

```powershell
# Verifica Python
python --version
# Output atteso: Python 3.8.x o superiore

# Verifica Node
node --version
# Output atteso: v18.x.x o superiore

# Verifica npm
npm --version
# Output atteso: 9.x.x o superiore
```

---

## 🔧 SETUP INIZIALE

### Step 1: Installa Dipendenze Backend

```powershell
# Vai nella cartella backend
cd backend

# Crea virtual environment (consigliato)
python -m venv venv

# Attiva virtual environment
.\venv\Scripts\activate

# Installa dipendenze
pip install -r requirements.txt
```

**Tempo**: ~2-3 minuti

**Note**:
- Se `python-magic` da errore su Windows, è normale
- L'app funzionerà comunque (validazione MIME sarà skippata)
- Per installare python-magic su Windows: `pip install python-magic-bin`

### Step 2: Configura Environment (Opzionale)

```powershell
# Copia template configurazione
copy .env.example .env

# Modifica .env se necessario (opzionale)
notepad .env
```

**Configurazione minima** (già nei default):
```bash
# Tutto opzionale, l'app funziona con i default
ENABLE_AUTH=false
LOG_FORMAT=text
LOG_LEVEL=INFO
MAX_WORKERS=4
```

### Step 3: Installa Dipendenze Frontend

```powershell
# Apri un NUOVO terminale
# Vai nella cartella frontend
cd frontend

# Installa dipendenze
npm install
```

**Tempo**: ~1-2 minuti

---

## 🚀 AVVIO APPLICAZIONE

### Opzione A: Avvio Manuale (2 Terminali)

#### Terminale 1: Backend

```powershell
# Vai in backend
cd backend

# Attiva venv (se non già attivo)
.\venv\Scripts\activate

# Avvia server
python main.py
```

**Output atteso**:
```
✅ Prometheus metrics enabled
   Endpoint: GET /metrics
⚠️  Redis non disponibile: ... Uso storage in-memory
Application started
   version=3.1.0
   workers=4
   event=startup
INFO:     Uvicorn running on http://0.0.0.0:8001
```

**Backend pronto su**: http://localhost:8001

#### Terminale 2: Frontend

```powershell
# Vai in frontend
cd frontend

# Avvia dev server
npm run dev
```

**Output atteso**:
```
  ▲ Next.js 14.2.3
  - Local:        http://localhost:3000
  - Network:      http://192.168.x.x:3000

 ✓ Ready in 2.5s
```

**Frontend pronto su**: http://localhost:3000

### Opzione B: Avvio con Script (1 Click)

#### Windows PowerShell Script

Crea file `start_app.ps1`:

```powershell
# start_app.ps1
Write-Host "🚀 Avvio Music Text Generator..." -ForegroundColor Green

# Avvia backend in background
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; .\venv\Scripts\activate; python main.py"

# Aspetta 3 secondi
Start-Sleep -Seconds 3

# Avvia frontend in background
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

# Aspetta 5 secondi
Start-Sleep -Seconds 5

# Apri browser
Start-Process "http://localhost:3000"

Write-Host "✅ Applicazione avviata!" -ForegroundColor Green
Write-Host "   Backend:  http://localhost:8001" -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor Cyan
```

**Esegui**:
```powershell
.\start_app.ps1
```

---

## 🧪 TEST FUNZIONAMENTO

### 1. Verifica Backend

```powershell
# Test health check
curl http://localhost:8001/health

# Output atteso:
# {"status":"ok","message":"Server operativo (versione semplificata)"}
```

### 2. Verifica Metrics

```powershell
# Test Prometheus metrics
curl http://localhost:8001/metrics

# Output atteso: metrics in formato Prometheus
```

### 3. Verifica Frontend

Apri browser su: http://localhost:3000

**Dovresti vedere**:
- Interfaccia upload file
- Pulsante "Processa Audio"
- Area risultati

### 4. Test Completo Upload

1. Vai su http://localhost:3000
2. Clicca "Scegli file" o drag & drop
3. Seleziona un file audio (MP3, WAV, etc.)
4. Clicca "Processa Audio"
5. Attendi processamento
6. Visualizza risultati

**Tempo processamento**: 30-120 secondi (dipende da file e CPU)

---

## 🐛 TROUBLESHOOTING

### Problema: "Port 8001 already in use"

**Soluzione**:
```powershell
# Trova processo su porta 8001
netstat -ano | findstr :8001

# Termina processo (sostituisci PID)
taskkill /PID <PID> /F

# Oppure cambia porta in main.py
# uvicorn.run(app, host="0.0.0.0", port=8002)
```

### Problema: "Port 3000 already in use"

**Soluzione**:
```powershell
# Termina processo Node
taskkill /F /IM node.exe

# Oppure usa porta diversa
$env:PORT=3001
npm run dev
```

### Problema: "Module not found"

**Backend**:
```powershell
cd backend
.\venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend**:
```powershell
cd frontend
npm install
```

### Problema: "python-magic not available"

**Soluzione**:
```powershell
# Windows
pip install python-magic-bin

# Oppure ignora (app funziona comunque)
```

### Problema: "Redis non disponibile"

**Soluzione**: È normale! L'app funziona senza Redis (usa fallback in-memory)

**Per installare Redis (opzionale)**:
```powershell
# Docker (consigliato)
docker run -d -p 6379:6379 redis:alpine

# Oppure WSL
wsl
sudo apt-get install redis-server
redis-server
```

### Problema: Backend si avvia ma frontend non si connette

**Verifica CORS**:
```python
# In backend/main.py, verifica:
allow_origins=["http://localhost:3000", "http://localhost:3001"]
```

**Verifica URL frontend**:
```typescript
// In frontend, verifica .env.local:
NEXT_PUBLIC_API_URL=http://localhost:8001
```

---

## 📊 MONITORING DURANTE ESECUZIONE

### Visualizza Log Backend

I log appariranno nel terminale backend:

```
Application started version=3.1.0 workers=4
File uploaded job_id=abc-123 filename=song.mp3 size_mb=5.2
Job processing started job_id=abc-123
Vocal separation completed job_id=abc-123 duration_s=15.3
...
```

### Visualizza Metrics Real-time

```powershell
# In un nuovo terminale
while ($true) {
    curl http://localhost:8001/metrics | Select-String "http_requests_total"
    Start-Sleep -Seconds 5
}
```

### Visualizza Job Status

```powershell
# Lista tutti i job
curl http://localhost:8001/jobs

# Status job specifico
curl http://localhost:8001/status/<job_id>
```

### Visualizza Stats Sistema

```powershell
curl http://localhost:8001/stats
```

---

## 🎯 WORKFLOW TIPICO

### 1. Avvio

```powershell
# Terminale 1: Backend
cd backend
.\venv\Scripts\activate
python main.py

# Terminale 2: Frontend
cd frontend
npm run dev
```

### 2. Utilizzo

1. Apri http://localhost:3000
2. Carica file audio
3. Attendi processamento
4. Visualizza risultati
5. Scarica output

### 3. Monitoring

```powershell
# Terminale 3: Monitoring
curl http://localhost:8001/metrics
curl http://localhost:8001/stats
```

### 4. Shutdown

```powershell
# In ogni terminale: Ctrl+C
# Oppure chiudi finestre terminale
```

---

## 🔧 CONFIGURAZIONI AVANZATE

### Abilita Autenticazione

```bash
# In .env
ENABLE_AUTH=true
API_KEYS=secret-key-1,secret-key-2
```

**Uso**:
```powershell
curl -H "X-API-Key: secret-key-1" http://localhost:8001/stats
```

### Cambia Rate Limiting

```bash
# In .env
RATE_LIMIT_REQUESTS=20  # 20 richieste
RATE_LIMIT_WINDOW=60    # per minuto
```

### Abilita Logging JSON

```bash
# In .env
LOG_FORMAT=json
```

### Aumenta Workers

```bash
# In .env
MAX_WORKERS=8  # Più job paralleli
```

---

## 📝 CHECKLIST AVVIO

Prima di iniziare:

- [ ] Python 3.8+ installato
- [ ] Node.js 18+ installato
- [ ] Dipendenze backend installate
- [ ] Dipendenze frontend installate
- [ ] Porta 8001 libera
- [ ] Porta 3000 libera

Durante avvio:

- [ ] Backend avviato (http://localhost:8001)
- [ ] Frontend avviato (http://localhost:3000)
- [ ] Health check OK
- [ ] Metrics accessibili
- [ ] UI caricata correttamente

Test funzionamento:

- [ ] Upload file funziona
- [ ] Processamento completa
- [ ] Risultati visualizzati
- [ ] Download funziona

---

## 🎉 SUCCESSO!

Se vedi:
- ✅ Backend su http://localhost:8001
- ✅ Frontend su http://localhost:3000
- ✅ UI caricata
- ✅ Upload funziona

**Congratulazioni! L'applicazione è in esecuzione! 🚀**

---

## 📞 SUPPORTO

### Log Utili

**Backend**:
```powershell
cd backend
python main.py > backend.log 2>&1
```

**Frontend**:
```powershell
cd frontend
npm run dev > frontend.log 2>&1
```

### File Importanti

- `backend/main.py` - Entry point backend
- `frontend/app/page.tsx` - UI principale
- `backend/.env` - Configurazione
- `backend/requirements.txt` - Dipendenze Python
- `frontend/package.json` - Dipendenze Node

---

**Buon divertimento con Music Text Generator! 🎵**