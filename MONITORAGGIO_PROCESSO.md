# 🔍 Monitoraggio Processo in Corso

## 📊 Script di Monitoraggio Creati

### 1. `monitor_process.py` - Monitora Job Specifico
```bash
# Monitora un job specifico
python monitor_process.py <job_id>

# Monitora automaticamente l'ultimo job
python monitor_process.py
```

**Funzionalità**:
- Progress bar in tempo reale
- Mostra step corrente
- Tempo trascorso
- Risultati finali quando completato

### 2. `monitor_live.py` - Monitora Tutti i Nuovi Processi
```bash
# Monitora automaticamente tutti i nuovi processi
python monitor_live.py

# Monitora job specifico
python monitor_live.py <job_id>
```

**Funzionalità**:
- Rileva automaticamente nuovi job caricati
- Monitora progress in tempo reale
- Mostra completamento automaticamente

---

## 🎯 Come Usare

### Opzione 1: Monitora Job Specifico
Se conosci il `job_id`:
```bash
cd backend
python monitor_process.py <job_id>
```

### Opzione 2: Monitora Automaticamente
Lo script rileva automaticamente l'ultimo job:
```bash
cd backend
python monitor_process.py
```

### Opzione 3: Monitora Live (Tutti i Nuovi Processi)
Per monitorare continuamente tutti i nuovi processi:
```bash
cd backend
python monitor_live.py
```

---

## 📊 Output Esempio

```
======================================================================
🔍 MONITORAGGIO JOB: 3ee66b52-b254-49c8-803d-1fef6c78e6ce
======================================================================
⏰ Inizio monitoraggio: 2025-11-19 14:00:07

[██████████████████████████████████████████████████] 100% | Step 4/4 |  444.9s
📋 Completato

✅ PROCESSO COMPLETATO!
⏱️  Tempo totale: 444.9 secondi (7.4 minuti)

📊 RISULTATI:
----------------------------------------------------------------------
Varianti testo generate: 3
Testo trascritto: 299 caratteri
Metodo usato: metric_grid
```

---

## ⏱️ Tempi Attesi

- **Separazione vocale**: 5-30 secondi
- **Trascrizione Whisper**: 30-120 secondi
- **Analisi audio**: 5-15 secondi
- **Generazione testo**: 10-300 secondi (dipende da AI)
- **Totale**: 1-10 minuti (dipende da lunghezza file e AI usata)

---

## 💡 Suggerimenti

1. **Lascia lo script in esecuzione** mentre testi
2. **Non chiudere il terminale** durante il processamento
3. **Controlla il frontend** per vedere i risultati completi
4. **Usa Ctrl+C** per interrompere il monitoraggio

---

## 🔗 Link Utili

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **Health Check**: http://localhost:8001/health
- **Docs API**: http://localhost:8001/docs

