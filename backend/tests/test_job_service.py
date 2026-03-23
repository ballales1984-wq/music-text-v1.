"""
Tests for job service.
"""
import pytest
from pathlib import Path
import tempfile
import shutil

from services.job_service import JobService
from domain.models import Job, JobStatus


class TestJobService:
    """Test JobService."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories."""
        temp_dir = tempfile.mkdtemp()
        upload_dir = Path(temp_dir) / "uploads"
        output_dir = Path(temp_dir) / "outputs"
        
        yield upload_dir, output_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    def test_create_job(self, temp_dirs):
        """Test job creation from file."""
        upload_dir, output_dir = temp_dirs
        service = JobService(upload_dir, output_dir)
        
        file_content = b"fake audio data"
        
        job = service.create_job(
            filename="test.mp3",
            file_content=file_content,
            mood="happy",
            style="pop"
        )
        
        assert job.id is not None
        assert job.mood == "happy"
        assert job.style == "pop"
        assert job.status == JobStatus.PENDING
        
        # Check file was saved
        assert Path(job.original_audio_path).exists()
    
    def test_get_job(self, temp_dirs):
        """Test job retrieval."""
        upload_dir, output_dir = temp_dirs
        service = JobService(upload_dir, output_dir)
        
        file_content = b"test data"
        job = service.create_job("test.wav", file_content)
        
        retrieved = service.get_job(job.id)
        
        assert retrieved.id == job.id
    
    def test_get_job_not_found(self, temp_dirs):
        """Test job not found error."""
        upload_dir, output_dir = temp_dirs
        service = JobService(upload_dir, output_dir)
        
        from domain.errors import JobNotFoundError
        
        with pytest.raises(JobNotFoundError):
            service.get_job("nonexistent-id")
    
    def test_list_jobs(self, temp_dirs):
        """Test job listing."""
        upload_dir, output_dir = temp_dirs
        service = JobService(upload_dir, output_dir)
        
        # Create multiple jobs
        for i in range(3):
            service.create_job(f"test{i}.wav", b"data")
        
        jobs = service.list_jobs(limit=10)
        
        assert len(jobs) == 3
    
    def test_job_file_extension(self, temp_dirs):
        """Test file extension handling."""
        upload_dir, output_dir = temp_dirs
        service = JobService(upload_dir, output_dir)
        
        # Test different extensions
        for ext in [".mp3", ".wav", ".m4a", ".flac"]:
            job = service.create_job(f"test{ext}", b"data")
            path = Path(job.original_audio_path)
            assert path.suffix == ext
    
    def test_invalid_extension(self, temp_dirs):
        """Test default extension for unknown formats."""
        upload_dir, output_dir = temp_dirs
        service = JobService(upload_dir, output_dir)
        
        job = service.create_job("test.xyz", b"data")
        
        # Should default to .wav
        path = Path(job.original_audio_path)
        assert path.suffix == ".wav"
