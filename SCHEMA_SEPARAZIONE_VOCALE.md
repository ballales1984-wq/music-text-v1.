# 🎵 Schema Logico: Separazione Vocale Corretta

## PROBLEMA ATTUALE
- Il metodo `(L-R)/2` potrebbe estrarre la base strumentale invece della voce
- Non c'è separazione esplicita tra voce e base
- La base ritmica non viene analizzata separatamente

## SOLUZIONE PROPOSTA

### STEP 1: SEPARAZIONE CORRETTA
```
INPUT: Audio completo (L, R stereo)
  ↓
SEPARAZIONE:
  - VOCE ISOLATA = Canale centrale (L+R)/2 (voce tipicamente al centro)
  - BASE STRUMENTALE = Differenza o (L-R)/2 (strumenti ai lati)
  ↓
OUTPUT:
  - vocals.wav (solo voce)
  - instrumental.wav (solo base strumentale)
```

### STEP 2: ANALISI PARALLELA
```
VOCE ISOLATA                    BASE STRUMENTALE
  ↓                                    ↓
MODULO LINGUISTICO              MODULO RITMICO
  ↓                                    ↓
- Trascrizione Whisper          - Analisi BPM
- Analisi prosodia              - Pattern ritmico
- Fonemi/parole                 - Beat detection
- Intonazione                   - Timing
  ↓                                    ↓
RISULTATI LINGUISTICI           RISULTATI RITMICI
```

### STEP 3: INTEGRAZIONE
```
RISULTATI LINGUISTICI + RISULTATI RITMICI
  ↓
MODULO GENERAZIONE TESTO
  ↓
- Combina testo (da voce) con ritmo (da base)
- Adatta sillabe alle durate ritmiche
- Allinea accenti ai beat
- Genera testo finale che si adatta perfettamente
  ↓
TESTO FINALE GENERATO
```

## IMPLEMENTAZIONE

### Funzione `separate_vocals_and_instrumental()`
```python
def separate_vocals_and_instrumental(input_path, job_id, output_dir):
    """
    Separa correttamente voce e base strumentale.
    
    Returns:
        (vocal_path, instrumental_path)
    """
    # Carica audio stereo
    wav, sr = load_audio(input_path)
    
    if wav.shape[0] == 2:  # Stereo
        # VOCE = Canale centrale (L+R)/2
        vocals = (wav[0] + wav[1]) / 2
        
        # BASE = Differenza (L-R)/2 o meglio: mix completo - voce
        # Oppure usa solo un canale laterale
        instrumental = (wav[0] - wav[1]) / 2
        # Normalizza
    else:  # Mono
        # Per mono, usa filtri per separare frequenze
        # Voce: 80-8000 Hz
        # Base: resto
        vocals = apply_bandpass(wav, 80, 8000)
        instrumental = wav - vocals
    
    # Salva entrambi
    vocal_path = save_audio(vocals, f"{job_id}_vocals.wav")
    instrumental_path = save_audio(instrumental, f"{job_id}_instrumental.wav")
    
    return vocal_path, instrumental_path
```

### Pipeline Aggiornata
```python
# STEP 1: Separazione
vocal_path, instrumental_path = separate_vocals_and_instrumental(...)

# STEP 2: Analisi parallela
# Thread 1: Analisi linguistica (voce)
linguistic_results = {
    "transcription": transcribe_audio(vocal_path),
    "prosody": analyze_prosody(vocal_path),
    "phonemes": extract_phonemes(vocal_path)
}

# Thread 2: Analisi ritmica (base)
rhythmic_results = {
    "tempo": analyze_tempo(instrumental_path),
    "beats": detect_beats(instrumental_path),
    "rhythm_pattern": analyze_rhythm_pattern(instrumental_path)
}

# STEP 3: Integrazione
final_text = generate_lyrics(
    linguistic_data=linguistic_results,
    rhythmic_data=rhythmic_results
)
```

## VERIFICA CORRETTEZZA

### Test 1: Voce isolata
- Deve contenere principalmente frequenze vocali (80-8000 Hz)
- Deve essere trascrivibile con Whisper
- Deve avere prosodia chiara

### Test 2: Base strumentale
- NON deve contenere voce (o minimo)
- Deve avere pattern ritmico chiaro
- Deve avere BPM rilevabile

### Test 3: Integrazione
- Il testo generato deve adattarsi al ritmo della base
- Le sillabe devono allinearsi ai beat
- Gli accenti devono coincidere con i beat forti

