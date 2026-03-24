# Analisi rapida del repository

## Obiettivo del progetto
Il progetto implementa una web app che:
1. riceve in upload un file audio,
2. separa la voce dalla base,
3. trascrive la voce,
4. genera testo creativo coerente con metrica/struttura.

## Stack tecnologico
- **Backend**: FastAPI + pipeline Python orchestrata a step.
- **Frontend**: Next.js/React (TypeScript) con polling dello stato job.

## Flusso backend (alto livello)
- Endpoint principale `POST /upload` valida formato/dimensione, salva il file e avvia la pipeline in background.
- Lo stato è tracciato in memoria (`job_status`) e viene interrogato dal frontend via `GET /status/{job_id}`.
- L'esecuzione è coordinata da `ProcessingOrchestrator`, che gestisce retry, warning e fallback step-by-step.

## Flusso frontend (alto livello)
- L’utente seleziona il file, avvia upload e riceve `job_id`.
- Parte polling periodico su `/status/{job_id}` finché il job non è `completed` o `error`.
- In caso di successo visualizza testo finale, varianti e URL audio processati.

## Punti di forza osservati
- Architettura pipeline ben modulare (separazione, trascrizione, analisi, generazione).
- Retry con backoff in orchestrazione.
- Validazioni input lato backend (estensione, dimensione min/max).
- UX asincrona robusta grazie al polling.

## Rischi/attenzioni
- `job_status` in memoria: con restart server si perde lo stato job.
- ThreadPool fisso a 2 worker: può diventare collo di bottiglia sotto carico.
- Molto logging di debug nel frontend: utile in sviluppo, da ridurre in produzione.
- Gestione timeout/polling aggressiva (500ms): da tarare per ridurre traffico su ambienti condivisi.

## Suggerimenti pragmatici
1. Persistenza stato job (Redis/DB) per resilienza.
2. Coda task (Celery/RQ) per scalabilità e controllo concorrenza.
3. Introduzione di endpoint `DELETE /job/{id}` o cleanup schedulato.
4. Riduzione log frontend in modalità production.
5. Aggiunta test automatici minimi su API upload/status.
