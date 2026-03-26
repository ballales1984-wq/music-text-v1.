"""
Music Text Generator - Backend migliorato
Pipeline: trascrizione -> struttura -> conteggio sillabe -> generazione testo
Versione 3.1.0 con sicurezza, persistenza, validazione, logging e monitoring
"""
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, Response
import uuid
from pathlib import Path
from typing import Dict, Optional
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import os

from transcription import transcribe_audio
from text_structure import extract_structure
from syllable_counter import count_syllables_in_text, get_key_words
from lyrics_generator_simple import generate_english_text_from_vocals, translate_to_italian, generate_lyrics_variants
from text_cleaner import clean_and_filter_text, validate_text_quality
from separation import separate_vocals_and_instrumental
from audio_analysis import analyze_audio_features

# Import nuovi moduli
from middleware.security import rate_limiter, api_key_auth
from middleware.file_validation import get_file_validator
from services.job_manager import get_job_manager
from services.file_manager import get_file_manager

# Import logging e metrics
from utils.structured_logger import get_logger
from utils.metrics import (
    init_metrics, get_metrics, track_request, track_job,
    track_file_upload, update_storage_metrics, jobs_active
)

# Configurazione logging strutturato
logger = get_logger(__name__)

app = FastAPI(
    title="Music Text Generator",
    version="3.1.0",
    description="API per generazione testo da audio con AI"
)

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

# Executor per processi lunghi (aumentato a 4 workers)
executor = ThreadPoolExecutor(max_workers=int(os.getenv("MAX_WORKERS", "4")))


@app.on_event("startup")
async def startup_event():
    """Inizializzazione app"""
    # Inizializza metrics
    init_metrics(app_version="3.1.0")
    
    logger.info(
        "Application started",
        version="3.1.0",
        workers=executor._max_workers,
        event="startup"
    )
    
    # Cleanup iniziale file vecchi
    file_manager = get_file_manager()
    stats = file_manager.cleanup_all()
    
    logger.info(
        "Initial cleanup completed",
        files_deleted=sum(stats.values()),
        details=stats,
        event="cleanup"
    )
    
    # Stats storage e aggiorna metrics
    storage_stats = file_manager.get_all_stats()
    update_storage_metrics(
        uploads_bytes=storage_stats["uploads"]["size_mb"] * 1024 * 1024,
        outputs_bytes=storage_stats["outputs"]["size_mb"] * 1024 * 1024,
        temp_bytes=storage_stats["temp"]["size_mb"] * 1024 * 1024
    )
    
    logger.info(
        "Storage stats",
        storage=storage_stats,
        event="storage_check"
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup finale"""
    logger.info("Application shutting down", event="shutdown")
    executor.shutdown(wait=True)
    logger.info("Executor shutdown complete", event="shutdown")


@app.post("/upload")
async def upload_audio(
    request: Request,
    file: UploadFile = File(...),
    _rate_limit: None = Depends(rate_limiter),
    _auth: None = Depends(api_key_auth)
):
    """
    Carica e processa file audio.
    
    Miglioramenti v3.1:
    - Rate limiting (10 req/min per IP)
    - Autenticazione API key (opzionale)
    - Validazione MIME type
    - Job persistence con Redis
    - Cleanup automatico file temporanei
    """
    job_id = None
    audio_path = None
    
    try:
        # Ottieni servizi
        file_validator = get_file_validator()
        job_manager = get_job_manager()
        file_manager = get_file_manager()
        
        # Valida nome file
        if not file.filename:
            raise HTTPException(400, "Nome file non valido")
        
        # Sanitizza filename
        safe_filename = file_validator.sanitize_filename(file.filename)
        if not file_validator.is_safe_filename(safe_filename):
            raise HTTPException(400, "Nome file non sicuro")
        
        # Leggi contenuto
        file_content = await file.read()
        file_size = len(file_content)
        
        # Validazione base (estensione + dimensione)
        is_valid, error = file_validator.validate_file(safe_filename, file_size)
        if not is_valid:
            raise HTTPException(400, error)
        
        # Crea job ID
        job_id = str(uuid.uuid4())
        
        # Salva file temporaneo
        ext = Path(safe_filename).suffix.lower()
        audio_path = UPLOAD_DIR / f"{job_id}{ext}"
        with open(audio_path, "wb") as f:
            f.write(file_content)
        
        # Validazione MIME type (su file salvato)
        is_valid, error = file_validator.validate_mime_type(audio_path)
        if not is_valid:
            # Elimina file non valido
            audio_path.unlink()
            raise HTTPException(400, error)
        
        # Crea job in job manager (persistente)
        job_data = job_manager.create_job(job_id, {
            "filename": safe_filename,
            "file_size": file_size,
            "client_ip": request.client.host if request.client else "unknown"
        })
        
        # Track metrics
        ext = Path(safe_filename).suffix.lower().replace(".", "")
        track_file_upload(ext, file_size)
        jobs_active.inc()
        
        logger.info(
            "File uploaded",
            job_id=job_id,
            filename=safe_filename,
            size_mb=round(file_size / (1024*1024), 2),
            format=ext,
            event="upload"
        )
        
        # Processa in background
        executor.submit(process_audio, job_id, audio_path)
        
        return {
            "job_id": job_id,
            "message": "File caricato, processamento avviato",
            "status_url": f"/status/{job_id}"
        }
        
    except HTTPException as e:
        # Cleanup in caso di errore
        if audio_path and audio_path.exists():
            audio_path.unlink()
        
        logger.warning(
            "Upload rejected",
            job_id=job_id,
            status_code=e.status_code,
            detail=e.detail,
            event="upload_error"
        )
        raise
    except Exception as e:
        logger.error(
            "Upload failed",
            job_id=job_id,
            error=e,
            event="upload_error"
        )
        
        # Cleanup
        if audio_path and audio_path.exists():
            audio_path.unlink()
        if job_id:
            job_manager = get_job_manager()
            job_manager.update_job(job_id, {
                "status": "error",
                "error": "Errore interno del server"
            })
        raise HTTPException(500, "Errore interno del server")


def process_audio(job_id: str, audio_path: Path):
    """Processa l'audio - separazione, trascrizione, generazione."""
    job_manager = get_job_manager()
    file_manager = get_file_manager()
    start_time = time.time()
    
    try:
        # Step 1: Separazione voce
        job_manager.update_job(job_id, {"progress": 10, "step": "Separazione voce..."})
        
        vocal_path, instrumental_path = separate_vocals_and_instrumental(
            audio_path, job_id, OUTPUT_DIR
        )
        
        # Step 2: Trascrizione
        job_manager.update_job(job_id, {"progress": 30, "step": "Trascrizione voce..."})
        transcription = transcribe_audio(vocal_path)
        
        # Step 3: Analisi struttura
        job_manager.update_job(job_id, {"progress": 50, "step": "Analisi struttura..."})
        structure = extract_structure(transcription.get("text", ""))
        syllables = count_syllables_in_text(transcription.get("text", ""))
        key_words = get_key_words(transcription.get("text", ""))
        
        # Step 4: Generazione testo
        job_manager.update_job(job_id, {"progress": 70, "step": "Generazione testo..."})
        
        lyrics_data = {
            "text": transcription.get("text", ""),
            "phonemes": transcription.get("phonemes", ""),
            "has_clear_words": transcription.get("has_clear_words", False),
            "language": transcription.get("language", "en"),
            "segments": transcription.get("segments", [])
        }
        final_text = generate_english_text_from_vocals(lyrics_data)
        
        # Genera varianti
        variants = generate_lyrics_variants(transcription.get("text", ""), num_variants=3)
        
        # Step 5: Traduzione
        job_manager.update_job(job_id, {"progress": 90, "step": "Traduzione..."})
        
        translation_cache: Dict[str, str] = {}
        final_text_italian = ""
        
        if final_text:
            final_text_italian = translate_to_italian(final_text)
            if final_text_italian:
                translation_cache[final_text] = final_text_italian
        
        # Traduci varianti
        for variant in variants:
            variant_text = variant
            if variant_text and variant_text not in translation_cache:
                translation_cache[variant_text] = translate_to_italian(variant_text)
        
        # Completato
        elapsed = time.time() - start_time
        result = {
            "job_id": job_id,
            "original_audio_url": f"/audio/{job_id}",
            "vocal_audio_url": str(vocal_path).replace("\\", "/").split("/")[-1],
            "instrumental_audio_url": str(instrumental_path).replace("\\", "/").split("/")[-1],
            "raw_transcription": transcription,
            "structure": structure,
            "syllables": syllables,
            "key_words": key_words,
            "final_text": final_text,
            "italian_translation": final_text_italian,
            "lyrics_variants": variants,
            "message": "Processamento completato",
            "elapsed_seconds": round(elapsed, 2)
        }
        
        job_manager.update_job(job_id, {
            "status": "completed",
            "progress": 100,
            "step": "Completato",
            "result": result,
            "elapsed_seconds": round(elapsed, 2)
        })
        
        logger.info(f"[{job_id}] Completato in {elapsed:.1f}s")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[{job_id}] Errore: {error_msg}", exc_info=True)
        
        job_manager.update_job(job_id, {
            "status": "error",
            "error": error_msg,
            "progress": 0
        })
        
        # Cleanup file in caso di errore
        file_manager.cleanup_job_files(job_id)


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
    """
    Ottieni stato job.
    
    Miglioramenti v3.1:
    - Persistenza con Redis
    - Informazioni dettagliate
    """
    job_manager = get_job_manager()
    status = job_manager.get_job(job_id)
    
    if not status:
        raise HTTPException(404, "Job non trovato")
    
    return status


@app.get("/jobs")
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
    _auth: None = Depends(api_key_auth)
):
    """
    Lista job (richiede autenticazione se abilitata).
    
    Query params:
    - status: filtra per status (processing, completed, error)
    - limit: numero massimo risultati (default 50)
    """
    job_manager = get_job_manager()
    jobs = job_manager.list_jobs(status=status, limit=limit)
    return {"jobs": jobs, "total": len(jobs)}


@app.get("/stats")
async def get_stats(_auth: None = Depends(api_key_auth)):
    """
    Statistiche sistema (richiede autenticazione se abilitata).
    """
    job_manager = get_job_manager()
    file_manager = get_file_manager()
    
    return {
        "jobs": job_manager.get_stats(),
        "storage": file_manager.get_all_stats(),
        "workers": executor._max_workers
    }


@app.post("/cleanup")
async def manual_cleanup(_auth: None = Depends(api_key_auth)):
    """
    Cleanup manuale file vecchi (richiede autenticazione se abilitata).
    """
    file_manager = get_file_manager()
    job_manager = get_job_manager()
    
    file_stats = file_manager.cleanup_all()
    job_count = job_manager.cleanup_old_jobs()
    
    return {
        "files_deleted": file_stats,
        "jobs_deleted": job_count,
        "message": "Cleanup completato"
    }


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
    
    raise HTTPException(404, "Audio non trovato")


@app.get("/audio/{job_id}/vocals")
async def get_vocal_audio(job_id: str):
    """Download traccia vocale isolata."""
    for ext in [".wav", ".mp3"]:
        vocal_path = OUTPUT_DIR / f"{job_id}_vocals{ext}"
        if vocal_path.exists():
            return FileResponse(
                vocal_path,
                media_type="audio/wav" if ext == ".wav" else "audio/mpeg",
                filename=f"{job_id}_vocals{ext}"
            )
    
    raise HTTPException(404, "Audio vocale non trovato")


@app.get("/audio/{job_id}/instrumental")
async def get_instrumental_audio(job_id: str):
    """Download traccia strumentale."""
    for ext in [".wav", ".mp3"]:
        instrumental_path = OUTPUT_DIR / f"{job_id}_instrumental{ext}"
        if instrumental_path.exists():
            return FileResponse(
                instrumental_path,
                media_type="audio/wav" if ext == ".wav" else "audio/mpeg",
                filename=f"{job_id}_instrumental{ext}"
            )
    
    raise HTTPException(404, "Audio strumentale non trovato")

@app.get("/metrics")
async def metrics_endpoint():
    """
    Prometheus metrics endpoint.
    
    Returns metrics in Prometheus text format.
    Utile per monitoring con Prometheus/Grafana.
    """
    metrics_data = get_metrics()
    return Response(content=metrics_data, media_type="text/plain")

