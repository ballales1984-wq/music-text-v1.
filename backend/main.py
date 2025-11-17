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
from denoise import denoise_vocals
from audio_analysis import analyze_audio_features, format_features_for_prompt
from rhythmic_analysis import analyze_rhythmic_features, format_rhythmic_features_for_prompt
from metric_analysis import analyze_metric_pattern, generate_metric_lyrics
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
        logger.info(f"[{job_id}] Step 1/7: Separazione VOCE e BASE strumentale...")
        job_status[job_id]["progress"] = 8
        job_status[job_id]["current_step"] = "Separazione voce e base (può richiedere 30-60s con Spleeter)"
        job_status[job_id]["total_steps"] = 7
        start = time.time()
        vocal_path, instrumental_path = separate_vocals_and_instrumental(input_path, job_id, OUTPUT_DIR)
        elapsed = time.time() - start
        logger.info(f"[{job_id}] ✅ Separazione completata in {elapsed:.1f}s")
        if elapsed > 30:
            logger.info(f"[{job_id}] ⚠️  Separazione lenta ({elapsed:.1f}s) - considera metodi più veloci per file grandi")
        logger.info(f"[{job_id}] 📁 VOCE isolata: {vocal_path.name}")
        logger.info(f"[{job_id}] 📁 BASE strumentale: {instrumental_path.name}")
        
        # STEP 2: Denoise vocale (restoration professionale)
        logger.info(f"[{job_id}] Step 2/7: Denoise e restoration vocale...")
        job_status[job_id]["progress"] = 15
        job_status[job_id]["current_step"] = "Denoise vocale (rimozione rumore)"
        start = time.time()
        vocal_clean_path = OUTPUT_DIR / f"{job_id}_vocals_clean.wav"
        vocal_clean_path = denoise_vocals(vocal_path, vocal_clean_path)
        logger.info(f"[{job_id}] ✅ Denoise completato in {time.time()-start:.1f}s")
        logger.info(f"[{job_id}] 📁 VOCE pulita: {vocal_clean_path.name}")
        
        # STEP 3: Analisi LINGUISTICA (VOCE PULITA) - pitch, prosodia, trascrizione
        logger.info(f"[{job_id}] Step 3/7: Analisi LINGUISTICA della VOCE (pitch, prosodia)...")
        job_status[job_id]["progress"] = 25
        job_status[job_id]["current_step"] = "Analisi linguistica (voce pulita)"
        start = time.time()
        audio_features = analyze_audio_features(vocal_clean_path)  # Usa voce pulita!
        audio_features_str = format_features_for_prompt(audio_features)
        logger.info(f"[{job_id}] ✅ Analisi linguistica: {len(audio_features.get('notes', []))} note, prosodia analizzata")
        
        # STEP 4: Analisi RITMICA (BASE) - BPM, beat, pattern
        logger.info(f"[{job_id}] Step 4/7: Analisi RITMICA della BASE (BPM, beat, pattern)...")
        job_status[job_id]["progress"] = 40
        job_status[job_id]["current_step"] = "Analisi ritmica (base)"
        start = time.time()
        rhythmic_features = analyze_rhythmic_features(instrumental_path)
        rhythmic_features_str = format_rhythmic_features_for_prompt(rhythmic_features)
        logger.info(f"[{job_id}] ✅ Analisi ritmica: BPM={rhythmic_features.get('tempo', 'N/A')}, {len(rhythmic_features.get('beats', []))} beat")
        
        # STEP 5: Analisi METRICA (stile Beatles) - sillabe, accenti, pattern metrico
        logger.info(f"[{job_id}] Step 5/7: Analisi METRICA (sillabe, accenti, pattern)...")
        job_status[job_id]["progress"] = 50
        job_status[job_id]["current_step"] = "Analisi metrica (sillabe e accenti)"
        start = time.time()
        # Combina features per analisi metrica
        combined_features = {**audio_features, "rhythm": rhythmic_features}
        metric_pattern = analyze_metric_pattern(combined_features)
        logger.info(f"[{job_id}] ✅ Analisi metrica: {metric_pattern['syllable_count']} sillabe, {metric_pattern['strong_beats']} accenti")
        
        # STEP 6: Trascrizione Whisper (VOCE PULITA)
        logger.info(f"[{job_id}] Step 6/7: Trascrizione Whisper della VOCE PULITA...")
        job_status[job_id]["progress"] = 60
        job_status[job_id]["current_step"] = "Trascrizione Whisper (voce pulita)"
        start = time.time()
        transcription = transcribe_audio(vocal_clean_path)  # Usa voce pulita!
        transcription["audio_features"] = audio_features
        transcription["audio_features_str"] = audio_features_str
        transcription["rhythmic_features"] = rhythmic_features
        transcription["rhythmic_features_str"] = rhythmic_features_str
        transcription["metric_pattern"] = metric_pattern
        logger.info(f"[{job_id}] ✅ Trascrizione completata in {time.time()-start:.1f}s")
        
        # STEP 7: Integrazione e Generazione testo METRICO (stile Beatles)
        # Le tre parti (linguistica, ritmica, metrica) si "parlano" per generare testo finale
        logger.info(f"[{job_id}] Step 7/7: Integrazione LINGUISTICA + RITMICA + METRICA per generazione testo...")
        job_status[job_id]["progress"] = 75
        job_status[job_id]["current_step"] = "Generazione testo metrico (stile Beatles)"
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
            "vocal_clean_audio_url": f"/results/{job_id}/vocal_clean",
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
            "metric_pattern": {
                "syllable_count": metric_pattern.get("syllable_count", 0),
                "strong_beats": metric_pattern.get("strong_beats", 0),
                "time_signature": metric_pattern.get("time_signature", "4/4")
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


@app.get("/results/{job_id}/vocal_clean")
async def get_vocal_clean_audio(job_id: str):
    """Download traccia vocale pulita (denoise)."""
    vocal_clean_path = OUTPUT_DIR / f"{job_id}_vocals_clean.wav"
    if not vocal_clean_path.exists():
        raise HTTPException(404, "File non trovato")
    return FileResponse(vocal_clean_path, media_type="audio/wav", filename=f"{job_id}_vocals_clean.wav")


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

