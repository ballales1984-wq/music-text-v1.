# 🎵 Pipeline "Stile Beatles" - Documentazione Completa

## Panoramica

Questa pipeline implementa un sistema professionale per:
1. **Isolare la voce** dal mix completo (source separation)
2. **Analizzare la voce** per estrarre pattern metrici, pitch, ritmo
3. **Generare nuovo testo in inglese** che segue esattamente la metrica della melodia originale

**NON trascrive le parole esistenti** - crea nuovo testo che si adatta perfettamente alla melodia.

---

## Architettura Pipeline (7 Step)

### Step 1: Separazione Vocale
- **Input**: File audio completo (voce + strumenti + rumore)
- **Metodo**: 
  - Priorità: Spleeter (ML model, qualità migliore)
  - Fallback: Metodi semplici (filtri frequenza + differenza canali)
- **Output**: `vocals.wav` (voce isolata), `instrumental.wav` (base strumentale)

### Step 2: Denoise Vocale (NUOVO)
- **Input**: `vocals.wav`
- **Metodo**: `noisereduce` (rimozione rumore, click, hum)
- **Output**: `vocals_clean.wav` (voce pulita per analisi migliore)

### Step 3: Analisi Linguistica (Voce Pulita)
- **Input**: `vocals_clean.wav`
- **Estrae**:
  - Pitch (altezza note) - CREPE o Librosa
  - Prosodia (intonazione, enfasi, durata, pause, dinamica)
  - Melodia (contorno melodico)
- **Output**: `audio_features` (dizionario con tutte le features)

### Step 4: Analisi Ritmica (Base Strumentale)
- **Input**: `instrumental.wav`
- **Estrae**:
  - BPM (tempo)
  - Beat positions
  - Rhythm pattern (regolare/variato)
  - Time signature
- **Output**: `rhythmic_features`

### Step 5: Analisi Metrica (NUOVO - Stile Beatles)
- **Input**: `audio_features` + `rhythmic_features`
- **Estrae**:
  - Numero sillabe (da onset detection)
  - Pattern accenti (ogni 4 beat = accento forte)
  - Durata note/sillabe
- **Metodo**: 
  - Stima sillabe da `onset_times`
  - Pattern accenti basato su posizione nel ciclo di 4 beat
  - CMUdict per validazione conteggio sillabe
- **Output**: `metric_pattern` (sillabe, accenti, time signature)

### Step 6: Trascrizione Whisper (Voce Pulita)
- **Input**: `vocals_clean.wav`
- **Metodo**: OpenAI Whisper (per riferimento, non per generazione)
- **Output**: `transcription` (testo grezzo, fonemi, confidence)

### Step 7: Generazione Testo Metrico (NUOVO)
- **Input**: `transcription` + `audio_features` + `rhythmic_features` + `metric_pattern`
- **Metodo**:
  - Priorità: Ollama/OpenAI con prompt che include pattern metrico
  - Fallback: Generazione diretta con CMUdict
- **Requisiti critici**:
  - **Numero esatto di sillabe** (da `metric_pattern`)
  - **Accenti forti nelle posizioni corrette** (da `metric_pattern`)
  - **Rispetto del ritmo e fraseggio** (da `rhythmic_features`)
  - **Adattamento alla melodia** (da `audio_features`)
- **Output**: Testo in inglese che segue perfettamente la metrica

---

## Componenti Tecnici

### 1. Separazione Vocale (`backend/separation.py`)

**Metodi disponibili**:
- **Spleeter** (ML model, qualità migliore)
  - Modello: `spleeter:2stems` (vocals + accompaniment)
  - Richiede: `spleeter>=2.3.0`
  - Tempo: 30-60s per file medio
  
- **Metodi semplici** (fallback)
  - Stereo: `vocals = (L-R)/2`, `instrumental = (L+R)/2 - vocals`
  - Mono: Filtri frequenza (80-8000 Hz per voce)
  - Tempo: <5s

**Configurazione**:
```bash
# Disabilita Spleeter (usa metodi veloci)
export USE_SPLEETER=false
```

### 2. Denoise (`backend/denoise.py`)

**Metodo**: `noisereduce.reduce_noise()`
- Rimozione rumore non stazionario (voce)
- Spectral gating
- Normalizzazione automatica

**Dipendenze**: `noisereduce>=2.0.0`

### 3. Analisi Metrica (`backend/metric_analysis.py`)

**Funzioni principali**:

```python
# Stima sillabe e accenti
n_syllables, accents = estimate_syllables_from_onsets(onset_times, tempo)

# Analisi pattern metrico completo
metric_pattern = analyze_metric_pattern(audio_features)

# Generazione testo metrico (fallback diretto)
lyrics = generate_metric_lyrics(n_syllables, accents, pitch_contour)
```

**Pattern accenti**:
- Ogni 4 beat = accento forte (stile 4/4)
- Calcolato da posizione nel ciclo ritmico

**CMUdict**:
- Conteggio sillabe preciso
- Validazione parole
- Fallback a parole comuni se CMUdict non disponibile

### 4. Generazione Testi (`backend/lyrics_generator.py`)

**Priorità**:
1. **Ollama** (locale, modelli: llama3.2, mistral)
   - Prompt include pattern metrico esatto
   - Timeout: 30s (fallback veloce se lento)
   
2. **OpenAI** (API, richiede chiave)
   - GPT-3.5-turbo o GPT-4-mini
   - Prompt con requisiti metrici
   
3. **Fallback metrico diretto** (CMUdict)
   - Genera parole con numero esatto di sillabe
   - Rispetta pattern accenti
   - Veloce e funzionante offline

**Prompt template** (per LLM):
```
METRIC PATTERN (CRITICAL - must follow exactly):
- Total syllables: {syllable_count}
- Strong accents: {strong_beats} (positions: {accent_positions})
- Time signature: {time_signature}
- Accent pattern: {accents}

IMPORTANT: Generate English lyrics that:
1. Have EXACTLY {syllable_count} syllables total
2. Place strong accents on syllables at positions {accent_positions}
3. Follow the rhythm and phrasing of the original melody
4. Sound natural and poetic in English
```

---

## Installazione Dipendenze

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

**Dipendenze principali**:
- `spleeter>=2.3.0` - Separazione vocale ML
- `noisereduce>=2.0.0` - Denoise
- `pronouncing>=0.2.0` - CMUdict (conteggio sillabe)
- `librosa>=0.11.0` - Analisi audio
- `crepe>=0.0.14` - Pitch detection avanzata
- `openai-whisper>=20231117` - Trascrizione
- `requests>=2.31.0` - Ollama API

---

## Utilizzo

### Backend
```bash
cd backend
python main.py
# Server su http://localhost:8000
```

### Frontend
```bash
cd frontend
npm run dev
# UI su http://localhost:3000
```

### API Endpoint
```bash
POST /upload
# Carica file audio, riceve job_id

GET /status/{job_id}
# Stato processamento (progress, step corrente)

GET /results/{job_id}/vocal
# Download voce isolata

GET /results/{job_id}/vocal_clean
# Download voce pulita (denoise)

GET /results/{job_id}/instrumental
# Download base strumentale
```

---

## Note Pratiche

### Qualità Tecnica
- **Demucs**: Se disponibile (richiede FFmpeg), qualità migliore di Spleeter
- **Pitch extraction**: `crepe` è più accurato di `librosa.yin`
- **Denoise**: `noisereduce` è semplice; per risultati professionali valuta iZotope RX
- **LLM remoti**: OpenAI GPT-4-mini offre qualità migliore per testi metrici

### Performance
- **Separazione Spleeter**: 30-60s per file medio (primo uso: download modello ~100MB)
- **Denoise**: <5s
- **Analisi metrica**: <2s
- **Generazione testi**: 5-30s (dipende da LLM)

### Avvertimenti Etici
- **Copyright**: Non usare per distribuire remix o estrazioni vocali di brani protetti senza autorizzazione
- **Uso creativo**: Va bene per studio, ricerca, esercizi di songwriting o demo personali
- **Bias linguistici**: CMUdict è centrato sull'inglese americano
- **LLM remoti**: I dati inviati (pattern metrico, testi) vengono processati da terzi

---

## Esempio Output

**Input**: `demo.mp3` (voce + strumenti)

**Output**:
- `vocals.wav` - Voce isolata
- `vocals_clean.wav` - Voce pulita (denoise)
- `instrumental.wav` - Base strumentale
- `lyrics.txt` - Testo generato che segue la metrica

**Metric Pattern rilevato**:
```
Syllables: 24
Strong accents: 6 (positions: 0, 4, 8, 12, 16, 20)
Time signature: 4/4
Tempo: 120 BPM
```

**Testo generato**:
```
Love in the night
Time passes by
Dreaming of light
Under the sky

(Chorus)
Singing with the melody
Feeling free, feeling free
```

---

## Miglioramenti Futuri

1. **Demucs integration**: Aggiungere supporto Demucs (richiede FFmpeg)
2. **Pitch-aware generation**: Usare pitch contour per suggerire tono emotivo
3. **Multi-language**: Estendere CMUdict ad altre lingue
4. **Real-time processing**: Chunking per file molto lunghi
5. **GPU acceleration**: Ottimizzazione per CUDA/ROCm

---

## Riferimenti

- **Spleeter**: https://github.com/deezer/spleeter
- **Demucs**: https://github.com/facebookresearch/demucs
- **CMUdict**: http://www.speech.cs.cmu.edu/cgi-bin/cmudict
- **Librosa**: https://librosa.org/
- **Noisereduce**: https://github.com/timsainb/noisereduce

