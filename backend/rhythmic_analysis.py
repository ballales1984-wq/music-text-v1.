"""
Analisi ritmica della BASE STRUMENTALE
Estrae BPM, beat, pattern ritmico per allineare il testo generato
"""
import logging
from pathlib import Path
from typing import Dict, Optional
import numpy as np

logger = logging.getLogger(__name__)

LIBROSA_AVAILABLE = False
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    logger.warning("Librosa non disponibile per analisi ritmica")


def analyze_rhythmic_features(instrumental_path: Path, sr: Optional[int] = None) -> Dict:
    """
    Analizza la BASE STRUMENTALE per estrarre:
    - BPM (tempo)
    - Beat detection (posizioni beat)
    - Pattern ritmico (accenti, suddivisioni)
    - Timing preciso per allineare testo
    """
    logger.info(f"🥁 Analisi ritmica BASE: {instrumental_path}")
    
    features = {
        "tempo": None,
        "beats": [],
        "beat_times": [],
        "strong_beats": [],
        "rhythm_pattern": None,
        "time_signature": None,
        "beat_intervals": []
    }
    
    if not LIBROSA_AVAILABLE:
        logger.warning("Librosa non disponibile, analisi ritmica limitata")
        return features
    
    try:
        # Carica base strumentale
        y, sample_rate = librosa.load(str(instrumental_path), sr=sr, mono=True)
        duration = len(y) / sample_rate
        logger.info(f"Base strumentale: {duration:.2f}s, {sample_rate}Hz")
        
        # 1. BPM e Beat Detection
        tempo, beats = librosa.beat.beat_track(y=y, sr=sample_rate)
        features["tempo"] = float(tempo)
        features["beats"] = beats.tolist()
        beat_times = librosa.frames_to_time(beats, sr=sample_rate)
        features["beat_times"] = beat_times.tolist()
        
        logger.info(f"BPM: {features['tempo']:.1f}, {len(beats)} beat rilevati")
        
        # 2. Strong Beats (accenti forti)
        onset_strength = librosa.onset.onset_strength(y=y, sr=sample_rate)
        onset_times = librosa.frames_to_time(np.arange(len(onset_strength)), sr=sample_rate)
        
        # Trova beat forti (picchi di energia)
        strong_threshold = np.percentile(onset_strength, 75)
        strong_beats = []
        for beat_time in beat_times:
            idx = np.argmin(np.abs(onset_times - beat_time))
            if idx < len(onset_strength) and onset_strength[idx] > strong_threshold:
                strong_beats.append(float(beat_time))
        features["strong_beats"] = strong_beats
        
        logger.info(f"Beat forti: {len(strong_beats)} su {len(beats)} totali")
        
        # 3. Pattern Ritmico
        if len(beat_times) > 1:
            intervals = np.diff(beat_times)
            avg_interval = float(np.mean(intervals))
            std_interval = float(np.std(intervals))
            features["beat_intervals"] = intervals.tolist()
            
            # Pattern: regolare se std bassa, variato se alta
            if std_interval / avg_interval < 0.1:
                features["rhythm_pattern"] = "regular"
            elif std_interval / avg_interval < 0.3:
                features["rhythm_pattern"] = "slightly_varied"
            else:
                features["rhythm_pattern"] = "varied"
            
            logger.info(f"Pattern ritmico: {features['rhythm_pattern']}")
        
        # 4. Time Signature (stima)
        # Analizza pattern di accentazione per stimare 4/4, 3/4, etc.
        if len(strong_beats) > 4:
            strong_intervals = []
            for i in range(1, len(strong_beats)):
                strong_intervals.append(strong_beats[i] - strong_beats[i-1])
            
            # Se gli intervalli sono simili, probabile 4/4
            if len(strong_intervals) > 0:
                avg_strong_interval = np.mean(strong_intervals)
                # Stima: se intervallo ~2 secondi a 120 BPM = 4/4
                estimated_beats_per_measure = round(avg_strong_interval * tempo / 60)
                if estimated_beats_per_measure == 4:
                    features["time_signature"] = "4/4"
                elif estimated_beats_per_measure == 3:
                    features["time_signature"] = "3/4"
                else:
                    features["time_signature"] = f"{estimated_beats_per_measure}/4"
        
        logger.info(f"✅ Analisi ritmica completata: BPM={features['tempo']:.1f}, pattern={features['rhythm_pattern']}")
        
    except Exception as e:
        logger.error(f"Errore analisi ritmica: {str(e)}", exc_info=True)
    
    return features


def format_rhythmic_features_for_prompt(rhythmic_features: Dict) -> str:
    """Formatta features ritmiche per prompt modello linguistico."""
    parts = []
    
    if rhythmic_features.get("tempo"):
        parts.append(f"Rhythmic tempo: {rhythmic_features['tempo']:.1f} BPM")
    
    if rhythmic_features.get("rhythm_pattern"):
        parts.append(f"Rhythm pattern: {rhythmic_features['rhythm_pattern']}")
    
    if rhythmic_features.get("time_signature"):
        parts.append(f"Time signature: {rhythmic_features['time_signature']}")
    
    if rhythmic_features.get("strong_beats"):
        parts.append(f"Strong beats: {len(rhythmic_features['strong_beats'])} accents")
    
    if rhythmic_features.get("beat_times"):
        parts.append(f"Beat count: {len(rhythmic_features['beat_times'])} total beats")
    
    return "\n".join(parts)

