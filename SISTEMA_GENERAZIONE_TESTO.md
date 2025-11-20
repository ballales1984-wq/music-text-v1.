# 🎵 Sistema di Generazione Testo - Versione Migliorata

## 🎯 Obiettivo

L'app ora genera testo in inglese **ascoltando la canzone** e scrivendo il testo che corrisponde a quello che viene cantato, considerando:
- **Musica completa** (base strumentale + voce)
- **Contesto musicale** (BPM, ritmo, mood, energia)
- **Tema della canzone** (rilevato automaticamente)
- **Metrica precisa** (timing, durata sillabe, accenti)

---

## 🔄 Pipeline Migliorata

### 1. Analisi Completa

#### Voce Isolata
- **Pitch** (altezza note)
- **Timing** (onset times - quando iniziano le sillabe)
- **Durata sillabe** (quanto dura ogni sillaba)
- **Accenti** (forte/debole)
- **Prosodia** (intonazione, enfasi, pause)

#### Base Strumentale
- **BPM** (tempo)
- **Pattern ritmico** (regolare/variato)
- **Beat forti** (accenti)
- **Time signature** (4/4, 3/4, ecc.)

### 2. Creazione Griglia Metrica

La griglia contiene **slot temporali** per ogni sillaba:
```python
{
    "slot_index": 0,
    "start_time": 0.0,
    "end_time": 0.25,
    "duration": 0.25,
    "accent": 1,
    "pitch": 440.0,
    "transcribed_text": "la",  # Anche se sbagliato
    "is_valid_english": False,
    "syllable_count": 1
}
```

### 3. Analisi Contesto Musicale

Il sistema analizza:
- **Tempo**: Fast (>140 BPM), Medium (100-140), Slow (<100)
- **Mood**: Romantic, Sad, Happy, Energetic, Powerful
- **Energy**: High, Medium, Low
- **Tema**: Love, Loss, Hope, Freedom, Struggle, Celebration

### 4. Rilevamento Tema

Analizza il testo trascritto per rilevare il tema:
- Cerca parole chiave (love, pain, hope, free, fight, party)
- Combina con mood musicale
- Determina tema principale della canzone

### 5. Generazione Testo per Righe

**Per ogni riga della canzone**:

1. **Se testo trascritto è inglese valido**:
   - Controlla se sillabe corrispondono
   - Se sì → mantieni
   - Se no → migliora con AI nel contesto

2. **Se testo trascritto NON è inglese valido**:
   - Genera nuova riga usando AI con:
     * Contesto musicale completo
     * Tema della canzone
     * Righe precedenti (per coerenza)
     * Sillabe esatte richieste
     * Timing e durata

---

## 🤖 Prompt AI Migliorato

Il prompt ora dice esplicitamente all'AI:

```
"You are listening to a song and writing the English lyrics that match what you hear.

MUSICAL CONTEXT - What you're hearing:
- Song theme: love
- Musical tempo: 120 BPM (medium speed)
- Mood/emotion: romantic
- Energy level: medium
- This line duration: 2.5 seconds

CRITICAL: You are WRITING THE LYRICS FOR THE SONG YOU'RE LISTENING TO.
The lyrics must match:
- The melody (pitch and notes you hear)
- The rhythm (timing and beat)
- The emotion (how it's being sung)
- The theme (love)
```

---

## 📊 Contesto Musicale

Il sistema crea un contesto completo:

```python
{
    "tempo": 120,
    "tempo_category": "medium",
    "mood": "romantic",
    "energy": "medium",
    "rhythm_style": "regular",
    "song_theme": "love"
}
```

Questo contesto viene passato all'AI per generare testo appropriato.

---

## 🎯 Coerenza Narrativa

Il sistema ora:
- **Traccia righe precedenti** per ogni nuova riga generata
- **Passa contesto narrativo** all'AI
- **Genera righe coerenti** che formano una canzone completa
- **Rispetta posizione** (prima riga = opening, ultima = conclusion)

---

## ✅ Vantaggi del Nuovo Sistema

1. **Ascolta la canzone**: Analizza musica completa (voce + strumenti)
2. **Rileva tema automaticamente**: Capisce di cosa parla la canzone
3. **Genera testo coerente**: Righe che formano una canzone completa
4. **Rispetta metrica perfettamente**: Sillabe, timing, accenti esatti
5. **Adattivo**: Si adatta al mood e energia della musica

---

## 🔧 File Modificati

- `backend/metric_grid_generator.py` - Sistema completo migliorato
- `backend/main.py` - Integrazione analisi base strumentale

---

## 🧪 Come Testare

1. Carica file audio con voce (anche "la la la")
2. Il sistema:
   - Analizza voce e base strumentale
   - Crea griglia metrica
   - Rileva tema
   - Genera testo riga per riga
3. Verifica che:
   - Testo corrisponda al tema rilevato
   - Righe siano coerenti tra loro
   - Sillabe corrispondano alla metrica
   - Testo si adatti alla musica

---

## 📝 Esempio

**Input**: Canzone con voce che canta "la la la" su base strumentale 120 BPM, mood romantico

**Processo**:
1. Analizza: BPM=120, mood=romantic, tema=love
2. Crea griglia: 8 slot, 2 righe da 4 sillabe ciascuna
3. Genera:
   - Riga 1: "I love you more each day" (4 sillabe)
   - Riga 2: "Together we will stay" (4 sillabe)

**Output**: Testo coerente che si adatta perfettamente alla metrica e al tema della canzone.

