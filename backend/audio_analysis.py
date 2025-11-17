"""
Analisi audio avanzata: pitch, timing, ritmo, envelope, metrica
Estrae informazioni musicali per adattare il testo alla melodia
"""
import logging
from pathlib import Path
from typing import Dict, Optional
import numpy as np

logger = logging.getLogger(__name__)

# Check librerie
LIBROSA_AVAILABLE = False
CREPE_AVAILABLE = False

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    logger.warning("Librosa non disponibile")

try:
    import crepe
    CREPE_AVAILABLE = True
except ImportError:
    pass


def analyze_audio_features(audio_path: Path, sr: Optional[int] = None) -> Dict:
    """
    Analizza audio e estrae:
    - Pitch (altezza note) - CREPE o Librosa
    - Timing (ritmo, beat, tempo BPM)
    - Envelope (dinamica voce)
    - Melodia (contorno melodico, sequenza note)
    - Metrica (pattern ritmico)
    """
    logger.info(f"🎵 Analisi audio: {audio_path}")
    
    features = {
        "pitch": [],
        "pitch_contour": [],
        "notes": [],
        "tempo": None,
        "beats": [],
        "rhythm": {},
        "envelope": [],
        "melody": []
    }
    
    if not LIBROSA_AVAILABLE:
        logger.warning("Librosa non disponibile, analisi limitata")
        return features
    
    try:
        # Carica audio
        y, sample_rate = librosa.load(str(audio_path), sr=sr, mono=True)
        duration = len(y) / sample_rate
        logger.info(f"Audio: {duration:.2f}s, {sample_rate}Hz")
        
        # 1. PITCH DETECTION
        if CREPE_AVAILABLE:
            try:
                time, frequency, confidence, _ = crepe.predict(y, sample_rate, viterbi=True)
                valid = confidence > 0.5
                pitches = frequency[valid].tolist()
                times = time[valid].tolist()
                contour = list(zip(times, pitches))
                notes = [_freq_to_note(f) for f in pitches if f > 0]
                features["pitch"] = pitches
                features["pitch_contour"] = contour
                features["notes"] = notes
                logger.info(f"CREPE: {len(pitches)} frame pitch")
            except Exception as e:
                logger.warning(f"CREPE fallito: {str(e)[:50]}")
                # Fallback Librosa
                pitches_freq, _, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
                valid_pitches = pitches_freq[~np.isnan(pitches_freq)]
                features["pitch"] = valid_pitches.tolist()
                times = librosa.frames_to_time(np.arange(len(pitches_freq)), sr=sample_rate)
                features["pitch_contour"] = [(t, p) for t, p in zip(times, pitches_freq) if not np.isnan(p)]
                features["notes"] = [_freq_to_note(f) for f in valid_pitches if f > 0]
        else:
            # Solo Librosa
            pitches_freq, _, _ = librosa.pyin(y, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'))
            valid_pitches = pitches_freq[~np.isnan(pitches_freq)]
            features["pitch"] = valid_pitches.tolist()
            times = librosa.frames_to_time(np.arange(len(pitches_freq)), sr=sample_rate)
            features["pitch_contour"] = [(t, p) for t, p in zip(times, pitches_freq) if not np.isnan(p)]
            features["notes"] = [_freq_to_note(f) for f in valid_pitches if f > 0]
            logger.info(f"Librosa: {len(features['pitch'])} frame pitch")
        
        # 2. TIMING E RITMO
        tempo, beats = librosa.beat.beat_track(y=y, sr=sample_rate)
        features["tempo"] = float(tempo)
        features["beats"] = beats.tolist()
        beat_times = librosa.frames_to_time(beats, sr=sample_rate)
        
        # Pattern ritmico
        onset_frames = librosa.onset.onset_detect(y=y, sr=sample_rate)
        onset_times = librosa.frames_to_time(onset_frames, sr=sample_rate)
        if len(onset_times) > 1:
            intervals = np.diff(onset_times)
            features["rhythm"] = {
                "onset_times": onset_times.tolist(),
                "avg_interval": float(np.mean(intervals)),
                "pattern": "regular" if np.std(intervals) / np.mean(intervals) < 0.1 else "varied"
            }
        
        logger.info(f"Tempo: {features['tempo']:.1f} BPM, {len(beats)} beat")
        
        # 3. ENVELOPE
        rms = librosa.feature.rms(y=y)[0]
        max_rms = max(rms) if len(rms) > 0 else 1.0
        features["envelope"] = (rms / max_rms).tolist() if max_rms > 0 else []
        
        # 4. MELODIA (contorno semplificato)
        if features["notes"]:
            melody = []
            current_note = None
            note_start = 0
            for i, note in enumerate(features["notes"][:100]):  # Prime 100 note
                if note != current_note:
                    if current_note:
                        melody.append({"note": current_note, "start": note_start, "duration": i - note_start})
                    current_note = note
                    note_start = i
            if current_note:
                melody.append({"note": current_note, "start": note_start, "duration": len(features["notes"]) - note_start})
            features["melody"] = melody[:20]  # Prime 20 note
        
        logger.info(f"✅ Analisi completata: {len(features['notes'])} note, tempo {features['tempo']:.1f} BPM")
        
    except Exception as e:
        logger.error(f"Errore analisi: {str(e)}", exc_info=True)
    
    return features


def format_features_for_prompt(features: Dict) -> str:
    """Formatta features per prompt modello linguistico."""
    parts = []
    
    if features.get("notes"):
        notes_str = ", ".join(features["notes"][:20])
        parts.append(f"Musical notes: {notes_str}")
    
    if features.get("tempo"):
        parts.append(f"Tempo: {features['tempo']:.1f} BPM")
    
    if features.get("melody"):
        melody_str = " -> ".join([m["note"] for m in features["melody"][:15]])
        parts.append(f"Melody: {melody_str}")
    
    if features.get("rhythm", {}).get("pattern"):
        parts.append(f"Rhythm pattern: {features['rhythm']['pattern']}")
    
    return "\n".join(parts)


def _freq_to_note(freq: float) -> str:
    """Converte frequenza in nota musicale."""
    if freq <= 0:
        return ""
    A4 = 440.0
    semitones = 12 * np.log2(freq / A4)
    note_number = int(round(semitones)) % 12
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = int(4 + semitones / 12)
    return f"{notes[note_number]}{octave}"

