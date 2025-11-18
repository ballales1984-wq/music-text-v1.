# 🚀 Eseguibile Backend - Music Text Generator

## Creazione Eseguibile

### Metodo 1: Script Automatico (Consigliato)
```bash
cd backend
build_exe.bat
```

### Metodo 2: Manuale
```bash
cd backend
pip install pyinstaller
pyinstaller --onefile --name=music-text-generator-backend main.py
```

## ⚠️ Note Importanti

1. **Dimensione**: L'eseguibile sarà grande (~500MB-1GB) perché include:
   - PyTorch
   - Whisper model
   - Tutte le dipendenze Python

2. **Prima Esecuzione**: Potrebbe essere lenta (caricamento modelli)

3. **Dipendenze**: L'eseguibile è standalone, non richiede Python installato

4. **Configurazione**: 
   - Crea le directory `uploads/` e `outputs/` nella stessa cartella dell'exe
   - L'exe si avvia automaticamente su `http://0.0.0.0:8000`

## 🎯 Uso

1. Esegui `music-text-generator-backend.exe`
2. Apri browser su `http://localhost:8000`
3. Il frontend deve essere avviato separatamente (Next.js)

## 📦 Versione
- **Versione**: 3.0.0-simple
- **Data Build**: Vedi commit git

