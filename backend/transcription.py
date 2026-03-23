"""
Trascrizione audio con Whisper
Estrae testo, fonemi, sillabe per generazione testo
Supporta chunking automatico per file lunghi
"""
import logging
from pathlib import Path
from typing import Dict, Optional, List, Any

logger = logging.getLogger(__name__)

WHISPER_AVAILABLE = False
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    logger.warning("Whisper non disponibile")

LIBROSA_AVAILABLE = False
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    logger.warning("Librosa non disponibile - chunking disabilitato")

SOUNDFILE_AVAILABLE = False
try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    pass


def transcribe_audio(audio_path: Path, model_name: str = "medium", language: Optional[str] = None) -> Dict:
    """
    Trascrive audio con Whisper.
    
    Modelli consigliati per lyrics/cantato (2026):
    - "medium": 769M parametri - buon equilibrio velocita'/qualita' (default)
    - "large-v3": 1.55B parametri - massima qualita' (richiede +VRAM)
    - "large-v3-turbo": 809M parametri - qualita' near-large con velocita' medium
    
    Per CPU, "medium" e' il miglior compromesso.
    Per GPU con 8GB+ VRAM, usa "large-v3" o "large-v3-turbo".
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
        
        # Verifica durata audio (solo se librosa disponibile)
        duration = None
        if LIBROSA_AVAILABLE:
            try:
                duration = librosa.get_duration(path=str(audio_path))
                logger.info(f"📊 Durata audio: {duration:.2f}s ({duration/60:.2f} minuti)")
            except Exception as e:
                logger.warning(f"⚠️  Impossibile ottenere durata audio: {e}")
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Whisper: {model_name} su {device.upper()}")
        
        model = whisper.load_model(model_name, device=device)
        
        # Per file lunghi (>30s), usa chunking automatico (solo se librosa e soundfile disponibili)
        use_chunking = LIBROSA_AVAILABLE and SOUNDFILE_AVAILABLE and duration is not None and duration > 30.0
        
        if use_chunking:
            logger.info(f"📦 File lungo ({duration:.1f}s), uso chunking automatico per processare tutto l'audio")
            result = _transcribe_long_audio(model, str(audio_path), language, device)
        else:
            # Se la lingua non è specificata, per default usiamo inglese
            if language is None:
                language = "en"

            result = model.transcribe(
                str(audio_path),
                language=language,
                task="transcribe",
                verbose=False,
                fp16=(device == "cuda"),
                # Parametri leggermente più accurati (beam search)
                beam_size=5,
                best_of=5,
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
    if not LIBROSA_AVAILABLE or not SOUNDFILE_AVAILABLE:
        raise ImportError("librosa e soundfile richiesti per chunking")
    
    try:
        import numpy as np
        
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
            if SOUNDFILE_AVAILABLE:
                sf.write(str(temp_chunk), chunk_audio, sr, format='WAV', subtype='PCM_16')
            else:
                raise ImportError("soundfile richiesto per salvare chunk")
            
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


def transcribe_audio_segments(
    audio_path: Path,
    segments_info: Dict,
    model_name: str = "small",
    language: Optional[str] = None,
    min_segment_duration: float = 0.4,
) -> Dict:
    """
    Trascrive l'audio segmento per segmento (ordine reale di ascolto),
    usando i segmenti vocali calcolati da voice_segmentation.

    Evita che Whisper inventi ripetizioni lunghe su pezzi grandi.
    """
    if not WHISPER_AVAILABLE or not LIBROSA_AVAILABLE or not SOUNDFILE_AVAILABLE:
        # Fallback: usa trascrizione normale
        logger.warning("transcribe_audio_segments: requisiti mancanti, uso transcribe_audio normale")
        return transcribe_audio(audio_path, model_name=model_name, language=language)

    try:
        import torch
        import numpy as np
        import soundfile as sf  # type: ignore
        import librosa  # type: ignore

        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Whisper (per segmenti): {model_name} su {device.upper()}")

        model = whisper.load_model(model_name, device=device)

        # Carica audio una sola volta
        y, sr = librosa.load(str(audio_path), sr=16000, mono=True)
        duration = len(y) / sr if sr > 0 else 0.0

        voice_segments: List[Dict[str, Any]] = []
        all_text_parts: List[str] = []

        for seg in segments_info.get("segments", []):
            if not seg.get("has_voice", False):
                continue

            start = float(seg.get("start", 0.0))
            end = float(seg.get("end", 0.0))
            if end <= start:
                continue

            seg_dur = end - start
            if seg_dur < min_segment_duration:
                # troppo corto, Whisper tende a inventare / non capire
                continue

            start_sample = int(start * sr)
            end_sample = int(end * sr)
            start_sample = max(0, min(start_sample, len(y)))
            end_sample = max(0, min(end_sample, len(y)))

            if end_sample <= start_sample:
                continue

            chunk_audio = y[start_sample:end_sample]

            # Salva chunk temporaneo
            temp_chunk = audio_path.parent / f"_temp_vseg_{int(start*1000)}_{int(end*1000)}.wav"
            sf.write(str(temp_chunk), chunk_audio, sr, format="WAV", subtype="PCM_16")

            # Se la lingua non è specificata, per default usiamo inglese
            seg_language = language or "en"

            seg_result = model.transcribe(
                str(temp_chunk),
                language=seg_language,
                task="transcribe",
                verbose=False,
                fp16=(device == "cuda"),
                beam_size=5,
                best_of=5,
                temperature=0,
            )

            seg_text = (seg_result.get("text") or "").strip()

            # Pulizia base: comprimi ripetizioni immediate identiche
            if seg_text:
                tokens = seg_text.split()
                cleaned_tokens: List[str] = []
                prev_token = None
                for tok in tokens:
                    if tok == prev_token:
                        # salta ripetizione immediata
                        continue
                    cleaned_tokens.append(tok)
                    prev_token = tok
                cleaned_seg_text = " ".join(cleaned_tokens)
            else:
                cleaned_seg_text = ""

            # Rimuovi chunk temporaneo
            try:
                temp_chunk.unlink()
            except Exception:
                pass

            if cleaned_seg_text:
                voice_segments.append(
                    {
                        "start": start,
                        "end": end,
                        "duration": seg_dur,
                        "text": cleaned_seg_text,
                    }
                )
                all_text_parts.append(cleaned_seg_text)

        full_text = " ".join(all_text_parts).strip()

        logger.info(
            f"✅ Trascrizione per segmenti: {len(voice_segments)} segmenti vocali, "
            f"{len(full_text)} caratteri totali"
        )

        # Stima approssimativa confidence (non abbiamo no_speech_prob per segmento qui)
        avg_confidence = 0.6 if full_text else 0.3

        phonemes = _extract_phonemes_approximation(full_text)
        has_clear_words = bool(full_text and len(full_text.split()) > 2)

        return {
            "text": full_text,
            "phonemes": phonemes,
            "language": language or "en",
            "confidence": avg_confidence,
            "has_clear_words": has_clear_words,
            "segments": voice_segments,
        }

    except Exception as e:
        logger.error(f"Errore trascrizione per segmenti: {e}", exc_info=True)
        # Fallback: trascrizione normale
        return transcribe_audio(audio_path, model_name=model_name, language=language)

