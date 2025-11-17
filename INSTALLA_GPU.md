# 🚀 Guida Installazione GPU per Accelerazione

## ⚡ Stato Attuale

Il codice è già configurato per usare GPU automaticamente quando disponibile.

**Stato GPU**: Non rilevata (CPU mode)

## 📋 Requisiti per GPU

1. **Scheda video NVIDIA** con supporto CUDA
2. **Driver NVIDIA** installati
3. **PyTorch con CUDA** installato

## 🔍 Verifica GPU

### 1. Verifica se hai GPU NVIDIA

Apri **Gestione Dispositivi** → **Schede video**
- Se vedi "NVIDIA ..." → hai GPU NVIDIA ✅
- Se vedi solo "Intel" o "AMD" → nessuna GPU NVIDIA ❌

### 2. Verifica Driver NVIDIA

```powershell
# Dovrebbe mostrare informazioni GPU
nvidia-smi
```

Se il comando non funziona, installa i driver NVIDIA da:
https://www.nvidia.com/Download/index.aspx

### 3. Verifica Versione CUDA

Dopo aver installato i driver, verifica CUDA:
```powershell
nvcc --version
```

## 📦 Installazione PyTorch con CUDA

### Opzione 1: CUDA 11.8 (Consigliato)

```bash
cd backend
.\venv\Scripts\Activate.ps1
pip uninstall torch torchaudio -y
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Opzione 2: CUDA 12.1

```bash
cd backend
.\venv\Scripts\Activate.ps1
pip uninstall torch torchaudio -y
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### Opzione 3: CUDA 12.4

```bash
cd backend
.\venv\Scripts\Activate.ps1
pip uninstall torch torchaudio -y
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
```

## ✅ Verifica Installazione

Dopo l'installazione, verifica:

```bash
python -c "import torch; print('CUDA:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

Dovresti vedere:
```
CUDA: True
Device: NVIDIA GeForce ...
```

## ⚡ Velocità con GPU

### Con GPU NVIDIA:
- **Whisper trascrizione**: 10-20 secondi (vs 1-2 minuti su CPU)
- **Speedup**: 5-10x più veloce

### File 2.5 minuti:
- **CPU**: ~2-5 minuti totali
- **GPU**: ~20-40 secondi totali ⚡

## 🔧 Se Non Hai GPU NVIDIA

Il sistema funziona comunque su CPU, ma sarà più lento.

**Alternative**:
1. Usa modello Whisper più piccolo (già configurato: "tiny")
2. Processa file più corti
3. Considera upgrade hardware

## 📝 Note

- Il sistema rileva automaticamente la GPU all'avvio
- Se GPU disponibile, la usa automaticamente
- Se GPU non disponibile, usa CPU (funziona comunque)
- I log mostrano quale device sta usando

## 🎯 Prossimi Passi

1. Verifica se hai GPU NVIDIA
2. Installa driver NVIDIA se necessario
3. Installa PyTorch con CUDA (vedi sopra)
4. Riavvia il backend
5. Verifica nei log che usi GPU

