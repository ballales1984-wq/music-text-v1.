# 🎵 Music Text Generator - Versione Semplificata

## 📋 Cosa fa l'app

L'app genera **testo in inglese ascoltando la traccia vocale** della canzone che carichi.

### Pipeline Semplificata:

1. **Carica Audio** → Carica un file audio (MP3, WAV, M4A, FLAC)
2. **Isola Voce** → Separa la voce dalla base strumentale
3. **Trascrive Voce** → Usa Whisper per trascrivere quello che sente nella voce
4. **Genera Testo Inglese** → Crea testo poetico in inglese basato sulla voce

---

## 🚀 Come Usare

### Backend (Versione Semplificata)

```bash
cd backend
python main_simple.py
```

Il server sarà disponibile su `http://localhost:8001`

### Frontend

Il frontend esistente funziona anche con la versione semplificata. Avvia come al solito:

```bash
cd frontend
npm run dev
```

---

## 📁 File Nuovi

### Backend

- **`main_simple.py`** - API semplificata con pipeline essenziale
- **`lyrics_generator_simple.py`** - Generatore di testo inglese semplificato

### Differenze dalla Versione Completa

| Versione Completa | Versione Semplificata |
|-------------------|----------------------|
| Pipeline complessa con analisi metriche | Pipeline semplice: voce → testo |
| Analisi ritmo, metrica, sillabe | Solo trascrizione e generazione |
| Multiple varianti di testo | Una versione di testo |
| Analisi audio avanzata | Solo essenziale |

---

## 🔧 Configurazione

### AI per Generazione Testo

L'app usa AI per generare testo in inglese. Supporta:

1. **Ollama** (consigliato - gratuito, locale)
   - Installa: https://ollama.ai
   - Modello consigliato: `llama3.2` o `mistral`
   - L'app rileva automaticamente se Ollama è disponibile

2. **OpenAI** (opzionale - a pagamento)
   - Configura `OPENAI_API_KEY` in `.env`
   - L'app usa GPT-3.5-turbo se disponibile

3. **Fallback** (sempre disponibile)
   - Se nessuna AI è disponibile, genera testo base poetico

---

## 📊 Flusso Dettagliato

### Step 1: Isolamento Voce

```
Canzone Completa → [Separazione] → Voce Isolata + Base Strumentale
```

- Usa Spleeter (ML) se disponibile (migliore qualità)
- Fallback a metodi semplici se Spleeter non disponibile

### Step 2: Trascrizione

```
Voce Isolata → [Whisper] → Testo Trascritto
```

- Usa modello Whisper "base" (veloce e accurato)
- Rileva automaticamente la lingua
- Estrae testo, fonemi, confidenza

### Step 3: Generazione Testo Inglese

```
Testo Trascritto → [AI] → Testo Inglese Poetico
```

- Se ci sono parole chiare: migliora il testo esistente
- Se solo suoni vocali: genera testo creativo
- Usa Ollama o OpenAI se disponibili
- Fallback a generazione base se AI non disponibile

---

## 🎯 Obiettivo

L'obiettivo è **semplice e diretto**:

> **"Ascolta la voce della canzone e genera testo in inglese"**

Niente analisi complesse, niente metriche avanzate - solo:
- Voce isolata
- Trascrizione
- Testo inglese generato

---

## 🔄 Migrazione dalla Versione Completa

Se vuoi usare la versione semplificata invece di quella completa:

1. **Backup** del file `main.py` originale
2. **Rinomina** `main_simple.py` → `main.py` (o modifica script di avvio)
3. **Rinomina** `lyrics_generator_simple.py` → `lyrics_generator.py` (o aggiorna import)

Oppure mantieni entrambe le versioni e scegli quale usare.

---

## ⚙️ Variabili d'Ambiente

Crea un file `.env` nella cartella `backend`:

```env
# Ollama (opzionale - rilevato automaticamente se installato)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2

# OpenAI (opzionale)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo
```

---

## 🐛 Troubleshooting

### Ollama non rilevato
- Verifica che Ollama sia installato: `ollama --version`
- Verifica che sia in esecuzione: `ollama serve`
- L'app userà fallback se Ollama non disponibile

### OpenAI non funziona
- Verifica che `OPENAI_API_KEY` sia configurata correttamente
- Verifica che la chiave sia valida
- L'app userà Ollama o fallback se OpenAI fallisce

### Testo generato troppo corto
- Verifica che Ollama/OpenAI siano disponibili
- Prova con un modello più grande (es. `llama3` invece di `llama3.2`)
- Il fallback genera sempre testo base

---

## 📝 Note

- La versione semplificata è **più veloce** della versione completa
- **Meno accuratezza** nelle sillabe/metriche (non le analizza)
- **Più semplice** da capire e modificare
- **Focus** solo sulla generazione di testo inglese dalla voce

---

**Versione**: 4.0.0-simple  
**Data**: 2025-01-27

