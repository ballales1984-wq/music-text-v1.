"""
Custom errors for the domain layer.
"""
from typing import Optional


class DomainError(Exception):
    """Base domain error."""
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class SeparationError(DomainError):
    """Error during audio separation."""
    def __init__(self, message: str):
        super().__init__(message, "SEPARATION_ERROR")


class TranscriptionError(DomainError):
    """Error during transcription."""
    def __init__(self, message: str):
        super().__init__(message, "TRANSCRIPTION_ERROR")


class TextGenerationError(DomainError):
    """Error during text generation."""
    def __init__(self, message: str):
        super().__init__(message, "TEXT_GENERATION_ERROR")


class StorageError(DomainError):
    """Error during file storage operations."""
    def __init__(self, message: str):
        super().__init__(message, "STORAGE_ERROR")


class JobNotFoundError(DomainError):
    """Job not found."""
    def __init__(self, job_id: str):
        super().__init__(f"Job {job_id} not found", "JOB_NOT_FOUND")
        self.job_id = job_id


class InvalidInputError(DomainError):
    """Invalid input parameter."""
    def __init__(self, message: str):
        super().__init__(message, "INVALID_INPUT")
