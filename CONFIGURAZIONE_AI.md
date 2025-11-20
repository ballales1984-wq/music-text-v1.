# 🤖 Configurazione AI - Music Text Generator

## 🎯 AI Supportate

L'app supporta **4 diverse AI** per la generazione testo:

1. **DeepSeek** (priorità alta) - API cloud
2. **Claude (Anthropic)** (priorità alta) - API cloud
3. **OpenAI (ChatGPT)** (priorità media) - API cloud
4. **Ollama** (priorità bassa) - Locale

L'app **rileva automaticamente** quali AI sono disponibili e le usa in ordine di priorità.

---

## 🔧 Configurazione

### 1. DeepSeek

1. Ottieni API key da: https://platform.deepseek.com/
2. Imposta variabile ambiente:
   ```bash
   # Windows PowerShell
   $env:DEEPSEEK_API_KEY="sk-..."
   
   # Windows CMD
   set DEEPSEEK_API_KEY=sk-...
   
   # Linux/Mac
   export DEEPSEEK_API_KEY="sk-..."
   ```

3. Opzionale - Personalizza modello:
   ```bash
   $env:DEEPSEEK_MODEL="deepseek-chat"  # Default
   $env:DEEPSEEK_BASE_URL="https://api.deepseek.com"  # Default
   ```

### 2. Claude (Anthropic)

1. Ottieni API key da: https://console.anthropic.com/
2. Installa libreria:
   ```bash
   pip install anthropic
   ```

3. Imposta variabile ambiente:
   ```bash
   $env:ANTHROPIC_API_KEY="sk-ant-..."
   ```

4. Opzionale - Personalizza modello:
   ```bash
   $env:CLAUDE_MODEL="claude-3-5-sonnet-20241022"  # Default
   ```

### 3. OpenAI (ChatGPT)

1. Ottieni API key da: https://platform.openai.com/
2. Imposta variabile ambiente:
   ```bash
   $env:OPENAI_API_KEY="sk-..."
   ```

3. Opzionale - Personalizza modello:
   ```bash
   $env:OPENAI_MODEL="gpt-3.5-turbo"  # Default (o gpt-4, gpt-4-turbo)
   ```

### 4. Ollama (Locale)

1. Installa Ollama: https://ollama.ai/
2. Scarica modello:
   ```bash
   ollama pull llama3.2
   # o
   ollama pull mistral
   ```

3. Opzionale - Personalizza URL e modello:
   ```bash
   $env:OLLAMA_BASE_URL="http://localhost:11434"  # Default
   $env:OLLAMA_MODEL="llama3.2"  # Default
   ```

---

## 📋 File .env (Raccomandato)

Crea file `.env` nella cartella `backend/`:

```env
# DeepSeek
DEEPSEEK_API_KEY=sk-...
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Claude
ANTHROPIC_API_KEY=sk-ant-...
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

**Nota**: Per usare `.env`, installa `python-dotenv`:
```bash
pip install python-dotenv
```

E aggiungi all'inizio di `main.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

---

## 🔄 Priorità AI

L'app usa le AI in questo ordine:

1. **DeepSeek** (se disponibile)
2. **Claude** (se DeepSeek fallisce)
3. **OpenAI** (se Claude fallisce)
4. **Ollama** (se OpenAI fallisce)
5. **Fallback locale** (se nessuna AI disponibile)

Se una AI fallisce, l'app **prova automaticamente** la successiva.

---

## ✅ Verifica Configurazione

All'avvio, l'app mostra quali AI sono disponibili:

```
✅ DeepSeek disponibile (API key configurata)
✅ Claude (Anthropic) disponibile
✅ OpenAI disponibile
✅ Ollama disponibile
🤖 AI disponibili: DeepSeek, Claude, OpenAI, Ollama
```

Se nessuna AI è disponibile:
```
⚠️  Nessuna AI disponibile - userà solo fallback locale
```

---

## 💰 Costi

- **DeepSeek**: ~$0.14 per 1M token (molto economico)
- **Claude**: ~$3 per 1M token input, ~$15 per 1M token output
- **OpenAI GPT-3.5**: ~$0.50 per 1M token input, ~$1.50 per 1M token output
- **OpenAI GPT-4**: ~$30 per 1M token input, ~$60 per 1M token output
- **Ollama**: Gratis (locale)

**Raccomandazione**: Usa DeepSeek per costi bassi e buone prestazioni.

---

## 🧪 Test

Per testare una specifica AI, puoi disabilitare temporaneamente le altre commentando il codice in `lyrics_generator.py`.

Oppure, usa solo una API key alla volta per forzare l'uso di quella AI.

---

## 📝 Note

- L'app **rileva automaticamente** le AI disponibili all'avvio
- Se un'AI fallisce, l'app **prova automaticamente** la successiva
- **Nessuna configurazione manuale** necessaria - basta impostare le API key
- L'app funziona anche **senza AI** usando fallback locale (meno preciso)

---

## 🔗 Link Utili

- DeepSeek: https://platform.deepseek.com/
- Claude: https://console.anthropic.com/
- OpenAI: https://platform.openai.com/
- Ollama: https://ollama.ai/

