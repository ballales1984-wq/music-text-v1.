"""
Trascrizione audio con Whisper
Estrae testo, fonemi, sillabe per generazione testo
Supporta chunking automatico per file lunghi
"""
import logging
from pathlib import Path
from typing import Dict, Optional
import librosa

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
        
        # Verifica durata audio
        try:
            duration = librosa.get_duration(path=str(audio_path))
            logger.info(f"📊 Durata audio: {duration:.2f}s ({duration/60:.2f} minuti)")
        except Exception as e:
            logger.warning(f"⚠️  Impossibile ottenere durata audio: {e}")
            duration = None
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Whisper: {model_name} su {device.upper()}")
        
        model = whisper.load_model(model_name, device=device)
        
        # Per file lunghi (>30s), usa chunking automatico
        use_chunking = duration is not None and duration > 30.0
        
        if use_chunking:
            logger.info(f"📦 File lungo ({duration:.1f}s), uso chunking automatico per processare tutto l'audio")
            result = _transcribe_long_audio(model, str(audio_path), language, device)
        else:
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
        
        logger.info(f"✅ Trascrizione: {len(text)} caratteri, lingua={language_detected}, {len(segments)} segmenti")
        
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


def _transcribe_long_audio(model, audio_path: str, language: Optional[str], device: str) -> Dict:
    """
    Trascrive audio lungo usando chunking automatico.
    Divide l'audio in chunk di 30 secondi con overlap.
    """
    try:
        import numpy as np
        import soundfile as sf
        
        # Carica audio completo
        audio, sr = librosa.load(audio_path, sr=16000, mono=True)
        duration = len(audio) / sr
        
        chunk_duration = 30.0  # Whisper ottimale: 30s
        overlap = 5.0  # Overlap per evitare tagli
        
        all_segments = []
        all_text = []
        
        chunk_idx = 0
        start_time = 0.0
        
        logger.info(f"🔄 Processando audio in chunk da {chunk_duration}s (overlap: {overlap}s)")
        
        while start_time < duration:
            end_time = min(start_time + chunk_duration, duration)
            
            # Estrai chunk
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            chunk_audio = audio[start_sample:end_sample]
            
            # Salva chunk temporaneo
            temp_chunk = Path(audio_path).parent / f"_temp_chunk_{chunk_idx}.wav"
            sf.write(str(temp_chunk), chunk_audio, sr, format='WAV', subtype='PCM_16')
            
            logger.info(f"📝 Chunk {chunk_idx + 1}: {start_time:.1f}s - {end_time:.1f}s")
            
            # Trascrivi chunk
            chunk_result = model.transcribe(
                str(temp_chunk),
                language=language,
                task="transcribe",
                verbose=False,
                fp16=(device == "cuda"),
                beam_size=1,
                best_of=1,
                temperature=0
            )
            
            # Aggiungi offset temporale ai segmenti
            chunk_segments = chunk_result.get("segments", [])
            for seg in chunk_segments:
                seg["start"] += start_time
                seg["end"] += start_time
                all_segments.append(seg)
            
            chunk_text = chunk_result.get("text", "").strip()
            if chunk_text:
                all_text.append(chunk_text)
            
            # Rimuovi chunk temporaneo
            try:
                temp_chunk.unlink()
            except:
                pass
            
            # Prossimo chunk
            chunk_idx += 1
            if end_time >= duration:
                break
            start_time = end_time - overlap
        
        logger.info(f"✅ Processati {chunk_idx} chunk, {len(all_segments)} segmenti totali")
        
        # Unisci tutto
        full_text = " ".join(all_text)
        
        return {
            "text": full_text,
            "language": chunk_result.get("language", "unknown"),
            "segments": all_segments
        }
        
    except Exception as e:
        logger.error(f"Errore chunking: {e}, fallback a trascrizione normale", exc_info=True)
        # Fallback: trascrizione normale
        return model.transcribe(
            audio_path,
            language=language,
            task="transcribe",
            verbose=False,
            fp16=(device == "cuda"),
            beam_size=1,
            best_of=1,
            temperature=0
        )


def _extract_phonemes_approximation(text: str) -> str:
    """Approssimazione fonemi da testo."""
    if not text:
        return ""
    # Semplificato: restituisce testo in minuscolo come approssimazione
    return text.lower()

