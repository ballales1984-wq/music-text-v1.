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
import os

from transcription import transcribe_audio
from text_structure import extract_structure
from syllable_counter import count_syllables_in_text, get_key_words
from lyrics_generator_simple import generate_english_text_from_vocals, translate_to_italian, generate_lyrics_variants
from text_cleaner import clean_and_filter_text, validate_text_quality
from separation import separate_vocals_and_instrumental
from audio_analysis import analyze_audio_features

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

# La funzione translate_to_italian è importata da lyrics_generator_simple


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
            raise HTTPException(400, "File troppo piccolo")
        
        # Crea job ID
        job_id = str(uuid.uuid4())
        job_status[job_id] = {
            "status": "processing",
            "progress": 0,
            "step": "Caricamento file...",
            "job_id": job_id
        }
        
        # Salva file
        audio_path = UPLOAD_DIR / f"{job_id}{ext}"
        with open(audio_path, "wb") as f:
            f.write(file_content)
        
        logger.info(f"[{job_id}] File caricato: {audio_path.name} ({file_size / (1024*1024):.2f}MB)")
        
        # Processa in background
        executor.submit(process_audio, job_id, audio_path)
        
        return {"job_id": job_id, "message": "File caricato, processamento avviato"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore upload: {e}")
        if job_id and job_id in job_status:
            job_status[job_id]["status"] = "error"
            job_status[job_id]["error"] = str(e)
        raise HTTPException(500, str(e))


def process_audio(job_id: str, audio_path: Path):
    """Processa l'audio - separazione, trascrizione, generazione."""
    try:
        job_status[job_id]["progress"] = 10
        job_status[job_id]["step"] = "Separazione voce..."
        
        # Step 1: Separa voce
        vocal_path, instrumental_path = separate_vocals_and_instrumental(str(audio_path))
        job_status[job_id]["progress"] = 30
        job_status[job_id]["step"] = "Trascrizione voce..."
        
        # Step 2: Trascrivi
        transcription = transcribe_audio(vocal_path)
        job_status[job_id]["progress"] = 50
        job_status[job_id]["step"] = "Analisi struttura..."
        
        # Step 3: Estrai struttura
        structure = extract_structure(transcription.get("text", ""))
        syllables = count_syllables_in_text(transcription.get("text", ""))
        key_words = get_key_words(transcription.get("text", ""))
        
        job_status[job_id]["progress"] = 70
        job_status[job_id]["step"] = "Generazione testo..."
        
        # Step 4: Genera lyrics
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
        
        job_status[job_id]["progress"] = 90
        job_status[job_id]["step"] = "Completamento..."
        
        # Traduci in italiano
        translation_cache: Dict[str, str] = {}
        final_text_italian = ""
        
        if final_text:
            final_text_italian = translate_to_italian(final_text)
            if final_text_italian:
                translation_cache[final_text] = final_text_italian
        
        # Traduci le varianti
        for variant in variants:
            variant_text = variant
            if variant_text and variant_text not in translation_cache:
                translation_cache[variant_text] = translate_to_italian(variant_text)
        
        job_status[job_id]["status"] = "completed"
        job_status[job_id]["progress"] = 100
        job_status[job_id]["step"] = "Completato"
        job_status[job_id]["result"] = {
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
            "message": "Processamento completato"
        }
        
        logger.info(f"[{job_id}] Completato in {job_status[job_id].get('elapsed', 0):.1f}s")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[{job_id}] Errore: {error_msg}")
        job_status[job_id]["status"] = "error"
        job_status[job_id]["error"] = error_msg
        job_status[job_id]["progress"] = 0


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
    """Stato del job."""
    status = job_status.get(job_id)
    
    if not status:
        raise HTTPException(404, "Job non trovato")
    
    # Se completato, restituisci direttamente il risultato
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
