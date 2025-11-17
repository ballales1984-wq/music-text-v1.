"""
Processamento audio a chunk per velocizzare il processamento.
Divide l'audio in sezioni e le processa in parallelo quando possibile.
"""
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import librosa
import torch
import torchaudio
import soundfile as sf

logger = logging.getLogger(__name__)

# Dimensione chunk in secondi (ottimale per Whisper: 30s)
CHUNK_DURATION = 30.0
OVERLAP_DURATION = 1.0  # Overlap tra chunk per evitare tagli


def split_audio_into_chunks(
    audio_path: Path,
    chunk_duration: float = CHUNK_DURATION,
    overlap: float = OVERLAP_DURATION
) -> List[Tuple[Path, float, float]]:
    """
    Divide audio in chunk e salva file temporanei.
    Returns: Lista di (chunk_path, start_time, end_time)
    """
    logger.info(f"Dividendo audio in chunk: {audio_path}")
    
    try:
        # Carica audio per ottenere durata
        y, sr = librosa.load(str(audio_path), sr=None, mono=True)
        duration = len(y) / sr
        
        logger.info(f"Audio durata: {duration:.2f}s, sample_rate: {sr}Hz")
        
        if duration <= chunk_duration:
            # File troppo corto, non serve chunking
            logger.info("File troppo corto, nessun chunking necessario")
            return [(audio_path, 0.0, duration)]
        
        chunks = []
        output_dir = audio_path.parent / "chunks"
        output_dir.mkdir(exist_ok=True)
        
        chunk_idx = 0
        start_time = 0.0
        
        while start_time < duration:
            end_time = min(start_time + chunk_duration, duration)
            
            # Calcola sample range
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            
            # Estrai chunk
            chunk_audio = y[start_sample:end_sample]
            
            # Salva chunk
            chunk_path = output_dir / f"{audio_path.stem}_chunk_{chunk_idx:03d}.wav"
            sf.write(str(chunk_path), chunk_audio, sr, format='WAV', subtype='PCM_16')
            
            chunks.append((chunk_path, start_time, end_time))
            logger.info(f"Chunk {chunk_idx}: {start_time:.1f}s - {end_time:.1f}s ({end_time-start_time:.1f}s)")
            
            # Prossimo chunk con overlap
            start_time = end_time - overlap
            chunk_idx += 1
        
        logger.info(f"✅ Audio diviso in {len(chunks)} chunk")
        return chunks
        
    except Exception as e:
        logger.error(f"Errore chunking: {str(e)}", exc_info=True)
        # Fallback: ritorna file originale
        return [(audio_path, 0.0, librosa.get_duration(path=audio_path))]


def merge_chunk_results(
    chunk_results: List[dict],
    chunk_times: List[Tuple[float, float]]
) -> dict:
    """
    Unisce risultati da chunk multipli in un risultato unico.
    """
    if not chunk_results:
        return {}
    
    if len(chunk_results) == 1:
        return chunk_results[0]
    
    # Merge trascrizioni
    merged_text = " ".join([r.get("text", "").strip() for r in chunk_results if r.get("text")])
    merged_phonemes = " ".join([r.get("phonemes", "") for r in chunk_results if r.get("phonemes")])
    
    # Merge segments con offset temporale
    merged_segments = []
    for i, (result, (start, end)) in enumerate(zip(chunk_results, chunk_times)):
        segments = result.get("segments", [])
        for seg in segments:
            # Aggiungi offset temporale
            merged_seg = seg.copy()
            if "start" in merged_seg:
                merged_seg["start"] += start
            if "end" in merged_seg:
                merged_seg["end"] += start
            merged_segments.append(merged_seg)
    
    # Merge features audio (media pesata per durata)
    merged_features = {}
    total_duration = sum(end - start for _, (start, end) in zip(chunk_results, chunk_times))
    
    if total_duration > 0:
        # Tempo: media pesata
        tempos = [r.get("audio_features", {}).get("tempo") for r in chunk_results]
        valid_tempos = [t for t in tempos if t is not None]
        if valid_tempos:
            merged_features["tempo"] = np.mean(valid_tempos)
        
        # Note: unisci tutte
        all_notes = []
        for r in chunk_results:
            notes = r.get("audio_features", {}).get("notes", [])
            all_notes.extend(notes)
        merged_features["notes"] = all_notes
        merged_features["notes_count"] = len(all_notes)
    
    # Prendi lingua dalla prima chunk (di solito è la stessa)
    language = chunk_results[0].get("language", "unknown")
    confidence = np.mean([r.get("confidence", 0.5) for r in chunk_results])
    has_clear_words = any(r.get("has_clear_words", False) for r in chunk_results)
    
    return {
        "text": merged_text,
        "phonemes": merged_phonemes,
        "language": language,
        "confidence": confidence,
        "has_clear_words": has_clear_words,
        "segments": merged_segments,
        "audio_features": merged_features
    }


def cleanup_chunks(chunk_paths: List[Path]):
    """Rimuove file chunk temporanei."""
    try:
        for chunk_path in chunk_paths:
            if chunk_path.exists() and chunk_path.parent.name == "chunks":
                chunk_path.unlink()
        # Rimuovi directory chunks se vuota
        chunks_dir = chunk_paths[0].parent / "chunks" if chunk_paths else None
        if chunks_dir and chunks_dir.exists() and not any(chunks_dir.iterdir()):
            chunks_dir.rmdir()
        logger.info(f"✅ Puliti {len(chunk_paths)} chunk temporanei")
    except Exception as e:
        logger.warning(f"Errore pulizia chunk: {str(e)}")

