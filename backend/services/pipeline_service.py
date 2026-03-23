"""
Pipeline service - orchestrates the complete audio-to-lyrics pipeline.
"""
import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any

from domain.models import Job, JobStatus, PipelineStep, PipelineResult
from domain.errors import (
    SeparationError, 
    TranscriptionError, 
    TextGenerationError,
    InvalidInputError
)
from infrastructure.audio_separation import create_separator, AudioSeparator
from infrastructure.transcription_whisper import create_transcriber, Transcriber
from infrastructure.text_generation import create_text_generator, TextGenerator

logger = logging.getLogger(__name__)


class PipelineService:
    """
    Orchestrates the complete audio-to-lyrics pipeline.
    
    Pipeline steps:
    1. Audio separation (Demucs/fallback) - isolate vocals from instrumental
    2. Transcription (Whisper) - transcribe vocals to text
    3. Text generation (Ollama/OpenAI/fallback) - generate creative lyrics
    """
    
    def __init__(
        self,
        separator: AudioSeparator = None,
        transcriber: Transcriber = None,
        text_generator: TextGenerator = None
    ):
        self.separator = separator or create_separator()
        self.transcriber = transcriber or create_transcriber()
        self.text_generator = text_generator or create_text_generator()
        
        logger.info("PipelineService initialized")
    
    def run_pipeline(
        self,
        job: Job,
        output_dir: Path
    ) -> PipelineResult:
        """
        Run the complete pipeline for a job.
        
        Args:
            job: Job object with input parameters
            output_dir: Directory for output files
            
        Returns:
            PipelineResult with all outputs
        """
        start_time = time.time()
        result = PipelineResult(job_id=job.id, success=False)
        
        try:
            # Get input audio path
            audio_path = Path(job.original_audio_path)
            if not audio_path.exists():
                raise InvalidInputError(f"Audio file not found: {audio_path}")
            
            # ========== STEP 1: Separation ==========
            job.update_status(JobStatus.RUNNING, progress=0.1, step=PipelineStep.SEPARATION)
            logger.info(f"[{job.id}] Step 1: Audio separation...")
            
            try:
                vocal_path, instrumental_path = self.separator.separate(
                    audio_path, job.id, output_dir
                )
                result.vocal_path = str(vocal_path)
                result.instrumental_path = str(instrumental_path)
                job.vocal_audio_path = str(vocal_path)
                job.instrumental_audio_path = str(instrumental_path)
                logger.info(f"[{job.id}] Separation complete: {vocal_path.name}")
            except SeparationError as e:
                logger.warning(f"[{job.id}] Separation failed, using fallback: {e}")
                # Continue with original audio as vocals
                result.vocal_path = str(audio_path)
                result.instrumental_path = str(audio_path)
                job.vocal_audio_path = str(audio_path)
                job.instrumental_audio_path = str(audio_path)
            
            # ========== STEP 2: Transcription ==========
            job.update_status(JobStatus.RUNNING, progress=0.4, step=PipelineStep.TRANSCRIPTION)
            logger.info(f"[{job.id}] Step 2: Transcription...")
            
            vocal_audio = Path(result.vocal_path)
            transcription = self.transcriber.transcribe(
                vocal_audio,
                model_name=job.whisper_model,
                language=job.language
            )
            
            result.raw_transcription = transcription.get("text", "")
            result.language = transcription.get("language", job.language)
            result.confidence = transcription.get("confidence", 0.0)
            result.segments = transcription.get("segments", [])
            
            job.raw_transcription = result.raw_transcription
            job.confidence = result.confidence
            
            logger.info(f"[{job.id}] Transcription complete: {len(result.raw_transcription)} chars")
            
            # ========== STEP 3: Text Generation ==========
            job.update_status(JobStatus.RUNNING, progress=0.7, step=PipelineStep.TEXT_GENERATION)
            logger.info(f"[{job.id}] Step 3: Text generation...")
            
            try:
                final_lyrics = self.text_generator.generate(
                    result.raw_transcription,
                    mood=job.mood,
                    style=job.style
                )
                result.final_lyrics = final_lyrics
                job.final_lyrics = final_lyrics
                logger.info(f"[{job.id}] Generation complete: {len(final_lyrics)} chars")
            except TextGenerationError as e:
                logger.warning(f"[{job.id}] Generation failed: {e}")
                # Use raw transcription as fallback
                result.final_lyrics = result.raw_transcription
                job.final_lyrics = result.raw_transcription
            
            # ========== COMPLETE ==========
            result.success = True
            job.update_status(JobStatus.DONE, progress=1.0, step=PipelineStep.COMPLETED)
            result.processing_time = time.time() - start_time
            job.processing_time_seconds = result.processing_time
            
            logger.info(f"[{job.id}] Pipeline complete in {result.processing_time:.1f}s")
            
        except Exception as e:
            logger.error(f"[{job.id}] Pipeline failed: {e}", exc_info=True)
            result.error = str(e)
            job.error_message = str(e)
            job.update_status(JobStatus.ERROR, progress=job.progress)
        
        return result
    
    def get_available_models(self) -> Dict[str, Any]:
        """Get information about available models."""
        return {
            "separator": type(self.separator).__name__,
            "transcriber": type(self.transcriber).__name__,
            "text_generator": type(self.text_generator).__name__,
        }
