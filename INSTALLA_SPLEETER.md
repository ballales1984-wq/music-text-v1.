# 🎵 Installazione Spleeter per Separazione Vocale Avanzata

## ⚠️ Problema
Spleeter richiede **Python 3.10 o precedente**. Il tuo sistema ha Python 3.11, 3.12, 3.13 che non sono compatibili.

## 🎯 Soluzione: Installare Python 3.10

### Opzione 1: Download Manuale (Consigliato)

1. **Scarica Python 3.10.11** (ultima versione 3.10):
   - Vai su: https://www.python.org/downloads/release/python-31011/
   - Scarica: **Windows installer (64-bit)** (es: `python-3.10.11-amd64.exe`)

2. **Installa Python 3.10**:
   - Esegui l'installer
   - ✅ **IMPORTANTE**: Seleziona "Add Python 3.10 to PATH"
   - ✅ Seleziona "Install for all users" (opzionale)
   - Clicca "Install Now"

3. **Verifica installazione**:
   ```powershell
   py -3.10 --version
   ```
   Dovrebbe mostrare: `Python 3.10.11`

### Opzione 2: Usando py launcher (Windows Store)

```powershell
# Abilita installazione automatica
$env:PYLAUNCHER_ALLOW_INSTALL = "1"
py -3.10 --version
```

Questo aprirà Microsoft Store per installare Python 3.10.

---

## 🔧 Configurazione Venv con Python 3.10

Dopo aver installato Python 3.10:

```powershell
cd backend

# Crea venv con Python 3.10
py -3.10 -m venv venv_spleeter

# Attiva venv
.\venv_spleeter\Scripts\Activate.ps1

# Installa dipendenze base
pip install --upgrade pip
pip install numpy<1.24.0  # Spleeter richiede numpy < 1.24
pip install tensorflow==2.12.1
pip install spleeter

# Installa altre dipendenze del progetto
pip install -r requirements.txt
```

---

## 🚀 Uso del Venv con Spleeter

### Metodo 1: Modifica start.bat

Modifica `backend/start.bat` per usare `venv_spleeter` invece di `venv`:

```batch
if exist venv_spleeter\Scripts\python.exe (
    echo ✅ Usando Python 3.10 dal venv_spleeter
    venv_spleeter\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
) else if exist venv\Scripts\python.exe (
    echo ✅ Usando Python dal venv
    venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
) else (
    echo ⚠️  Venv non trovato, uso Python di sistema
    python -m uvicorn main:app --host 0.0.0.0 --port 8001 --reload
)
```

### Metodo 2: Usa venv_spleeter solo per Spleeter

Mantieni il venv principale (3.13) per tutto il resto e usa `venv_spleeter` solo quando serve Spleeter.

---

## ✅ Verifica Funzionamento

Dopo l'installazione, verifica:

```powershell
.\venv_spleeter\Scripts\python.exe -c "from spleeter.separator import Separator; print('✅ Spleeter installato correttamente!')"
```

---

## 🔄 Alternative (se Python 3.10 non è disponibile)

### Opzione A: lite-spleeter (compatibile con Python 3.11+)

```powershell
pip install lite-spleeter
```

Poi modifica `backend/separation.py` per usare `lite-spleeter` invece di `spleeter`.

### Opzione B: torchspleeter (basato su PyTorch)

```powershell
pip install torchspleeter
```

### Opzione C: Usa metodi semplici (già implementato)

Il sistema già usa metodi semplici come fallback. Funzionano ma sono meno precisi.

---

## 📝 Note

- **Spleeter richiede ~100MB** per il modello (scaricato automaticamente al primo uso)
- **Separazione con Spleeter richiede 30-60 secondi** per file
- **Metodi semplici richiedono 1-3 secondi** ma sono meno precisi

---

## 🆘 Troubleshooting

### "No module named 'spleeter'"
- Verifica di essere nel venv corretto: `.\venv_spleeter\Scripts\Activate.ps1`
- Reinstalla: `pip install spleeter`

### "TensorFlow error"
- Spleeter richiede TensorFlow 2.12.1: `pip install tensorflow==2.12.1`

### "Numpy compatibility error"
- Spleeter richiede numpy < 1.24: `pip install "numpy<1.24.0"`

