"""
Music Text Generator - Versione Semplificata
Pipeline: Audio → Voce Isolata → Trascrizione → Testo Inglese
"""
import sys
import io

# ============================================
# FIX CRITICO: Gestione stdout in modalità windowed
# Necessario PRIMA di importare uvicorn/fastapi
# ============================================
import logging

# In modalità windowed (--windowed), sys.stdout è None
# uvicorn cerca di chiamare stdout.isatty() e fallisce
# Creiamo un stdout fittizio se non esiste
if sys.stdout is None:
    # Crea un file-like fittizio che ignora tutto
    sys.stdout = io.StringIO()

# Configura logging base PRIMA di altri import
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(name)s:%(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
    ]
)

# Previeni uvicorn dal usare la configurazione di default che richiede isatty
# Rimuovi tutti gli handler esistenti
for logger_name in ['uvicorn', 'uvicorn.access', 'uvicorn.error']:
    logger = logging.getLogger(logger_name)
    logger.handlers = []
    logger.setLevel(logging.INFO)

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import uuid
from pathlib import Path
from typing import Dict
import time

from separation import separate_vocals_and_instrumental
from transcription import transcribe_audio
from lyrics_generator_simple import generate_english_text_from_vocals  # Attualmente non usato: generatore creativo disattivato
from memory_manager import save_lyrics_to_memory, build_memory_video, save_knowledge_base_to_memory
from song_patterns_analyzer import analyze_song_patterns, get_knowledge_base_for_memvid
from text_structure import extract_structure
from timing_analysis import build_word_timing
from grammar_corrector import suggest_corrections

# Configurazione
logger = logging.getLogger(__name__)

app = FastAPI(title="Music Text Generator - Simple", version="4.0.0-simple")

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
async def upload_audio(file: UploadFile = File(...), mood: str = None, style: str = None):
    """
    Carica e processa file audio.
    Pipeline semplificata:
    1. Isola voce dalla canzone
    2. Trascrive la voce con Whisper
    3. Genera testo in inglese
    
    Parametri opzionali:
    - mood: happy, sad, angry, romantic, dreamy, energetic
    - style: pop, rock, rap, ballad, electronic, folk
    """
    job_id = None
    try:
        # Valida mood
        valid_moods = {"happy", "sad", "angry", "romantic", "dreamy", "energetic"}
        if mood and mood not in valid_moods:
            raise HTTPException(400, f"Mood non valido. Valori: {', '.join(valid_moods)}")
        
        # Valida style
        valid_styles = {"pop", "rock", "rap", "ballad", "electronic", "folk"}
        if style and style not in valid_styles:
            raise HTTPException(400, f"Style non valido. Valori: {', '.join(valid_styles)}")
        
        logger.info(f"📝 Upload richiesto: mood={mood}, style={style}")
        # Valida file
        if not file.filename:
            raise HTTPException(400, "Nome file non valido")
        
        allowed = {".mp3", ".wav", ".m4a", ".flac"}
        ext = Path(file.filename).suffix.lower()
        if ext not in allowed:
            raise HTTPException(400, f"Formato non supportato. Formati: {', '.join(allowed)}")
        
        # Valida dimensione (max 100MB)
        MAX_FILE_SIZE = 100 * 1024 * 1024
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(400, f"File troppo grande ({file_size / (1024*1024):.1f}MB). Max: 100MB")
        
        if file_size < 1024:
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
            "total_steps": 3,
            "current_step": "Inizializzazione",
            "progress": 0,
            "mood": mood,
            "style": style
        }
        
        # Processa in thread separato
        import threading
        thread = threading.Thread(target=process_audio_simple, args=(job_id, input_path, mood, style))
        thread.daemon = True
        thread.start()
        
        return JSONResponse({
            "job_id": job_id,
            "status": "processing",
            "message": "File caricato, processamento avviato."
        })
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[{job_id if job_id else 'UNKNOWN'}] Errore: {error_msg}", exc_info=True)
        
        if job_id and job_id in job_status:
            job_status[job_id]["status"] = "error"
            job_status[job_id]["error"] = error_msg
        
        raise HTTPException(500, detail=f"Errore durante il processamento: {error_msg}")


def process_audio_simple(job_id: str, input_path: Path, mood: str = None, style: str = None):
    """Processa audio con pipeline semplificata."""
    try:
        start_time = time.time()
        
        # STEP 1: Isola voce
        update_status(job_id, 1, 3, "Isolamento voce dalla canzone...", 20)
        logger.info(f"[{job_id}] Step 1: Isolamento voce...")
        
        vocal_path, instrumental_path = separate_vocals_and_instrumental(
            input_path, job_id, OUTPUT_DIR
        )
        
        logger.info(f"[{job_id}] ✅ Voce isolata: {vocal_path.name}")
        
        # STEP 2: Trascrivi direttamente tutta la voce (segmentazione disattivata)
        update_status(job_id, 2, 3, "Trascrizione voce completa con Whisper...", 50)
        logger.info(f"[{job_id}] Step 2: Trascrizione voce COMPLETA (senza segmentazione)...")
        
        # Usiamo trascrizione diretta, lingua inglese forzata
        # Modello medium per migliore qualita' su cantato/lyrics
        transcription = transcribe_audio(vocal_path, model_name="medium", language="en")
        
        logger.info(f"[{job_id}] ✅ Trascrizione completata: {len(transcription.get('text', ''))} caratteri")
        
        # STEP 3: Genera testo in inglese dalla trascrizione (Ollama/OpenAI/fallback)
        update_status(job_id, 3, 3, "Generazione testo inglese con AI...", 80)
        logger.info(f"[{job_id}] Step 3: Generazione testo inglese dalla voce (mood={mood}, style={style})...")

        # Usa la funzione robusta per generare lyrics
        from lyrics_generator_simple import generate_lyrics_robust
        
        transcription_text = transcription.get("text", "")
        final_text = generate_lyrics_robust(transcription_text, mood=mood, style=style)
        final_text = (final_text or "").strip()

        logger.info(f"[{job_id}] ✅ Testo finale generato: {len(final_text)} caratteri")

        # Analisi timing parole (usa la trascrizione per distanza/ripetizioni/tempi)
        word_timing = build_word_timing(transcription)
        
        # Estrai struttura verse/chorus dal testo generato
        structure = None
        try:
            structure = extract_structure(final_text)
            logger.info(f"[{job_id}] ✅ Struttura estratta: {len(structure.get('verses', []))} strofe, chorus={'sì' if structure.get('chorus') else 'no'}")
        except Exception as e:
            logger.warning(f"[{job_id}] ⚠️ Errore estrazione struttura (non critico): {e}")
        
        # Analizza pattern per database conoscenza
        try:
            analyze_song_patterns(transcription, final_text, structure, metrics=None)
            logger.info(f"[{job_id}] ✅ Pattern analizzati per database conoscenza")
        except Exception as e:
            logger.warning(f"[{job_id}] ⚠️ Errore analisi pattern (non critico): {e}")
        
        # Salva in memoria video (opzionale, non blocca se fallisce)
        try:
            metadata = {
                "original_filename": input_path.name,
                "file_size_mb": input_path.stat().st_size / (1024 * 1024)
            }
            save_lyrics_to_memory(job_id, transcription, final_text, metadata)
        except Exception as e:
            logger.warning(f"[{job_id}] ⚠️ Errore salvataggio memoria (non critico): {e}")
        
        # Completa
        total_time = time.time() - start_time
        update_status(job_id, 3, 3, "Completato", 100)
        
        job_status[job_id]["status"] = "completed"
        job_status[job_id]["progress"] = 100
        job_status[job_id]["result"] = {
            "job_id": job_id,
            "original_audio_url": f"/audio/{job_id}",
            "vocal_audio_url": f"/audio/{job_id}/vocals",
            "instrumental_audio_url": f"/audio/{job_id}/instrumental",
            "raw_transcription": transcription,
            "voice_segments": transcription.get("segments", []),
            "word_timing": word_timing,
            "final_text": final_text,
            "processing_time": total_time
        }
        
        logger.info(f"[{job_id}] 🎉 Processamento completato in {total_time:.1f}s")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[{job_id}] ❌ Errore: {error_msg}", exc_info=True)
        if job_id in job_status:
            job_status[job_id]["status"] = "error"
            job_status[job_id]["error"] = error_msg
            job_status[job_id]["progress"] = 0


def update_status(job_id: str, step: int, total_steps: int, current_step: str, progress: int):
    """Aggiorna stato job."""
    if job_id in job_status:
        job_status[job_id].update({
            "step": step,
            "total_steps": total_steps,
            "current_step": current_step,
            "progress": progress
        })


@app.get("/")
async def root():
    """Endpoint root."""
    return {
        "message": "Music Text Generator API - Versione Semplificata",
        "version": "4.0.0-simple",
        "pipeline": "Audio → Voce Isolata → Trascrizione → Testo Inglese",
        "status": "operativo"
    }


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok"}


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Stato job."""
    if job_id not in job_status:
        raise HTTPException(404, "Job non trovato")
    
    status = job_status[job_id].copy()
    
    if status.get("status") == "completed" and "result" in status:
        status["result"] = status["result"]
    
    return status


class CorrectionRequest(BaseModel):
    text: str
    target_syllables: int | None = None


class UploadRequest(BaseModel):
    mood: str | None = None  # happy, sad, angry, romantic, dreamy, energetic
    style: str | None = None  # pop, rock, rap, ballad, electronic, folk


class CorrectionRequest(BaseModel):
    text: str
    target_syllables: int | None = None


@app.post("/correct_line")
async def correct_line(req: CorrectionRequest):
    """
    Corregge una singola riga/frase:
    - corregge la grammatica
    - propone alternative con metrica simile (se Ollama è disponibile)
    """
    try:
        result = suggest_corrections(req.text, target_syllables=req.target_syllables)
        return result
    except Exception as e:
        logger.error(f"Errore /correct_line: {e}", exc_info=True)
        raise HTTPException(500, f"Errore correttore: {str(e)}")


@app.get("/audio/{job_id}")
async def get_original_audio(job_id: str):
    """Download audio originale."""
    for ext in [".mp3", ".wav", ".m4a", ".flac"]:
        audio_path = UPLOAD_DIR / f"{job_id}{ext}"
        if audio_path.exists():
            content_type = {
                ".mp3": "audio/mpeg",
                ".wav": "audio/wav",
                ".m4a": "audio/mp4",
                ".flac": "audio/flac"
            }.get(ext, "audio/mpeg")
            
            return FileResponse(audio_path, media_type=content_type, filename=f"{job_id}{ext}")
    
    raise HTTPException(404, "File audio non trovato")


@app.get("/audio/{job_id}/vocals")
async def get_vocal_audio(job_id: str):
    """Download audio vocale isolato."""
    vocal_path = OUTPUT_DIR / f"{job_id}_vocals.wav"
    if vocal_path.exists():
        return FileResponse(vocal_path, media_type="audio/wav", filename=f"{job_id}_vocals.wav")
    raise HTTPException(404, "File vocale non trovato")


@app.get("/audio/{job_id}/instrumental")
async def get_instrumental_audio(job_id: str):
    """Download audio base strumentale."""
    instrumental_path = OUTPUT_DIR / f"{job_id}_instrumental.wav"
    if instrumental_path.exists():
        return FileResponse(instrumental_path, media_type="audio/wav", filename=f"{job_id}_instrumental.wav")
    raise HTTPException(404, "File strumentale non trovato")


@app.post("/memory/build")
async def build_memory():
    """Costruisce/aggiorna il video memoria con tutti i testi salvati."""
    try:
        success = build_memory_video()
        if success:
            return {"status": "success", "message": "Memoria video costruita con successo"}
        else:
            raise HTTPException(500, "Errore costruzione memoria")
    except Exception as e:
        raise HTTPException(500, f"Errore: {str(e)}")


@app.get("/memory/search")
async def search_memory(query: str, top_k: int = 5):
    """Cerca nei testi generati salvati."""
    from memory_manager import search_in_memory
    
    try:
        results = search_in_memory(query, top_k)
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(500, f"Errore ricerca: {str(e)}")


@app.post("/memory/chat")
async def chat_memory(query: str):
    """Chat con la memoria dei testi generati."""
    from memory_manager import chat_with_memory
    
    try:
        response = chat_with_memory(query)
        return {
            "query": query,
            "response": response
        }
    except Exception as e:
        raise HTTPException(500, f"Errore chat: {str(e)}")


@app.post("/knowledge/build")
async def build_knowledge_base():
    """
    Costruisce database conoscenza con pattern, frasi comuni, regole metriche.
    Analizza tutte le canzoni processate e crea database per memvid.
    """
    try:
        # Ottieni dati conoscenza base
        knowledge_data = get_knowledge_base_for_memvid()
        
        if not knowledge_data or not knowledge_data.get("chunks"):
            return {
                "status": "warning",
                "message": "Nessuna canzone analizzata ancora. Processa alcune canzoni prima.",
                "stats": knowledge_data.get("stats", {})
            }
        
        # Salva in memoria video
        success = save_knowledge_base_to_memory(knowledge_data)
        
        if success:
            return {
                "status": "success",
                "message": "Database conoscenza costruito con successo",
                "stats": knowledge_data.get("stats", {}),
                "chunks_count": len(knowledge_data.get("chunks", []))
            }
        else:
            raise HTTPException(500, "Errore costruzione database conoscenza")
            
    except Exception as e:
        logger.error(f"❌ Errore costruzione knowledge base: {e}", exc_info=True)
        raise HTTPException(500, f"Errore: {str(e)}")


@app.get("/knowledge/stats")
async def get_knowledge_stats():
    """Statistiche database conoscenza."""
    try:
        knowledge_data = get_knowledge_base_for_memvid()
        return {
            "stats": knowledge_data.get("stats", {}),
            "chunks_count": len(knowledge_data.get("chunks", []))
        }
    except Exception as e:
        raise HTTPException(500, f"Errore: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    # Configura uvicorn con logging personalizzato per evitare errore isatty()
    # Usa il modulo standard senza la configurazione di default
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        log_config=None  # Usa la configurazione basicConfig già impostata
    )

