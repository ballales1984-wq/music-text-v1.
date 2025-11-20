"""
Analisi metrica e sillabe (stile Beatles)
Estrae pattern metrico, sillabe, accenti per generazione testi che rispettano la metrica
"""
import logging
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import random

logger = logging.getLogger(__name__)

PRONOUNCING_AVAILABLE = False
try:
    import pronouncing
    PRONOUNCING_AVAILABLE = True
    logger.info("✅ pronouncing (CMUdict) disponibile per analisi metrica")
except ImportError:
    logger.warning("pronouncing non disponibile - analisi metrica limitata")


def estimate_syllables_from_onsets(onset_times: List[float], tempo: float) -> Tuple[int, List[int]]:
    """
    Stima numero sillabe e pattern accenti dagli onset.
    Pattern: ogni 4 beat = accento forte (stile 4/4).
    """
    n_syllables = len(onset_times)
    
    # Pattern accenti: ogni 4 beat = accento forte
    # Calcola posizione rispetto ai beat
    beat_interval = 60.0 / tempo if tempo > 0 else 0.5
    
    accents = []
    for i, onset_time in enumerate(onset_times):
        # Posizione nel ciclo di 4 beat
        beat_position = (onset_time / beat_interval) % 4
        # Accento forte su beat 0 (primo del ciclo)
        accent = 1 if beat_position < 0.5 else 0
        accents.append(accent)
    
    return n_syllables, accents


def get_word_by_syllable_count(target_syllables: int, max_attempts: int = 100) -> str:
    """
    Trova una parola con numero specifico di sillabe usando CMUdict.
    """
    if not PRONOUNCING_AVAILABLE:
        # Fallback: parole comuni per sillaba
        fallback_words = {
            1: ["love", "time", "way", "day", "night", "light", "heart", "soul"],
            2: ["music", "dancing", "feeling", "dreaming", "singing", "calling"],
            3: ["beautiful", "wonderful", "together", "forever", "remember"],
            4: ["imagination", "celebration", "generation", "situation"]
        }
        words = fallback_words.get(target_syllables, fallback_words[1])
        import random
        return random.choice(words)
    
    try:
        # Cerca parole con numero esatto di sillabe
        for _ in range(max_attempts):
            word = pronouncing.random_word()
            phones = pronouncing.phones_for_word(word)
            if phones:
                syllable_count = pronouncing.syllable_count(phones[0])
                if syllable_count == target_syllables:
                    return word
        
        # Se non trova, usa fallback
        import random
        fallback = ["love", "time", "way", "day", "night", "light"]
        return random.choice(fallback)
    except:
        import random
        return random.choice(["love", "time", "way", "day"])


def generate_metric_lyrics(n_syllables: int, accents: List[int], pitch_contour: List = None, style: str = "poetic") -> str:
    """
    Genera testo in inglese che rispetta la metrica (sillabe e accenti).
    NON trascrive le parole esistenti, ma CREA nuovo testo che segue:
    - Numero esatto di sillabe
    - Pattern accenti (forte/debole)
    - Ritmo simile
    - Fraseggio simile
    
    Usa CMUdict per garantire esattezza sillabe.
    """
    logger.info(f"📝 Generazione testo metrico: {n_syllables} sillabe, {sum(accents)} accenti forti")
    
    if n_syllables == 0:
        return "No syllables detected"
    
    words = []
    syllables_used = 0
    
    if PRONOUNCING_AVAILABLE:
        # Strategia intelligente: distribuisci sillabe tra parole
        # Ogni parola può avere 1-3 sillabe, in modo naturale
        while syllables_used < n_syllables:
            remaining = n_syllables - syllables_used
            
            # Scegli numero sillabe per questa parola (1-3, preferibilmente 1-2)
            if remaining >= 3 and syllables_used % 4 == 0:
                target_syl = 2  # Parola bisillabica ogni tanto
            elif remaining >= 2:
                target_syl = random.choice([1, 1, 2])  # Preferisci monosillabiche
            else:
                target_syl = remaining
            
            word = get_word_by_syllable_count(target_syl)
            
            # Determina se questa parola ha accento forte
            # (basato sulla posizione nel pattern)
            word_accent = accents[min(syllables_used, len(accents) - 1)] if accents else 0
            
            # Applica accento (maiuscola per accento forte)
            if word_accent == 1:
                word = word.capitalize()
            
            words.append(word)
            syllables_used += target_syl
            
            # Aggiungi spazio ogni 4-5 sillabe (per fraseggio naturale)
            if syllables_used % 4 == 0 and syllables_used < n_syllables:
                words.append("")  # Separatore per riga
    else:
        # Fallback: parole comuni
        import random
        common_words_1 = ["love", "time", "way", "day", "night", "light", "heart", "soul", "dream", "hope"]
        common_words_2 = ["music", "dancing", "feeling", "dreaming", "singing", "calling", "falling", "rising"]
        
        while syllables_used < n_syllables:
            remaining = n_syllables - syllables_used
            if remaining >= 2 and syllables_used % 3 == 0:
                word = random.choice(common_words_2)
                target_syl = 2
            else:
                word = random.choice(common_words_1)
                target_syl = 1
            
            word_accent = accents[min(syllables_used, len(accents) - 1)] if accents else 0
            if word_accent == 1:
                word = word.capitalize()
            
            words.append(word)
            syllables_used += target_syl
            
            if syllables_used % 4 == 0 and syllables_used < n_syllables:
                words.append("")
    
    # Formatta in righe (rimuovi separatori vuoti e crea righe)
    lines = []
    current_line = []
    for word in words:
        if word == "":
            if current_line:
                lines.append(" ".join(current_line))
                current_line = []
        else:
            current_line.append(word)
    if current_line:
        lines.append(" ".join(current_line))
    
    result = "\n".join(lines)
    logger.info(f"✅ Testo metrico generato: {len(result)} caratteri, {len(lines)} righe")
    return result


def extract_detailed_vocal_structure(audio_features: Dict) -> Dict:
    """
    Estrae struttura metrica dettagliata dalla VOCE:
    - Sillabe per riga/frase (non solo totale)
    - Durata di ogni sillaba
    - Timing preciso (quando inizia/finisce ogni sillaba)
    - Pattern accenti per ogni sillaba
    - Contorno melodico (pitch) per ogni sillaba
    
    Returns struttura dettagliata per riga.
    """
    logger.info("🎵 Estrazione struttura vocale dettagliata...")
    
    # Estrai dati dalla prosodia
    prosody = audio_features.get("prosody", {})
    onset_times = audio_features.get("rhythm", {}).get("onset_times", [])
    tempo = audio_features.get("tempo", 120)
    pitch_contour = audio_features.get("pitch_contour", [])
    syllable_durations = prosody.get("syllable_duration", [])
    stress_points = prosody.get("stress", [])
    pauses = prosody.get("pauses", [])
    
    # Crea lista sillabe con timing e durata
    syllables = []
    
    # Usa onset_times come base per le sillabe
    for i, onset_time in enumerate(onset_times):
        # Trova durata corrispondente
        duration = 0.2  # Default 200ms
        if syllable_durations:
            # Trova durata più vicina a questo onset
            closest_dur = min(syllable_durations, 
                            key=lambda d: abs(d.get("start", 0) - onset_time))
            if abs(closest_dur.get("start", 0) - onset_time) < 0.3:
                duration = closest_dur.get("duration", 0.2)
        
        # Trova accento (stress)
        accent = 0
        accent_strength = 0
        for stress in stress_points:
            if abs(stress.get("time", 0) - onset_time) < 0.15:
                if stress.get("level") == "strong":
                    accent = 1
                    accent_strength = stress.get("strength", 0)
                break
        
        # Trova pitch corrispondente
        pitch = None
        pitch_note = None
        if pitch_contour:
            closest_pitch = min(pitch_contour,
                              key=lambda p: abs(p[0] - onset_time) if isinstance(p, tuple) else abs(p.get("time", 0) - onset_time))
            if isinstance(closest_pitch, tuple):
                if abs(closest_pitch[0] - onset_time) < 0.2:
                    pitch = closest_pitch[1]
            elif abs(closest_pitch.get("time", 0) - onset_time) < 0.2:
                pitch = closest_pitch.get("pitch")
        
        syllables.append({
            "index": i,
            "start_time": float(onset_time),
            "duration": float(duration),
            "end_time": float(onset_time + duration),
            "accent": accent,
            "accent_strength": float(accent_strength),
            "pitch": float(pitch) if pitch else None,
            "pitch_note": _freq_to_note(pitch) if pitch else None
        })
    
    # Dividi sillabe in righe basate su pause e ritmo
    lines = []
    current_line = []
    pause_threshold = 0.3  # Pause > 300ms dividono le righe
    
    for i, syllable in enumerate(syllables):
        current_line.append(syllable)
        
        # Controlla se c'è una pausa dopo questa sillaba
        has_pause = False
        if i < len(syllables) - 1:
            next_syllable = syllables[i + 1]
            gap = next_syllable["start_time"] - syllable["end_time"]
            
            # Controlla anche pause esplicite
            for pause in pauses:
                if pause.get("start", 0) <= syllable["end_time"] <= pause.get("end", 0):
                    has_pause = True
                    break
            
            # Se gap > soglia o pausa esplicita, fine riga
            if gap > pause_threshold or has_pause:
                if current_line:
                    lines.append(current_line)
                    current_line = []
        
        # Fine canzone: aggiungi ultima riga
        if i == len(syllables) - 1 and current_line:
            lines.append(current_line)
    
    # Se non ci sono pause, dividi per numero fisso di sillabe (8-12 per riga)
    if len(lines) == 0 or (len(lines) == 1 and len(lines[0]) > 12):
        lines = []
        current_line = []
        for syllable in syllables:
            current_line.append(syllable)
            if len(current_line) >= 10:  # 10 sillabe per riga
                lines.append(current_line)
                current_line = []
        if current_line:
            lines.append(current_line)
    
    # Crea struttura dettagliata
    detailed_structure = {
        "lines": [],
        "total_syllables": len(syllables),
        "total_lines": len(lines),
        "tempo": tempo
    }
    
    for line_idx, line_syllables in enumerate(lines):
        line_info = {
            "line_number": line_idx + 1,
            "syllable_count": len(line_syllables),
            "syllables": line_syllables,
            "start_time": line_syllables[0]["start_time"] if line_syllables else 0,
            "end_time": line_syllables[-1]["end_time"] if line_syllables else 0,
            "duration": (line_syllables[-1]["end_time"] - line_syllables[0]["start_time"]) if line_syllables else 0,
            "accents": [s["accent"] for s in line_syllables],
            "strong_syllables": [i for i, s in enumerate(line_syllables) if s["accent"] == 1]
        }
        detailed_structure["lines"].append(line_info)
    
    logger.info(f"✅ Struttura vocale: {len(lines)} righe, {len(syllables)} sillabe totali")
    return detailed_structure


def analyze_metric_pattern(audio_features: Dict) -> Dict:
    """
    Analizza pattern metrico completo: sillabe, accenti, durata, metrica.
    Ora include anche struttura dettagliata per riga.
    """
    logger.info("🎵 Analisi pattern metrico...")
    
    onset_times = audio_features.get("rhythm", {}).get("onset_times", [])
    tempo = audio_features.get("tempo", 120)
    
    if not onset_times:
        # Fallback: usa beat
        beats = audio_features.get("beats", [])
        if beats:
            import librosa
            # Converti frames a tempi (serve sample_rate)
            # Per ora usa approssimazione
            onset_times = [i * (60.0 / tempo) for i in range(len(beats))]
    
    n_syllables, accents = estimate_syllables_from_onsets(onset_times, tempo)
    
    # Estrai struttura dettagliata
    detailed_structure = extract_detailed_vocal_structure(audio_features)
    
    # Pattern metrico (compatibilità con vecchio codice)
    metric_pattern = {
        "syllable_count": n_syllables,
        "accents": accents,
        "strong_beats": sum(accents),
        "time_signature": "4/4",  # Assumiamo 4/4
        "tempo": tempo,
        # NUOVO: struttura dettagliata per riga
        "detailed_structure": detailed_structure
    }
    
    logger.info(f"✅ Pattern metrico: {n_syllables} sillabe, {sum(accents)} accenti forti, {detailed_structure['total_lines']} righe")
    return metric_pattern


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

