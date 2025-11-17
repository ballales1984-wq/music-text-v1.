"""
Trascrizione audio con Whisper
Estrae testo, fonemi, sillabe per generazione testo
"""
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

WHISPER_AVAILABLE = False
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    logger.warning("Whisper non disponibile")


def transcribe_audio(audio_path: Path, model_name: str = "tiny", language: Optional[str] = None) -> Dict:
    """
    Trascrive audio con Whisper.
    Restituisce testo, fonemi, lingua, confidence.
    """
    if not WHISPER_AVAILABLE:
        return {
            "text": "[Whisper non disponibile]",
            "phonemes": "[mock]",
            "language": "en",
            "confidence": 0.5,
            "has_clear_words": False,
            "segments": []
        }
    
    try:
        import torch
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Whisper: {model_name} su {device.upper()}")
        
        model = whisper.load_model(model_name, device=device)
        
        result = model.transcribe(
            str(audio_path),
            language=language,
            task="transcribe",
            verbose=False,
            fp16=(device == "cuda"),
            beam_size=1,
            best_of=1,
            temperature=0
        )
        
        text = result.get("text", "").strip()
        language_detected = result.get("language", "unknown")
        segments = result.get("segments", [])
        
        confidences = [seg.get("no_speech_prob", 0) for seg in segments]
        avg_confidence = 1 - (sum(confidences) / len(confidences)) if confidences else 0.5
        
        phonemes = _extract_phonemes_approximation(text)
        has_clear_words = bool(text and len(text.split()) > 2)
        
        logger.info(f"✅ Trascrizione: {len(text)} caratteri, lingua={language_detected}")
        
        return {
            "text": text,
            "phonemes": phonemes,
            "language": language_detected,
            "confidence": avg_confidence,
            "has_clear_words": has_clear_words,
            "segments": segments
        }
        
    except Exception as e:
        logger.error(f"Errore trascrizione: {str(e)}", exc_info=True)
        raise Exception(f"Trascrizione fallita: {str(e)}")


def _extract_phonemes_approximation(text: str) -> str:
    """Approssimazione fonemi da testo."""
    if not text:
        return ""
    # Semplificato: restituisce testo in minuscolo come approssimazione
    return text.lower()

