# 🦙 Installazione Ollama per Generazione Testo in Inglese

## 🎯 Perché Ollama?

Ollama permette di usare modelli LLM **locali** (senza API esterne) per generare testo in inglese. È:
- ✅ **Gratuito** (nessun costo API)
- ✅ **Locale** (i dati restano sul tuo computer)
- ✅ **Veloce** (se hai GPU, è molto veloce)
- ✅ **Ottimo per inglese** (modelli ottimizzati per inglese)

---

## 🚀 Installazione Rapida

### 1. Scarica e Installa Ollama

**Windows:**
1. Vai su [https://ollama.com/download](https://ollama.com/download)
2. Scarica `OllamaSetup.exe`
3. Esegui l'installer
4. Ollama si avvierà automaticamente

**Verifica installazione:**
```powershell
ollama --version
```

### 2. Scarica un Modello in Inglese

Apri un terminale e scarica uno di questi modelli (consigliato per inglese):

**Opzione 1: Llama 3.2 (Consigliato - ~2GB, veloce e buono)**
```bash
ollama pull llama3.2
```

**Opzione 2: Mistral (Alternativa - ~4GB, molto buono)**
```bash
ollama pull mistral
```

**Opzione 3: Phi-3 (Leggero - ~2GB, veloce)**
```bash
ollama pull phi3
```

**Opzione 4: Llama 3.1 (Più grande - ~4.7GB, migliore qualità)**
```bash
ollama pull llama3.1
```

> **Nota**: La prima volta, il download può richiedere alcuni minuti. I modelli vengono salvati localmente.

### 3. Verifica che Ollama Funzioni

```bash
ollama run llama3.2 "Write a short song lyric"
```

Dovresti vedere una risposta generata dal modello.

---

## ⚙️ Configurazione nel Backend

### Opzione 1: Usa Default (llama3.2)

Se hai scaricato `llama3.2`, non serve configurare nulla! Il backend lo rileverà automaticamente.

### Opzione 2: Usa un Modello Diverso

Crea/modifica `backend/.env` e aggiungi:

```env
OLLAMA_MODEL=mistral
# oppure
OLLAMA_MODEL=phi3
# oppure
OLLAMA_MODEL=llama3.1
```

### Opzione 3: Ollama su Porta Diversa

Se Ollama è su una porta diversa (default: 11434):

```env
OLLAMA_BASE_URL=http://localhost:11435
```

---

## 🎵 Come Funziona

1. **Backend rileva Ollama** automaticamente all'avvio
2. **Quando generi testo**, il backend:
   - Prova prima **Ollama** (se disponibile)
   - Altrimenti prova **GPT-2 locale**
   - Altrimenti usa **formattazione base**

3. **Il testo generato è in inglese** (come richiesto)

---

## ✅ Verifica che Funzioni

1. Avvia il backend:
   ```bash
   cd backend
   python main.py
   ```

2. Nei log dovresti vedere:
   ```
   ✅ Ollama disponibile per generazione testo
   ```

3. Processa un file audio e verifica che il testo generato sia in inglese!

---

## 🐛 Troubleshooting

### "Cannot connect to Ollama"

**Problema**: Ollama non è in esecuzione

**Soluzione**:
```bash
# Avvia Ollama manualmente
ollama serve
```

Oppure riavvia Ollama dal menu Start (Windows).

### "Model not found"

**Problema**: Il modello specificato non è stato scaricato

**Soluzione**:
```bash
# Scarica il modello
ollama pull llama3.2
```

### "Ollama lento"

**Soluzione**:
- Usa un modello più piccolo (llama3.2 o phi3)
- Se hai GPU NVIDIA, Ollama la userà automaticamente
- Chiudi altre applicazioni pesanti

---

## 📊 Modelli Consigliati per Inglese

| Modello | Dimensione | Velocità | Qualità | Consigliato |
|---------|-----------|----------|---------|-------------|
| **llama3.2** | ~2GB | ⚡⚡⚡ | ⭐⭐⭐⭐ | ✅ **Sì** |
| phi3 | ~2GB | ⚡⚡⚡ | ⭐⭐⭐ | ✅ Sì |
| mistral | ~4GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | ✅ Sì |
| llama3.1 | ~4.7GB | ⚡⚡ | ⭐⭐⭐⭐⭐ | ✅ Sì |

**Raccomandazione**: Inizia con **llama3.2** (bilanciato tra velocità e qualità).

---

## 🎉 Fatto!

Ora l'app genererà testo in inglese usando Ollama locale, senza bisogno di API esterne!

Per testare, processa un file audio e verifica che il testo generato sia in inglese.

