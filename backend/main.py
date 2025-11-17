"""
Music Text Generator - Backend principale
Pipeline completa: separazione vocale -> analisi audio -> trascrizione -> generazione testo
"""
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import uuid
from pathlib import Path
import logging
from typing import Dict
import time

from separation import separate_vocals
from audio_analysis import analyze_audio_features, format_features_for_prompt
from transcription import transcribe_audio
from lyrics_generator import generate_lyrics

# Configurazione
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Music Text Generator", version="2.0.0")

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
    """Carica e processa file audio completo."""
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
        
        # Pipeline completa
        total_start = time.time()
        
        # Inizializza stato
        job_status[job_id] = {
            "status": "processing",
            "step": 0,
            "total_steps": 5,
            "current_step": "Separazione vocale",
            "progress": 0
        }
        
        # STEP 1: Separazione vocale
        logger.info(f"[{job_id}] Step 1/5: Separazione vocale...")
        job_status[job_id]["progress"] = 10
        job_status[job_id]["current_step"] = "Separazione vocale"
        start = time.time()
        vocal_path = separate_vocals(input_path, job_id, OUTPUT_DIR)
        logger.info(f"[{job_id}] ✅ Separazione completata in {time.time()-start:.1f}s")
        logger.info(f"[{job_id}] 📁 File vocale isolato: {vocal_path}")
        
        # STEP 2: Analisi audio avanzata (pitch, timing, metrica, envelope)
        # IMPORTANTE: Analizza SOLO la traccia vocale isolata, non la base strumentale!
        logger.info(f"[{job_id}] Step 2/5: Analisi audio avanzata della VOCE ISOLATA (pitch, timing, metrica)...")
        logger.info(f"[{job_id}] ⚠️  Analizzando: {vocal_path.name} (traccia vocale isolata)")
        job_status[job_id]["progress"] = 30
        job_status[job_id]["current_step"] = "Analisi audio avanzata (voce isolata)"
        start = time.time()
        audio_features = analyze_audio_features(vocal_path)
        audio_features_str = format_features_for_prompt(audio_features)
        logger.info(f"[{job_id}] ✅ Analisi completata: tempo={audio_features.get('tempo', 'N/A')} BPM, {len(audio_features.get('notes', []))} note")
        
        # STEP 3: Trascrizione Whisper
        # IMPORTANTE: Trascrive SOLO la traccia vocale isolata!
        logger.info(f"[{job_id}] Step 3/5: Trascrizione Whisper della VOCE ISOLATA...")
        logger.info(f"[{job_id}] ⚠️  Trascrivendo: {vocal_path.name} (traccia vocale isolata)")
        job_status[job_id]["progress"] = 50
        job_status[job_id]["current_step"] = "Trascrizione Whisper (voce isolata)"
        start = time.time()
        transcription = transcribe_audio(vocal_path)
        transcription["audio_features"] = audio_features
        transcription["audio_features_str"] = audio_features_str
        logger.info(f"[{job_id}] ✅ Trascrizione completata in {time.time()-start:.1f}s")
        
        # STEP 4: Generazione testo in inglese (usa pitch, timing, metrica)
        logger.info(f"[{job_id}] Step 4/5: Generazione testo in inglese (varianti)...")
        job_status[job_id]["progress"] = 80
        job_status[job_id]["current_step"] = "Generazione testo (varianti)"
        start = time.time()
        lyrics_result = generate_lyrics(transcription, num_variants=3)
        logger.info(f"[{job_id}] ✅ Generazione completata: {lyrics_result['total']} varianti in {time.time()-start:.1f}s")
        
        # Completato
        total_time = time.time() - total_start
        logger.info(f"[{job_id}] 🎉 Processamento completo in {total_time:.1f}s")
        job_status[job_id]["progress"] = 100
        job_status[job_id]["status"] = "completed"
        job_status[job_id]["current_step"] = "Completato"
        
        return JSONResponse({
            "job_id": job_id,
            "status": "completed",
            "vocal_audio_url": f"/results/{job_id}/vocal",
            "raw_transcription": transcription,
            "final_text": lyrics_result["variants"][0]["full_text"],  # Default: prima variante
            "lyrics_variants": lyrics_result,  # Tutte le varianti
            "audio_features": {
                "tempo": audio_features.get("tempo"),
                "notes_count": len(audio_features.get("notes", [])),
                "melody": audio_features.get("melody", [])[:10]  # Prime 10 note
            },
            "message": "Processamento completato"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore: {str(e)}", exc_info=True)
        raise HTTPException(500, detail=f"Errore: {str(e)}")


@app.get("/results/{job_id}/vocal")
async def get_vocal_audio(job_id: str):
    """Download traccia vocale isolata."""
    vocal_path = OUTPUT_DIR / f"{job_id}_vocals.wav"
    if not vocal_path.exists():
        raise HTTPException(404, "File non trovato")
    return FileResponse(vocal_path, media_type="audio/wav", filename=f"{job_id}_vocals.wav")


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok", "message": "Server operativo"}


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """Stato job."""
    if job_id not in job_status:
        raise HTTPException(404, "Job non trovato")
    return job_status[job_id]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

