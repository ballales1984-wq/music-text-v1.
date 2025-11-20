# 📊 Analisi Processo - Music Text Generator

## 🔍 Monitoraggio Processo in Corso

### Come Analizzare i Dati del Processo

#### 1. **Controllo File Caricati**
- **Cartella**: `backend/uploads/`
- **Formato**: `{job_id}.mp3` (o .wav, .m4a, .flac)
- **Info**: File audio originale caricato dall'utente

#### 2. **Controllo File Generati**
- **Cartella**: `backend/outputs/`
- **File generati**:
  - `{job_id}_vocals.wav` - Voce isolata
  - `{job_id}_instrumental.wav` - Base strumentale isolata

#### 3. **Stato Job (API)**
- **Endpoint**: `GET http://localhost:8001/status/{job_id}`
- **Risposta**:
```json
{
  "status": "processing" | "completed" | "error",
  "step": 0-4,
  "total_steps": 4,
  "current_step": "Descrizione step corrente",
  "progress": 0-100,
  "result": {...}  // Solo se completato
}
```

#### 4. **Log Backend**
I log vengono stampati nella console dove è avviato il backend. Cerca:
- `[job_id]` - Identificatore univoco del processo
- `✅` - Operazione completata
- `⚠️` - Warning
- `❌` - Errore
- `⏳` - In corso

---

## 📋 Pipeline di Processamento

### Step 0: Separazione Vocale (10% progress)
- **Input**: File audio originale
- **Output**: 
  - `{job_id}_vocals.wav` - Voce isolata
  - `{job_id}_instrumental.wav` - Base strumentale
- **Tempo**: 5-30 secondi (dipende da Spleeter o metodi semplici)

### Step 1: Trascrizione Whisper (20% progress)
- **Input**: Voce isolata
- **Output**: Testo trascritto (anche se sbagliato/non inglese)
- **Tempo**: 30-120 secondi (dipende dalla lunghezza)

### Step 1.5: Pulizia Testo (30% progress)
- **Input**: Testo trascritto grezzo
- **Output**: Testo pulito (rimozione ripetizioni)
- **Tempo**: < 1 secondo

### Step 1.7: Analisi Audio Avanzata (35% progress)
- **Input**: Voce isolata + Base strumentale
- **Output**: 
  - Features audio (pitch, timing, prosodia)
  - Features ritmiche (BPM, beat, pattern)
- **Tempo**: 5-15 secondi

### Step 2: Estrazione Struttura (60% progress)
- **Input**: Testo pulito + Features audio
- **Output**: 
  - Struttura testo (righe, strofe, chorus)
  - Conteggio sillabe per riga
  - Parole chiave
- **Tempo**: < 1 secondo

### Step 3: Generazione Testo (80-100% progress)
- **Input**: Tutti i dati precedenti
- **Output**: Testo generato in inglese
- **Metodi**:
  - **Griglia Metrica** (se analisi audio disponibile) - più preciso
  - **Tradizionale AI** (fallback) - più generico
- **Tempo**: 10-180 secondi (dipende da AI usata)

---

## 🔍 Come Analizzare i Dati

### 1. **Verifica File Generati**
```bash
# Controlla file caricati
dir backend\uploads\*.mp3

# Controlla file generati
dir backend\outputs\*_vocals.wav
dir backend\outputs\*_instrumental.wav
```

### 2. **Controlla Stato Job**
```bash
# Sostituisci {job_id} con l'ID reale
curl http://localhost:8001/status/{job_id}
```

### 3. **Analizza Log Backend**
Cerca nella console del backend:
- `[job_id] ✅` - Step completato
- `[job_id] ⚠️` - Warning (non critico)
- `[job_id] ❌` - Errore (critico)

### 4. **Verifica Risultati**
Una volta completato, il risultato contiene:
- `raw_transcription.text` - Testo trascritto grezzo
- `raw_transcription.cleaned_text` - Testo pulito
- `final_text` - Testo finale generato
- `lyrics_variants` - Varianti del testo
- `structure` - Struttura (righe, strofe)
- `syllables` - Conteggio sillabe
- `key_words` - Parole chiave

---

## 📊 Dati Analizzati

### Analisi Audio
- **Tempo (BPM)**: Velocità della canzone
- **Pitch Contour**: Altezza delle note
- **Onset Times**: Quando iniziano le sillabe
- **Prosodia**: Intonazione, enfasi, durata, pause

### Analisi Ritmica
- **BPM Base**: Tempo della base strumentale
- **Beat Pattern**: Pattern ritmico (regolare/variato)
- **Time Signature**: Firma temporale (4/4, 3/4, ecc.)

### Analisi Metrica
- **Sillabe Totali**: Numero totale di sillabe
- **Sillabe per Riga**: Distribuzione sillabe
- **Accenti**: Posizioni accenti forti
- **Struttura Dettagliata**: Analisi riga per riga

### Analisi Testo
- **Trascrizione**: Testo grezzo da Whisper
- **Pulizia**: Rimozione ripetizioni
- **Qualità**: Score qualità testo (0-100)
- **Parole Chiave**: Parole più importanti

---

## ⚠️ Problemi Comuni

### 1. **Processo Bloccato**
- **Sintomo**: Progress fermo, nessun log
- **Soluzione**: Controlla log backend per errori

### 2. **Trascrizione Vuota**
- **Sintomo**: `raw_transcription.text` vuoto
- **Causa**: Whisper non rileva voce
- **Soluzione**: Verifica che il file contenga voce

### 3. **Generazione Testo Fallita**
- **Sintomo**: `final_text` vuoto
- **Causa**: AI non disponibile o errore
- **Soluzione**: Verifica che almeno un'AI sia configurata

### 4. **Separazione Vocale Fallita**
- **Sintomo**: Nessun file `_vocals.wav` generato
- **Causa**: Spleeter non disponibile o errore
- **Soluzione**: Il sistema usa fallback (audio completo)

---

## 🎯 Prossimi Passi

1. **Monitora Progress**: Controlla `/status/{job_id}` ogni 500ms
2. **Verifica Log**: Controlla console backend per dettagli
3. **Analizza Risultati**: Una volta completato, esamina tutti i dati
4. **Ottimizza**: Usa i dati per migliorare la generazione

