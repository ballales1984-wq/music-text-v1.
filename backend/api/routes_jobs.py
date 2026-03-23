"""
API routes for job management.
"""
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse, FileResponse

from domain.models import Job, JobStatus
from domain.errors import JobNotFoundError, InvalidInputError
from services.job_service import JobService
from services.pipeline_service import PipelineService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["jobs"])

# Global services (will be injected via dependency)
_job_service: Optional[JobService] = None
_pipeline_service: Optional[PipelineService] = None


def set_services(job_service: JobService, pipeline_service: PipelineService):
    """Set global services for routes."""
    global _job_service, _pipeline_service
    _job_service = job_service
    _pipeline_service = pipeline_service


@router.post("/jobs", status_code=201)
async def create_job(
    file: UploadFile = File(...),
    mood: str = Query(None),
    style: str = Query(None),
    whisper_model: str = Query("medium")
):
    """
    Create a new job for audio processing.
    
    Parameters:
    - file: Audio file (MP3, WAV, M4A, FLAC)
    - mood: Optional mood (happy, sad, angry, romantic, dreamy, energetic)
    - style: Optional style (pop, rock, rap, ballad, electronic, folk)
    - whisper_model: Whisper model (base, small, medium, large-v3)
    
    Returns:
    - job_id: ID for tracking the job
    """
    # Validate mood
    valid_moods = {"happy", "sad", "angry", "romantic", "dreamy", "energetic", None}
    if mood and mood not in valid_moods:
        raise HTTPException(400, f"Invalid mood. Use: {', '.join(sorted(valid_moods - {None}))}")
    
    # Validate style
    valid_styles = {"pop", "rock", "rap", "ballad", "electronic", "folk", None}
    if style and style not in valid_styles:
        raise HTTPException(400, f"Invalid style. Use: {', '.join(sorted(valid_styles - {None}))}")
    
    # Validate file
    if not file.filename:
        raise HTTPException(400, "No filename provided")
    
    ext = Path(file.filename).suffix.lower()
    if ext not in {".mp3", ".wav", ".m4a", ".flac"}:
        raise HTTPException(400, f"Invalid format. Use: mp3, wav, m4a, flac")
    
    # Read file
    try:
        file_content = await file.read()
    except Exception as e:
        raise HTTPException(400, f"Cannot read file: {e}")
    
    # Check size (max 100MB)
    if len(file_content) > 100 * 1024 * 1024:
        raise HTTPException(400, "File too large (max 100MB)")
    
    if len(file_content) < 1024:
        raise HTTPException(400, "File too small")
    
    # Create job
    try:
        job = _job_service.create_job(
            filename=file.filename,
            file_content=file_content,
            mood=mood,
            style=style,
            whisper_model=whisper_model
        )
    except Exception as e:
        logger.error(f"Failed to create job: {e}")
        raise HTTPException(500, f"Failed to create job: {e}")
    
    # Start processing in background
    import threading
    thread = threading.Thread(
        target=_process_job_background,
        args=(job.id,)
    )
    thread.daemon = True
    thread.start()
    
    return {
        "job_id": job.id,
        "status": job.status.value,
        "message": "Job created, processing started"
    }


def _process_job_background(job_id: str):
    """Process job in background thread."""
    try:
        job = _job_service.get_job(job_id)
        _pipeline_service.run_pipeline(job, _job_service.output_dir)
        _job_service.update_job(job)
    except Exception as e:
        logger.error(f"Background processing failed for {job_id}: {e}")
        job = _job_service.get_job(job_id)
        job.error_message = str(e)
        job.status = JobStatus.ERROR
        _job_service.update_job(job)


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """
    Get job status and results.
    
    Returns:
    - Job status, progress, results (if complete)
    """
    try:
        job = _job_service.get_job(job_id)
        return job.to_dict()
    except JobNotFoundError:
        raise HTTPException(404, f"Job {job_id} not found")


@router.get("/jobs")
async def list_jobs(limit: int = Query(20, le=100)):
    """
    List recent jobs.
    """
    jobs = _job_service.list_jobs(limit=limit)
    return {
        "jobs": [job.to_dict() for job in jobs],
        "count": len(jobs)
    }


@router.get("/audio/{job_id}")
async def get_original_audio(job_id: str):
    """Get original audio file."""
    try:
        job = _job_service.get_job(job_id)
        if not job.original_audio_path:
            raise HTTPException(404, "Original audio not found")
        
        path = Path(job.original_audio_path)
        if not path.exists():
            raise HTTPException(404, "File not found")
        
        return FileResponse(path, media_type="audio/mpeg")
    except JobNotFoundError:
        raise HTTPException(404, f"Job {job_id} not found")


@router.get("/audio/{job_id}/vocals")
async def get_vocal_audio(job_id: str):
    """Get isolated vocal audio."""
    try:
        job = _job_service.get_job(job_id)
        if not job.vocal_audio_path:
            raise HTTPException(404, "Vocal audio not found")
        
        path = Path(job.vocal_audio_path)
        if not path.exists():
            raise HTTPException(404, "File not found")
        
        return FileResponse(path, media_type="audio/wav")
    except JobNotFoundError:
        raise HTTPException(404, f"Job {job_id} not found")


@router.get("/audio/{job_id}/instrumental")
async def get_instrumental_audio(job_id: str):
    """Get instrumental audio."""
    try:
        job = _job_service.get_job(job_id)
        if not job.instrumental_audio_path:
            raise HTTPException(404, "Instrumental audio not found")
        
        path = Path(job.instrumental_audio_path)
        if not path.exists():
            raise HTTPException(404, "File not found")
        
        return FileResponse(path, media_type="audio/wav")
    except JobNotFoundError:
        raise HTTPException(404, f"Job {job_id} not found")
