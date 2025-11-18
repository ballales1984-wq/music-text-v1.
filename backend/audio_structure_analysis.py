"""
Analisi struttura audio per identificare ritornello/strofa
basandosi su cambiamenti di intensità, energia, pattern ripetitivi
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)

LIBROSA_AVAILABLE = False
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    logger.warning("Librosa non disponibile - analisi struttura audio disabilitata")


def analyze_audio_structure(audio_path: Path, sr: Optional[int] = None) -> Dict:
    """
    Analizza struttura audio (ritornello/strofa) basandosi su:
    - Cambiamenti di intensità/energia
    - Pattern ripetitivi di energia
    - Variazioni di volume
    - Segmentazione automatica
    
    Returns:
    {
        "segments": [{"start": 0.0, "end": 10.0, "type": "verse|chorus", "intensity": 0.8}],
        "chorus_candidates": [{"start": 20.0, "end": 30.0, "confidence": 0.9}],
        "verse_candidates": [...],
        "structure": {"verses": [...], "chorus": {...}},
        "intensity_profile": [(time, intensity), ...],
        "word_intervals": [{"word": "...", "start": 0.0, "end": 1.0, "intensity": 0.7}]
    }
    """
    if not LIBROSA_AVAILABLE:
        return {
            "segments": [],
            "chorus_candidates": [],
            "verse_candidates": [],
            "structure": {"verses": [], "chorus": None},
            "intensity_profile": [],
            "word_intervals": [],
            "available": False
        }
    
    try:
        # Carica audio
        y, sample_rate = librosa.load(str(audio_path), sr=sr, mono=True)
        duration = len(y) / sample_rate
        
        logger.info(f"🎵 Analisi struttura audio: {duration:.2f}s")
        
        # 1. Calcola profilo di intensità/energia nel tempo
        intensity_profile = _compute_intensity_profile(y, sample_rate)
        
        # 2. Identifica segmenti basati su cambiamenti di intensità
        segments = _segment_by_intensity(intensity_profile, duration)
        
        # 3. Identifica ritornello (segmenti ripetitivi ad alta intensità)
        chorus_candidates = _identify_chorus_candidates(intensity_profile, segments, duration)
        
        # 4. Identifica strofe (segmenti con pattern simile ma meno intensi)
        verse_candidates = _identify_verse_candidates(intensity_profile, segments, chorus_candidates, duration)
        
        # 5. Crea struttura finale
        structure = _build_structure(chorus_candidates, verse_candidates, duration)
        
        # 6. Estrai intervalli approssimativi per parole (basati su onset detection)
        word_intervals = _estimate_word_intervals(y, sample_rate)
        
        logger.info(f"✅ Struttura identificata: {len(verse_candidates)} strofe, {len(chorus_candidates)} ritornelli")
        
        return {
            "segments": segments,
            "chorus_candidates": chorus_candidates,
            "verse_candidates": verse_candidates,
            "structure": structure,
            "intensity_profile": intensity_profile,
            "word_intervals": word_intervals,
            "available": True
        }
        
    except Exception as e:
        logger.error(f"Errore analisi struttura audio: {e}", exc_info=True)
        return {
            "segments": [],
            "chorus_candidates": [],
            "verse_candidates": [],
            "structure": {"verses": [], "chorus": None},
            "intensity_profile": [],
            "word_intervals": [],
            "available": False
        }


def _compute_intensity_profile(y: np.ndarray, sr: int, hop_length: int = 512) -> List[Tuple[float, float]]:
    """
    Calcola profilo di intensità nel tempo usando RMS energy.
    Returns: [(time, intensity), ...]
    """
    # RMS (Root Mean Square) energy
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_length)
    
    # Normalizza (0-1)
    rms_normalized = (rms - rms.min()) / (rms.max() - rms.min() + 1e-10)
    
    profile = [(float(t), float(intensity)) for t, intensity in zip(times, rms_normalized)]
    return profile


def _segment_by_intensity(intensity_profile: List[Tuple[float, float]], duration: float, 
                         window_size: float = 3.0) -> List[Dict]:
    """
    Segmenta audio in base a cambiamenti di intensità.
    """
    if not intensity_profile:
        return []
    
    segments = []
    current_start = 0.0
    current_intensity = intensity_profile[0][1] if intensity_profile else 0.5
    
    threshold = 0.15  # Soglia per cambiamento significativo
    
    for i in range(1, len(intensity_profile)):
        time, intensity = intensity_profile[i]
        
        # Se c'è un cambiamento significativo
        if abs(intensity - current_intensity) > threshold:
            segments.append({
                "start": current_start,
                "end": time,
                "intensity": current_intensity,
                "duration": time - current_start
            })
            current_start = time
            current_intensity = intensity
    
    # Aggiungi ultimo segmento
    if current_start < duration:
        segments.append({
            "start": current_start,
            "end": duration,
            "intensity": current_intensity,
            "duration": duration - current_start
        })
    
    return segments


def _identify_chorus_candidates(intensity_profile: List[Tuple[float, float]], 
                                segments: List[Dict], duration: float) -> List[Dict]:
    """
    Identifica ritornelli:
    - Alta intensità media
    - Pattern ripetitivi
    - Durata tipica 15-30 secondi
    """
    if not segments:
        return []
    
    # Calcola intensità media per segmento
    segment_intensities = []
    for seg in segments:
        # Media intensità nel segmento
        times_in_seg = [t for t, i in intensity_profile if seg["start"] <= t <= seg["end"]]
        if times_in_seg:
            intensities_in_seg = [i for t, i in intensity_profile if seg["start"] <= t <= seg["end"]]
            avg_intensity = np.mean(intensities_in_seg) if intensities_in_seg else seg["intensity"]
        else:
            avg_intensity = seg["intensity"]
        
        segment_intensities.append(avg_intensity)
    
    # Soglia: intensità > percentile 70
    threshold = np.percentile(segment_intensities, 70) if segment_intensities else 0.6
    
    candidates = []
    for seg, intensity in zip(segments, segment_intensities):
        # Ritornello tipico: intensità alta, durata 10-40s
        if intensity >= threshold and 10 <= seg["duration"] <= 40:
            # Confidenza basata su intensità e durata
            confidence = min(0.9, intensity * 1.2 + (0.3 if 15 <= seg["duration"] <= 30 else 0.1))
            candidates.append({
                "start": seg["start"],
                "end": seg["end"],
                "intensity": float(intensity),
                "confidence": float(confidence),
                "duration": seg["duration"]
            })
    
    return candidates


def _identify_verse_candidates(intensity_profile: List[Tuple[float, float]], 
                               segments: List[Dict], chorus_candidates: List[Dict],
                               duration: float) -> List[Dict]:
    """
    Identifica strofe:
    - Intensità media-bassa (non alta come ritornello)
    - Pattern simili tra loro
    - Non sovrapposte con ritornelli
    """
    if not segments:
        return []
    
    # Escludi segmenti già identificati come ritornelli
    chorus_ranges = [(c["start"], c["end"]) for c in chorus_candidates]
    
    candidates = []
    for seg in segments:
        # Controlla sovrapposizione con ritornelli
        is_overlapping = any(c_start <= seg["start"] < c_end or c_start < seg["end"] <= c_end 
                            for c_start, c_end in chorus_ranges)
        
        if not is_overlapping:
            # Strofa tipica: intensità media, durata 10-30s
            if 0.3 <= seg["intensity"] <= 0.8 and 8 <= seg["duration"] <= 35:
                confidence = 0.7 if seg["intensity"] >= 0.4 else 0.5
                candidates.append({
                    "start": seg["start"],
                    "end": seg["end"],
                    "intensity": float(seg["intensity"]),
                    "confidence": float(confidence),
                    "duration": seg["duration"]
                })
    
    return candidates


def _build_structure(chorus_candidates: List[Dict], verse_candidates: List[Dict], 
                    duration: float) -> Dict:
    """
    Costruisce struttura finale combinando strofe e ritornelli.
    """
    # Ordina per tempo
    all_segments = sorted(chorus_candidates + verse_candidates, key=lambda x: x["start"])
    
    verses = []
    chorus = None
    
    if chorus_candidates:
        # Ritornello più probabile (confidenza alta, intensità alta)
        best_chorus = max(chorus_candidates, key=lambda x: x.get("confidence", 0) * x.get("intensity", 0))
        chorus = {
            "start": best_chorus["start"],
            "end": best_chorus["end"],
            "intensity": best_chorus["intensity"],
            "confidence": best_chorus["confidence"]
        }
    
    # Strofe sono i segmenti non-ritornello
    for candidate in verse_candidates:
        verses.append({
            "start": candidate["start"],
            "end": candidate["end"],
            "intensity": candidate["intensity"],
            "confidence": candidate["confidence"]
        })
    
    return {
        "verses": verses,
        "chorus": chorus,
        "total_duration": duration
    }


def _estimate_word_intervals(y: np.ndarray, sr: int) -> List[Dict]:
    """
    Stima intervalli tra parole usando onset detection.
    Non estrae le parole reali, ma identifica punti di inizio parola.
    """
    try:
        # Onset detection (punti dove iniziano nuovi eventi sonori, tipicamente parole)
        onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time', backtrack=True)
        
        intervals = []
        for i in range(len(onsets) - 1):
            start = onsets[i]
            end = onsets[i + 1]
            
            # Estrai intensità nel segmento
            start_frame = librosa.time_to_samples(start, sr=sr)
            end_frame = librosa.time_to_samples(end, sr=sr)
            segment = y[start_frame:end_frame] if end_frame <= len(y) else y[start_frame:]
            
            if len(segment) > 0:
                intensity = float(np.sqrt(np.mean(segment**2)))  # RMS
            else:
                intensity = 0.0
            
            intervals.append({
                "start": float(start),
                "end": float(end),
                "duration": float(end - start),
                "intensity": intensity
            })
        
        return intervals
        
    except Exception as e:
        logger.warning(f"Errore estrazione intervalli: {e}")
        return []

