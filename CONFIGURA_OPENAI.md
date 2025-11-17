# 🔑 Configurazione OpenAI API Key

## Perché configurare OpenAI?

Attualmente l'app funziona con un **fallback** che genera testo base. Con OpenAI API Key ottieni:

✅ **Testi più creativi e coerenti**  
✅ **Miglioramento automatico della trascrizione**  
✅ **Trasformazione intelligente di fonemi in parole**  
✅ **Risultati professionali**

---

## 🚀 Setup Rapido (2 minuti)

### 1. Ottieni la tua API Key

1. Vai su [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Crea un account o accedi
3. Clicca "Create new secret key"
4. Copia la chiave (inizia con `sk-...`)

### 2. Configura nel Backend

Crea un file `.env` nella cartella `backend`:

```bash
cd backend
```

**Su Windows (PowerShell):**
```powershell
New-Item -Path .env -ItemType File
notepad .env
```

**Su Linux/Mac:**
```bash
touch .env
nano .env
```

Aggiungi questa riga (sostituisci con la tua chiave):

```
OPENAI_API_KEY=sk-la-tua-chiave-qui
```

### 3. Riavvia il Backend

Ferma il backend (Ctrl+C) e riavvialo:

```bash
python main.py
```

---

## ✅ Verifica

Dopo aver configurato, quando processi un file audio vedrai nei log:

```
✅ OpenAI API disponibile - generazione testo avanzata
```

Invece di:

```
⚠️  OpenAI non disponibile - uso fallback
```

---

## 💰 Costi

OpenAI API ha un costo basato sull'uso:
- **GPT-3.5-turbo**: ~$0.0015 per 1K token (molto economico)
- Per un file audio di 2-3 minuti: **~$0.01-0.02** per processamento
- Puoi impostare un limite di spesa mensile su OpenAI

---

## 🎯 Risultati Attesi

### Senza OpenAI (Fallback):
```
I suoni rilevati suggeriscono una melodia vocale.
Per una generazione più accurata, configura l'API key...
```

### Con OpenAI:
```
[Testo creativo e coerente basato sulla trascrizione]
[Parole migliorate e contestualizzate]
[Testo di canzone professionale]
```

---

## 🐛 Problemi?

### "Invalid API Key"
- Verifica di aver copiato tutta la chiave (inizia con `sk-`)
- Assicurati che non ci siano spazi prima/dopo

### "Insufficient quota"
- Controlla il tuo account OpenAI per crediti disponibili
- Verifica limiti di spesa

### "Module not found"
- Installa: `pip install openai`

---

## 📝 Nota

L'app **funziona anche senza OpenAI**, ma i risultati sono più basici.  
Con OpenAI ottieni risultati professionali! 🚀

