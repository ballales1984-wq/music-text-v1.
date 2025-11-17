"""
Modulo per rilevare le sezioni vocali/cantate in un file audio.
Identifica dove ci sono parti con voce per processare solo quelle.
"""
import logging
import numpy as np
from pathlib import Path
import torch
import torchaudio
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("Librosa non disponibile per rilevamento vocale avanzato")


def detect_vocal_segments(
    audio_path: Path,
    min_duration: float = 0.5,
    energy_threshold: float = 0.01
) -> List[Tuple[float, float]]:
    """
    Rileva le sezioni vocali/cantate in un file audio.
    
    Args:
        audio_path: Path del file audio
        min_duration: Durata minima di una sezione vocale (secondi)
        energy_threshold: Soglia di energia per considerare una sezione vocale
    
    Returns:
        Lista di tuple (start_time, end_time) per ogni sezione vocale rilevata
    """
    try:
        logger.info(f"Rilevamento sezioni vocali in: {audio_path}")
        
        if LIBROSA_AVAILABLE:
            return _detect_with_librosa(audio_path, min_duration, energy_threshold)
        else:
            return _detect_simple(audio_path, min_duration, energy_threshold)
            
    except Exception as e:
        logger.error(f"Errore durante rilevamento sezioni vocali: {str(e)}")
        # Fallback: considera tutto l'audio come vocale
        return [(0.0, _get_audio_duration(audio_path))]


def _detect_with_librosa(
    audio_path: Path,
    min_duration: float,
    energy_threshold: float
) -> List[Tuple[float, float]]:
    """
    Rileva sezioni vocali usando librosa (metodo avanzato).
    """
    import librosa
    
    # Carica audio
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    duration = len(y) / sr
    
    logger.info(f"Audio caricato: {duration:.2f} secondi, sample rate: {sr} Hz")
    
    # Calcola energia in finestre temporali
    frame_length = int(0.025 * sr)  # 25ms per frame
    hop_length = int(0.010 * sr)    # 10ms hop
    
    # RMS Energy
    rms = librosa.feature.rms(y=y, frame_length=frame_length, hop_length=hop_length)[0]
    
    # Spectral centroid (centroide spettrale - spesso più alto per voce)
    spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr, hop_length=hop_length)[0]
    
    # Zero crossing rate (ZCR - più alto per voce)
    zcr = librosa.feature.zero_crossing_rate(y, frame_length=frame_length, hop_length=hop_length)[0]
    
    # Normalizza le features
    rms_norm = (rms - rms.min()) / (rms.max() - rms.min() + 1e-10)
    spectral_norm = (spectral_centroids - spectral_centroids.min()) / (spectral_centroids.max() - spectral_centroids.min() + 1e-10)
    zcr_norm = (zcr - zcr.min()) / (zcr.max() - zcr.min() + 1e-10)
    
    # Combina features per score vocale
    # Voce tipicamente ha: energia media-alta, centroide medio-alto, ZCR medio
    vocal_score = (rms_norm * 0.5 + spectral_norm * 0.3 + zcr_norm * 0.2)
    
    # Applica soglia
    vocal_mask = vocal_score > energy_threshold
    
    # Trova segmenti continui
    segments = _find_continuous_segments(vocal_mask, hop_length, sr, min_duration)
    
    logger.info(f"Rilevate {len(segments)} sezioni vocali")
    for i, (start, end) in enumerate(segments):
        logger.info(f"  Sezione {i+1}: {start:.2f}s - {end:.2f}s (durata: {end-start:.2f}s)")
    
    return segments


def _detect_simple(
    audio_path: Path,
    min_duration: float,
    energy_threshold: float
) -> List[Tuple[float, float]]:
    """
    Rileva sezioni vocali usando metodo semplice (solo energia).
    """
    try:
        # Carica audio
        wav, sr = torchaudio.load(str(audio_path), backend="soundfile")
        if wav.shape[0] > 1:
            wav = wav[0:1]  # Mono
        
        audio_array = wav[0].numpy()
        duration = len(audio_array) / sr
        
        # Calcola energia in finestre
        window_size = int(0.1 * sr)  # 100ms
        hop_size = int(0.05 * sr)    # 50ms
        
        segments = []
        for i in range(0, len(audio_array) - window_size, hop_size):
            window = audio_array[i:i+window_size]
            energy = np.mean(window ** 2)
            
            if energy > energy_threshold:
                start_time = i / sr
                end_time = (i + window_size) / sr
                segments.append((start_time, end_time))
        
        # Unisci segmenti vicini
        merged = _merge_nearby_segments(segments, gap=0.2, min_duration=min_duration)
        
        logger.info(f"Rilevate {len(merged)} sezioni vocali (metodo semplice)")
        return merged if merged else [(0.0, duration)]
        
    except Exception as e:
        logger.warning(f"Errore metodo semplice: {str(e)}")
        duration = _get_audio_duration(audio_path)
        return [(0.0, duration)]


def _find_continuous_segments(
    mask: np.ndarray,
    hop_length: int,
    sr: int,
    min_duration: float
) -> List[Tuple[float, float]]:
    """
    Trova segmenti continui da una maschera booleana.
    """
    segments = []
    in_segment = False
    start_idx = 0
    
    for i, is_vocal in enumerate(mask):
        if is_vocal and not in_segment:
            # Inizio nuovo segmento
            start_idx = i
            in_segment = True
        elif not is_vocal and in_segment:
            # Fine segmento
            end_idx = i
            start_time = start_idx * hop_length / sr
            end_time = end_idx * hop_length / sr
            
            if end_time - start_time >= min_duration:
                segments.append((start_time, end_time))
            
            in_segment = False
    
    # Gestisci segmento finale
    if in_segment:
        end_time = len(mask) * hop_length / sr
        start_time = start_idx * hop_length / sr
        if end_time - start_time >= min_duration:
            segments.append((start_time, end_time))
    
    return segments


def _merge_nearby_segments(
    segments: List[Tuple[float, float]],
    gap: float = 0.2,
    min_duration: float = 0.5
) -> List[Tuple[float, float]]:
    """
    Unisce segmenti vicini (separati da meno di 'gap' secondi).
    """
    if not segments:
        return []
    
    segments = sorted(segments)
    merged = [segments[0]]
    
    for current in segments[1:]:
        last = merged[-1]
        
        # Se il segmento corrente è vicino all'ultimo, uniscili
        if current[0] - last[1] <= gap:
            merged[-1] = (last[0], current[1])
        else:
            merged.append(current)
    
    # Filtra segmenti troppo corti
    return [(s, e) for s, e in merged if e - s >= min_duration]


def _get_audio_duration(audio_path: Path) -> float:
    """Ottiene la durata di un file audio."""
    try:
        if LIBROSA_AVAILABLE:
            y, sr = librosa.load(str(audio_path), sr=None)
            return len(y) / sr
        else:
            wav, sr = torchaudio.load(str(audio_path), backend="soundfile")
            return wav.shape[1] / sr
    except:
        return 0.0


def extract_vocal_segments(
    audio_path: Path,
    segments: List[Tuple[float, float]],
    output_dir: Path,
    job_id: str
) -> List[Path]:
    """
    Estrae le sezioni vocali rilevate in file separati.
    
    Returns:
        Lista di path ai file audio estratti
    """
    extracted_files = []
    
    try:
        # Carica audio completo
        if LIBROSA_AVAILABLE:
            y, sr = librosa.load(str(audio_path), sr=None, mono=False)
            is_librosa = True
        else:
            wav, sr = torchaudio.load(str(audio_path), backend="soundfile")
            is_librosa = False
        
        for i, (start_time, end_time) in enumerate(segments):
            start_sample = int(start_time * sr)
            end_sample = int(end_time * sr)
            
            if is_librosa:
                segment_audio = y[:, start_sample:end_sample] if y.ndim > 1 else y[start_sample:end_sample]
                segment_tensor = torch.from_numpy(segment_audio)
                if segment_tensor.ndim == 1:
                    segment_tensor = segment_tensor.unsqueeze(0)
            else:
                segment_audio = wav[:, start_sample:end_sample]
                segment_tensor = segment_audio
            
            # Salva segmento
            segment_path = output_dir / f"{job_id}_vocal_segment_{i+1}.wav"
            torchaudio.save(str(segment_path), segment_tensor, sr, backend="soundfile")
            extracted_files.append(segment_path)
            
            logger.info(f"Estratto segmento {i+1}: {start_time:.2f}s - {end_time:.2f}s")
        
        return extracted_files
        
    except Exception as e:
        logger.error(f"Errore durante estrazione segmenti: {str(e)}")
        return []

