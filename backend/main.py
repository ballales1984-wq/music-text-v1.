from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os
import uuid
from pathlib import Path
import logging
from typing import Dict

from separation import separate_vocals
from transcription import transcribe_audio
from lyrics_generator import generate_lyrics
from vocal_detection import detect_vocal_segments, extract_vocal_segments
from audio_analysis import analyze_audio_features, format_features_for_prompt

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Music Text Generator", version="1.0.0")

# CORS per permettere richieste dal frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directory per file temporanei
UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Dizionario per tracciare lo stato dei job
job_status: Dict[str, Dict] = {}


@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    """
    Endpoint per caricare un file audio e processarlo.
    Restituisce un job_id per tracciare il processo.
    """
    try:
        # Valida estensione file
        allowed_extensions = {".mp3", ".wav", ".m4a", ".flac"}
        file_ext = Path(file.filename).suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Formato file non supportato. Usa: {', '.join(allowed_extensions)}"
            )
        
        # Genera ID univoco per questo job
        job_id = str(uuid.uuid4())
        input_path = UPLOAD_DIR / f"{job_id}{file_ext}"
        
        # Salva file caricato
        with open(input_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        logger.info(f"File caricato: {input_path}, job_id: {job_id}")
        
        # Avvia processamento asincrono
        try:
            import time
            total_start = time.time()
            
            # Inizializza stato job
            job_status[job_id] = {
                "status": "processing",
                "step": 0,
                "total_steps": 5,  # Aggiornato: ora 5 step (aggiunto analisi audio)
                "current_step": "Rilevamento sezioni vocali",
                "progress": 0
            }
            
            # Step 0: Rilevamento sezioni vocali (NUOVO)
            logger.info(f"[{job_id}] ⏳ Step 0/5: Rilevamento sezioni vocali in corso...")
            job_status[job_id]["progress"] = 5
            start_time = time.time()
            vocal_segments = detect_vocal_segments(input_path, min_duration=0.5)
            elapsed = time.time() - start_time
            logger.info(f"[{job_id}] ✅ Step 0/5 completato: trovate {len(vocal_segments)} sezioni vocali in {elapsed:.1f} secondi")
            
            # Estrai segmenti vocali se necessario (opzionale, per analisi più dettagliata)
            if len(vocal_segments) > 0:
                logger.info(f"[{job_id}] Sezioni vocali rilevate: {vocal_segments}")
                # Calcola durata totale delle sezioni vocali
                total_vocal_duration = sum(end - start for start, end in vocal_segments)
                total_duration = _get_audio_duration(input_path)
                vocal_percentage = (total_vocal_duration / total_duration * 100) if total_duration > 0 else 0
                logger.info(f"[{job_id}] Durata totale sezioni vocali: {total_vocal_duration:.2f}s su {total_duration:.2f}s ({vocal_percentage:.1f}%)")
            
            job_status[job_id]["progress"] = 10
            job_status[job_id]["step"] = 1
            job_status[job_id]["current_step"] = "Separazione vocale"
            
            # Step 1: Separazione vocale
            logger.info(f"[{job_id}] ⏳ Step 1/5: Separazione vocale in corso...")
            start_time = time.time()
            vocal_path = separate_vocals(input_path, job_id, OUTPUT_DIR)
            elapsed = time.time() - start_time
            logger.info(f"[{job_id}] ✅ Step 1/5 completato in {elapsed:.1f} secondi")
            job_status[job_id]["progress"] = 25
            job_status[job_id]["step"] = 2
            job_status[job_id]["current_step"] = "Analisi audio avanzata"
            
            # Step 2a: Analisi audio avanzata (pitch, timing, envelope, melodia)
            logger.info(f"[{job_id}] ⏳ Step 2a/5: Analisi audio avanzata (pitch, timing, envelope)...")
            job_status[job_id]["progress"] = 30
            start_time = time.time()
            
            audio_features = analyze_audio_features(vocal_path)
            audio_features_str = format_features_for_prompt(audio_features)
            
            elapsed = time.time() - start_time
            logger.info(f"[{job_id}] ✅ Step 2a/5 completato in {elapsed:.1f} secondi")
            logger.info(f"[{job_id}] 📊 Features: tempo={audio_features.get('tempo', 'N/A')} BPM, {len(audio_features.get('notes', []))} note rilevate")
            
            job_status[job_id]["progress"] = 40
            job_status[job_id]["step"] = 2
            job_status[job_id]["current_step"] = "Trascrizione Whisper"
            
            # Step 2b: Trascrizione (usa info sulle sezioni vocali per migliorare)
            logger.info(f"[{job_id}] ⏳ Step 2b/5: Trascrizione con Whisper in corso...")
            logger.info(f"[{job_id}] ⚠️  NOTA: La prima volta Whisper scarica il modello (~39MB per 'tiny'), può richiedere 30-60 secondi")
            logger.info(f"[{job_id}] 📊 Processando {len(vocal_segments)} sezioni vocali rilevate")
            job_status[job_id]["progress"] = 45
            start_time = time.time()
            
            # Trascrivi l'intero file vocale (già isolato)
            raw_transcription = transcribe_audio(vocal_path)
            
            # Aggiungi informazioni sulle sezioni vocali e features audio alla trascrizione
            raw_transcription["vocal_segments"] = vocal_segments
            raw_transcription["vocal_segments_count"] = len(vocal_segments)
            raw_transcription["audio_features"] = audio_features  # Aggiungi features audio
            raw_transcription["audio_features_str"] = audio_features_str  # Stringa formattata per prompt
            if len(vocal_segments) > 0:
                total_vocal_duration = sum(end - start for start, end in vocal_segments)
                total_duration = _get_audio_duration(input_path)
                raw_transcription["vocal_percentage"] = (total_vocal_duration / total_duration * 100) if total_duration > 0 else 0
            
            elapsed = time.time() - start_time
            logger.info(f"[{job_id}] ✅ Step 2b/5 completato in {elapsed:.1f} secondi")
            job_status[job_id]["progress"] = 75
            job_status[job_id]["step"] = 3
            job_status[job_id]["current_step"] = "Generazione testo"
            
            # Step 3: Generazione testo creativo (usa info sezioni vocali + features audio)
            logger.info(f"[{job_id}] ⏳ Step 3/5: Generazione testo creativo in corso...")
            job_status[job_id]["progress"] = 80
            start_time = time.time()
            final_text = generate_lyrics(raw_transcription)
            elapsed = time.time() - start_time
            logger.info(f"[{job_id}] ✅ Step 3/5 completato in {elapsed:.1f} secondi")
            
            total_time = time.time() - total_start
            logger.info(f"[{job_id}] 🎉 Processamento completo! Tempo totale: ~{total_time:.1f} secondi")
            job_status[job_id]["progress"] = 100
            job_status[job_id]["status"] = "completed"
            job_status[job_id]["step"] = 5
            job_status[job_id]["current_step"] = "Completato"
            
            # Prepara risposta
            result = {
                "job_id": job_id,
                "status": "completed",
                "vocal_audio_url": f"/results/{job_id}/vocal",
                "raw_transcription": raw_transcription,
                "final_text": final_text,
                "vocal_segments": vocal_segments,
                "vocal_segments_count": len(vocal_segments),
                "message": "Processamento completato con successo"
            }
            
            logger.info(f"[{job_id}] Processamento completato")
            return JSONResponse(content=result)
            
        except Exception as e:
            logger.error(f"[{job_id}] Errore durante processamento: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Errore processamento: {str(e)}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Errore upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore server: {str(e)}")


@app.get("/results/{job_id}/vocal")
async def get_vocal_audio(job_id: str):
    """
    Endpoint per scaricare la traccia vocale isolata.
    """
    vocal_path = OUTPUT_DIR / f"{job_id}_vocals.wav"
    
    if not vocal_path.exists():
        raise HTTPException(status_code=404, detail="File vocale non trovato")
    
    return FileResponse(
        vocal_path,
        media_type="audio/wav",
        filename=f"{job_id}_vocals.wav"
    )


@app.get("/results/{job_id}")
async def get_results(job_id: str):
    """
    Endpoint per recuperare i risultati completi di un job.
    """
    # Cerca file di output
    vocal_path = OUTPUT_DIR / f"{job_id}_vocals.wav"
    
    if not vocal_path.exists():
        raise HTTPException(status_code=404, detail="Risultati non trovati per questo job_id")
    
    # In una versione completa, potresti salvare i risultati in un DB
    # Per ora restituiamo solo l'URL del file vocale
    return {
        "job_id": job_id,
        "vocal_audio_url": f"/results/{job_id}/vocal",
        "status": "completed"
    }


@app.get("/health")
async def health_check():
    """Endpoint per verificare lo stato del server."""
    return {"status": "ok", "message": "Server operativo"}


@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """
    Endpoint per ottenere lo stato di un job.
    """
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job non trovato")
    
    return job_status[job_id]


def _get_audio_duration(audio_path: Path) -> float:
    """Helper per ottenere durata audio."""
    try:
        import librosa
        y, sr = librosa.load(str(audio_path), sr=None)
        return len(y) / sr
    except:
        try:
            import torchaudio
            wav, sr = torchaudio.load(str(audio_path), backend="soundfile")
            return wav.shape[1] / sr
        except:
            return 0.0


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

