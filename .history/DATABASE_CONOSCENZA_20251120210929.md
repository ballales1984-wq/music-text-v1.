# 🎵 Database Conoscenza - Pattern e Regole Metriche

## 🎯 Obiettivo

Creare un database con **memvid** che contiene:
1. **Frasi classiche** delle canzoni più comuni
2. **Struttura delle frasi** delle maggiori canzoni
3. **Regole metriche** per creare strofe e ritornelli
4. **Pattern strutturali** verse/chorus più usati

---

## 🔄 Come Funziona

### 1. Analisi Automatica

Ogni volta che processi una canzone, l'app **analizza automaticamente**:
- ✅ Frasi comuni (pattern come "I love you", "In the night", etc.)
- ✅ Struttura verse/chorus
- ✅ Lunghezza strofe e ritornelli
- ✅ Pattern metrici (sillabe, accenti)

### 2. Accumulo Pattern

I pattern vengono **accumulati** in memoria:
- Dopo 1 canzone: primi pattern
- Dopo 5 canzoni: pattern più comuni emergono
- Dopo 10+ canzoni: database ricco di conoscenza

### 3. Costruzione Database

Quando hai abbastanza canzoni analizzate, costruisci il database:

```bash
POST http://localhost:8001/knowledge/build
```

Questo crea:
- `memory/knowledge_base.mp4` - Video memoria con pattern
- `memory/knowledge_index.json` - Indice per ricerca

---

## 📊 Cosa Contiene il Database

### Frasi Comuni (Top 50)
- Pattern più frequenti nelle canzoni
- Esempi: "I love you", "In the night", "Every time", etc.
- Con conteggio occorrenze

### Pattern Strutturali
- Strutture verse/chorus più usate
- Esempi:
  - `Verse(2)-Chorus` (usato X volte)
  - `Verse(3)-Chorus` (usato Y volte)

### Regole Metriche
- Media sillabe per canzone
- Media sillabe per riga
- Pattern accenti comuni
- Lunghezza media strofe

### Esempi Struttura
- Prime 5 strutture analizzate
- Con dettagli verse/chorus

### Regole Songwriting
- Versi tipicamente 4-8 righe
- Chorus di solito 2-4 righe, ripetuto
- Ogni riga tipicamente 8-12 sillabe
- Accenti forti su battute 1 e 3 in 4/4

---

## 🚀 Come Usare

### Step 1: Processa Canzoni

Processa almeno 3-5 canzoni per avere pattern significativi:

```bash
# Carica canzoni tramite frontend o API
POST http://localhost:8001/upload
```

### Step 2: Verifica Statistiche

Controlla quante canzoni sono state analizzate:

```bash
GET http://localhost:8001/knowledge/stats
```

Risposta:
```json
{
  "stats": {
    "total_songs": 5,
    "total_phrases": 120,
    "total_structures": 5,
    "total_metrics": 5
  },
  "chunks_count": 150
}
```

### Step 3: Costruisci Database

Quando hai abbastanza dati:

```bash
POST http://localhost:8001/knowledge/build
```

Risposta:
```json
{
  "status": "success",
  "message": "Database conoscenza costruito con successo",
  "stats": {
    "total_songs": 5,
    "total_phrases": 120,
    "total_structures": 5
  },
  "chunks_count": 150
}
```

### Step 4: Cerca nel Database

Cerca pattern, frasi, regole:

```bash
# Cerca frasi comuni
GET http://localhost:8001/memory/search?query=common phrases in songs

# Cerca regole metriche
GET http://localhost:8001/memory/search?query=verse chorus structure rules

# Cerca pattern sillabe
GET http://localhost:8001/memory/search?query=syllable patterns
```

### Step 5: Chat con Database

Fai domande al database:

```bash
POST http://localhost:8001/memory/chat?query=What are the most common verse structures?
```

---

## 📝 Pattern Rilevati

### Pattern Frasi Comuni

L'app cerca automaticamente pattern come:

**Emotivi:**
- `I (love|want|need|feel|know|see|hear|think|believe)`
- `You (are|were|will|can|should|must|have|know)`
- `In the (night|day|dark|light|rain|sun|wind|storm)`

**Temporali:**
- `It's (time|a time|the time|my time|your time)`
- `When (I|you|we|they) (come|go|see|feel|know|think)`
- `Now (I|you|we|they) (know|see|feel|understand|believe)`

**Spaziali:**
- `Here (I|you|we|they) (am|are|stand|sit|wait|come)`
- `There (is|are|was|were|will be)`
- `Where (I|you|we|they) (go|come|stand|sit|wait)`

**Relazionali:**
- `With (you|me|us|them|him|her|love|hope|faith)`
- `Without (you|me|us|them|love|hope|faith|fear)`
- `Together (we|they|you and I) (are|will|can|must)`

**Azione:**
- `Let (me|us|it|them) (go|be|see|feel|know|try)`
- `Don't (stop|give|leave|forget|worry|cry)`
- `Can't (stop|give|leave|forget|see|feel|know)`

**Esistenziali:**
- `I'm (here|there|alive|free|lost|found|yours|mine)`
- `You're (here|there|mine|yours|alive|free|lost|found)`
- `We're (here|there|alive|free|together|apart)`

**Desiderio:**
- `I (wish|hope|dream|pray|want|need) (you|it|that|this)`
- `If (I|you|we|they) (could|would|should|might)`
- `Maybe (I|you|we|they) (can|will|should|could)`

---

## 🎯 Esempi di Ricerca

### Cercare Frasi Comuni

```bash
GET /memory/search?query=most common phrases in love songs
```

### Cercare Regole Metriche

```bash
GET /memory/search?query=how many syllables per line in verses
```

### Cercare Strutture

```bash
GET /memory/search?query=verse chorus structure patterns
```

### Chat con Database

```bash
POST /memory/chat?query=What are the rules for writing a good chorus?
```

---

## 📁 File Generati

Dopo la costruzione del database:

```
backend/
└── memory/
    ├── knowledge_base.mp4      # Video memoria con pattern
    ├── knowledge_index.json    # Indice per ricerca
    ├── lyrics_memory.mp4       # Video memoria testi (separato)
    └── lyrics_index.json       # Indice testi (separato)
```

---

## 🔄 Aggiornamento Database

Il database si aggiorna ogni volta che:
1. Processi nuove canzoni (pattern accumulati)
2. Chiami `/knowledge/build` (ricostruisce database)

**Consiglio**: Ricostruisci il database dopo ogni 5-10 nuove canzoni processate.

---

## 💡 Uso Pratico

### Scenario 1: Scrivere Nuova Canzone

1. Cerca pattern comuni: `GET /memory/search?query=common love song phrases`
2. Cerca struttura: `GET /memory/search?query=verse chorus structure`
3. Cerca regole metriche: `GET /memory/search?query=syllable count per line`
4. Usa i risultati per ispirazione

### Scenario 2: Analizzare Tendenze

1. Chat: `POST /memory/chat?query=What are the most common patterns in analyzed songs?`
2. Statistiche: `GET /knowledge/stats`
3. Ricerca: `GET /memory/search?query=trends in song structures`

### Scenario 3: Apprendimento

1. Processa 10+ canzoni di un genere
2. Costruisci database: `POST /knowledge/build`
3. Cerca pattern specifici del genere
4. Usa per generare testi nello stesso stile

---

## ⚙️ Configurazione

### Pattern Personalizzati

Puoi aggiungere pattern personalizzati in `song_patterns_analyzer.py`:

```python
COMMON_PHRASES_PATTERNS = [
    # Aggiungi qui i tuoi pattern
    r"Your custom pattern here",
    ...
]
```

### Dimensione Chunk

Modifica dimensione chunk in `memory_manager.py`:

```python
encoder = MemvidEncoder(chunk_size=512)  # Cambia qui
```

---

## 📊 Statistiche Esempio

Dopo 10 canzoni processate:

```json
{
  "stats": {
    "total_songs": 10,
    "total_phrases": 450,
    "total_structures": 10,
    "total_metrics": 10
  },
  "chunks_count": 200
}
```

---

## ✅ Checklist

- [ ] Processa almeno 3-5 canzoni
- [ ] Verifica statistiche: `GET /knowledge/stats`
- [ ] Costruisci database: `POST /knowledge/build`
- [ ] Testa ricerca: `GET /memory/search?query=test`
- [ ] Testa chat: `POST /memory/chat?query=test`

---

**Versione**: 1.0.0  
**Data**: 2025-01-27  
**Status**: ✅ Funzionante

