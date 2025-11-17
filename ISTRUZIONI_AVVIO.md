# 🚀 Istruzioni Avvio Rapido

## Versione Definitiva 2.0.0

### ⚡ Avvio Automatico (Più Semplice)

1. **Doppio click** su `avvia_app.bat` (Windows)
   - Oppure `avvia_app.ps1` (PowerShell)
   - Oppure il collegamento sul desktop "Music Text Generator"

2. Attendi 5-10 secondi

3. Il browser si aprirà automaticamente su http://localhost:3000

---

### 📋 Avvio Manuale

#### Terminale 1 - Backend
```bash
cd backend
venv\Scripts\activate
python main.py
```

#### Terminale 2 - Frontend
```bash
cd frontend
npm run dev
```

Poi apri: http://localhost:3000

---

### 🔧 Build Eseguibile .exe

```bash
# Installa PyInstaller
pip install pyinstaller

# Build
cd backend
python build_exe.py
```

File creato: `backend/dist/MusicTextGenerator_Backend.exe`

---

### ✅ Verifica Funzionamento

1. Apri http://localhost:3000
2. Carica un file audio (MP3, WAV, M4A, FLAC)
3. Clicca "Processa Audio"
4. Attendi il processamento
5. Vedi 3 varianti di testo generate
6. Seleziona la variante preferita

---

### 🎯 Funzionalità

- ✅ Separazione vocale
- ✅ Analisi audio avanzata (pitch, timing, metrica)
- ✅ Trascrizione Whisper
- ✅ Generazione 3 varianti testo in inglese
- ✅ Selezione interattiva
- ✅ Download testo e audio

---

**Versione: 2.0.0 - DEFINITIVA E PERFETTA**

