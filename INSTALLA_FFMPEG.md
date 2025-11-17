# 🎬 Installazione FFmpeg (Opzionale)

FFmpeg è richiesto da Demucs per la separazione vocale avanzata. Se non è installato, l'app userà automaticamente un metodo fallback.

## ⚠️ Nota Importante

**L'app funziona anche senza FFmpeg!** Il sistema userà automaticamente un metodo alternativo (estrazione canale centrale) che funziona bene per molti file.

## 📥 Installazione FFmpeg (Opzionale, per risultati migliori)

### Metodo 1: Usando Chocolatey (Consigliato su Windows)

```powershell
# Installa Chocolatey se non ce l'hai
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Installa FFmpeg
choco install ffmpeg
```

### Metodo 2: Download Manuale

1. Vai su: https://ffmpeg.org/download.html
2. Scarica la versione Windows
3. Estrai l'archivio
4. Aggiungi la cartella `bin` al PATH di sistema

### Metodo 3: Usando pip (limitato)

```bash
pip install ffmpeg-python
```

**Nota**: Questo installa solo il wrapper Python, non FFmpeg stesso. Devi installare FFmpeg separatamente.

## ✅ Verifica Installazione

Dopo l'installazione, verifica con:

```powershell
ffmpeg -version
```

## 🎯 Quando Installare FFmpeg

- ✅ **Installa FFmpeg se**: Vuoi la migliore qualità di separazione vocale
- ❌ **Non serve se**: Il metodo fallback funziona bene per i tuoi file

## 🔄 Dopo l'Installazione

Riavvia il backend per usare Demucs con FFmpeg:

```bash
cd backend
.\venv\Scripts\Activate.ps1
python main.py
```

