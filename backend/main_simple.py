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

import logging
import sys
import io
import locale

# FIX: Forza encoding UTF-8 per il logging su Windows
if sys.platform == 'win32':
    # Prova a impostare UTF-8 mode
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except:
        pass

# Crea handler con encoding esplicito UTF-8
class UTF8StreamHandler(logging.StreamHandler):
    def __init__(self, stream=None):
        # Forza encoding UTF-8
        if hasattr(stream, 'reconfigure'):
            try:
                stream.reconfigure(encoding='utf-8', errors='replace')
            except:
                pass
        super().__init__(stream)
    
    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            # Force UTF-8 encoding on write
            if hasattr(stream, 'encoding') and stream.encoding.lower() != 'utf-8':
                # Write with UTF-8 manually
                stream.write(msg + self.terminator)
            else:
                super().emit(record)
        except Exception:
            self.handleError(record)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(name)s:%(message)s',
    handlers=[
        UTF8StreamHandler(sys.stdout),
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

# Import job status manager (Redis se disponibile, fallback memoria)
try:
    from job_status_redis import job_status
    logger.info("📡 Job status: usa Redis (persistente)")
except ImportError:
    # Fallback semplice
    job_status = {}
    logger.warning("⚠️ Job status: usa memoria (NON persistente)")

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

# Job status gestito da job_status_redis.py (Redis con fallback memoria)


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
        CHUNK_SIZE = 1024 * 1024  # 1MB chunks
        
        # Salva file con streaming per evitare di caricare tutto in RAM
        job_id = str(uuid.uuid4())
        input_path = UPLOAD_DIR / f"{job_id}{ext}"
        
        total_size = 0
        with open(input_path, "wb") as f:
            while True:
                chunk = await file.read(CHUNK_SIZE)
                if not chunk:
                    break
                total_size += len(chunk)
                
                if total_size > MAX_FILE_SIZE:
                    # Cleanup on error
                    if input_path.exists():
                        input_path.unlink()
                    raise HTTPException(400, f"File troppo grande ({total_size / (1024*1024):.1f}MB). Max: 100MB")
                
                f.write(chunk)
        
        file_size = total_size
        
        if file_size < 1024:
            # Cleanup on error
            if input_path.exists():
                input_path.unlink()
            raise HTTPException(400, "File troppo piccolo o corrotto")
        
        logger.info(f"[{job_id}] File caricato: {input_path.name} ({file_size / (1024*1024):.2f}MB)")
        
        # Inizializza stato
        job_status.set(job_id, {
            "status": "processing",
            "step": 0,
            "total_steps": 3,
            "current_step": "Inizializzazione",
            "progress": 0,
            "mood": mood,
            "style": style
        })
        
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
        
        if job_id and job_status.exists(job_id):
            job_status.update(job_id, {
                "status": "error",
                "error": error_msg
            })
        
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
        # Modello base per velocita' - medium e' troppo lento su CPU
        # Usa "small" per migliore qualita' se hai GPU
        transcription = transcribe_audio(vocal_path, model_name="base", language="en")
        
        logger.info(f"[{job_id}] ✅ Trascrizione completata: {len(transcription.get('text', ''))} caratteri")
        
        # STEP 3: Genera testo in inglese dalla trascrizione (Ollama/OpenAI/fallback)
        update_status(job_id, 3, 3, "Generazione testo inglese con AI...", 80)
        logger.info(f"[{job_id}] Step 3: Generazione testo inglese dalla voce (mood={mood}, style={style})...")

        # Usa la funzione robusta per generare lyrics
        from lyrics_generator_simple import generate_lyrics_robust
        from text_cleaner import clean_and_filter_text
        
        # Pulisci la trascrizione per rimuovere ripetizioni eccessive
        transcription_text_raw = transcription.get("text", "")
        cleaned_result = clean_and_filter_text(transcription_text_raw)
        transcription_text = cleaned_result.get("cleaned_text", transcription_text_raw)
        
        logger.info(f"[{job_id}] ✅ Trascrizione pulita: {len(transcription_text)} caratteri (era {len(transcription_text_raw)})")
        final_text = generate_lyrics_robust(transcription_text, mood=mood, style=style)
        final_text = (final_text or "").strip()

        logger.info(f"[{job_id}] ✅ Testo finale generato: {len(final_text)} caratteri")

        # STEP 3.5: Traduzione in italiano
        italian_translation = ""
        if final_text and len(final_text) > 50:
            try:
                from lyrics_generator_simple import translate_to_italian
                update_status(job_id, 3, 4, "Traduzione in italiano...", 90)
                logger.info(f"[{job_id}] Step 3.5: Traduzione in italiano...")
                italian_translation = translate_to_italian(final_text)
                if italian_translation:
                    logger.info(f"[{job_id}] ✅ Traduzione italiana: {len(italian_translation)} char")
                else:
                    logger.warning(f"[{job_id}] ⚠️ Traduzione non disponibile (servizio non configurato)")
            except Exception as e:
                logger.warning(f"[{job_id}] ⚠️ Errore traduzione (non critico): {e}")

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
        
        job_status.set(job_id, {
            "status": "completed",
            "progress": 100,
            "job_id": job_id,
            "original_audio_url": f"/audio/{job_id}",
            "vocal_audio_url": f"/audio/{job_id}/vocals",
            "instrumental_audio_url": f"/audio/{job_id}/instrumental",
            "raw_transcription": transcription,
            "cleaned_transcription": transcription_text,  # Trascrizione pulita
            "voice_segments": transcription.get("segments", []),
            "word_timing": word_timing,
            "final_text": final_text,
            "italian_translation": italian_translation,
            "processing_time": total_time
        })
        
        logger.info(f"[{job_id}] 🎉 Processamento completato in {total_time:.1f}s")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[{job_id}] ❌ Errore: {error_msg}", exc_info=True)
        if job_status.exists(job_id):
            job_status.update(job_id, {
                "status": "error",
                "error": error_msg,
                "progress": 0
            })


def update_status(job_id: str, step: int, total_steps: int, current_step: str, progress: int):
    """Aggiorna stato job."""
    if job_status.exists(job_id):
        job_status.update(job_id, {
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
    status = job_status.get(job_id)
    if not status:
        raise HTTPException(404, "Job non trovato")
    
    # Se job completato, Wrappa i dati nel formato atteso dal frontend
    if status.get("status") == "completed":
        status["result"] = {
            "raw_transcription": status.get("raw_transcription"),
            "original_audio_url": status.get("original_audio_url"),
            "vocal_audio_url": status.get("vocal_audio_url"),
            "vocal_clean_audio_url": status.get("vocal_clean_audio_url"),
            "instrumental_audio_url": status.get("instrumental_audio_url"),
            "final_text": status.get("final_text"),
            "voice_segments": status.get("voice_segments", []),
            "word_timing": status.get("word_timing"),
            "processing_time": status.get("processing_time")
        }
    
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


# Modello per richiesta di varianti
class VariantsRequest(BaseModel):
    transcription: str
    mood: str | None = None
    style: str | None = None
    num_variants: int = 3


@app.post("/generate-variants")
async def generate_variants(req: VariantsRequest):
    """
    Genera multiple varianti uniche di lyrics dalla trascrizione.
    Usa diverse temperature per creare variazione:
    - 0.5: conservativo, simile all'originale
    - 0.7: bilanciato
    - 0.9: creativo, più variazioni
    """
    try:
        from lyrics_generator_simple import generate_lyrics_variants
        
        variants = generate_lyrics_variants(
            transcription=req.transcription,
            mood=req.mood,
            style=req.style,
            num_variants=req.num_variants
        )
        
        return {
            "success": True,
            "variants": variants,
            "count": len(variants)
        }
    except Exception as e:
        logger.error(f"Errore /generate-variants: {e}", exc_info=True)
        raise HTTPException(500, f"Errore generazione varianti: {str(e)}")


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

