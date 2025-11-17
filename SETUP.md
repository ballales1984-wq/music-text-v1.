# 🛠️ Guida Setup Rapida

## Installazione Veloce

### 1. Backend (Python)

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

**Nota importante**: L'installazione può richiedere tempo perché:
- PyTorch è grande (~2GB)
- Whisper scarica modelli al primo uso
- Demucs scarica modelli al primo uso

### 2. Frontend (Node.js)

```bash
cd frontend
npm install
```

### 3. Configurazione

**Backend**: Crea `backend/.env` da `backend/env.example`:
```bash
cp backend/env.example backend/.env
# Aggiungi la tua OPENAI_API_KEY se vuoi usare GPT
```

**Frontend**: Crea `frontend/.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Avvio

### Terminale 1 - Backend
```bash
cd backend
python main.py
# Oppure: ./start.sh (Linux/Mac) o start.bat (Windows)
```

### Terminale 2 - Frontend
```bash
cd frontend
npm run dev
```

Apri `http://localhost:3000` nel browser.

## Test Rapido

1. Prepara un file audio (MP3 o WAV) con voce chiara
2. Caricalo nell'interfaccia web
3. Attendi il processamento (può richiedere 1-5 minuti)
4. Visualizza i risultati

## Troubleshooting

### "Demucs non disponibile"
- Installa: `pip install demucs`
- Il sistema userà un metodo fallback (meno accurato)

### "Whisper lento"
- Usa modelli più piccoli modificando `transcription.py`:
  - `model_name = "tiny"` (veloce, meno accurato)
  - `model_name = "base"` (bilanciato)
  - `model_name = "large"` (lento, molto accurato)

### "OpenAI API error"
- Se non hai una API key, il sistema userà metodi fallback
- Per generazione testo avanzata, ottieni una key su: https://platform.openai.com

### Errori CORS
- Verifica che `NEXT_PUBLIC_API_URL` nel frontend punti a `http://localhost:8000`
- Controlla che il backend sia in esecuzione

## Modelli AI - Dimensioni

- **Whisper tiny**: ~39 MB
- **Whisper base**: ~74 MB
- **Whisper small**: ~244 MB
- **Whisper medium**: ~769 MB
- **Whisper large**: ~1550 MB

- **Demucs htdemucs**: ~340 MB

I modelli vengono scaricati automaticamente al primo utilizzo.

