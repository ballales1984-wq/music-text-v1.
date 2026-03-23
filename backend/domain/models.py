"""
Domain models for the Music Text Generator pipeline.
Pure domain models with no external dependencies.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any


class JobStatus(str, Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class PipelineStep(str, Enum):
    """Pipeline processing steps."""
    SEPARATION = "separation"
    TRANSCRIPTION = "transcription"
    TEXT_GENERATION = "text_generation"
    COMPLETED = "completed"


@dataclass
class AudioFile:
    """Audio file metadata."""
    filename: str
    job_id: str
    path: str
    size_bytes: int
    duration_seconds: Optional[float] = None
    format: str = "unknown"
    
    @property
    def size_mb(self) -> float:
        return self.size_bytes / (1024 * 1024)


@dataclass
class Job:
    """Job domain model."""
    id: str
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    progress: float = 0.0
    current_step: Optional[PipelineStep] = None
    error_message: Optional[str] = None
    
    # Input parameters
    mood: Optional[str] = None
    style: Optional[str] = None
    whisper_model: str = "medium"
    
    # Audio paths
    original_audio_path: Optional[str] = None
    vocal_audio_path: Optional[str] = None
    instrumental_audio_path: Optional[str] = None
    
    # Results
    raw_transcription: Optional[str] = None
    final_lyrics: Optional[str] = None
    processing_time_seconds: Optional[float] = None
    
    # Metadata
    language: str = "en"
    confidence: float = 0.0
    
    def update_status(self, status: JobStatus, progress: float = None, step: PipelineStep = None):
        """Update job status."""
        self.status = status
        self.updated_at = datetime.now()
        if progress is not None:
            self.progress = progress
        if step is not None:
            self.current_step = step
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "status": self.status.value,
            "progress": self.progress,
            "current_step": self.current_step.value if self.current_step else None,
            "error_message": self.error_message,
            "result": {
                "vocal_url": f"/audio/{self.id}/vocals" if self.vocal_audio_path else None,
                "instrumental_url": f"/audio/{self.id}/instrumental" if self.instrumental_audio_path else None,
                "raw_transcription": self.raw_transcription,
                "final_lyrics": self.final_lyrics,
                "processing_time": self.processing_time_seconds,
                "language": self.language,
                "confidence": self.confidence,
            } if self.status == JobStatus.DONE else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass
class PipelineResult:
    """Result of the complete pipeline."""
    job_id: str
    success: bool
    
    # Separation results
    vocal_path: Optional[str] = None
    instrumental_path: Optional[str] = None
    
    # Transcription results
    raw_transcription: str = ""
    language: str = "en"
    confidence: float = 0.0
    segments: List[Dict] = field(default_factory=list)
    
    # Generation results
    final_lyrics: str = ""
    
    # Timing
    processing_time: float = 0.0
    error: Optional[str] = None
