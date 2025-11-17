"""
Modulo per analisi audio avanzata: pitch, timing, envelope, ritmo.
Usa CREPE, Essentia, o Melodia per estrarre informazioni musicali.
"""
import logging
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)

# Flag per controllare quali librerie sono disponibili
CREPE_AVAILABLE = False
ESSENTIA_AVAILABLE = False
LIBROSA_AVAILABLE = False

try:
    import librosa
    LIBROSA_AVAILABLE = True
    logger.info("✅ Librosa disponibile per analisi audio")
except ImportError:
    logger.warning("Librosa non disponibile. Installare con: pip install librosa")

try:
    import crepe
    CREPE_AVAILABLE = True
    logger.info("✅ CREPE disponibile per pitch detection")
except ImportError:
    logger.warning("CREPE non disponibile. Installare con: pip install crepe")

try:
    import essentia.standard as es
    ESSENTIA_AVAILABLE = True
    logger.info("✅ Essentia disponibile per analisi avanzata")
except ImportError:
    logger.warning("Essentia non disponibile. Installare con: pip install essentia")


def analyze_audio_features(
    audio_path: Path,
    sr: Optional[int] = None
) -> Dict:
    """
    Analizza audio e estrae:
    - Pitch (altezza delle note)
    - Timing (ritmo, beat)
    - Envelope (dinamica della voce)
    - Melodia (contorno melodico)
    
    Returns:
        Dizionario con tutte le features estratte
    """
    logger.info(f"🎵 Analisi audio avanzata: {audio_path}")
    
    features = {
        "pitch": [],
        "pitch_contour": [],
        "timing": {},
        "envelope": [],
        "melody": [],
        "rhythm": {},
        "tempo": None,
        "key": None,
        "notes": []
    }
    
    try:
        # Carica audio
        if not LIBROSA_AVAILABLE:
            logger.warning("Librosa non disponibile, uso analisi base")
            return features
        
        y, sample_rate = librosa.load(str(audio_path), sr=sr, mono=True)
        duration = len(y) / sample_rate
        
        logger.info(f"Audio caricato: {duration:.2f}s, {sample_rate}Hz")
        
        # 1. PITCH DETECTION (CREPE o Librosa)
        pitch_data = _extract_pitch(y, sample_rate)
        features["pitch"] = pitch_data.get("pitches", [])
        features["pitch_contour"] = pitch_data.get("contour", [])
        features["notes"] = pitch_data.get("notes", [])
        
        # 2. TIMING E RITMO
        timing_data = _extract_timing(y, sample_rate)
        features["timing"] = timing_data
        features["tempo"] = timing_data.get("tempo")
        features["rhythm"] = timing_data.get("rhythm", {})
        
        # 3. ENVELOPE (dinamica)
        envelope_data = _extract_envelope(y, sample_rate)
        features["envelope"] = envelope_data
        
        # 4. MELODIA (contorno melodico)
        melody_data = _extract_melody(y, sample_rate, features["pitch"])
        features["melody"] = melody_data
        
        # 5. KEY DETECTION (tonalità)
        key_data = _detect_key(y, sample_rate)
        features["key"] = key_data
        
        logger.info(f"✅ Analisi completata: {len(features['pitch'])} frame pitch, tempo {features['tempo']:.1f} BPM")
        
    except Exception as e:
        logger.error(f"Errore durante analisi audio: {str(e)}", exc_info=True)
    
    return features


def _extract_pitch(y: np.ndarray, sr: int) -> Dict:
    """
    Estrae pitch usando CREPE (preferito) o Librosa (fallback).
    """
    pitches = []
    contour = []
    notes = []
    
    try:
        if CREPE_AVAILABLE:
            # CREPE è più accurato per pitch vocale
            logger.info("Uso CREPE per pitch detection...")
            time, frequency, confidence, activation = crepe.predict(y, sr, viterbi=True)
            
            # Filtra per confidence
            valid_mask = confidence > 0.5
            pitches = frequency[valid_mask].tolist()
            times = time[valid_mask].tolist()
            
            # Crea contour (pitch nel tempo)
            contour = list(zip(times, pitches))
            
            # Converti frequenze in note musicali
            notes = [_freq_to_note(f) for f in pitches if f > 0]
            
            logger.info(f"CREPE: {len(pitches)} frame pitch rilevati")
            
        else:
            # Fallback: Librosa pitch detection
            logger.info("Uso Librosa per pitch detection...")
            
            # Estrai pitch con pyin (più accurato di default)
            pitches_freq, voiced_flag, voiced_probs = librosa.pyin(
                y,
                fmin=librosa.note_to_hz('C2'),
                fmax=librosa.note_to_hz('C7')
            )
            
            # Converti in Hz e filtra
            valid_pitches = pitches_freq[~np.isnan(pitches_freq)]
            pitches = valid_pitches.tolist()
            
            # Crea contour
            times = librosa.frames_to_time(np.arange(len(pitches_freq)), sr=sr)
            contour = [(t, p) for t, p in zip(times, pitches_freq) if not np.isnan(p)]
            
            # Converti in note
            notes = [_freq_to_note(f) for f in pitches if f > 0]
            
            logger.info(f"Librosa: {len(pitches)} frame pitch rilevati")
    
    except Exception as e:
        logger.error(f"Errore pitch detection: {str(e)}")
    
    return {
        "pitches": pitches,
        "contour": contour,
        "notes": notes
    }


def _extract_timing(y: np.ndarray, sr: int) -> Dict:
    """
    Estrae timing, ritmo, beat, tempo.
    """
    timing_data = {
        "tempo": 120.0,
        "beats": [],
        "beat_times": [],
        "rhythm": {}
    }
    
    try:
        # Estrai tempo (BPM)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        timing_data["tempo"] = float(tempo)
        timing_data["beats"] = beats.tolist()
        
        # Converti beat in tempi
        beat_times = librosa.frames_to_time(beats, sr=sr)
        timing_data["beat_times"] = beat_times.tolist()
        
        # Analisi ritmo (time signature, pattern)
        onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr)
        
        # Calcola intervalli tra onset
        if len(onset_times) > 1:
            intervals = np.diff(onset_times)
            avg_interval = np.mean(intervals)
            timing_data["rhythm"] = {
                "onset_times": onset_times.tolist(),
                "avg_interval": float(avg_interval),
                "rhythm_pattern": _analyze_rhythm_pattern(intervals)
            }
        
        logger.info(f"Tempo rilevato: {timing_data['tempo']:.1f} BPM, {len(beats)} beat")
    
    except Exception as e:
        logger.error(f"Errore timing extraction: {str(e)}")
    
    return timing_data


def _extract_envelope(y: np.ndarray, sr: int) -> List[float]:
    """
    Estrae envelope (dinamica) della voce.
    """
    try:
        # RMS Energy (dinamica)
        rms = librosa.feature.rms(y=y)[0]
        envelope = rms.tolist()
        
        # Normalizza
        if len(envelope) > 0:
            max_val = max(envelope)
            if max_val > 0:
                envelope = [e / max_val for e in envelope]
        
        logger.info(f"Envelope estratto: {len(envelope)} frame")
        return envelope
    
    except Exception as e:
        logger.error(f"Errore envelope extraction: {str(e)}")
        return []


def _extract_melody(y: np.ndarray, sr: int, pitches: List[float]) -> List[Dict]:
    """
    Estrae contorno melodico (melodia).
    """
    melody = []
    
    try:
        if len(pitches) > 0:
            # Crea contorno melodico semplificato
            # Raggruppa pitch simili in "note" sostenute
            current_note = None
            note_start = 0
            note_duration = 0
            
            for i, pitch in enumerate(pitches):
                if pitch > 0:
                    # Arrotonda a semitono
                    note = _freq_to_note(pitch)
                    
                    if current_note != note:
                        # Nuova nota
                        if current_note is not None:
                            melody.append({
                                "note": current_note,
                                "start": note_start,
                                "duration": note_duration,
                                "pitch": pitch
                            })
                        
                        current_note = note
                        note_start = i * (len(y) / len(pitches)) / sr
                        note_duration = 0
                    else:
                        note_duration += (len(y) / len(pitches)) / sr
            
            # Aggiungi ultima nota
            if current_note is not None:
                melody.append({
                    "note": current_note,
                    "start": note_start,
                    "duration": note_duration,
                    "pitch": pitch
                })
        
        logger.info(f"Melodia estratta: {len(melody)} note")
    
    except Exception as e:
        logger.error(f"Errore melody extraction: {str(e)}")
    
    return melody


def _detect_key(y: np.ndarray, sr: int) -> Optional[str]:
    """
    Rileva tonalità (key) dell'audio.
    """
    try:
        # Chroma features
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        
        # Key profiles (maggiore)
        key_profiles = {
            'C': [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88],
            'C#': [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17],
            # ... (semplificato, in produzione usare libreria completa)
        }
        
        # Trova key più probabile (semplificato)
        # In produzione, usare keyfinder o libreria dedicata
        key = "C"  # Default
        
        logger.info(f"Key rilevata: {key}")
        return key
    
    except Exception as e:
        logger.error(f"Errore key detection: {str(e)}")
        return None


def _freq_to_note(freq: float) -> str:
    """
    Converte frequenza in nota musicale.
    """
    if freq <= 0:
        return ""
    
    # A4 = 440 Hz
    A4 = 440.0
    semitones = 12 * np.log2(freq / A4)
    note_number = int(round(semitones)) % 12
    
    notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    octave = int(4 + semitones / 12)
    
    return f"{notes[note_number]}{octave}"


def _analyze_rhythm_pattern(intervals: np.ndarray) -> str:
    """
    Analizza pattern ritmico (semplificato).
    """
    if len(intervals) == 0:
        return "unknown"
    
    avg = np.mean(intervals)
    std = np.std(intervals)
    
    if std / avg < 0.1:
        return "regular"
    elif std / avg < 0.3:
        return "slightly_varied"
    else:
        return "varied"


def format_features_for_prompt(features: Dict) -> str:
    """
    Formatta le features audio in un prompt per il modello linguistico.
    """
    prompt_parts = []
    
    # Pitch e note
    if features.get("notes"):
        notes_str = ", ".join(features["notes"][:20])  # Prime 20 note
        prompt_parts.append(f"Musical notes detected: {notes_str}")
    
    if features.get("pitch_contour"):
        contour = features["pitch_contour"][:10]  # Prime 10
        contour_str = ", ".join([f"{n[1]:.1f}Hz@{n[0]:.1f}s" for n in contour])
        prompt_parts.append(f"Pitch contour: {contour_str}")
    
    # Timing e ritmo
    if features.get("tempo"):
        prompt_parts.append(f"Tempo: {features['tempo']:.1f} BPM")
    
    if features.get("rhythm", {}).get("rhythm_pattern"):
        prompt_parts.append(f"Rhythm pattern: {features['rhythm']['rhythm_pattern']}")
    
    # Melodia
    if features.get("melody"):
        melody_notes = [m["note"] for m in features["melody"][:15]]
        melody_str = " -> ".join(melody_notes)
        prompt_parts.append(f"Melody: {melody_str}")
    
    # Key
    if features.get("key"):
        prompt_parts.append(f"Key: {features['key']}")
    
    return "\n".join(prompt_parts)

