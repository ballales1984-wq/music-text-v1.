"""
Analisi audio avanzata: pitch, timing, ritmo, envelope, metrica, prosodia
Estrae informazioni musicali e prosodiche (intonazione, enfasi, durata, pause, dinamica)
per adattare il testo alla melodia e al modo in cui è cantata la voce
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
        "melody": [],
        # Prosodia (modo in cui è detta la parola)
        "prosody": {
            "intonation": [],  # Variazione pitch nel tempo (andamento intonativo)
            "stress": [],  # Enfasi/accents (punti di stress)
            "syllable_duration": [],  # Durata delle sillabe/note
            "pauses": [],  # Pause e silenzi
            "dynamics": [],  # Variazioni di volume (dinamica)
            "articulation": None,  # Articolazione (ZCR)
            "vibrato": None,  # Presenza di vibrato
            "portamento": []  # Glissando/portamento tra note
        }
    }
    
    if not LIBROSA_AVAILABLE:
        logger.warning("Librosa non disponibile, analisi limitata")
        return features
    
    try:
        # Carica audio
        y, sample_rate = librosa.load(str(audio_path), sr=sr, mono=True)
        duration = len(y) / sample_rate
        logger.info(f"Audio: {duration:.2f}s, {sample_rate}Hz")
        
        # OTTIMIZZAZIONE: Per file molto lunghi, downsampling o analisi parziale
        use_downsampling = duration > 60
        if use_downsampling:
            logger.info(f"File lungo ({duration:.1f}s) - applico downsampling per velocizzare analisi")
            # Downsample a 22050 Hz per analisi più veloce (sufficiente per pitch detection)
            y_analysis = librosa.resample(y, orig_sr=sample_rate, target_sr=22050)
            sr_analysis = 22050
            logger.info(f"Downsampled: {len(y_analysis)/sr_analysis:.1f}s a {sr_analysis}Hz")
        else:
            y_analysis = y
            sr_analysis = sample_rate
        
        # 1. PITCH DETECTION
        # Per file lunghi (>60s), usa Librosa invece di CREPE (molto più veloce)
        use_crepe = CREPE_AVAILABLE and duration <= 30  # CREPE solo per file molto corti
        
        if use_crepe:
            try:
                logger.info(f"Usando CREPE per pitch detection (file corto: {duration:.1f}s)")
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
                logger.warning(f"CREPE fallito: {str(e)[:50]}, uso Librosa")
                # Fallback Librosa
                logger.info("Calcolo pitch con Librosa (può richiedere tempo per file lunghi)...")
                pitches_freq, _, _ = librosa.pyin(y_analysis, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr_analysis)
                valid_pitches = pitches_freq[~np.isnan(pitches_freq)]
                features["pitch"] = valid_pitches.tolist()
                times = librosa.frames_to_time(np.arange(len(pitches_freq)), sr=sr_analysis)
                # Scala i tempi al sample rate originale se necessario
                if use_downsampling:
                    times = times * (sample_rate / sr_analysis)
                features["pitch_contour"] = [(t, p) for t, p in zip(times, pitches_freq) if not np.isnan(p)]
                features["notes"] = [_freq_to_note(f) for f in valid_pitches if f > 0]
        else:
            # Usa Librosa direttamente per file lunghi (molto più veloce)
            if duration > 30:
                logger.info(f"File lungo ({duration:.1f}s) - uso Librosa invece di CREPE per velocità (CREPE troppo lento per file > 30s)")
            logger.info("Calcolo pitch con Librosa (può richiedere tempo per file lunghi)...")
            pitches_freq, _, _ = librosa.pyin(y_analysis, fmin=librosa.note_to_hz('C2'), fmax=librosa.note_to_hz('C7'), sr=sr_analysis)
            valid_pitches = pitches_freq[~np.isnan(pitches_freq)]
            features["pitch"] = valid_pitches.tolist()
            times = librosa.frames_to_time(np.arange(len(pitches_freq)), sr=sr_analysis)
            # Scala i tempi al sample rate originale se necessario
            if use_downsampling:
                times = times * (sample_rate / sr_analysis)
            features["pitch_contour"] = [(t, p) for t, p in zip(times, pitches_freq) if not np.isnan(p)]
            features["notes"] = [_freq_to_note(f) for f in valid_pitches if f > 0]
            logger.info(f"Librosa: {len(features['pitch'])} frame pitch")
        
        # 2. TIMING E RITMO
        logger.info("Calcolo tempo e beat...")
        tempo, beats = librosa.beat.beat_track(y=y_analysis, sr=sr_analysis)
        features["tempo"] = float(tempo)
        beats_scaled = librosa.frames_to_time(beats, sr=sr_analysis)
        if use_downsampling:
            beats_scaled = beats_scaled * (sample_rate / sr_analysis)
        features["beats"] = beats_scaled.tolist()
        beat_times = beats_scaled
        
        # Pattern ritmico
        logger.info("Rilevamento onset...")
        onset_frames = librosa.onset.onset_detect(y=y_analysis, sr=sr_analysis)
        onset_times = librosa.frames_to_time(onset_frames, sr=sr_analysis)
        if use_downsampling:
            onset_times = onset_times * (sample_rate / sr_analysis)
        if len(onset_times) > 1:
            intervals = np.diff(onset_times)
            features["rhythm"] = {
                "onset_times": onset_times.tolist(),
                "avg_interval": float(np.mean(intervals)),
                "pattern": "regular" if np.std(intervals) / np.mean(intervals) < 0.1 else "varied"
            }
        
        logger.info(f"Tempo: {features['tempo']:.1f} BPM, {len(beats)} beat")
        
        # 3. ENVELOPE (dinamica)
        logger.info("Calcolo envelope...")
        rms = librosa.feature.rms(y=y_analysis)[0]
        max_rms = max(rms) if len(rms) > 0 else 1.0
        features["envelope"] = (rms / max_rms).tolist() if max_rms > 0 else []
        
        # 4. PROSODIA (modo in cui è detta la parola - andamento vocale)
        logger.info("Analisi prosodia: intonazione, enfasi, durata, pause, dinamica...")
        
        # 4.1 INTONAZIONE (variazione pitch nel tempo - andamento)
        if features["pitch_contour"]:
            intonation_contour = []
            for i in range(1, len(features["pitch_contour"])):
                t_prev, p_prev = features["pitch_contour"][i-1]
                t_curr, p_curr = features["pitch_contour"][i]
                if p_prev > 0 and p_curr > 0:
                    pitch_change = p_curr - p_prev
                    time_diff = t_curr - t_prev
                    if time_diff > 0:
                        pitch_slope = pitch_change / time_diff  # Hz/s (velocità variazione)
                        intonation_contour.append({
                            "time": t_curr,
                            "pitch": p_curr,
                            "change": pitch_change,
                            "slope": pitch_slope,
                            "direction": "rising" if pitch_change > 0 else "falling" if pitch_change < 0 else "stable"
                        })
            features["prosody"]["intonation"] = intonation_contour[:50]  # Prime 50 variazioni
        
        # 4.2 ENFASI/STRESS (punti di massima energia - accenti)
        onset_frames = librosa.onset.onset_detect(y=y, sr=sample_rate, energy=True)
        onset_times = librosa.frames_to_time(onset_frames, sr=sample_rate)
        onset_strength = librosa.onset.onset_strength(y=y, sr=sample_rate)
        onset_strength_times = librosa.frames_to_time(np.arange(len(onset_strength)), sr=sample_rate)
        
        # Trova i picchi di energia (stress points)
        stress_points = []
        for onset_time in onset_times[:30]:  # Prime 30 onset
            idx = np.argmin(np.abs(onset_strength_times - onset_time))
            if idx < len(onset_strength):
                strength = float(onset_strength[idx])
                stress_points.append({
                    "time": float(onset_time),
                    "strength": strength,
                    "level": "strong" if strength > np.percentile(onset_strength, 75) else "medium" if strength > np.percentile(onset_strength, 50) else "weak"
                })
        features["prosody"]["stress"] = stress_points
        
        # 4.3 DURATA DELLE SILLABE/NOTE (quanto dura ogni suono)
        if features["notes"] and len(features["notes"]) > 1:
            note_durations = []
            if features["pitch_contour"]:
                # Raggruppa note consecutive per calcolare durata
                current_note = None
                note_start_time = 0
                for i, (time, pitch) in enumerate(features["pitch_contour"][:100]):
                    note = _freq_to_note(pitch) if pitch > 0 else None
                    if note != current_note:
                        if current_note and note_start_time > 0:
                            duration = time - note_start_time
                            note_durations.append({
                                "note": current_note,
                                "duration": float(duration),
                                "start": float(note_start_time)
                            })
                        current_note = note
                        note_start_time = time
            features["prosody"]["syllable_duration"] = note_durations[:30]
        
        # 4.4 PAUSE E SILENZI (momenti senza voce)
        # Usa RMS per trovare silenzi
        rms_threshold = np.percentile(rms, 20)  # Soglia per silenzio (20% più basso)
        silence_frames = np.where(rms < rms_threshold)[0]
        silence_times = librosa.frames_to_time(silence_frames, sr=sample_rate)
        
        # Raggruppa pause consecutive
        pauses = []
        if len(silence_times) > 0:
            pause_start = silence_times[0]
            for i in range(1, len(silence_times)):
                if silence_times[i] - silence_times[i-1] > 0.1:  # Gap > 100ms = pausa
                    pause_duration = silence_times[i-1] - pause_start
                    if pause_duration > 0.1:  # Pause significative > 100ms
                        pauses.append({
                            "start": float(pause_start),
                            "end": float(silence_times[i-1]),
                            "duration": float(pause_duration)
                        })
                    pause_start = silence_times[i]
        features["prosody"]["pauses"] = pauses[:20]  # Prime 20 pause
        
        # 4.5 DINAMICA (variazioni di volume nel tempo)
        rms_times = librosa.frames_to_time(np.arange(len(rms)), sr=sample_rate)
        dynamics = []
        for i in range(0, len(rms), max(1, len(rms) // 50)):  # 50 punti
            if i < len(rms) and i < len(rms_times):
                dynamics.append({
                    "time": float(rms_times[i]),
                    "volume": float(rms[i]),
                    "level": "loud" if rms[i] > np.percentile(rms, 75) else "medium" if rms[i] > np.percentile(rms, 50) else "soft"
                })
        features["prosody"]["dynamics"] = dynamics
        
        # 4.6 ARTICOLAZIONE (Zero Crossing Rate - quanto è "chiara" la voce)
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        avg_zcr = float(np.mean(zcr))
        features["prosody"]["articulation"] = {
            "zcr": avg_zcr,
            "quality": "clear" if avg_zcr > 0.1 else "smooth" if avg_zcr > 0.05 else "muffled"
        }
        
        # 4.7 VIBRATO (oscillazione rapida del pitch)
        if features["pitch_contour"] and len(features["pitch_contour"]) > 10:
            pitch_values = [p for _, p in features["pitch_contour"][:100] if p > 0]
            if len(pitch_values) > 10:
                # Calcola varianza locale del pitch (vibrato = alta varianza locale)
                pitch_array = np.array(pitch_values)
                local_variance = []
                window = 5
                for i in range(window, len(pitch_array) - window):
                    local_std = np.std(pitch_array[i-window:i+window])
                    local_variance.append(local_std)
                avg_variance = np.mean(local_variance) if local_variance else 0
                relative_variance = avg_variance / np.mean(pitch_array) if np.mean(pitch_array) > 0 else 0
                features["prosody"]["vibrato"] = {
                    "present": bool(relative_variance > 0.02),  # Soglia 2% - convertito in bool esplicito
                    "intensity": float(relative_variance)
                }
        
        # 4.8 PORTAMENTO/GLISSANDO (transizioni fluide tra note)
        if features["pitch_contour"] and len(features["pitch_contour"]) > 2:
            portamento_segments = []
            for i in range(1, len(features["pitch_contour"]) - 1):
                t_prev, p_prev = features["pitch_contour"][i-1]
                t_curr, p_curr = features["pitch_contour"][i]
                t_next, p_next = features["pitch_contour"][i+1]
                if p_prev > 0 and p_curr > 0 and p_next > 0:
                    # Portamento = transizione graduale (non salto netto)
                    pitch_change_1 = abs(p_curr - p_prev)
                    pitch_change_2 = abs(p_next - p_curr)
                    time_1 = t_curr - t_prev
                    time_2 = t_next - t_curr
                    if time_1 > 0 and time_2 > 0:
                        slope_1 = pitch_change_1 / time_1
                        slope_2 = pitch_change_2 / time_2
                        # Se la variazione è graduale (slope moderato), è portamento
                        if 10 < slope_1 < 200 and 10 < slope_2 < 200:  # Hz/s moderato
                            portamento_segments.append({
                                "time": float(t_curr),
                                "pitch": float(p_curr),
                                "transition_type": "smooth"
                            })
            features["prosody"]["portamento"] = portamento_segments[:20]
        
        logger.info(f"✅ Prosodia analizzata: {len(features['prosody']['intonation'])} variazioni intonative, {len(features['prosody']['stress'])} accenti, {len(features['prosody']['pauses'])} pause")
        
        # 5. MELODIA (contorno semplificato)
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
        
        logger.info(f"✅ Analisi completata: {len(features['notes'])} note, tempo {features['tempo']:.1f} BPM, prosodia analizzata")
        
    except Exception as e:
        logger.error(f"Errore analisi: {str(e)}", exc_info=True)
    
    return features


def format_features_for_prompt(features: Dict) -> str:
    """Formatta features per prompt modello linguistico, includendo prosodia."""
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
    
    # PROSODIA (modo in cui è detta la parola - andamento vocale)
    prosody = features.get("prosody", {})
    
    if prosody.get("intonation"):
        intonation_dirs = [i.get("direction", "") for i in prosody["intonation"][:10]]
        rising = sum(1 for d in intonation_dirs if d == "rising")
        falling = sum(1 for d in intonation_dirs if d == "falling")
        parts.append(f"Intonation pattern: {rising} rising, {falling} falling (voice contour)")
    
    if prosody.get("stress"):
        strong_stress = sum(1 for s in prosody["stress"] if s.get("level") == "strong")
        parts.append(f"Stress points: {strong_stress} strong accents, {len(prosody['stress'])} total")
    
    if prosody.get("syllable_duration"):
        avg_duration = np.mean([d.get("duration", 0) for d in prosody["syllable_duration"]])
        parts.append(f"Syllable/note duration: avg {avg_duration:.2f}s (how long each sound lasts)")
    
    if prosody.get("pauses"):
        parts.append(f"Pauses: {len(prosody['pauses'])} significant pauses (breathing/rests)")
    
    if prosody.get("dynamics"):
        loud_count = sum(1 for d in prosody["dynamics"] if d.get("level") == "loud")
        parts.append(f"Dynamics: {loud_count} loud sections, {len(prosody['dynamics'])} total (volume variations)")
    
    if prosody.get("articulation"):
        art_quality = prosody["articulation"].get("quality", "unknown")
        parts.append(f"Articulation: {art_quality} (voice clarity)")
    
    if prosody.get("vibrato", {}).get("present"):
        vibrato_intensity = prosody["vibrato"].get("intensity", 0)
        parts.append(f"Vibrato: present (intensity: {vibrato_intensity:.3f})")
    
    if prosody.get("portamento"):
        parts.append(f"Portamento: {len(prosody['portamento'])} smooth transitions (glissando)")
    
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

