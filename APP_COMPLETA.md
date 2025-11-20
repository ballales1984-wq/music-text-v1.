# ✅ App Music Text Generator - COMPLETA

## 🎯 Funzionalità Principale

**Genera testo in inglese ascoltando la traccia vocale della canzone che carichi.**

### Pipeline Semplificata:
1. **Carica Audio** → File audio (MP3, WAV, M4A, FLAC)
2. **Isola Voce** → Separa voce dalla base strumentale
3. **Trascrive Voce** → Whisper ascolta e trascrive
4. **Genera Testo Inglese** → Ollama crea testo poetico unico

---

## ✅ Stato App

- ✅ **Backend**: In esecuzione su `http://localhost:8001`
- ✅ **Frontend**: In esecuzione su `http://localhost:3000`
- ✅ **Ollama**: Configurato e funzionante (llama3)
- ✅ **Memvid**: Integrato (opzionale - installa con `pip install memvid`)

---

## 🚀 Come Usare

### 1. Apri Frontend
```
http://localhost:3000
```

### 2. Carica una Canzone
- Clicca "Seleziona file audio"
- Scegli MP3, WAV, M4A o FLAC
- Clicca "Processa Audio"

### 3. Attendi Processamento
- **Step 1**: Isolamento voce (20%)
- **Step 2**: Trascrizione Whisper (50%)
- **Step 3**: Generazione testo inglese con Ollama (80%)

### 4. Risultati
- ✅ Voce isolata (audio)
- ✅ Base strumentale (audio)
- ✅ Trascrizione grezza
- ✅ **Testo finale in inglese** (unico per ogni canzone)

---

## 🎵 Caratteristiche

### Testi Unici
- ✅ Ogni canzone genera testo **DIVERSO**
- ✅ Basato sulla trascrizione specifica
- ✅ Usa parole chiave e tema della canzone
- ✅ Non usa più template generici

### Ollama Integrato
- ✅ Rilevamento automatico
- ✅ Usa llama3 (migliore qualità)
- ✅ Retry automatico se necessario
- ✅ Prompt ottimizzati per creatività

### Memoria Video (Opzionale)
- ✅ Salva automaticamente ogni testo generato
- ✅ Ricerca semantica nei testi salvati
- ✅ Chat con la memoria
- ✅ Storage ultra-compresso (50-100× più piccolo)

---

## 📁 Struttura File

```
music text/
├── backend/
│   ├── main_simple.py              # API semplificata
│   ├── lyrics_generator_simple.py  # Generatore con Ollama
│   ├── memory_manager.py           # Gestione memoria video
│   ├── separation.py               # Isolamento voce
│   ├── transcription.py            # Trascrizione Whisper
│   └── requirements.txt            # Dipendenze
├── frontend/
│   └── app/page.tsx                # Interfaccia React
└── README.md
```

---

## 🔧 API Endpoints

### Principali
- `POST /upload` - Carica e processa audio
- `GET /status/{job_id}` - Stato processamento
- `GET /audio/{job_id}` - Download audio originale
- `GET /audio/{job_id}/vocals` - Download voce isolata
- `GET /audio/{job_id}/instrumental` - Download base strumentale

### Memoria (Opzionale)
- `POST /memory/build` - Costruisce video memoria
- `GET /memory/search?query=testo` - Cerca nei testi
- `POST /memory/chat?query=domanda` - Chat con memoria

---

## ⚙️ Configurazione

### Ollama (Consigliato)
```bash
# Installa Ollama: https://ollama.ai
ollama pull llama3
```

### Memvid (Opzionale)
```bash
cd backend
pip install memvid
```

### OpenAI (Opzionale)
Crea `.env` in `backend/`:
```
OPENAI_API_KEY=sk-...
```

---

## 🎯 Risultato Atteso

Per ogni canzone processata:

1. **Voce Isolata** - Audio pulito della voce
2. **Base Strumentale** - Solo strumenti
3. **Trascrizione** - Quello che Whisper ha sentito
4. **Testo Inglese** - Testo poetico unico generato con Ollama

**Ogni canzone = Testo diverso e unico!**

---

## 📊 Performance

- **Separazione voce**: 1-60 secondi (dipende da Spleeter)
- **Trascrizione**: 10-60 secondi (dipende da durata)
- **Generazione testo**: 5-30 secondi (dipende da Ollama)
- **Totale**: ~1-3 minuti per canzone

---

## 🐛 Troubleshooting

### Ollama non rilevato
```bash
# Verifica che Ollama sia in esecuzione
ollama serve

# Verifica modelli
ollama list
```

### Testo sempre uguale
- Verifica nei log che Ollama venga usato
- Controlla che la trascrizione contenga testo
- Prova con canzoni diverse

### Memvid non disponibile
- L'app funziona anche senza memvid
- Per abilitare: `pip install memvid`
- Il salvataggio è opzionale

---

## 📝 Note Finali

- ✅ App **semplificata** e **focalizzata**
- ✅ **Testi unici** per ogni canzone
- ✅ **Ollama integrato** e funzionante
- ✅ **Memoria video** opzionale per ricerca
- ✅ **Pronta per l'uso**

---

**Versione**: 4.0.1-complete  
**Data**: 2025-01-27  
**Status**: ✅ COMPLETA E FUNZIONANTE

