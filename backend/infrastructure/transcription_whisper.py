"""
Transcription infrastructure adapter.
Uses Whisper for audio transcription.
"""
import logging
from pathlib import Path
from typing import Dict, Protocol

from domain.errors import TranscriptionError

logger = logging.getLogger(__name__)


class Transcriber(Protocol):
    """Protocol for transcription implementations."""
    def transcribe(self, audio_path: Path, model_name: str = "medium", language: str = "en") -> Dict:
        """Transcribe audio file. Returns dict with text, language, confidence, etc."""
        ...


class WhisperTranscriber:
    """Whisper-based transcriber."""
    
    def __init__(self):
        self._model = None
        self._model_name = None
    
    def transcribe(self, audio_path: Path, model_name: str = "medium", language: str = "en") -> Dict:
        """Transcribe using Whisper."""
        try:
            import whisper
            import torch
            
            # Load model (cache it)
            if self._model is None or self._model_name != model_name:
                device = "cuda" if torch.cuda.is_available() else "cpu"
                logger.info(f"Loading Whisper model: {model_name} on {device}")
                self._model = whisper.load_model(model_name, device=device)
                self._model_name = model_name
            
            # Transcribe
            result = self._model.transcribe(
                str(audio_path),
                language=language,
                task="transcribe",
                verbose=False
            )
            
            return {
                "text": result.get("text", "").strip(),
                "language": result.get("language", language),
                "confidence": result.get("avg_logprob", -1.0),
                "segments": result.get("segments", []),
                "has_clear_words": len(result.get("text", "").split()) > 5
            }
            
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            raise TranscriptionError(f"Transcription failed: {e}")
    
    def transcribe_with_timestamps(self, audio_path: Path, model_name: str = "medium") -> Dict:
        """Transcribe with word-level timestamps (for timing analysis)."""
        try:
            import whisper
            import torch
            
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = whisper.load_model(model_name, device=device)
            
            # Use word_timestamps option
            result = model.transcribe(
                str(audio_path),
                language="en",
                word_timestamps=True,
                verbose=False
            )
            
            return result
            
        except Exception as e:
            logger.warning(f"Timestamp transcription failed: {e}, using standard")
            return self.transcribe(audio_path, model_name)


class FasterWhisperTranscriber:
    """Faster-Whisper transcriber (4-10x faster)."""
    
    def __init__(self):
        self._model = None
        self._model_name = None
    
    def transcribe(self, audio_path: Path, model_name: str = "medium", language: str = "en") -> Dict:
        """Transcribe using Faster-Whisper."""
        try:
            from faster_whisper import WhisperModel
            
            # Determine compute type based on device
            import torch
            compute_type = "int8" if not torch.cuda.is_available() else "float16"
            
            # Load model (cache it)
            if self._model is None or self._model_name != model_name:
                logger.info(f"Loading Faster-Whisper model: {model_name} ({compute_type})")
                self._model = WhisperModel(
                    model_name,
                    device="cuda" if torch.cuda.is_available() else "cpu",
                    compute_type=compute_type
                )
                self._model_name = model_name
            
            # Transcribe
            segments, info = self._model.transcribe(
                str(audio_path),
                language=language,
                beam_size=5,
                vad_filter=True
            )
            
            # Collect segments
            text_segments = []
            full_text = []
            
            for segment in segments:
                text_segments.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": segment.text
                })
                full_text.append(segment.text)
            
            return {
                "text": " ".join(full_text).strip(),
                "language": language,
                "confidence": info.language_probability if hasattr(info, 'language_probability') else 0.9,
                "segments": text_segments,
                "has_clear_words": len(full_text) > 5
            }
            
        except ImportError:
            logger.warning("faster-whisper not available, falling back to standard Whisper")
            return WhisperTranscriber().transcribe(audio_path, model_name, language)
        except Exception as e:
            logger.error(f"Faster-Whisper transcription failed: {e}")
            raise TranscriptionError(f"Transcription failed: {e}")


# Factory function
def create_transcriber() -> Transcriber:
    """Create the appropriate transcriber based on availability."""
    try:
        # Try faster-whisper first (faster)
        from faster_whisper import WhisperModel
        return FasterWhisperTranscriber()
    except ImportError:
        return WhisperTranscriber()
