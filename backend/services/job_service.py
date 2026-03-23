"""
Job service - manages job lifecycle and storage.
"""
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from domain.models import Job, JobStatus
from domain.errors import JobNotFoundError

logger = logging.getLogger(__name__)


class JobService:
    """
    Manages job lifecycle.
    
    Provides:
    - Job creation
    - Job status updates
    - Job retrieval
    - Job persistence
    """
    
    def __init__(self, upload_dir: Path, output_dir: Path):
        self.upload_dir = upload_dir
        self.output_dir = output_dir
        self._jobs: Dict[str, Job] = {}
        
        # Ensure directories exist
        upload_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"JobService initialized with dirs: {upload_dir}, {output_dir}")
    
    def create_job(
        self,
        filename: str,
        file_content: bytes,
        mood: Optional[str] = None,
        style: Optional[str] = None,
        whisper_model: str = "medium"
    ) -> Job:
        """
        Create a new job from uploaded file.
        
        Args:
            filename: Original filename
            file_content: File binary content
            mood: Optional mood parameter
            style: Optional style parameter
            whisper_model: Whisper model to use
            
        Returns:
            Created Job object
        """
        job_id = str(uuid.uuid4())
        
        # Determine file extension
        ext = Path(filename).suffix.lower()
        if ext not in {".mp3", ".wav", ".m4a", ".flac"}:
            ext = ".wav"
        
        # Save file
        file_path = self.upload_dir / f"{job_id}{ext}"
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Create job
        job = Job(
            id=job_id,
            status=JobStatus.PENDING,
            original_audio_path=str(file_path),
            mood=mood,
            style=style,
            whisper_model=whisper_model,
            language="en"
        )
        
        # Store job
        self._jobs[job_id] = job
        
        logger.info(f"Created job {job_id} for file {filename}")
        return job
    
    def get_job(self, job_id: str) -> Job:
        """Get job by ID."""
        if job_id not in self._jobs:
            raise JobNotFoundError(job_id)
        return self._jobs[job_id]
    
    def update_job(self, job: Job):
        """Update job in storage."""
        self._jobs[job.id] = job
    
    def list_jobs(self, limit: int = 100) -> list[Job]:
        """List recent jobs."""
        jobs = sorted(
            self._jobs.values(),
            key=lambda j: j.created_at,
            reverse=True
        )
        return jobs[:limit]
    
    def delete_old_jobs(self, days: int = 7):
        """Delete jobs older than specified days."""
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(days=days)
        to_delete = []
        
        for job_id, job in self._jobs.items():
            if job.status in (JobStatus.DONE, JobStatus.ERROR) and job.updated_at < cutoff:
                to_delete.append(job_id)
        
        for job_id in to_delete:
            job = self._jobs[job_id]
            
            # Delete files
            for path_key in ["original_audio_path", "vocal_audio_path", "instrumental_audio_path"]:
                path = getattr(job, path_key, None)
                if path and Path(path).exists():
                    try:
                        Path(path).unlink()
                    except Exception:
                        pass
            
            del self._jobs[job_id]
            logger.info(f"Deleted old job {job_id}")
        
        return len(to_delete)
