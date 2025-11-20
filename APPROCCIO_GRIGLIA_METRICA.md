# 🎯 Nuovo Approccio: Griglia Metrica

## 📋 Concetto

L'app ora usa un approccio **semplice e diretto** basato su **griglia metrica**:

1. **Analizza la voce isolata** → Estrae timing, durata sillabe, accenti, pitch
2. **Trascrive** (anche se sbagliato/non ha significato in inglese)
3. **Crea una griglia temporale** con "slot" da riempire
4. **Identifica parole/frasi senza significato** in inglese
5. **Sostituisce** con frasi inglesi che si adattano alla griglia
6. **Genera testo finale** riempiendo gli spazi nella metrica

---

## 🔄 Pipeline Nuova

### Step 1.7: Analisi Audio Avanzata (NUOVO)
- Analizza voce isolata con `analyze_audio_features()`
- Estrae:
  - **Onset times** (quando iniziano le sillabe)
  - **Tempo** (BPM)
  - **Pitch contour** (altezza note)
  - **Prosodia** (stress, durata sillabe, pause)

### Step 3: Generazione con Griglia Metrica (NUOVO)

#### Se analisi audio disponibile → **Approccio Griglia Metrica**
1. **Crea griglia metrica** (`create_metric_grid_from_vocal()`)
   - Crea "slot" temporali per ogni sillaba
   - Ogni slot contiene:
     - Timing (start_time, end_time, duration)
     - Accento (forte/debole)
     - Pitch (opzionale)
     - Testo trascritto (anche sbagliato)
     - Validazione se è inglese valido
     - Numero di sillabe

2. **Genera testo** (`generate_text_from_grid()`)
   - Per ogni slot:
     - Se testo trascritto è inglese valido → mantieni
     - Se testo trascritto NON è inglese valido → sostituisci con:
       * Parola/frase inglese
       * Stesso numero di sillabe
       * Durata simile
       * Accento rispettato
   - Costruisce righe complete

3. **Risultato**: Testo che si adatta perfettamente alla metrica del cantato

#### Se analisi audio non disponibile → **Approccio Tradizionale**
- Usa il metodo precedente (AI linguistica con prompt avanzato)

---

## 📊 Struttura Griglia

```python
{
    "grid": [
        {
            "slot_index": 0,
            "start_time": 0.0,
            "end_time": 0.25,
            "duration": 0.25,
            "accent": 1,
            "pitch": 440.0,
            "transcribed_text": "la",
            "is_valid_english": False,
            "syllable_count": 1,
            "filled_text": "love"  # Dopo generazione
        },
        ...
    ],
    "lines": [
        {
            "line_index": 0,
            "slots": [0, 1, 2, 3, 4, 5, 6, 7],
            "start_time": 0.0,
            "end_time": 2.0,
            "total_syllables": 8
        },
        ...
    ]
}
```

---

## ✅ Vantaggi

1. **Semplice**: Non dipende da AI complessa per generare testo
2. **Preciso**: Rispetta esattamente timing e metrica
3. **Diretto**: Sostituisce solo ciò che non è inglese valido
4. **Veloce**: Non richiede generazione AI pesante
5. **Adattivo**: Si adatta automaticamente alla metrica del cantato

---

## 🔧 File Creati/Modificati

### Nuovo File
- `backend/metric_grid_generator.py` - Logica griglia metrica

### File Modificati
- `backend/main.py` - Integrato nuovo approccio nella pipeline

---

## 🎯 Come Funziona

### Esempio Pratico

**Input**: Voce che canta "la la la la" (4 sillabe, 1 secondo)

**Griglia creata**:
- Slot 0: 0.0s-0.25s, "la" → NON inglese valido → sostituito con "love"
- Slot 1: 0.25s-0.5s, "la" → NON inglese valido → sostituito con "time"
- Slot 2: 0.5s-0.75s, "la" → NON inglese valido → sostituito con "way"
- Slot 3: 0.75s-1.0s, "la" → NON inglese valido → sostituito con "day"

**Output**: "love time way day" (4 sillabe, stesso timing)

---

## 📝 Prossimi Miglioramenti

1. **Sostituzione più intelligente**: Usa AI per trovare frasi inglesi semanticamente appropriate
2. **Miglioramento parole valide**: Se parola è inglese ma sbagliata nel contesto, migliorarla
3. **Frasi invece di parole**: Sostituire con frasi complete che si adattano a più slot
4. **Validazione contesto**: Controllare che le parole sostituite formino frasi sensate

---

## 🧪 Test

Per testare:
1. Carica file audio con voce (anche "la la la")
2. Verifica che venga creata la griglia metrica
3. Controlla log per vedere sostituzioni
4. Verifica che testo generato rispetti timing e metrica

