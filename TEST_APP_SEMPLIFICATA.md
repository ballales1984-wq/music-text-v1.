# 🧪 Test App Semplificata

## ✅ Stato Attuale

- ✅ Backend semplificato: **IN ESECUZIONE** su `http://localhost:8001`
- ⚠️ Frontend: Verifica se è in esecuzione su `http://localhost:3000`

---

## 🚀 Come Testare

### 1. Verifica Backend

Apri nel browser o usa curl:
```
http://localhost:8001/
```

Dovresti vedere:
```json
{
  "message": "Music Text Generator API - Versione Semplificata",
  "version": "4.0.0-simple",
  "pipeline": "Audio → Voce Isolata → Trascrizione → Testo Inglese",
  "status": "operativo"
}
```

### 2. Verifica Frontend

Apri nel browser:
```
http://localhost:3000
```

Se non è in esecuzione, avvialo:
```bash
cd frontend
npm run dev
```

### 3. Test Completo

1. **Carica un file audio** (MP3, WAV, M4A, FLAC)
   - Scegli una canzone con voce chiara
   - File non troppo grande (< 50MB per test veloce)

2. **Clicca "Processa Audio"**

3. **Attendi i 3 step**:
   - Step 1: Isolamento voce (20%)
   - Step 2: Trascrizione Whisper (50%)
   - Step 3: Generazione testo inglese (80%)

4. **Verifica risultati**:
   - ✅ Voce isolata (audio)
   - ✅ Base strumentale (audio)
   - ✅ Trascrizione grezza
   - ✅ **Testo finale in inglese**

---

## 🔍 Cosa Verificare

### ✅ Funziona se:
- La voce viene isolata correttamente
- Whisper trascrive la voce
- Viene generato testo in inglese
- Il testo è poetico e coerente

### ❌ Problemi comuni:

1. **"Ollama non disponibile"**
   - L'app userà fallback (testo base)
   - Per risultati migliori: installa Ollama (https://ollama.ai)

2. **"Whisper lento"**
   - Normale per file lunghi (> 2 minuti)
   - Usa file più corti per test rapidi

3. **"Errore separazione voce"**
   - Prova con file stereo (non mono)
   - File con voce chiara funzionano meglio

---

## 📊 Test Rapido con curl

```bash
# Test health
curl http://localhost:8001/health

# Test upload (sostituisci con percorso file reale)
curl -X POST http://localhost:8001/upload -F "file=@C:\percorso\file.mp3"
```

---

## 🎯 Risultato Atteso

Dopo il processamento dovresti vedere:

1. **Audio Originale** - La canzone completa
2. **Voce Isolata** - Solo la parte vocale
3. **Base Strumentale** - Solo gli strumenti
4. **Trascrizione Grezza** - Quello che Whisper ha sentito
5. **✨ Testo Finale in Inglese** - Testo poetico generato

---

## 🐛 Debug

Se qualcosa non funziona:

1. **Controlla i log del backend** (nella finestra PowerShell)
2. **Controlla la console del browser** (F12)
3. **Verifica che Ollama sia in esecuzione** (se vuoi usarlo):
   ```bash
   ollama serve
   ```

---

**Buon test! 🎵**

