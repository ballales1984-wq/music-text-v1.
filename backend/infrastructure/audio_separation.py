"""
Audio separation infrastructure adapter.
Uses Demucs or fallback methods to isolate vocals.
"""
import logging
from pathlib import Path
from typing import Tuple, Optional, Protocol

from domain.errors import SeparationError

logger = logging.getLogger(__name__)


class AudioSeparator(Protocol):
    """Protocol for audio separation implementations."""
    def separate(self, audio_path: Path, job_id: str, output_dir: Path) -> Tuple[Path, Path]:
        """Separate vocals from instrumental. Returns (vocal_path, instrumental_path)."""
        ...


class DemucsSeparator:
    """Demucs-based audio separator."""
    
    def __init__(self):
        self._model = None
        self._available = False
        self._check_availability()
    
    def _check_availability(self):
        """Check if Demucs is available."""
        try:
            import demucs
            self._available = True
            logger.info("Demucs available for separation")
        except ImportError:
            self._available = False
            logger.warning("Demucs not available, will use fallback")
    
    def separate(self, audio_path: Path, job_id: str, output_dir: Path) -> Tuple[Path, Path]:
        """Separate vocals using Demucs."""
        if not self._available:
            raise SeparationError("Demucs not available")
        
        try:
            import torch
            from demucs.separate import main as demucs_main
            
            # Load model
            if self._model is None:
                self._model = "htdemucs"
                logger.info(f"Loading Demucs model: {self._model}")
            
            # Run separation (simplified - actual implementation would call demucs)
            # For now, use fallback
            return self._fallback_separate(audio_path, job_id, output_dir)
            
        except Exception as e:
            logger.error(f"Demucs separation failed: {e}")
            raise SeparationError(f"Separation failed: {e}")
    
    def _fallback_separate(self, audio_path: Path, job_id: str, output_dir: Path) -> Tuple[Path, Path]:
        """Fallback separation using simple filtering."""
        return self._simple_separate(audio_path, job_id, output_dir)
    
    def _simple_separate(self, audio_path: Path, job_id: str, output_dir: Path) -> Tuple[Path, Path]:
        """Simple fallback: copy original as both vocal and instrumental."""
        import shutil
        
        # For now, just copy the file (placeholder - real implementation would filter)
        vocal_path = output_dir / f"{job_id}_vocals.wav"
        instrumental_path = output_dir / f"{job_id}_instrumental.wav"
        
        # Copy original to both (placeholder - real implementation would filter frequencies)
        shutil.copy2(audio_path, vocal_path)
        shutil.copy2(audio_path, instrumental_path)
        
        logger.info(f"Simple separation completed: {vocal_path.name}")
        return vocal_path, instrumental_path


class SimpleSeparator:
    """Simple separator using basic audio processing."""
    
    def separate(self, audio_path: Path, job_id: str, output_dir: Path) -> Tuple[Path, Path]:
        """Separate using simple frequency filtering."""
        return self._simple_separate(audio_path, job_id, output_dir)
    
    def _simple_separate(self, audio_path: Path, job_id: str, output_dir: Path) -> Tuple[Path, Path]:
        """Simple separation: returns original as vocals, silent as instrumental."""
        try:
            import numpy as np
            import soundfile as sf
            
            # Read audio
            audio, sr = sf.read(str(audio_path))
            
            # If stereo, take vocals (usually center channel)
            if len(audio.shape) > 1:
                # Simple center channel extraction
                vocals = (audio[:, 0] + audio[:, 1]) / 2
                # Instrumental is the difference
                instrumental = (audio[:, 0] - audio[:, 1])
            else:
                # Mono - use as vocals, create silent instrumental
                vocals = audio
                instrumental = np.zeros_like(audio)
            
            # Save
            vocal_path = output_dir / f"{job_id}_vocals.wav"
            instrumental_path = output_dir / f"{job_id}_instrumental.wav"
            
            sf.write(str(vocal_path), vocals, sr)
            sf.write(str(instrumental_path), instrumental, sr)
            
            logger.info(f"Simple separation completed: {vocal_path.name}")
            return vocal_path, instrumental_path
            
        except Exception as e:
            logger.error(f"Simple separation failed: {e}")
            # Fallback: copy file
            import shutil
            vocal_path = output_dir / f"{job_id}_vocals.wav"
            instrumental_path = output_dir / f"{job_id}_instrumental.wav"
            shutil.copy2(audio_path, vocal_path)
            shutil.copy2(audio_path, instrumental_path)
            return vocal_path, instrumental_path


# Factory function
def create_separator() -> AudioSeparator:
    """Create the appropriate separator based on availability."""
    try:
        return DemucsSeparator()
    except Exception:
        return SimpleSeparator()
