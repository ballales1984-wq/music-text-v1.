# ⚡ Accelerazione GPU

## 🚀 Supporto GPU Implementato

Il sistema ora supporta automaticamente l'uso della GPU per accelerare il processamento.

### ✅ Cosa Usa GPU

1. **Whisper (Trascrizione)**: Usa GPU se disponibile
   - Velocità: **5-10x più veloce** su GPU
   - File 2.5 minuti: ~10-20 secondi (invece di 1-2 minuti)

2. **PyTorch/TorchAudio**: Supporto GPU automatico
   - Operazioni tensor su GPU quando disponibile

### 🔍 Verifica GPU

Per verificare se la GPU è disponibile:

```bash
cd backend
.\venv\Scripts\Activate.ps1
python -c "import torch; print('CUDA:', torch.cuda.is_available()); print('Device:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

### 📦 Installazione PyTorch con CUDA

Se la GPU non è rilevata, installa PyTorch con supporto CUDA:

#### Per CUDA 11.8:
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### Per CUDA 12.1:
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
```

#### Verifica versione CUDA:
```bash
nvidia-smi
```

### ⚡ Velocità Attese con GPU

#### File 2.5 minuti (con GPU):
- **Separazione vocale**: ~5-10 secondi
- **Whisper (prima volta)**: ~30-60 secondi (scarica modello)
- **Whisper trascrizione**: ~10-20 secondi ⚡ (vs 1-2 minuti su CPU)
- **Generazione testo**: ~5-10 secondi

**Totale**: ~50-100 secondi (prima volta), ~20-40 secondi (volte successive) ⚡

### 🎯 Ottimizzazioni Applicate

- **fp16 su GPU**: Usa precisione mezza (più veloce)
- **fp32 su CPU**: Usa precisione piena (più stabile)
- **Device automatico**: Rileva GPU e la usa automaticamente
- **Fallback CPU**: Se GPU non disponibile, usa CPU

### 📊 Confronto Velocità

| Operazione | CPU | GPU | Speedup |
|------------|-----|-----|---------|
| Whisper (tiny) | 1-2 min | 10-20 sec | **5-10x** |
| Whisper (base) | 2-3 min | 20-30 sec | **6-9x** |
| Separazione | 5-10 sec | 5-10 sec | ~1x |

### 💡 Note

- La GPU viene rilevata automaticamente all'avvio
- Se GPU non disponibile, usa CPU (funziona comunque)
- Il sistema mostra quale device sta usando nei log
- Per massima velocità, usa GPU NVIDIA con CUDA

