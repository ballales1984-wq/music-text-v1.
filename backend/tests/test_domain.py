"""
Tests for domain models.
"""
import pytest
from datetime import datetime

from domain.models import Job, JobStatus, PipelineStep


class TestJob:
    """Test Job domain model."""
    
    def test_create_job(self):
        """Test job creation."""
        job = Job(
            id="test-123",
            original_audio_path="/path/to/audio.wav"
        )
        
        assert job.id == "test-123"
        assert job.status == JobStatus.PENDING
        assert job.progress == 0.0
        assert job.original_audio_path == "/path/to/audio.wav"
    
    def test_update_status(self):
        """Test status updates."""
        job = Job(id="test-123")
        
        job.update_status(JobStatus.RUNNING, progress=0.5, step=PipelineStep.SEPARATION)
        
        assert job.status == JobStatus.RUNNING
        assert job.progress == 0.5
        assert job.current_step == PipelineStep.SEPARATION
    
    def test_to_dict(self):
        """Test dictionary conversion."""
        job = Job(
            id="test-123",
            status=JobStatus.DONE,
            final_lyrics="Test lyrics"
        )
        
        result = job.to_dict()
        
        assert result["id"] == "test-123"
        assert result["status"] == "done"
        assert result["result"]["final_lyrics"] == "Test lyrics"
    
    def test_job_with_mood_style(self):
        """Test job with mood and style parameters."""
        job = Job(
            id="test-456",
            mood="sad",
            style="ballad"
        )
        
        assert job.mood == "sad"
        assert job.style == "ballad"


class TestJobStatus:
    """Test JobStatus enum."""
    
    def test_status_values(self):
        """Test all status values exist."""
        assert JobStatus.PENDING.value == "pending"
        assert JobStatus.RUNNING.value == "running"
        assert JobStatus.DONE.value == "done"
        assert JobStatus.ERROR.value == "error"


class TestPipelineStep:
    """Test PipelineStep enum."""
    
    def test_step_values(self):
        """Test all step values exist."""
        assert PipelineStep.SEPARATION.value == "separation"
        assert PipelineStep.TRANSCRIPTION.value == "transcription"
        assert PipelineStep.TEXT_GENERATION.value == "text_generation"
        assert PipelineStep.COMPLETED.value == "completed"
