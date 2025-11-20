"""
Segmentazione dinamica della traccia vocale

- VAD semplice basato su energia (voce / non-voce)
- Mel-spectrogram per analisi timbrica
- Onset detection per punti di inizio/frase
- Finestra mobile per segmenti adattivi
"""

import logging
from pathlib import Path
from typing import List, Dict, Any

import numpy as np

logger = logging.getLogger(__name__)

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    logger.warning("Librosa non disponibile: segmentazione avanzata disabilitata")


def _compute_energy(y: np.ndarray, frame_length: int, hop_length: int) -> np.ndarray:
    """Energia per frame (usata per VAD semplice)."""
    if len(y) == 0:
        return np.array([])
    # energia = somma dei quadrati per frame
    frames = librosa.util.frame(y, frame_length=frame_length, hop_length=hop_length)
    energy = np.sum(frames**2, axis=0)
    return energy


def segment_vocals_dynamic(
    audio_path: Path,
    sr: int = 16000,
    vad_sensitivity: float = 0.5,
    min_segment_sec: float = 1.0,
    max_segment_sec: float = 8.0,
) -> Dict[str, Any]:
    """
    Segmenta la traccia vocale usando:
    - VAD (energia) per voce/silenzio
    - onset detection per punti di taglio musicali
    - finestra mobile per segmenti dinamici

    Ritorna:
        {
          "segments": [
             {"start": float, "end": float, "has_voice": bool, "type": "voice"|"silence"},
             ...
          ],
          "sample_rate": sr,
          "duration": float
        }
    """
    if not LIBROSA_AVAILABLE:
        logger.warning("Librosa non disponibile, nessuna segmentazione vocale effettuata")
        return {
            "segments": [],
            "sample_rate": None,
            "duration": None,
        }

    try:
        y, sample_rate = librosa.load(str(audio_path), sr=sr, mono=True)
        duration = len(y) / sample_rate if sample_rate > 0 else 0.0

        if duration <= 0:
            return {"segments": [], "sample_rate": sample_rate, "duration": duration}

        logger.info(f"🎧 Segmentazione vocale: durata {duration:.2f}s, sr={sample_rate}")

        # Parametri finestra mobile (ca. 50 ms)
        frame_length = int(0.05 * sample_rate)
        hop_length = int(0.025 * sample_rate)

        # 1) Energia (per VAD)
        energy = _compute_energy(y, frame_length=frame_length, hop_length=hop_length)
        if energy.size == 0:
            return {"segments": [], "sample_rate": sample_rate, "duration": duration}

        # Soglia dinamica: mediana * fattore
        med_energy = np.median(energy)
        threshold = med_energy * (0.5 + vad_sensitivity)  # 0.5–1.5 circa
        voice_mask = energy > max(threshold, med_energy * 0.3)

        # 2) Onset detection (punti musicali)
        onset_env = librosa.onset.onset_strength(y=y, sr=sample_rate)
        onsets_frames = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sample_rate, units="frames")
        onsets_times = librosa.frames_to_time(onsets_frames, sr=sample_rate)

        # 3) Costruzione segmenti base da VAD (voce/silenzio)
        segments: List[Dict[str, Any]] = []
        current_state = voice_mask[0]
        current_start = 0

        for i in range(1, len(voice_mask)):
            if voice_mask[i] != current_state:
                # chiudi segmento precedente
                seg_start_time = current_start * hop_length / sample_rate
                seg_end_time = i * hop_length / sample_rate
                segments.append(
                    {
                        "start": float(seg_start_time),
                        "end": float(seg_end_time),
                        "has_voice": bool(current_state),
                        "type": "voice" if current_state else "silence",
                    }
                )
                current_state = voice_mask[i]
                current_start = i

        # ultimo segmento
        last_start_time = current_start * hop_length / sample_rate
        segments.append(
            {
                "start": float(last_start_time),
                "end": float(duration),
                "has_voice": bool(current_state),
                "type": "voice" if current_state else "silence",
            }
        )

        # 4) Merge segmenti molto piccoli e applica min/max durata (segmentazione dinamica)
        merged_segments: List[Dict[str, Any]] = []
        buffer_seg = None

        for seg in segments:
            seg_dur = seg["end"] - seg["start"]

            if buffer_seg is None:
                buffer_seg = seg
                continue

            same_type = buffer_seg["type"] == seg["type"]
            new_dur = seg["end"] - buffer_seg["start"]

            # Unisci se stesso tipo e durata totale sotto max_segment_sec
            if same_type and new_dur <= max_segment_sec:
                buffer_seg["end"] = seg["end"]
            else:
                # se buffer troppo corto, attaccalo al precedente se possibile
                if (buffer_seg["end"] - buffer_seg["start"]) < min_segment_sec and merged_segments:
                    merged_segments[-1]["end"] = buffer_seg["end"]
                else:
                    merged_segments.append(buffer_seg)
                buffer_seg = seg

        if buffer_seg is not None:
            if (buffer_seg["end"] - buffer_seg["start"]) < min_segment_sec and merged_segments:
                merged_segments[-1]["end"] = buffer_seg["end"]
            else:
                merged_segments.append(buffer_seg)

        # 5) Inserisci onsets interni come metadata (non tagliamo ancora sul serio,
        #    ma li salviamo per passi successivi di metrica/testo)
        for seg in merged_segments:
            seg_onsets = [t for t in onsets_times if seg["start"] <= t <= seg["end"]]
            seg["onsets"] = seg_onsets

        logger.info(
            f"✅ Segmentazione completata: {len(merged_segments)} segmenti "
            f"({sum(1 for s in merged_segments if s['has_voice'])} con voce)"
        )

        return {
            "segments": merged_segments,
            "sample_rate": sample_rate,
            "duration": duration,
        }

    except Exception as e:
        logger.error(f"Errore segmentazione vocale: {e}", exc_info=True)
        return {
            "segments": [],
            "sample_rate": None,
            "duration": None,
            "error": str(e),
        }


