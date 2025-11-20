# 📊 Analisi Completa - Music Text Generator

## 🎯 Scopo Principale

**Music Text Generator** è un'applicazione che:
1. **Isola la voce** da brani musicali completi (separazione vocale)
2. **Trascrive** i suoni vocali usando Whisper (anche se sono solo "la la la" o fonemi)
3. **Genera testo in inglese** che si adatta perfettamente alla melodia, ritmo e metrica originale

### Caso d'uso principale
- Hai una canzone strumentale con voce (anche senza parole chiare)
- Vuoi generare testo in inglese che si adatta perfettamente alla melodia vocale
- Il testo generato deve rispettare: pitch, timing, ritmo, metrica, sillabe

---

## 🔄 Pipeline Completa

### STEP 0: Separazione Vocale
**File**: `backend/separation.py`
- **Input**: File audio completo (MP3, WAV, M4A, FLAC)
- **Processo**: 
  - Usa **Spleeter** (ML) se disponibile per separazione professionale
  - Fallback a metodi semplici (estrazione canale centrale) se Spleeter non disponibile
- **Output**: 
  - `{job_id}_vocals.wav` - Traccia vocale isolata
  - `{job_id}_instrumental.wav` - Base strumentale isolata

### STEP 1: Trascrizione Whisper
**File**: `backend/transcription.py`
- **Input**: Traccia vocale isolata
- **Processo**:
  - Usa **OpenAI Whisper** per speech-to-text
  - Supporta chunking automatico per file lunghi (>30s)
  - Rileva lingua automaticamente
  - Estrae fonemi approssimativi
- **Output**:
  - Testo trascritto (parole o fonemi se "la la la")
  - Lingua rilevata
  - Confidence score
  - Segmenti temporali

### STEP 1.5: Pulizia Testo
**File**: `backend/text_cleaner.py`
- **Input**: Testo trascritto grezzo
- **Processo**:
  - Rimuove ripetizioni eccessive (mantiene max 2 occorrenze per frase)
  - Identifica chorus probabili (frasi ripetute 3+ volte)
  - Migliora grammatica base (capitalizzazione, punteggiatura)
  - Valida qualità testo
- **Output**:
  - Testo pulito
  - Statistiche pulizia (ripetizioni rimosse, riduzione %)

### STEP 2: Analisi Struttura e Metrica
**File**: 
- `backend/text_structure.py` - Estrae struttura dal testo
- `backend/audio_structure_analysis.py` - Analizza struttura audio
- `backend/syllable_counter.py` - Conta sillabe

**Processo**:
1. **Struttura Testo**:
   - Divide in righe/frasi
   - Identifica pattern ripetitivi (ritornello)
   - Organizza in strofe

2. **Struttura Audio**:
   - Analizza profilo di intensità/energia
   - Identifica ritornello (segmenti ad alta intensità ripetitivi)
   - Identifica strofe (segmenti con pattern simili)
   - Estrae intervalli approssimativi per parole (onset detection)

3. **Conteggio Sillabe**:
   - Usa `pronouncing` (CMUdict) se disponibile
   - Fallback a euristica (conta vocali)
   - Calcola sillabe per riga e totali

4. **Parole Chiave**:
   - Estrae parole più frequenti (esclusi stopwords)

**Output**:
- Struttura (strofe, ritornello, righe totali)
- Sillabe totali e per riga
- Parole chiave
- Struttura audio (timing ritornello/strofe)

### STEP 3: Generazione Testo AI
**File**: `backend/lyrics_generator.py`
- **Input**: 
  - Testo trascritto (pulito)
  - Struttura (strofe/ritornello)
  - Sillabe (totali e per riga)
  - Parole chiave
  - Struttura audio (timing, intensità)

- **Processo**:
  1. Crea prompt avanzato con:
     - Testo originale trascritto
     - Struttura (righe, strofe, ritornello)
     - Sillabe per riga (CRITICO - deve rispettare esattamente)
     - Parole chiave
     - Informazioni audio (timing, intensità)
  
  2. Genera 3 varianti usando:
     - **Ollama** (llama3.2) - PRIORITÀ, locale e gratuito
     - **OpenAI GPT-3.5** - Opzionale, richiede API key
     - **Fallback locale** - Se AI non disponibile, rimodella testo esistente

  3. Ogni variante ha stile diverso:
     - Variante 1: Energetica e potente
     - Variante 2: Emotiva e profonda
     - Variante 3: Romantica e tenera

- **Output**:
  - 3 varianti di testo in inglese
  - Ogni variante con versi e chorus separati
  - Testo che rispetta sillabe e struttura originale

---

## 🎨 Frontend

**File**: `frontend/app/page.tsx`

### Funzionalità UI:
1. **Upload File Audio**
   - Supporta MP3, WAV, M4A, FLAC
   - Validazione formato

2. **Monitoraggio Progresso**
   - Barra progresso in tempo reale
   - Step corrente (Separazione → Trascrizione → Analisi → Generazione)
   - Percentuale completamento

3. **Visualizzazione Risultati**:
   - **Audio Originale** - Riproducibile e scaricabile
   - **Traccia Vocale Isolata** - Riproducibile e scaricabile
   - **Base Strumentale** - Riproducibile e scaricabile
   - **Trascrizione Grezza** - Testo originale trascritto
   - **Testo Pulito** - Dopo rimozione ripetizioni
   - **Analisi Metrica** - Sillabe, accenti, time signature, struttura riga per riga
   - **Analisi Ritmica** - BPM, beat, pattern ritmico
   - **Analisi Prosodia** - Intonazione, enfasi, pause, dinamica, vibrato
   - **Statistiche Pulizia** - Ripetizioni rimosse, qualità testo
   - **3 Varianti Testo** - Selezione interattiva
   - **Download** - Testo e audio

---

## ✅ Cosa Testare

### Test Funzionali

#### 1. Separazione Vocale
- [ ] File con voce chiara → Voce isolata di buona qualità
- [ ] File con voce mista → Voce isolata accettabile
- [ ] File solo strumentale → Gestione errore corretta
- [ ] File molto lungo (>5 min) → Processamento completo
- [ ] Formati diversi (MP3, WAV, M4A, FLAC) → Tutti funzionano

#### 2. Trascrizione Whisper
- [ ] Voce con parole chiare → Trascrizione accurata
- [ ] Voce con "la la la" → Rileva fonemi/suoni
- [ ] Voce in inglese → Lingua rilevata correttamente
- [ ] Voce in altra lingua → Lingua rilevata, testo generato in inglese
- [ ] File lungo (>30s) → Chunking automatico funziona
- [ ] Voce molto bassa/rumorosa → Gestione corretta

#### 3. Pulizia Testo
- [ ] Testo con molte ripetizioni → Rimozione corretta
- [ ] Chorus ripetuto 3+ volte → Mantiene 2 occorrenze
- [ ] Testo già pulito → Nessuna modifica eccessiva
- [ ] Testo molto corto (<10 caratteri) → Gestione corretta

#### 4. Analisi Struttura
- [ ] Testo con strofe chiare → Struttura identificata
- [ ] Testo con ritornello → Ritornello identificato
- [ ] Audio con pattern intensità → Struttura audio identificata
- [ ] Conteggio sillabe → Accurate per parole inglesi
- [ ] Parole chiave → Estratte correttamente

#### 5. Generazione Testo
- [ ] Con Ollama disponibile → Genera 3 varianti
- [ ] Con OpenAI disponibile → Genera 3 varianti
- [ ] Senza AI (fallback) → Rimodella testo esistente
- [ ] Varianti diverse → Stili diversi (energetica, emotiva, romantica)
- [ ] Rispetto sillabe → Testo generato rispetta sillabe per riga
- [ ] Rispetto struttura → Mantiene strofe/ritornello

#### 6. Frontend
- [ ] Upload file → Funziona correttamente
- [ ] Progress bar → Aggiorna in tempo reale
- [ ] Visualizzazione risultati → Tutte le sezioni visibili
- [ ] Selezione variante → Cambia testo visualizzato
- [ ] Download → File scaricati correttamente
- [ ] Errori → Messaggi chiari all'utente

### Test di Performance

- [ ] File 30s → Processamento < 2 minuti
- [ ] File 3 min → Processamento < 5 minuti
- [ ] File 5+ min → Processamento completo senza crash
- [ ] Memoria → Non supera limiti sistema
- [ ] CPU → Utilizzo ragionevole

### Test di Robustezza

- [ ] File corrotto → Gestione errore corretta
- [ ] File troppo grande → Messaggio appropriato
- [ ] Backend non disponibile → Messaggio chiaro
- [ ] Timeout → Gestione corretta
- [ ] Interruzione → Pulizia risorse

---

## 🚀 Cosa Migliorare

### Priorità Alta

#### 1. **Qualità Separazione Vocale**
- [ ] Migliorare fallback quando Spleeter non disponibile
- [ ] Aggiungere opzione per forzare metodo (Spleeter vs semplice)
- [ ] Post-processing vocale (denoise opzionale)

#### 2. **Accuratezza Trascrizione**
- [ ] Supporto per modelli Whisper più grandi (small, medium) come opzione
- [ ] Migliorare chunking per file molto lunghi
- [ ] Gestione meglio di voci molto basse/rumorose

#### 3. **Generazione Testo AI**
- [ ] Migliorare prompt per rispettare meglio sillabe
- [ ] Aggiungere validazione sillabe dopo generazione
- [ ] Opzione per regolare "creatività" vs "aderenza" al testo originale
- [ ] Supporto per più modelli Ollama (mistral, llama2, ecc.)

#### 4. **Analisi Metrica**
- [ ] Migliorare rilevamento accenti forti
- [ ] Analisi metrica più precisa (stile Beatles)
- [ ] Validazione che testo generato rispetta metrica

### Priorità Media

#### 5. **UI/UX**
- [ ] Preview audio durante upload
- [ ] Visualizzazione waveform
- [ ] Confronto varianti side-by-side
- [ ] Editor testo per modifiche manuali
- [ ] Export in formati diversi (TXT, DOCX, SRT per karaoke)

#### 6. **Performance**
- [ ] Caching modelli Whisper
- [ ] Processamento parallelo dove possibile
- [ ] Ottimizzazione memoria per file grandi
- [ ] Progress più dettagliato (sotto-step)

#### 7. **Funzionalità Aggiuntive**
- [ ] Supporto multi-lingua per generazione (non solo inglese)
- [ ] Opzione per mantenere lingua originale
- [ ] Export karaoke (testo sincronizzato con timing)
- [ ] Batch processing (più file insieme)
- [ ] API per integrazione esterna

### Priorità Bassa

#### 8. **Documentazione**
- [ ] Guida utente completa
- [ ] Video tutorial
- [ ] Esempi di utilizzo
- [ ] Troubleshooting guide

#### 9. **Testing**
- [ ] Test automatici (unit test)
- [ ] Test integrazione
- [ ] Test end-to-end
- [ ] Suite test con file audio di esempio

#### 10. **Deployment**
- [ ] Docker container
- [ ] Build eseguibile migliorato
- [ ] Installer Windows/Mac/Linux
- [ ] Cloud deployment (opzionale)

---

## 🔧 Configurazione Attuale

### Backend
- **Porta**: 8001 (cambiata da 8000 per evitare conflitti)
- **Framework**: FastAPI
- **Python**: 3.8+
- **Dipendenze**: Vedi `backend/requirements.txt`

### Frontend
- **Porta**: 3000
- **Framework**: Next.js 14
- **React**: 18.2
- **TypeScript**: 5.0

### AI Models
- **Whisper**: tiny (default), supporta altri modelli
- **Ollama**: llama3.2 (default), configurabile
- **OpenAI**: GPT-3.5-turbo (opzionale)

---

## 📝 Note Importanti

1. **L'app genera SEMPRE testo in inglese**, anche se l'audio è in altra lingua
2. **Il testo generato deve rispettare sillabe e metrica** della melodia originale
3. **3 varianti** vengono sempre generate per dare scelta all'utente
4. **Fallback locale** funziona anche senza Ollama/OpenAI (rimodella testo esistente)
5. **Separazione vocale** può fallire su mix complessi (usa fallback semplice)

---

## 🎯 Obiettivo Finale

Creare un'app che permetta di:
- Caricare qualsiasi brano musicale con voce
- Ottenere automaticamente testo in inglese che si adatta perfettamente alla melodia
- Avere 3 varianti tra cui scegliere
- Scaricare testo e audio processato

**Use case principale**: Hai una melodia vocale (anche senza parole) e vuoi testo in inglese che ci si adatta perfettamente.

