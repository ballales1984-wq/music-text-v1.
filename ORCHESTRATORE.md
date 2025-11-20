# 🎼 Orchestratore - Coordinamento Processo

## 🎯 Obiettivo

L'orchestratore (`backend/orchestrator.py`) coordina **tutto il processo** di generazione testo, gestisce errori e implementa **retry automatico**.

---

## ✨ Funzionalità

### 1. **Coordinamento Pipeline**
- Esegue tutti gli step in sequenza
- Gestisce lo stato tra le funzioni
- Passa dati da uno step al successivo

### 2. **Retry Automatico**
- **Tentativi multipli** per ogni operazione (configurabile)
- **Backoff esponenziale** tra tentativi (2^attempt secondi)
- **Skip opzionale** per step non critici

### 3. **Gestione Errori**
- Cattura e logga tutti gli errori
- Distingue errori critici da warning
- Continua con fallback quando possibile

### 4. **Stato Centralizzato**
- Mantiene stato completo del processo
- Traccia warnings ed errori
- Aggiorna progress in tempo reale

---

## 🔄 Pipeline Orchestrata

### Step 0: Separazione Vocale
- **Retry**: 2 tentativi
- **Critico**: Sì (ma ha fallback)
- **Fallback**: Usa audio completo se fallisce

### Step 1: Trascrizione
- **Retry**: 2 tentativi
- **Critico**: Sì
- **Validazione**: Verifica testo non vuoto

### Step 1.5: Pulizia Testo
- **Retry**: 1 tentativo
- **Critico**: Sì
- **Operazione**: Rimuove ripetizioni

### Step 1.7: Analisi Audio
- **Retry**: 2 tentativi
- **Critico**: No (può essere saltato)
- **Fallback**: Continua senza griglia metrica

### Step 2: Estrazione Struttura
- **Retry**: 1 tentativo
- **Critico**: Sì
- **Operazione**: Analizza struttura e sillabe

### Step 3: Generazione Testo
- **Retry**: 2 tentativi
- **Critico**: Sì
- **Strategia**: Prova griglia metrica, poi tradizionale

---

## 🛠️ Utilizzo

### Nel Backend (`main.py`)

```python
from orchestrator import ProcessingOrchestrator

# Crea orchestratore
orchestrator = ProcessingOrchestrator(
    job_id=job_id,
    input_path=input_path,
    output_dir=OUTPUT_DIR,
    upload_dir=UPLOAD_DIR
)

# Callback per aggiornare stato
def update_status(status_info: Dict):
    job_status[job_id].update(status_info)

# Esegui pipeline
result = orchestrator.execute_pipeline(status_callback=update_status)
```

---

## 📊 Stato Interno

L'orchestratore mantiene uno stato interno con:

```python
{
    "vocal_path": Path,              # Voce isolata
    "instrumental_path": Path,       # Base strumentale
    "transcription": Dict,           # Trascrizione Whisper
    "audio_features": Dict,          # Features audio voce
    "instrumental_features": Dict,   # Features base strumentale
    "metric_grid": Dict,             # Griglia metrica
    "final_result": Dict,            # Risultato finale
    "errors": List[str],             # Errori critici
    "warnings": List[str]            # Warning non critici
}
```

---

## 🔄 Retry Logic

### Configurazione per Step

```python
self._execute_with_retry(
    self._step_separation,
    max_retries=2,           # Numero tentativi
    step_name="Separazione",  # Nome per logging
    can_skip=False           # Se può essere saltato
)
```

### Backoff Esponenziale

- Tentativo 1: Attesa 0s
- Tentativo 2: Attesa 2s (2^1)
- Tentativo 3: Attesa 4s (2^2)

---

## ✅ Vantaggi

1. **Robustezza**: Retry automatico su errori temporanei
2. **Coordinamento**: Stato centralizzato tra funzioni
3. **Flessibilità**: Skip opzionale per step non critici
4. **Tracciabilità**: Log dettagliati di ogni operazione
5. **Manutenibilità**: Codice pulito e organizzato

---

## 🧪 Test

L'orchestratore gestisce automaticamente:
- Errori temporanei (retry)
- Errori permanenti (fallback o skip)
- Timeout (retry con backoff)
- Memoria insufficiente (retry)

---

## 📝 Esempio Log

```
[job_123] 🎼 Avvio orchestratore pipeline...
[job_123] 🔄 Separazione vocale - Tentativo 1/3
[job_123] ✅ Separazione vocale completato
[job_123] 🔄 Trascrizione - Tentativo 1/3
[job_123] ⚠️  Trascrizione fallito (tentativo 1/3): Timeout
[job_123] ⏳ Attendo 2s prima di ritentare...
[job_123] 🔄 Trascrizione - Tentativo 2/3
[job_123] ✅ Trascrizione completato
...
[job_123] ✅ Pipeline completata con successo
```

---

## 🔧 Decorator Retry

L'orchestratore include anche un decorator per retry su funzioni:

```python
from orchestrator import retry_on_failure

@retry_on_failure(max_retries=2, can_skip=False, delay=1.0)
def my_function():
    # Codice che può fallire
    pass
```

---

## 📌 Note

- L'orchestratore **sostituisce** la pipeline manuale in `main.py`
- Tutti gli step sono **indipendenti** e possono essere testati separatamente
- Lo stato è **immutabile** tra step (ogni step riceve dati, non modifica stato diretto)
- Gli errori sono **tracciati** ma non bloccano il processo se non critici

