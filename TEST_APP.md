# 🧪 Guida Test App

## ✅ Stato Attuale

- ✅ **Backend**: Attivo su `http://localhost:8000`
- ✅ **Frontend**: Attivo su `http://localhost:3000`
- ✅ **Connessione**: Backend e Frontend comunicano correttamente

## 🎵 Come Testare l'App

### 1. Apri l'Interfaccia Web
L'app dovrebbe essere già aperta nel browser su `http://localhost:3000`

Se non si è aperta automaticamente, apri manualmente:
- Vai su: `http://localhost:3000`

### 2. Carica un File Audio

**Formati supportati:**
- MP3
- WAV
- M4A
- FLAC

**Dove trovare file di test:**
- Usa un file audio dalla tua libreria musicale
- Oppure scarica un file audio di test da internet
- Consiglio: usa un file con voce chiara per risultati migliori

### 3. Processa l'Audio

1. Clicca su "Seleziona file audio"
2. Scegli il tuo file
3. Clicca "🚀 Processa Audio"
4. Attendi il processamento (può richiedere 1-5 minuti)

### 4. Visualizza i Risultati

Dopo il processamento vedrai:
- 🎤 **Traccia Vocale Isolata**: Player audio per ascoltare la voce estratta
- 📝 **Trascrizione Grezza**: Testo/fonemi rilevati da Whisper
- ✨ **Testo Finale Generato**: Testo creativo generato dall'IA

### 5. Scarica i Risultati

- 💾 **Scarica Audio Vocale**: Download della traccia vocale isolata (WAV)
- 💾 **Scarica Testo**: Download del testo completo in formato TXT

## ⚠️ Note Importanti

### Primo Utilizzo
- **Whisper** scaricherà automaticamente il modello "base" (~74 MB) al primo utilizzo
- **Demucs** scaricherà il modello "htdemucs" (~340 MB) al primo utilizzo
- Il primo processamento sarà più lento a causa del download dei modelli

### Performance
- File brevi (< 1 minuto): ~30-60 secondi
- File medi (1-3 minuti): ~1-3 minuti
- File lunghi (> 3 minuti): ~3-5+ minuti

### Qualità Risultati
- **Separazione vocale**: Dipende dal mix originale del brano
- **Trascrizione**: Whisper è ottimo sul parlato, meno preciso sul cantato
- **Generazione testo**: Migliore con OpenAI API key configurata

## 🔧 Troubleshooting

### Errore "Connection refused"
- Verifica che il backend sia in esecuzione: `http://localhost:8000/health`
- Riavvia il backend se necessario

### Errore durante processamento
- Controlla i log del backend per dettagli
- Verifica che il file audio sia in un formato supportato
- Prova con un file più breve per test

### Modelli non si scaricano
- Verifica connessione internet
- I modelli vengono scaricati automaticamente al primo uso

## 📊 Cosa Aspettarsi

### Con File Audio Buono
- ✅ Voce isolata chiara
- ✅ Trascrizione accurata
- ✅ Testo generato coerente

### Con File Audio Difficile
- ⚠️ Voce isolata con qualche strumento residuo
- ⚠️ Trascrizione parziale o con errori
- ⚠️ Testo generato basato su fonemi approssimati

## 🎯 Test Consigliati

1. **Test Base**: File con voce chiara e parlata
2. **Test Canzone**: File musicale con canto
3. **Test Difficile**: File con mix complesso o voce bassa

Buon test! 🚀

