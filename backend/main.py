"""
Music Text Generator - Backend semplificato
Pipeline: trascrizione -> struttura -> conteggio sillabe -> generazione testo
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uuid
from pathlib import Path
import logging
from typing import Dict
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor

from transcription import transcribe_audio
from text_structure import extract_structure
from syllable_counter import count_syllables_in_text, get_key_words
from lyrics_generator import generate_lyrics_simple
from text_cleaner import clean_and_filter_text, validate_text_quality
from audio_structure_analysis import analyze_audio_structure
from separation import separate_vocals_and_instrumental
from audio_analysis import analyze_audio_features
from metric_grid_generator import create_metric_grid_from_vocal, generate_text_from_grid
from rhythmic_analysis import analyze_rhythmic_features
from orchestrator import ProcessingOrchestrator

# Configurazione
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Music Text Generator", version="3.0.0-simple")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Stato job
job_status: Dict[str, Dict] = {}

# Executor per processi lunghi
executor = ThreadPoolExecutor(max_workers=2)


@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    """Carica e processa file audio - versione semplificata."""
    job_id = None
    try:
        # Valida nome file
        if not file.filename:
            raise HTTPException(400, "Nome file non valido")
        
        # Valida formato
        allowed = {".mp3", ".wav", ".m4a", ".flac"}
        ext = Path(file.filename).suffix.lower()
        if ext not in allowed:
            raise HTTPException(400, f"Formato non supportato. Formati supportati: {', '.join(allowed)}")
        
        # Valida dimensione file (max 100MB)
        MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(400, f"File troppo grande ({file_size / (1024*1024):.1f}MB). Dimensione massima: 100MB")
        
        if file_size < 1024:  # Minimo 1KB
            raise HTTPException(400, "File troppo piccolo o corrotto")
        
        # Salva file
        job_id = str(uuid.uuid4())
        input_path = UPLOAD_DIR / f"{job_id}{ext}"
        with open(input_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"[{job_id}] File caricato: {input_path.name} ({file_size / (1024*1024):.2f}MB)")
        
        # Inizializza stato
        job_status[job_id] = {
            "status": "processing",
            "step": 0,
            "total_steps": 4,
            "current_step": "Inizializzazione",
            "progress": 0
        }
        
        # Callback per aggiornare stato
        def update_status(status_info: Dict):
            if job_id in job_status:
                job_status[job_id].update(status_info)
        
        # Restituisci subito job_id e avvia processamento in background
        # Il frontend farà polling per lo stato
        logger.info(f"[{job_id}] ✅ File salvato, avvio processamento in background...")
        
        # Avvia processamento in thread separato per non bloccare la risposta
        process_start_time = time.time()  # Tempo di inizio processamento
        
        def process_audio():
            try:
                # Callback per aggiornare stato
                def update_status(status_info: Dict):
                    if job_id in job_status:
                        job_status[job_id].update(status_info)
                
                # Crea orchestratore
                orchestrator = ProcessingOrchestrator(
                    job_id=job_id,
                    input_path=input_path,
                    output_dir=OUTPUT_DIR,
                    upload_dir=UPLOAD_DIR
                )
                
                # Esegui pipeline completa
                result = orchestrator.execute_pipeline(status_callback=update_status)
                
                if not result:
                    job_status[job_id]["status"] = "error"
                    job_status[job_id]["error"] = "Pipeline completata ma nessun risultato generato"
                    logger.error(f"[{job_id}] ❌ Nessun risultato generato")
                    return
                
                # Aggiorna stato finale
                job_status[job_id]["status"] = "completed"
                job_status[job_id]["progress"] = 100
                job_status[job_id]["result"] = result
                
                total_time = time.time() - process_start_time
                logger.info(f"[{job_id}] 🎉 Processamento completo in {total_time:.1f}s")
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"[{job_id}] ❌ Errore durante processamento: {error_msg}", exc_info=True)
                if job_id in job_status:
                    job_status[job_id]["status"] = "error"
                    job_status[job_id]["error"] = error_msg
                    job_status[job_id]["progress"] = 0
        
        # Avvia processamento in thread separato
        executor.submit(process_audio)
        
        # Restituisci subito job_id (il frontend farà polling)
        return JSONResponse({
            "job_id": job_id,
            "status": "processing",
            "message": "File caricato, processamento avviato. Usa /status/{job_id} per monitorare il progresso."
        })
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[{job_id if job_id else 'UNKNOWN'}] Errore durante processamento: {error_msg}", exc_info=True)
        
        # Aggiorna stato job se esiste
        if job_id and job_id in job_status:
            job_status[job_id]["status"] = "error"
            job_status[job_id]["error"] = error_msg
            job_status[job_id]["progress"] = 0
        
        # Messaggi di errore più specifici
        error_detail = f"Errore durante il processamento: {error_msg}"
        
        if "Whisper" in error_msg or "transcribe" in error_msg.lower():
            error_detail = "Errore nella trascrizione Whisper. Verifica che il modello sia installato correttamente."
        elif "memory" in error_msg.lower() or "out of memory" in error_msg.lower():
            error_detail = "Memoria insufficiente. Prova con un file più piccolo o chiudi altre applicazioni."
        elif "cuda" in error_msg.lower() or "gpu" in error_msg.lower():
            error_detail = "Errore GPU. Il sistema userà la CPU automaticamente."
        elif "file" in error_msg.lower() and ("not found" in error_msg.lower() or "corrupt" in error_msg.lower()):
            error_detail = "File audio corrotto o non valido. Verifica che il file sia un audio valido."
        elif "timeout" in error_msg.lower():
            error_detail = "Timeout durante il processamento. Il file potrebbe essere troppo lungo. Prova con un file più corto."
        
        # Pulisci file temporanei in caso di errore
        if job_id:
            try:
                for ext in [".mp3", ".wav", ".m4a", ".flac"]:
                    temp_file = UPLOAD_DIR / f"{job_id}{ext}"
                    if temp_file.exists():
                        temp_file.unlink()
            except:
                pass
        
        raise HTTPException(500, detail=error_detail)


@app.get("/")
async def root():
    """Endpoint root - informazioni API."""
    return {
        "message": "Music Text Generator API - Versione Semplificata",
        "version": "3.0.0-simple",
        "endpoints": {
            "POST /upload": "Carica e processa file audio",
            "GET /health": "Health check",
            "GET /status/{job_id}": "Stato di un job",
            "GET /docs": "Documentazione API (Swagger UI)"
        },
        "status": "operativo"
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "message": "Server operativo (versione semplificata)"}


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Stato job."""
    if job_id not in job_status:
        raise HTTPException(404, "Job non trovato")
    
    status = job_status[job_id].copy()
    
    # Se completato, aggiungi risultato completo nel formato atteso dal frontend
    if status.get("status") == "completed" and "result" in status:
        result = status["result"]
        lyrics_result = result.get("lyrics_variants", {})
        raw_transcription = result.get("raw_transcription", {})
        structure = result.get("structure", {})
        syllables = result.get("syllables", {})
        key_words = result.get("key_words", [])
        
        # Pulisci il testo finale prima di restituirlo
        from text_cleaner import clean_generated_text
        final_text_raw = lyrics_result.get("variants", [{}])[0].get("full_text", "") if lyrics_result.get("variants") else ""
        final_text_cleaned = clean_generated_text(final_text_raw) if final_text_raw else ""
        
        # Pulisci anche le varianti
        cleaned_variants = []
        for variant in lyrics_result.get("variants", []):
            variant_text = variant.get("full_text", "")
            if variant_text:
                variant_text_cleaned = clean_generated_text(variant_text)
                variant_copy = variant.copy()
                variant_copy["full_text"] = variant_text_cleaned
                # Pulisci anche verses e chorus
                if "verses" in variant_copy:
                    variant_copy["verses"] = [clean_generated_text(v) for v in variant_copy["verses"] if v]
                if "chorus" in variant_copy:
                    variant_copy["chorus"] = [clean_generated_text(c) for c in variant_copy["chorus"] if c]
                cleaned_variants.append(variant_copy)
            else:
                cleaned_variants.append(variant)
        
        lyrics_result_cleaned = lyrics_result.copy()
        lyrics_result_cleaned["variants"] = cleaned_variants
        
        # Costruisci risposta completa nel formato frontend
        status["result"] = {
            "job_id": job_id,
            "status": "completed",
            "original_audio_url": result.get("original_audio_url", f"/audio/{job_id}"),
            "vocal_audio_url": result.get("vocal_audio_url"),
            "vocal_clean_audio_url": None,
            "instrumental_audio_url": result.get("instrumental_audio_url"),
            "raw_transcription": raw_transcription,
            "structure": structure,
            "syllables": syllables,
            "key_words": key_words,
            "final_text": final_text_cleaned,
            "lyrics_variants": lyrics_result_cleaned,
            "message": "Processamento completato"
        }
    
    return status


@app.get("/audio/{job_id}")
async def get_original_audio(job_id: str):
    """Download audio originale caricato."""
    # Cerca file audio nella cartella uploads
    for ext in [".mp3", ".wav", ".m4a", ".flac"]:
        audio_path = UPLOAD_DIR / f"{job_id}{ext}"
        if audio_path.exists():
            # Determina content type
            content_type = {
                ".mp3": "audio/mpeg",
                ".wav": "audio/wav",
                ".m4a": "audio/mp4",
                ".flac": "audio/flac"
            }.get(ext, "audio/mpeg")
            
            return FileResponse(
                audio_path,
                media_type=content_type,
                filename=f"{job_id}{ext}"
            )
    
    raise HTTPException(404, "File audio non trovato")


@app.get("/audio/{job_id}/vocals")
async def get_vocal_audio(job_id: str):
    """Download audio vocale isolato."""
    vocal_path = OUTPUT_DIR / f"{job_id}_vocals.wav"
    if vocal_path.exists():
        return FileResponse(
            vocal_path,
            media_type="audio/wav",
            filename=f"{job_id}_vocals.wav"
        )
    raise HTTPException(404, "File vocale non trovato")


@app.get("/audio/{job_id}/instrumental")
async def get_instrumental_audio(job_id: str):
    """Download audio base strumentale."""
    instrumental_path = OUTPUT_DIR / f"{job_id}_instrumental.wav"
    if instrumental_path.exists():
        return FileResponse(
            instrumental_path,
            media_type="audio/wav",
            filename=f"{job_id}_instrumental.wav"
        )
    raise HTTPException(404, "File strumentale non trovato")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
