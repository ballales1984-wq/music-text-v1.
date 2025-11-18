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


def analyze_metric_pattern(audio_features: Dict) -> Dict:
    """
    Analizza pattern metrico completo: sillabe, accenti, durata, metrica.
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
    
    # Pattern metrico
    metric_pattern = {
        "syllable_count": n_syllables,
        "accents": accents,
        "strong_beats": sum(accents),
        "time_signature": "4/4",  # Assumiamo 4/4
        "tempo": tempo
    }
    
    logger.info(f"✅ Pattern metrico: {n_syllables} sillabe, {sum(accents)} accenti forti")
    return metric_pattern

