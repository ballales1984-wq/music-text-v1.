# 🎬 Integrazione Memvid - Memoria Video dei Testi Generati

## 📋 Cosa fa

Memvid salva tutti i testi generati in un **video MP4** compresso, permettendo:
- ✅ **Ricerca semantica** nei testi generati
- ✅ **Chat con la memoria** dei testi
- ✅ **Storage ultra-compresso** (50-100× più piccolo di database vettoriali)
- ✅ **Ricerca in millisecondi** anche con milioni di testi

---

## 🚀 Installazione

```bash
cd backend
pip install memvid
```

**Nota**: L'installazione include:
- `memvid` - Libreria principale
- `faiss-cpu` - Ricerca vettoriale (18.7 MB)
- `opencv-python` - Elaborazione video
- `sentence-transformers` - Embeddings semantici

---

## 🔧 Come Funziona

### 1. Salvataggio Automatico

Ogni volta che generi testo da una canzone, viene **automaticamente salvato** nella memoria:

```python
# Automatico in main_simple.py
save_lyrics_to_memory(job_id, transcription, final_text, metadata)
```

### 2. Costruzione Video Memoria

Dopo aver processato alcune canzoni, costruisci il video memoria:

```bash
# Via API
curl -X POST http://localhost:8001/memory/build

# Oppure in Python
from memory_manager import build_memory_video
build_memory_video()
```

### 3. Ricerca nei Testi

Cerca nei testi generati:

```bash
# Via API
curl "http://localhost:8001/memory/search?query=love&top_k=5"

# Risposta:
{
  "query": "love",
  "results": [
    {
      "text": "Generated lyrics for job abc123:\nIn my heart I feel...",
      "metadata": {"job_id": "abc123", "timestamp": "2025-01-27..."},
      "score": 0.85
    }
  ],
  "count": 5
}
```

### 4. Chat con la Memoria

Chat con tutti i testi generati:

```bash
# Via API
curl -X POST "http://localhost:8001/memory/chat?query=Quali canzoni parlano di amore?"

# Risposta:
{
  "query": "Quali canzoni parlano di amore?",
  "response": "Basato sulla memoria, ho trovato queste canzoni..."
}
```

---

## 📁 File Generati

Dopo la costruzione, troverai:

- `backend/memory/lyrics_memory.mp4` - Video memoria compresso
- `backend/memory/lyrics_index.json` - Indice per ricerca veloce

**Dimensione**: ~1-2 MB per 100 canzoni (vs 50-100 MB con database vettoriale)

---

## 🎯 Esempi d'Uso

### Esempio 1: Salvataggio Automatico

```python
# Quando processi una canzone, viene salvato automaticamente
# Non devi fare nulla - è già integrato!
```

### Esempio 2: Costruisci Memoria Dopo N Canzoni

```python
from memory_manager import build_memory_video

# Dopo aver processato 10-20 canzoni
build_memory_video()
# Crea lyrics_memory.mp4 con tutti i testi
```

### Esempio 3: Cerca Testi

```python
from memory_manager import search_in_memory

# Cerca canzoni che parlano di "night"
results = search_in_memory("night", top_k=5)
for result in results:
    print(f"Job: {result['metadata']['job_id']}")
    print(f"Testo: {result['text'][:100]}...")
```

### Esempio 4: Chat con Memoria

```python
from memory_manager import chat_with_memory

# Chiedi alla memoria
response = chat_with_memory("Quali sono i temi più comuni nei testi generati?")
print(response)
```

---

## 🔍 API Endpoints

### POST `/memory/build`
Costruisce/aggiorna il video memoria.

**Risposta**:
```json
{
  "status": "success",
  "message": "Memoria video costruita con successo"
}
```

### GET `/memory/search?query=testo&top_k=5`
Cerca nei testi generati.

**Parametri**:
- `query`: Testo da cercare
- `top_k`: Numero risultati (default: 5)

**Risposta**:
```json
{
  "query": "testo",
  "results": [...],
  "count": 5
}
```

### POST `/memory/chat?query=domanda`
Chat con la memoria.

**Parametri**:
- `query`: Domanda/query

**Risposta**:
```json
{
  "query": "domanda",
  "response": "Risposta basata sulla memoria..."
}
```

---

## ⚙️ Configurazione

### Opzionale: Personalizza Encoder

Modifica `memory_manager.py` per personalizzare:

```python
# Più compressione
encoder = MemvidEncoder(
    chunk_size=256,      # Chunk più piccoli
    fps=60,              # Più frame/secondo
    frame_size=128       # QR codes più piccoli
)

# Migliore qualità
encoder = MemvidEncoder(
    chunk_size=1024,     # Chunk più grandi
    fps=30,              # Frame rate standard
    frame_size=512       # QR codes più grandi
)
```

---

## 📊 Performance

- **Indexing**: ~10K chunks/secondo
- **Search**: <100ms per 1M chunks
- **Storage**: 100MB testo → 1-2MB video
- **Memory**: Costante 500MB RAM

---

## 🐛 Troubleshooting

### Memvid non disponibile
```bash
# Installa
pip install memvid

# Verifica
python -c "from memvid import MemvidEncoder; print('OK')"
```

### Errore costruzione memoria
- Verifica che ci siano testi salvati (processa almeno 1 canzone)
- Controlla spazio disco disponibile
- Verifica permessi scrittura in `backend/memory/`

### Ricerca non funziona
- Assicurati di aver chiamato `/memory/build` prima
- Verifica che `lyrics_memory.mp4` e `lyrics_index.json` esistano

---

## 💡 Casi d'Uso

1. **Ricerca Temi**: "Quali canzoni parlano di amore?"
2. **Analisi Pattern**: "Quali parole sono più comuni?"
3. **Ripristino Testi**: "Trova il testo generato per job XYZ"
4. **Chat con Memoria**: "Raccontami cosa ho generato finora"

---

**Versione**: 4.0.1-memvid  
**Repository**: https://github.com/Olow304/memvid

