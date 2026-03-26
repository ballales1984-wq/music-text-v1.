# 🚀 Avvio Rapido - Music Text Generator

## Comandi per Avviare l'Applicazione

### 1️⃣ Backend (Terminale 1)

```powershell
# Vai nella cartella backend
cd backend

# Attiva ambiente virtuale
.\venv\Scripts\Activate.ps1

# Avvia server
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

**Oppure usa lo script:**
```powershell
cd backend
.\start_server.ps1
```

### 2️⃣ Frontend (Terminale 2)

```powershell
# Vai nella cartella frontend
cd frontend

# Avvia Next.js
npm run dev
```

---

## ✅ Verifica che Funzioni

### Backend
Apri browser: http://localhost:8001/docs

Dovresti vedere la documentazione API Swagger.

### Frontend
Apri browser: http://localhost:3000

Dovresti vedere l'interfaccia dell'app.

---

## 🔧 Se il Backend Non Parte

### Errore: "ModuleNotFoundError"

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Errore: "Port already in use"

```powershell
# Trova processo sulla porta 8001
netstat -ano | findstr :8001

# Termina processo (sostituisci PID)
taskkill /PID <numero_pid> /F
```

### Errore: "Cannot find module 'uvicorn'"

```powershell
cd backend
.\venv\Scripts\Activate.ps1
pip install uvicorn fastapi
```

---

## 📝 Note

- **Backend**: http://localhost:8001
- **Frontend**: http://localhost:3000
- **Docs API**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

---

## ⚠️ Warning Normali (Ignora)

Questi warning sono **NORMALI** e non bloccano l'app:

```
⚠️ pkg_resources is deprecated
⚠️ Ollama non raggiungibile
⚠️ python-magic not available
⚠️ Redis connection failed
```

L'app usa fallback automatici per tutto! ✅