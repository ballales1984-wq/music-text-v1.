# 🎵 Pipeline Avanzata: Analisi Audio + Generazione Testo

## 🎯 Obiettivo

Generare testo in inglese che si adatta **perfettamente** alla melodia, ritmo e struttura musicale del canto vocale (anche senza parole, tipo "la la la").

---

## 🔄 Pipeline Completa

### 1. **Rilevamento Sezioni Vocali**
- Identifica dove ci sono parti vocali nel brano
- Calcola durata e percentuale

### 2. **Separazione Vocale**
- Isola la traccia vocale dagli strumenti
- Output: file audio solo voce

### 3. **Analisi Audio Avanzata** ⭐ NUOVO
Estrae informazioni musicali dettagliate:

- **Pitch (Altezza Note)**: Usa CREPE o Librosa
  - Frequenze delle note
  - Contorno melodico (pitch nel tempo)
  - Note musicali (C4, D4, E4, ecc.)

- **Timing e Ritmo**:
  - Tempo (BPM)
  - Beat detection
  - Pattern ritmico
  - Onset detection

- **Envelope (Dinamica)**:
  - RMS Energy
  - Variazioni di volume nel tempo

- **Melodia**:
  - Contorno melodico semplificato
  - Sequenza di note sostenute
  - Durata delle note

- **Key Detection**:
  - Tonalità del brano

### 4. **Trascrizione Whisper**
- Trascrive parole (se presenti)
- Rileva fonemi/suoni vocali (se "la la la")

### 5. **Generazione Testo con Modello Linguistico** ⭐ MIGLIORATO
Usa **Ollama** (llama2/3, mistral, gpt-j, gpt-neox) con prompt avanzato che include:

```
Musical Information:
- Musical notes detected: C4, D4, E4, F4...
- Pitch contour: 261.6Hz@0.0s, 293.7Hz@0.5s...
- Tempo: 120.0 BPM
- Rhythm pattern: regular
- Melody: C4 -> D4 -> E4 -> F4...
- Key: C
```

Il modello genera testo che:
- ✅ **Si adatta al pitch contour** (sillabe su note alte/basse)
- ✅ **Segue il ritmo** (sillabe sui beat)
- ✅ **Rispetta il tempo** (lunghezza parole/sillabe)
- ✅ **Segue la melodia** (struttura delle frasi)
- ✅ **È in inglese** (come richiesto)

---

## 🛠️ Tecnologie Usate

### Analisi Audio
- **CREPE**: Pitch detection avanzata (preferito)
- **Librosa**: Analisi audio, beat detection, pitch fallback
- **Essentia**: Opzionale (analisi avanzata, richiede build)

### Modelli Linguistici (Ollama)
- **llama3.2**: Consigliato (veloce, buona qualità)
- **llama3.1**: Migliore qualità
- **mistral**: Alternativa eccellente
- **gpt-j**: Disponibile via Ollama
- **gpt-neox**: Disponibile via Ollama

---

## 📊 Esempio Output

### Input
- Audio: Canto "la la la" senza parole
- Melodia: C4 -> D4 -> E4 -> F4 -> G4
- Tempo: 120 BPM
- Ritmo: Regular

### Analisi Audio
```
Musical notes detected: C4, D4, E4, F4, G4
Pitch contour: 261.6Hz@0.0s, 293.7Hz@0.5s, 329.6Hz@1.0s...
Tempo: 120.0 BPM
Melody: C4 -> D4 -> E4 -> F4 -> G4
```

### Output Testo Generato
```
In the morning light I see
A world that's waiting just for me
With every step I take today
I find my way, I find my way
```

Il testo:
- ✅ Ha sillabe che salgono (come la melodia C4->G4)
- ✅ Segue il ritmo 120 BPM
- ✅ È in inglese
- ✅ Si adatta perfettamente alla melodia

---

## 🚀 Come Usare

1. **Installa dipendenze**:
   ```bash
   pip install crepe librosa
   ```

2. **Installa Ollama** (vedi [INSTALLA_OLLAMA.md](INSTALLA_OLLAMA.md))

3. **Scarica modello**:
   ```bash
   ollama pull llama3.2
   ```

4. **Processa audio**:
   - Carica file audio (anche con "la la la")
   - Il sistema analizza pitch, timing, melodia
   - Genera testo che si adatta perfettamente

---

## ⚙️ Configurazione

### Modello Ollama
In `backend/.env`:
```env
OLLAMA_MODEL=llama3.2  # o mistral, llama3.1, ecc.
```

### Analisi Audio
Il sistema usa automaticamente:
1. **CREPE** (se disponibile) - più accurato
2. **Librosa** (fallback) - sempre disponibile

---

## 🎯 Risultati Attesi

Con questa pipeline avanzata:
- ✅ Testo che **si adatta perfettamente** alla melodia
- ✅ Sillabe che seguono il **pitch contour**
- ✅ Parole che rispettano il **ritmo e timing**
- ✅ Testo **coerente e poetico** in inglese
- ✅ Funziona anche con **canto senza parole** ("la la la")

---

## 📝 Note

- La prima analisi audio può richiedere alcuni secondi
- CREPE è più accurato ma richiede più risorse
- Librosa è più veloce ma meno preciso
- Ollama deve essere in esecuzione per generare testo

---

## 🐛 Troubleshooting

### "CREPE non disponibile"
- Installa: `pip install crepe`
- Il sistema userà Librosa (fallback)

### "Ollama non disponibile"
- Installa Ollama (vedi [INSTALLA_OLLAMA.md](INSTALLA_OLLAMA.md))
- Avvia: `ollama serve`
- Scarica modello: `ollama pull llama3.2`

### "Analisi audio lenta"
- Usa Librosa invece di CREPE (più veloce)
- Riduci durata file audio per test

