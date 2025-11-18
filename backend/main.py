"""
Music Text Generator - Backend semplificato
Pipeline: trascrizione -> struttura -> conteggio sillabe -> generazione testo
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import uuid
from pathlib import Path
import logging
from typing import Dict
import time

from transcription import transcribe_audio
from text_structure import extract_structure
from syllable_counter import count_syllables_in_text, get_key_words
from lyrics_generator import generate_lyrics_simple
from text_cleaner import clean_and_filter_text, validate_text_quality
from audio_structure_analysis import analyze_audio_structure
from separation import separate_vocals_and_instrumental

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


@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    """Carica e processa file audio - versione semplificata."""
    job_id = None
    try:
        # Valida formato
        allowed = {".mp3", ".wav", ".m4a", ".flac"}
        ext = Path(file.filename).suffix.lower()
        if ext not in allowed:
            raise HTTPException(400, f"Formato non supportato. Usa: {', '.join(allowed)}")
        
        # Salva file
        job_id = str(uuid.uuid4())
        input_path = UPLOAD_DIR / f"{job_id}{ext}"
        with open(input_path, "wb") as f:
            f.write(await file.read())
        
        logger.info(f"[{job_id}] File caricato: {input_path}")
        
        # Pipeline semplificata
        total_start = time.time()
        
        # Inizializza stato
        job_status[job_id] = {
            "status": "processing",
            "step": 0,
            "total_steps": 4,
            "current_step": "Separazione vocale",
            "progress": 0
        }
        
        # STEP 0: Separazione voce e base strumentale
        logger.info(f"[{job_id}] ========================================")
        logger.info(f"[{job_id}] Step 0/4: Separazione voce e base strumentale...")
        logger.info(f"[{job_id}] ========================================")
        job_status[job_id]["progress"] = 10
        job_status[job_id]["current_step"] = "Separazione vocale (Spleeter o metodi semplici)"
        start = time.time()
        
        vocal_path = None
        instrumental_path = None
        try:
            vocal_path, instrumental_path = separate_vocals_and_instrumental(input_path, job_id, OUTPUT_DIR)
            elapsed = time.time() - start
            logger.info(f"[{job_id}] ✅ Separazione completata in {elapsed:.1f}s")
            logger.info(f"[{job_id}] 📁 Voce isolata: {vocal_path.name}")
            logger.info(f"[{job_id}] 📁 Base strumentale: {instrumental_path.name}")
        except Exception as e:
            logger.warning(f"[{job_id}] ⚠️  Separazione vocale fallita: {e}, uso audio completo")
            vocal_path = input_path  # Fallback: usa audio completo
        
        # STEP 1: Trascrizione Whisper (usa voce isolata se disponibile)
        logger.info(f"[{job_id}] ========================================")
        logger.info(f"[{job_id}] Step 1/4: Trascrizione Whisper...")
        logger.info(f"[{job_id}] ========================================")
        job_status[job_id]["progress"] = 20
        job_status[job_id]["current_step"] = "Trascrizione Whisper (può richiedere 1-2 minuti)"
        start = time.time()
        audio_for_transcription = vocal_path if vocal_path else input_path
        logger.info(f"[{job_id}] 🎤 Trascrivo: {'voce isolata' if vocal_path != input_path else 'audio completo'}")
        transcription = transcribe_audio(audio_for_transcription)
        elapsed = time.time() - start
        logger.info(f"[{job_id}] ✅ Trascrizione completata in {elapsed:.1f}s")
        logger.info(f"[{job_id}] ⏱️  Tempo totale finora: {time.time() - total_start:.1f}s")
        
        raw_text = transcription.get("text", "")
        if not raw_text or len(raw_text.strip()) < 5:
            logger.warning(f"[{job_id}] ⚠️  Testo trascritto molto corto o vuoto")
        
        # STEP 1.5: Pulizia e filtraggio testo (rimuove ripetizioni eccessive)
        logger.info(f"[{job_id}] ========================================")
        logger.info(f"[{job_id}] Step 1.5/4: Pulizia e filtraggio testo...")
        logger.info(f"[{job_id}] ========================================")
        job_status[job_id]["progress"] = 30
        job_status[job_id]["current_step"] = "Pulizia testo (rimozione ripetizioni)"
        start = time.time()
        
        cleaning_result = clean_and_filter_text(raw_text)
        cleaned_text = cleaning_result["cleaned_text"]
        cleaning_stats = cleaning_result["statistics"]
        
        elapsed = time.time() - start
        logger.info(f"[{job_id}] ✅ Pulizia completata in {elapsed:.1f}s")
        logger.info(f"[{job_id}] 📊 Rimossi {cleaning_result['removed_repetitions']} ripetizioni ({cleaning_stats.get('reduction_percent', 0):.1f}% riduzione)")
        
        # Valida qualità
        quality = validate_text_quality(raw_text, cleaned_text)
        logger.info(f"[{job_id}] 📊 Qualità testo: {quality['quality_score']}/100 (ripetizioni: {quality['repetition_ratio']:.2f}x)")
        
        # Usa testo pulito per le fasi successive
        text_to_process = cleaned_text if len(cleaned_text) > 10 else raw_text
        
        # STEP 2: Estrazione struttura e sillabe
        logger.info(f"[{job_id}] ========================================")
        logger.info(f"[{job_id}] Step 2/4: Estrazione struttura e conteggio sillabe...")
        logger.info(f"[{job_id}] ========================================")
        job_status[job_id]["progress"] = 60
        job_status[job_id]["current_step"] = "Analisi struttura e sillabe"
        start = time.time()
        
        # ANALISI STRUTTURA AUDIO (intensità, cambiamenti, intervalli)
        logger.info(f"[{job_id}] 🎵 Analisi struttura audio (intensità, ritornello/strofa)...")
        audio_structure = analyze_audio_structure(input_path)
        
        # Estrai struttura (strofe/ritornello) dal testo pulito
        text_structure = extract_structure(text_to_process)
        
        # Combina struttura audio e struttura testo (priorità a audio se disponibile)
        audio_struct = audio_structure.get("structure", {})
        has_audio_structure = audio_structure.get("available", False)
        has_audio_chorus = bool(audio_struct.get("chorus"))
        has_audio_verses = len(audio_struct.get("verses", [])) > 0
        
        if has_audio_structure and (has_audio_chorus or has_audio_verses):
            # Usa struttura audio anche se solo parziale
            structure = text_structure  # Mantieni struttura testo per righe
            if has_audio_chorus:
                chorus_info = audio_struct["chorus"]
                logger.info(f"[{job_id}] ✅ Ritornello identificato dall'audio: {chorus_info['start']:.1f}s - {chorus_info['end']:.1f}s (confidenza: {chorus_info.get('confidence', 0):.2f})")
                structure["audio_chorus"] = chorus_info
            if has_audio_verses:
                logger.info(f"[{job_id}] ✅ {len(audio_struct['verses'])} strofe identificate dall'audio")
                structure["audio_verses"] = audio_struct["verses"]
        else:
            if has_audio_structure:
                logger.info(f"[{job_id}] ℹ️  Analisi audio completata ma struttura non identificata, uso solo struttura testo")
            else:
                logger.info(f"[{job_id}] ℹ️  Struttura audio non disponibile, uso solo struttura testo")
            structure = text_structure
        
        # Conta sillabe dal testo pulito
        syllables_info = count_syllables_in_text(text_to_process)
        
        # Estrai parole chiave dal testo pulito
        key_words = get_key_words(text_to_process, max_words=10)
        
        elapsed = time.time() - start
        logger.info(f"[{job_id}] ✅ Analisi completata in {elapsed:.1f}s")
        logger.info(f"[{job_id}] 📊 Struttura: {structure['total_lines']} righe, {len(structure['verses'])} strofe")
        logger.info(f"[{job_id}] 📊 Sillabe: {syllables_info['total_syllables']} totali")
        logger.info(f"[{job_id}] 📊 Parole chiave: {', '.join(key_words[:5])}")
        
        # STEP 3: Generazione testo con AI linguistica
        logger.info(f"[{job_id}] ========================================")
        logger.info(f"[{job_id}] Step 3/4: Generazione testo con AI linguistica...")
        logger.info(f"[{job_id}] ========================================")
        logger.info(f"[{job_id}] ⚠️  Questo può richiedere 1-3 minuti (generazione AI)...")
        job_status[job_id]["progress"] = 80
        job_status[job_id]["current_step"] = "Generazione testo (AI linguistica) - può richiedere 1-3 minuti"
        start = time.time()
        
        # Prepara dati per generazione (usa testo pulito)
        generation_data = {
            "text": text_to_process,  # Usa testo pulito invece di raw_text
            "structure": structure,
            "syllables": syllables_info,
            "key_words": key_words,
            "audio_structure": audio_structure  # Aggiungi analisi audio
        }
        
        lyrics_result = generate_lyrics_simple(generation_data, num_variants=3)
        elapsed = time.time() - start
        logger.info(f"[{job_id}] ✅ Generazione completata: {lyrics_result['total']} varianti in {elapsed:.1f}s")
        logger.info(f"[{job_id}] ⏱️  Tempo totale finora: {time.time() - total_start:.1f}s")
        
        # Completato
        total_time = time.time() - total_start
        logger.info(f"[{job_id}] 🎉 Processamento completo in {total_time:.1f}s")
        job_status[job_id]["progress"] = 100
        job_status[job_id]["status"] = "completed"
        job_status[job_id]["current_step"] = "Completato"
        
        return JSONResponse({
            "job_id": job_id,
            "status": "completed",
            "original_audio_url": f"/audio/{job_id}",  # Audio originale caricato
            "vocal_audio_url": f"/audio/{job_id}/vocals" if vocal_path and vocal_path != input_path else None,
            "vocal_clean_audio_url": None,  # Denoise opzionale (non implementato per ora)
            "instrumental_audio_url": f"/audio/{job_id}/instrumental" if instrumental_path else None,
            "raw_transcription": {
                "text": raw_text,
                "cleaned_text": cleaned_text,  # Testo pulito
                "cleaning_stats": cleaning_stats,  # Statistiche pulizia
                "quality": quality,  # Qualità testo
                "language": transcription.get("language", "unknown"),
                "confidence": transcription.get("confidence", 0.5)
            },
            "structure": structure,
            "syllables": {
                "total": syllables_info["total_syllables"],
                "per_line": syllables_info["lines_syllables"]
            },
            "key_words": key_words,
            "final_text": lyrics_result["variants"][0]["full_text"],  # Default: prima variante
            "lyrics_variants": lyrics_result,  # Tutte le varianti
            "message": "Processamento completato"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{job_id if job_id else 'UNKNOWN'}] Errore durante processamento: {str(e)}", exc_info=True)
        if job_id and job_id in job_status:
            job_status[job_id]["status"] = "error"
            job_status[job_id]["error"] = str(e)
            job_status[job_id]["progress"] = 0
        error_detail = f"Errore durante il processamento: {str(e)}"
        if "Whisper" in str(e) or "transcribe" in str(e).lower():
            error_detail += " (Problema con la trascrizione Whisper - verifica che il modello sia installato)"
        elif "memory" in str(e).lower() or "out of memory" in str(e).lower():
            error_detail += " (Memoria insufficiente - prova con un file più piccolo)"
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
    return job_status[job_id]


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
    uvicorn.run(app, host="0.0.0.0", port=8000)
