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

from separation import separate_vocals_and_instrumental
from audio_analysis import analyze_audio_features, format_features_for_prompt
from rhythmic_analysis import analyze_rhythmic_features, format_rhythmic_features_for_prompt
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
        
        # STEP 1: Separazione VOCE e BASE
        logger.info(f"[{job_id}] Step 1/6: Separazione VOCE e BASE strumentale...")
        job_status[job_id]["progress"] = 10
        job_status[job_id]["current_step"] = "Separazione voce e base"
        job_status[job_id]["total_steps"] = 6
        start = time.time()
        vocal_path, instrumental_path = separate_vocals_and_instrumental(input_path, job_id, OUTPUT_DIR)
        logger.info(f"[{job_id}] ✅ Separazione completata in {time.time()-start:.1f}s")
        logger.info(f"[{job_id}] 📁 VOCE isolata: {vocal_path.name}")
        logger.info(f"[{job_id}] 📁 BASE strumentale: {instrumental_path.name}")
        
        # STEP 2: Analisi LINGUISTICA (VOCE) - pitch, prosodia, trascrizione
        logger.info(f"[{job_id}] Step 2/6: Analisi LINGUISTICA della VOCE (pitch, prosodia)...")
        job_status[job_id]["progress"] = 20
        job_status[job_id]["current_step"] = "Analisi linguistica (voce)"
        start = time.time()
        audio_features = analyze_audio_features(vocal_path)
        audio_features_str = format_features_for_prompt(audio_features)
        logger.info(f"[{job_id}] ✅ Analisi linguistica: {len(audio_features.get('notes', []))} note, prosodia analizzata")
        
        # STEP 3: Analisi RITMICA (BASE) - BPM, beat, pattern
        logger.info(f"[{job_id}] Step 3/6: Analisi RITMICA della BASE (BPM, beat, pattern)...")
        job_status[job_id]["progress"] = 35
        job_status[job_id]["current_step"] = "Analisi ritmica (base)"
        start = time.time()
        rhythmic_features = analyze_rhythmic_features(instrumental_path)
        rhythmic_features_str = format_rhythmic_features_for_prompt(rhythmic_features)
        logger.info(f"[{job_id}] ✅ Analisi ritmica: BPM={rhythmic_features.get('tempo', 'N/A')}, {len(rhythmic_features.get('beats', []))} beat")
        
        # STEP 4: Trascrizione Whisper (VOCE)
        logger.info(f"[{job_id}] Step 4/6: Trascrizione Whisper della VOCE...")
        job_status[job_id]["progress"] = 50
        job_status[job_id]["current_step"] = "Trascrizione Whisper (voce)"
        start = time.time()
        transcription = transcribe_audio(vocal_path)
        transcription["audio_features"] = audio_features
        transcription["audio_features_str"] = audio_features_str
        transcription["rhythmic_features"] = rhythmic_features
        transcription["rhythmic_features_str"] = rhythmic_features_str
        logger.info(f"[{job_id}] ✅ Trascrizione completata in {time.time()-start:.1f}s")
        
        # STEP 5: Integrazione e Generazione testo
        # Le due parti (linguistica e ritmica) si "parlano" per generare testo finale
        logger.info(f"[{job_id}] Step 5/6: Integrazione LINGUISTICA + RITMICA per generazione testo...")
        job_status[job_id]["progress"] = 70
        job_status[job_id]["current_step"] = "Integrazione e generazione testo"
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
            "instrumental_audio_url": f"/results/{job_id}/instrumental",
            "raw_transcription": transcription,
            "final_text": lyrics_result["variants"][0]["full_text"],  # Default: prima variante
            "lyrics_variants": lyrics_result,  # Tutte le varianti
            "audio_features": {
                "tempo": audio_features.get("tempo"),
                "notes_count": len(audio_features.get("notes", [])),
                "melody": audio_features.get("melody", [])[:10]  # Prime 10 note
            },
            "rhythmic_features": {
                "tempo": float(rhythmic_features.get("tempo")) if rhythmic_features.get("tempo") else None,
                "beat_count": int(len(rhythmic_features.get("beats", []))),
                "rhythm_pattern": str(rhythmic_features.get("rhythm_pattern")) if rhythmic_features.get("rhythm_pattern") else None,
                "time_signature": str(rhythmic_features.get("time_signature")) if rhythmic_features.get("time_signature") else None
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


@app.get("/results/{job_id}/instrumental")
async def get_instrumental_audio(job_id: str):
    """Download traccia base strumentale isolata."""
    instrumental_path = OUTPUT_DIR / f"{job_id}_instrumental.wav"
    if not instrumental_path.exists():
        raise HTTPException(404, "File non trovato")
    return FileResponse(instrumental_path, media_type="audio/wav", filename=f"{job_id}_instrumental.wav")


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

