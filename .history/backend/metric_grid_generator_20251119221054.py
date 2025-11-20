"""
Generatore di testo basato su GRIGLIA METRICA
Approccio semplificato:
1. Analizza voce isolata → estrae griglia metrica (timing, durata sillabe, accenti)
2. Trascrive (anche se sbagliato/non ha significato)
3. Identifica parole/frasi senza significato in inglese
4. Sostituisce con frasi inglesi che si adattano alla griglia metrica
5. Genera testo finale riempiendo gli "spazi" nella metrica
"""
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import re
import numpy as np

logger = logging.getLogger(__name__)

# Check pronouncing per validazione parole
PRONOUNCING_AVAILABLE = False
try:
    import pronouncing
    PRONOUNCING_AVAILABLE = True
except ImportError:
    pass


def create_metric_grid_from_vocal(audio_features: Dict, transcription: Dict) -> Dict:
    """
    Crea una GRIGLIA METRICA dalla voce isolata.
    
    La griglia contiene:
    - Slot temporali (quando inizia/finisce ogni sillaba)
    - Durata di ogni slot
    - Accenti (forte/debole)
    - Pitch (opzionale)
    - Testo trascritto (anche sbagliato) per ogni slot
    
    Returns:
    {
        "grid": [
            {
                "slot_index": 0,
                "start_time": 0.0,
                "end_time": 0.25,
                "duration": 0.25,
                "accent": 1,
                "pitch": 440.0,
                "transcribed_text": "la",
                "is_valid_english": False,
                "syllable_count": 1
            },
            ...
        ],
        "lines": [
            {
                "line_index": 0,
                "slots": [0, 1, 2, ...],
                "start_time": 0.0,
                "end_time": 2.5,
                "total_syllables": 8
            },
            ...
        ],
        "total_slots": 50,
        "total_lines": 4
    }
    """
    logger.info("📊 Creazione griglia metrica dalla voce isolata...")
    
    # Estrai informazioni dalla voce
    onset_times = audio_features.get("rhythm", {}).get("onset_times", [])
    tempo = audio_features.get("tempo", 120)
    pitch_contour = audio_features.get("pitch_contour", [])
    prosody = audio_features.get("prosody", {})
    stress_points = prosody.get("stress", [])
    syllable_durations = prosody.get("syllable_duration", [])
    pauses = prosody.get("pauses", [])
    
    # Testo trascritto (anche se sbagliato)
    # IMPORTANTE: Usa la trascrizione ORIGINALE INTATTA, non quella pulita
    # L'IA ha bisogno di vedere TUTTA la trascrizione (anche con ripetizioni) per generare il testo corretto
    transcribed_text = transcription.get("text", "")
    transcribed_segments = transcription.get("segments", [])
    
    logger.info(f"📝 Trascrizione originale: {len(transcribed_text)} caratteri, {len(transcribed_segments)} segmenti")
    if transcribed_segments:
        total_duration = max([seg.get("end", seg.get("start", 0) + seg.get("duration", 0)) for seg in transcribed_segments] or [0])
        logger.info(f"📝 Durata trascrizione: {total_duration:.1f}s (tutti i segmenti inclusi)")
    
    # Ottieni durata totale audio
    audio_duration = audio_features.get("duration", 0)
    if not audio_duration and transcribed_segments:
        # Calcola durata dall'ultimo segmento
        last_seg = transcribed_segments[-1] if transcribed_segments else {}
        audio_duration = last_seg.get("end", 0) or (last_seg.get("start", 0) + last_seg.get("duration", 0))
    
    # Se non ci sono onset_times, creali approssimativamente dal testo
    if not onset_times and transcribed_segments:
        onset_times = [seg.get("start", 0) for seg in transcribed_segments]
        logger.info(f"⚠️  Nessun onset rilevato, uso timing da trascrizione: {len(onset_times)} segmenti")
    
    if not onset_times:
        # Fallback: crea onset approssimativi basati su tempo
        if not audio_duration:
            audio_duration = 30.0  # Default
        avg_syllable_duration = 0.25  # 250ms per sillaba
        n_syllables = int(audio_duration / avg_syllable_duration)
        onset_times = [i * avg_syllable_duration for i in range(n_syllables)]
        logger.warning(f"⚠️  Creo onset approssimativi: {n_syllables} sillabe, durata media {avg_syllable_duration}s")
    
    # IMPORTANTE: Assicurati che la griglia copra TUTTA la durata dell'audio
    if onset_times and audio_duration > 0:
        last_onset = onset_times[-1]
        if last_onset < audio_duration - 0.5:  # Se manca più di 0.5s
            # Aggiungi slot aggiuntivi fino alla fine
            avg_duration = np.mean(np.diff(onset_times)) if len(onset_times) > 1 else 0.25
            current_time = last_onset + avg_duration
            additional_slots = []
            while current_time < audio_duration:
                additional_slots.append(current_time)
                current_time += avg_duration
            if additional_slots:
                onset_times.extend(additional_slots)
                logger.info(f"📊 Aggiunti {len(additional_slots)} slot per coprire tutta la durata audio ({audio_duration:.1f}s)")
    
    # Crea slot nella griglia
    grid = []
    transcribed_words = _split_transcription_into_words(transcribed_text, transcribed_segments)
    logger.info(f"📝 Parole trascritte: {len(transcribed_words)} (da {len(transcribed_segments)} segmenti originali)")
    
    for i, onset_time in enumerate(onset_times):
        # Durata slot
        if i < len(onset_times) - 1:
            duration = onset_times[i + 1] - onset_time
        else:
            # Ultimo slot: durata media
            if syllable_durations:
                duration = np.mean([d.get("duration", 0.25) for d in syllable_durations])
            else:
                duration = 0.25  # Default 250ms
        
        # Trova durata più precisa se disponibile
        if syllable_durations:
            closest_dur = min(syllable_durations,
                            key=lambda d: abs(d.get("start", 0) - onset_time))
            if abs(closest_dur.get("start", 0) - onset_time) < 0.3:
                duration = closest_dur.get("duration", duration)
        
        # Accento
        accent = 0
        for stress in stress_points:
            if abs(stress.get("time", 0) - onset_time) < 0.15:
                if stress.get("level") == "strong":
                    accent = 1
                break
        
        # Pitch
        pitch = None
        if pitch_contour:
            closest_pitch = min(pitch_contour,
                              key=lambda p: abs(p[0] - onset_time) if isinstance(p, tuple) 
                                          else abs(p.get("time", 0) - onset_time))
            if isinstance(closest_pitch, tuple):
                if abs(closest_pitch[0] - onset_time) < 0.2:
                    pitch = closest_pitch[1]
            elif abs(closest_pitch.get("time", 0) - onset_time) < 0.2:
                pitch = closest_pitch.get("pitch")
        
        # Testo trascritto per questo slot
        slot_text = ""
        if i < len(transcribed_words):
            slot_text = transcribed_words[i]
        elif transcribed_text:
            # Fallback: dividi testo per numero di slot
            words = transcribed_text.split()
            if words:
                word_idx = int(i * len(words) / len(onset_times))
                if word_idx < len(words):
                    slot_text = words[word_idx]
        
        # Valida se è inglese valido
        is_valid_english = _is_valid_english_word(slot_text)
        
        # Conta sillabe
        syllable_count = _count_syllables_simple(slot_text) if slot_text else 1
        
        slot = {
            "slot_index": i,
            "start_time": float(onset_time),
            "end_time": float(onset_time + duration),
            "duration": float(duration),
            "accent": accent,
            "pitch": float(pitch) if pitch else None,
            "transcribed_text": slot_text,
            "is_valid_english": is_valid_english,
            "syllable_count": syllable_count
        }
        grid.append(slot)
    
    # Dividi in righe basate su pause
    lines = _divide_grid_into_lines(grid, pauses, tempo)
    
    logger.info(f"✅ Griglia creata: {len(grid)} slot, {len(lines)} righe")
    
    return {
        "grid": grid,
        "lines": lines,
        "total_slots": len(grid),
        "total_lines": len(lines),
        "tempo": tempo
    }


def _split_transcription_into_words(text: str, segments: List[Dict]) -> List[str]:
    """Divide trascrizione in parole, usando timing se disponibile."""
    if not text:
        return []
    
    # Se ci sono segmenti con timing, usa quelli
    if segments:
        words = []
        for seg in segments:
            seg_text = seg.get("text", "").strip()
            if seg_text:
                # Dividi segmento in parole
                seg_words = seg_text.split()
                words.extend(seg_words)
        return words
    
    # Altrimenti dividi testo normale
    return text.split()


def _is_vocalization(word: str) -> bool:
    """Rileva se una parola è un vocalizzo (la-la-la, oh-oh-oh, ecc.)."""
    if not word:
        return False
    
    word = word.lower().strip('.,!?;:"()[]{}')
    
    # Pattern vocalizzi comuni nel canto
    vocalization_patterns = [
        r'^la+(-la+)*$',  # "la", "la-la", "la-la-la"
        r'^na+(-na+)*$',  # "na", "na-na", "na-na-na"
        r'^da+(-da+)*$',  # "da", "da-da", "da-da-da"
        r'^do+(-do+)*$',  # "do", "do-do", "do-do-do"
        r'^ba+(-ba+)*$',  # "ba", "ba-ba", "ba-ba-ba"
        r'^pa+(-pa+)*$',  # "pa", "pa-pa", "pa-pa-pa"
        r'^ma+(-ma+)*$',  # "ma", "ma-ma", "ma-ma-ma"
        r'^ah+(-ah+)*$',  # "ah", "ah-ah", "ah-ah-ah"
        r'^oh+(-oh+)*$',  # "oh", "oh-oh", "oh-oh-oh"
        r'^eh+(-eh+)*$',  # "eh", "eh-eh", "eh-eh-eh"
        r'^uh+(-uh+)*$',  # "uh", "uh-uh", "uh-uh-uh"
        r'^oo+(-oo+)*$',  # "oo", "oo-oo", "oo-oo-oo"
        r'^mm+(-mm+)*$',  # "mm", "mm-mm", "mm-mm-mm"
        r'^hm+(-hm+)*$',  # "hm", "hm-hm", "hm-hm-hm"
    ]
    
    for pattern in vocalization_patterns:
        if re.match(pattern, word):
            return True
    
    # Vocali singole ripetute
    if re.match(r'^[aeiou]+$', word) and len(word) <= 4:
        return True
    
    return False


def _is_valid_english_word(word: str) -> bool:
    """Verifica se una parola è inglese valida (esclude vocalizzi)."""
    if not word or len(word.strip()) < 2:
        return False
    
    # Pulisci parola
    word = word.lower().strip('.,!?;:"()[]{}')
    
    # PRIMA: Controlla se è un vocalizzo (non è inglese valido)
    if _is_vocalization(word):
        return False
    
    # Check con pronouncing se disponibile
    if PRONOUNCING_AVAILABLE:
        try:
            phones = pronouncing.phones_for_word(word)
            return len(phones) > 0
        except:
            pass
    
    # Se sembra una parola inglese (ha consonanti e vocali)
    if re.search(r'[bcdfghjklmnpqrstvwxyz]', word) and re.search(r'[aeiou]', word):
        return True
    
    return False


def _count_syllables_simple(word: str) -> int:
    """Conta sillabe in modo semplice."""
    if not word:
        return 1
    
    word = word.lower().strip('.,!?;:"()[]{}')
    
    if PRONOUNCING_AVAILABLE:
        try:
            phones = pronouncing.phones_for_word(word)
            if phones:
                return pronouncing.syllable_count(phones[0])
        except:
            pass
    
    # Euristica: conta vocali
    vowels = 'aeiouy'
    count = 0
    prev_was_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_was_vowel:
            count += 1
        prev_was_vowel = is_vowel
    
    # Regole speciali
    if word.endswith('e'):
        count -= 1
    if word.endswith('le') and len(word) > 2:
        count += 1
    
    return max(1, count)


def _divide_grid_into_lines(grid: List[Dict], pauses: List[Dict], tempo: float) -> List[Dict]:
    """Divide griglia in righe basate su pause e ritmo."""
    if not grid:
        return []
    
    lines = []
    current_line = []
    pause_threshold = 0.4  # Pause > 400ms dividono righe
    
    for i, slot in enumerate(grid):
        current_line.append(slot["slot_index"])
        
        # Controlla se c'è una pausa dopo questo slot
        has_pause = False
        if i < len(grid) - 1:
            next_slot = grid[i + 1]
            gap = next_slot["start_time"] - slot["end_time"]
            
            # Controlla pause esplicite
            for pause in pauses:
                if pause.get("start", 0) <= slot["end_time"] <= pause.get("end", 0):
                    has_pause = True
                    break
            
            # Se gap > soglia o pausa esplicita, fine riga
            if gap > pause_threshold or has_pause:
                if current_line:
                    start_time = grid[current_line[0]]["start_time"]
                    end_time = grid[current_line[-1]]["end_time"]
                    total_syllables = sum(grid[idx]["syllable_count"] for idx in current_line)
                    
                    lines.append({
                        "line_index": len(lines),
                        "slots": current_line.copy(),
                        "start_time": start_time,
                        "end_time": end_time,
                        "total_syllables": total_syllables
                    })
                    current_line = []
        
        # Ultimo slot: aggiungi ultima riga
        if i == len(grid) - 1 and current_line:
            start_time = grid[current_line[0]]["start_time"]
            end_time = grid[current_line[-1]]["end_time"]
            total_syllables = sum(grid[idx]["syllable_count"] for idx in current_line)
            
            lines.append({
                "line_index": len(lines),
                "slots": current_line.copy(),
                "start_time": start_time,
                "end_time": end_time,
                "total_syllables": total_syllables
            })
    
    # Se non ci sono pause, dividi per numero fisso di slot (8-12 per riga)
    if len(lines) == 0 or (len(lines) == 1 and len(lines[0]["slots"]) > 12):
        lines = []
        current_line = []
        for i, slot in enumerate(grid):
            current_line.append(slot["slot_index"])
            if len(current_line) >= 10:  # 10 slot per riga
                start_time = grid[current_line[0]]["start_time"]
                end_time = grid[current_line[-1]]["end_time"]
                total_syllables = sum(grid[idx]["syllable_count"] for idx in current_line)
                
                lines.append({
                    "line_index": len(lines),
                    "slots": current_line.copy(),
                    "start_time": start_time,
                    "end_time": end_time,
                    "total_syllables": total_syllables
                })
                current_line = []
        
        if current_line:
            start_time = grid[current_line[0]]["start_time"]
            end_time = grid[current_line[-1]]["end_time"]
            total_syllables = sum(grid[idx]["syllable_count"] for idx in current_line)
            
            lines.append({
                "line_index": len(lines),
                "slots": current_line.copy(),
                "start_time": start_time,
                "end_time": end_time,
                "total_syllables": total_syllables
            })
    
    return lines


def generate_text_from_grid(metric_grid: Dict, use_ai: bool = True, instrumental_features: Dict = None, transcription: Dict = None) -> Dict:
    """
    Genera testo inglese riempiendo la griglia metrica.
    
    Strategia MIGLIORATA:
    1. Analizza CONTESTO MUSICALE completo (base strumentale + voce)
    2. Per ogni slot nella griglia:
       - Se testo trascritto è inglese valido → mantieni o migliora nel contesto
       - Se testo trascritto NON è inglese valido → sostituisci con frase inglese che:
         * Ha stesso numero di sillabe
         * Si adatta al timing (durata)
         * Rispetta accenti
         * Ha senso nel CONTESTO della canzone (tema, emozione, ritmo)
    3. Genera righe complete che formano una canzone coerente
    
    Args:
        metric_grid: Griglia metrica dalla voce
        use_ai: Usa AI per generare sostituzioni intelligenti
        instrumental_features: Features dalla base strumentale (BPM, ritmo, tonalità)
        transcription: Trascrizione completa per contesto
    
    Returns:
    {
        "text": "testo completo generato",
        "lines": ["riga 1", "riga 2", ...],
        "replacements": [...],
        "song_context": {...}  # Contesto musicale usato
    }
    """
    logger.info("📝 Generazione testo dalla griglia metrica (con contesto musicale)...")
    
    grid = metric_grid.get("grid", [])
    lines_info = metric_grid.get("lines", [])
    
    if not grid:
        return {
            "text": "",
            "lines": [],
            "replacements": [],
            "song_context": {}
        }
    
    # Analizza contesto musicale completo
    song_context = _analyze_song_context(metric_grid, instrumental_features, transcription)
    logger.info(f"🎵 Contesto canzone: {song_context.get('mood', 'unknown')} mood, {song_context.get('tempo_category', 'unknown')} tempo")
    
    # Genera testo per righe (non slot per slot) per avere coerenza
    replacements = []
    filled_grid = []
    
    # PRIMA: Analizza tutte le righe per capire il tema generale
    all_transcribed = " ".join([slot.get("transcribed_text", "") for slot in grid if slot.get("transcribed_text")])
    song_theme = _detect_song_theme(all_transcribed, song_context)
    logger.info(f"🎯 Tema canzone rilevato: {song_theme}")
    
    # PER OGNI RIGA: Genera testo coerente che forma una canzone
    previous_lines = []  # Traccia righe precedenti per coerenza
    
    for line_idx, line_info in enumerate(lines_info):
        line_slots = line_info.get("slots", [])
        line_syllables = line_info.get("total_syllables", 0)
        
        # Estrai slot di questa riga
        line_slot_data = [grid[idx] for idx in line_slots if idx < len(grid)]
        
        # Genera testo per questa riga considerando:
        # - Sillabe totali della riga
        # - Timing della riga
        # - Contesto musicale
        # - Tema della canzone
        # - Righe precedenti (per coerenza narrativa)
        # Estrai caratteristiche del CANTO da questa riga (vibrato, portamento, melodia)
        line_pitches = [slot.get("pitch") for slot in line_slot_data if slot.get("pitch")]
        line_has_melody = len(line_pitches) > 0
        line_melody_range = (max(line_pitches) - min(line_pitches)) if line_pitches and len(line_pitches) > 1 else 0
        
        # Passa info melodia al contesto
        singing_features = {
            "has_melody": line_has_melody,
            "melody_range": line_melody_range,
            "pitch_variation": "high" if line_melody_range > 200 else "medium" if line_melody_range > 100 else "low"
        }
        
        line_text = _generate_line_text(
            line_slot_data, 
            song_context, 
            song_theme,
            use_ai=use_ai,
            previous_lines=previous_lines,
            line_index=line_idx,
            total_lines=len(lines_info),
            singing_features=singing_features  # Passa caratteristiche del canto
        )
        
        # Pulisci la riga generata prima di aggiungerla
        from text_cleaner import clean_generated_text
        line_text_original = line_text.strip()
        line_text = clean_generated_text(line_text_original)
        
        # Se la pulizia ha rimosso troppo, usa l'originale
        if len(line_text) < len(line_text_original) * 0.3 and len(line_text_original) > 10:
            logger.warning(f"⚠️  Pulizia troppo aggressiva per riga {line_idx}: {len(line_text_original)} -> {len(line_text)} caratteri, uso originale")
            line_text = line_text_original
        
        # Assicurati che la riga non sia vuota
        if not line_text or len(line_text.strip()) < 3:
            logger.warning(f"⚠️  Riga {line_idx} vuota o troppo corta dopo generazione, rigenero...")
            # Rigenera con fallback
            line_text = _generate_new_line(
                song_context, 
                song_theme, 
                line_syllables, 
                (line_slot_data[-1].get("end_time", 0) - line_slot_data[0].get("start_time", 0)) if line_slot_data else 2.0,
                use_ai=False,  # Usa fallback senza AI per velocità
                previous_lines=previous_lines,
                line_index=line_idx,
                total_lines=len(lines_info),
                singing_features=singing_features
            )
            if not line_text or len(line_text.strip()) < 3:
                # Ultimo fallback: usa testo trascritto
                line_text = " ".join([slot.get("transcribed_text", "") for slot in line_slot_data if slot.get("transcribed_text")])
                if not line_text:
                    line_text = f"Line {line_idx + 1}"  # Fallback finale
        
        logger.info(f"📝 Riga {line_idx + 1}/{len(lines_info)} generata: {len(line_text)} caratteri, {line_syllables} sillabe target")
        previous_lines.append(line_text)
        
        # Aggiorna griglia con testo generato
        # IMPORTANTE: Usa la riga completa generata, non spezzarla in singole parole
        # perché questo causa ripetizioni quando viene ricostruita
        words = line_text.split()
        word_idx = 0
        for slot in line_slot_data:
            if word_idx < len(words):
                filled_text = words[word_idx]
                word_idx += 1
            else:
                filled_text = slot.get("transcribed_text", "")
            
            # Traccia sostituzioni
            original = slot.get("transcribed_text", "")
            if original != filled_text and not slot.get("is_valid_english", False):
                replacements.append({
                    "slot_index": slot["slot_index"],
                    "original": original if original else "(vuoto)",
                    "replacement": filled_text,
                    "reason": "not_valid_english" if original else "empty",
                    "line_context": song_theme
                })
            
            filled_grid.append({
                **slot,
                "filled_text": filled_text
            })
    
    # Costruisci righe finali usando le righe generate (non ricostruirle dagli slot)
    # Questo evita ripetizioni causate dalla ricostruzione parola per parola
    result_lines = []
    for line_idx, line_info in enumerate(lines_info):
        # Usa direttamente la riga generata da previous_lines se disponibile
        if line_idx < len(previous_lines) and previous_lines[line_idx]:
            result_lines.append(previous_lines[line_idx])
        else:
            # Fallback: ricostruisci dalla griglia
            line_slots = line_info.get("slots", [])
            line_words = []
            
            for slot_idx in line_slots:
                if slot_idx < len(filled_grid):
                    filled_text = filled_grid[slot_idx].get("filled_text", "")
                    if filled_text:
                        line_words.append(filled_text)
            
            if line_words:
                result_lines.append(" ".join(line_words))
    
    full_text = "\n".join(result_lines)
    
    # Pulisci il testo generato per rimuovere ripetizioni eccessive
    # IMPORTANTE: Applica pulizia solo per rimuovere ripetizioni di parole, non righe intere
    # perché potrebbero essere parte di una canzone strutturata
    from text_cleaner import clean_generated_text
    full_text_before_clean = full_text
    full_text = clean_generated_text(full_text)
    
    # Se la pulizia ha rimosso troppe righe, usa il testo prima della pulizia
    lines_before = [l.strip() for l in full_text_before_clean.split('\n') if l.strip()]
    lines_after = [l.strip() for l in full_text.split('\n') if l.strip()]
    
    if len(lines_after) < len(lines_before) * 0.5 and len(lines_before) > 2:
        logger.warning(f"⚠️  Pulizia troppo aggressiva: {len(lines_before)} -> {len(lines_after)} righe, uso testo originale")
        full_text = full_text_before_clean
    
    result_lines = [line.strip() for line in full_text.split('\n') if line.strip()]
    
    # Assicurati che abbiamo almeno tante righe quante ne sono state generate
    if len(result_lines) < len(previous_lines):
        logger.warning(f"⚠️  Righe perse durante pulizia: {len(previous_lines)} -> {len(result_lines)}, ripristino")
        result_lines = [line for line in previous_lines if line and len(line.strip()) >= 3]
    
    logger.info(f"✅ Testo generato: {len(result_lines)} righe (target: {len(lines_info)}), {len(replacements)} sostituzioni, tema: {song_theme}")
    
    return {
        "text": full_text,
        "lines": result_lines,
        "replacements": replacements,
        "grid": filled_grid,
        "song_context": song_context,
        "song_theme": song_theme
    }


def _analyze_song_context(metric_grid: Dict, instrumental_features: Dict = None, transcription: Dict = None) -> Dict:
    """
    Analizza contesto musicale completo per capire la canzone.
    Combina informazioni da:
    - Base strumentale (BPM, ritmo, tonalità)
    - Voce (pitch, intonazione, emozione)
    - Trascrizione (parole chiave, tema)
    """
    context = {
        "tempo": metric_grid.get("tempo", 120),
        "tempo_category": "medium",
        "mood": "neutral",
        "energy": "medium",
        "key": None,
        "rhythm_style": "regular"
    }
    
    # Analizza tempo
    tempo = context["tempo"]
    if tempo > 140:
        context["tempo_category"] = "fast"
        context["energy"] = "high"
        context["mood"] = "energetic"
    elif tempo > 100:
        context["tempo_category"] = "medium"
        context["energy"] = "medium"
    else:
        context["tempo_category"] = "slow"
        context["energy"] = "low"
        context["mood"] = "calm"
    
    # Analizza base strumentale se disponibile
    if instrumental_features:
        inst_tempo = instrumental_features.get("tempo")
        if inst_tempo:
            context["tempo"] = inst_tempo
            # Aggiorna categoria se diversa
            if inst_tempo > 140:
                context["tempo_category"] = "fast"
                context["energy"] = "high"
        
        rhythm_pattern = instrumental_features.get("rhythm_pattern")
        if rhythm_pattern:
            context["rhythm_style"] = rhythm_pattern
    
    # Analizza trascrizione per tema/emozione
    if transcription:
        text = transcription.get("text", "").lower()
        # Rileva emozioni/temi dalle parole chiave
        if any(word in text for word in ["love", "heart", "soul", "forever"]):
            context["mood"] = "romantic"
        elif any(word in text for word in ["pain", "hurt", "cry", "sad"]):
            context["mood"] = "sad"
        elif any(word in text for word in ["happy", "joy", "smile", "laugh"]):
            context["mood"] = "happy"
        elif any(word in text for word in ["fight", "strong", "power", "war"]):
            context["mood"] = "powerful"
            context["energy"] = "high"
    
    return context


def _detect_song_theme(transcribed_text: str, song_context: Dict) -> str:
    """
    Rileva tema della canzone dal testo trascritto e contesto.
    """
    text_lower = transcribed_text.lower()
    
    # Temi comuni
    themes = {
        "love": ["love", "heart", "soul", "forever", "together", "you", "me"],
        "loss": ["gone", "miss", "lost", "away", "goodbye", "end"],
        "hope": ["hope", "dream", "future", "tomorrow", "light", "shine"],
        "freedom": ["free", "fly", "wind", "sky", "open", "break"],
        "struggle": ["fight", "pain", "hurt", "cry", "tears", "hard"],
        "celebration": ["party", "dance", "music", "night", "fun", "celebrate"]
    }
    
    theme_scores = {}
    for theme, keywords in themes.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            theme_scores[theme] = score
    
    if theme_scores:
        detected_theme = max(theme_scores.items(), key=lambda x: x[1])[0]
        return detected_theme
    
    # Fallback: usa mood dal contesto
    mood = song_context.get("mood", "neutral")
    mood_to_theme = {
        "romantic": "love",
        "sad": "loss",
        "happy": "celebration",
        "energetic": "freedom",
        "powerful": "struggle"
    }
    return mood_to_theme.get(mood, "life")


def _generate_line_text(line_slots: List[Dict], song_context: Dict, song_theme: str, use_ai: bool = True, previous_lines: List[str] = None, line_index: int = 0, total_lines: int = 0, singing_features: Dict = None) -> str:
    """
    Genera testo per una riga completa considerando contesto musicale e tema.
    IMPORTANTE: Questo è CANTO (singing voice), non parlato!
    """
    if not line_slots:
        return ""
    
    total_syllables = sum(slot.get("syllable_count", 1) for slot in line_slots)
    line_duration = (line_slots[-1].get("end_time", 0) - line_slots[0].get("start_time", 0)) if line_slots else 0
    
    # Caratteristiche del canto (default se non passate)
    if singing_features is None:
        singing_features = {
            "has_melody": True,
            "melody_range": 0,
            "pitch_variation": "medium"
        }
    
    # Estrai testo trascritto della riga (INPUT PRINCIPALE)
    transcribed_line = " ".join([slot.get("transcribed_text", "") for slot in line_slots if slot.get("transcribed_text")])
    
    # IMPORTANTE: Usa SEMPRE il testo trascritto come base, anche se non è inglese valido
    # Il testo trascritto contiene i suoni/vocalizzi che devono essere trasformati in testo inglese
    if transcribed_line and len(transcribed_line.strip()) > 2:
        # Migliora/trasforma il testo trascritto nel contesto della canzone
        # Questo è il punto chiave: prendiamo i suoni trascritti e li trasformiamo in testo inglese
        return _improve_existing_line(transcribed_line, song_context, song_theme, total_syllables, use_ai, singing_features=singing_features)
    
    # Se non c'è testo trascritto, genera nuova riga basata su tema e contesto
    return _generate_new_line(song_context, song_theme, total_syllables, line_duration, use_ai, previous_lines, line_index, total_lines, singing_features=singing_features)


def _improve_existing_line(line_text: str, song_context: Dict, song_theme: str, target_syllables: int, use_ai: bool, singing_features: Dict = None) -> str:
    """
    Migliora/trasforma riga esistente nel contesto della canzone.
    
    IMPORTANTE: Questa funzione prende il testo trascritto (anche se sono solo suoni/vocalizzi)
    e lo trasforma in testo inglese coerente che si adatta alla metrica.
    """
    from text_cleaner import clean_generated_text
    
    if not line_text or len(line_text.strip()) < 3:
        return _generate_new_line(song_context, song_theme, target_syllables, 2.0, use_ai, None, 0, 0, singing_features=singing_features)
    
    # Conta sillabe del testo esistente
    existing_syllables = _count_syllables_simple(line_text)
    
    # Se le sillabe corrispondono già e il testo è inglese valido, miglioralo leggermente
    if abs(existing_syllables - target_syllables) <= 1:
        # Verifica se è inglese valido
        valid_words = [w for w in line_text.split() if _is_valid_english_word(w)]
        if len(valid_words) >= len(line_text.split()) * 0.7:  # Se almeno 70% sono valide
            # È già buono, pulisci e restituisci
            return clean_generated_text(line_text.strip())
    
    # Altrimenti, trasforma il testo trascritto in testo inglese coerente
    # Questo è il punto chiave: prendiamo i suoni e li trasformiamo in parole inglesi
    
    # Se le sillabe non corrispondono, prova a migliorare con AI
    if use_ai:
        try:
            from lyrics_generator import (
                DEEPSEEK_AVAILABLE, CLAUDE_AVAILABLE, OPENAI_AVAILABLE, OLLAMA_AVAILABLE,
                DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
                CLAUDE_API_KEY, CLAUDE_MODEL,
                OLLAMA_BASE_URL, OLLAMA_MODEL
            )
            import os
            
            tempo = song_context.get("tempo", 120)
            mood = song_context.get("mood", "neutral")
            
            # Estrai info vocalizzi e melodia
            vocalization_note = ""
            if singing_features and singing_features.get("has_vocalizations"):
                vocalization_note = "\n- NOTE: The transcribed line contains vocalizations (la-la-la, oh-oh-oh, etc.) - replace them with meaningful English words that fit the melody."
            
            melody_note = ""
            if singing_features and singing_features.get("pitch_range"):
                avg_pitch = sum(singing_features["pitch_range"]) / len(singing_features["pitch_range"]) if singing_features["pitch_range"] else 0
                if avg_pitch > 0:
                    melody_note = f"\n- MELODY: The line has pitch variation (average: {avg_pitch:.0f} Hz) - the lyrics should match the melodic contour."
            
            prompt = f"""You are listening to a SONG (SINGING VOICE, not speech) and writing English lyrics that match what you hear.

CRITICAL: This is SINGING, not talking! The voice has melody, pitch variations, and musical rhythm.

TRANSCRIBED LINE (what you hear being SUNG): "{line_text}"

MUSICAL CONTEXT:
- Song theme: {song_theme}
- Tempo: {tempo} BPM ({song_context.get('tempo_category', 'medium')} speed)
- Mood: {mood}
- Energy: {song_context.get('energy', 'medium')}{vocalization_note}{melody_note}

CRITICAL REQUIREMENTS:
1. Have EXACTLY {target_syllables} syllables (currently has {existing_syllables}) - COUNT CAREFULLY, this determines if it fits the melody
2. Match the song theme: {song_theme}
3. Fit the musical tempo and mood perfectly
4. Sound natural and poetic in English
5. DO NOT repeat the same words/phrases excessively
6. Write ONE unique line that fits the melody - NO repetitions
7. Consider this is SINGING - words should flow with the melody and rhythm

IMPORTANT: 
- If the transcribed line contains vocalizations (la-la-la, oh-oh-oh) or non-English sounds, replace them with meaningful English words
- Transform the sounds/words you hear into proper English lyrics that match the musical context
- Make it fit the melody perfectly with EXACTLY {target_syllables} syllables
- The lyrics must match the SINGING style, not speech

Write ONLY the improved line (no repetitions, no explanations):"""
            
            # Prova DeepSeek (priorità 1)
            if DEEPSEEK_AVAILABLE:
                try:
                    import requests
                    response = requests.post(
                        f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": DEEPSEEK_MODEL,
                            "messages": [
                                {"role": "system", "content": "You are a songwriter. Improve song lyrics to match exact syllable count and musical context."},
                                {"role": "user", "content": prompt}
                            ],
                            "temperature": 0.7,
                            "max_tokens": 50
                        },
                        timeout=20
                    )
                    if response.status_code == 200:
                        improved = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                        if improved:
                            cleaned = clean_generated_text(improved.split('\n')[0].strip().strip('"'))
                            return cleaned
                except:
                    pass
            
            # Prova Claude (priorità 2)
            if CLAUDE_AVAILABLE:
                try:
                    import anthropic
                    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
                    message = client.messages.create(
                        model=CLAUDE_MODEL,
                        max_tokens=50,
                        temperature=0.7,
                        system="You are a songwriter. Improve song lyrics to match exact syllable count and musical context.",
                        messages=[{"role": "user", "content": prompt}]
                    )
                    if message.content:
                        cleaned = clean_generated_text(message.content[0].text.strip().split('\n')[0].strip('"'))
                        return cleaned
                except:
                    pass
            
            # Prova OpenAI (priorità 3)
            if OPENAI_AVAILABLE:
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a songwriter. Improve song lyrics to match exact syllable count and musical context."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=50,
                        temperature=0.7
                    )
                    if response.choices:
                        cleaned = clean_generated_text(response.choices[0].message.content.strip().strip('"'))
                        return cleaned
                except:
                    pass
            
            # Prova Ollama (priorità 4)
            if OLLAMA_AVAILABLE:
                try:
                    import requests
                    response = requests.post(
                        f"{OLLAMA_BASE_URL}/api/generate",
                        json={
                            "model": OLLAMA_MODEL,
                            "prompt": prompt,
                            "stream": False,
                            "options": {"temperature": 0.7, "num_predict": 50}
                        },
                        timeout=20
                    )
                    if response.status_code == 200:
                        improved = response.json().get("response", "").strip()
                        lines = [l.strip() for l in improved.split('\n') if l.strip() and not l.strip().startswith('"')]
                        if lines:
                            cleaned = clean_generated_text(lines[0].strip('"').strip())
                            return cleaned
                except:
                    pass
        except:
            pass
    
    # Fallback: mantieni testo originale (pulito)
    return clean_generated_text(line_text.strip())


def _generate_new_line(song_context: Dict, song_theme: str, target_syllables: int, duration: float, use_ai: bool, previous_lines: List[str] = None, line_index: int = 0, total_lines: int = 0, singing_features: Dict = None) -> str:
    """
    Genera nuova riga basata su tema, contesto musicale e metrica.
    Considera anche righe precedenti per coerenza narrativa.
    """
    # Usa AI se disponibile
    if use_ai:
        try:
            return _generate_line_with_ai(song_context, song_theme, target_syllables, duration, previous_lines, line_index, total_lines, singing_features=singing_features)
        except Exception as e:
            logger.warning(f"AI fallita per generazione riga: {e}, uso fallback")
    
    # Fallback: genera riga basata su tema e sillabe
    return _generate_line_fallback(song_context, song_theme, target_syllables, previous_lines, line_index)


def _generate_line_with_ai(song_context: Dict, song_theme: str, target_syllables: int, duration: float, previous_lines: List[str] = None, line_index: int = 0, total_lines: int = 0, singing_features: Dict = None) -> str:
    """Genera riga usando AI con contesto musicale e righe precedenti (priorità: DeepSeek > Claude > OpenAI > Ollama)."""
    # Check AI disponibili
    from lyrics_generator import (
        DEEPSEEK_AVAILABLE, CLAUDE_AVAILABLE, OPENAI_AVAILABLE, OLLAMA_AVAILABLE,
        DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, DEEPSEEK_MODEL,
        CLAUDE_API_KEY, CLAUDE_MODEL,
        OLLAMA_BASE_URL, OLLAMA_MODEL
    )
    from text_cleaner import clean_generated_text
    import os
    
    tempo = song_context.get("tempo", 120)
    mood = song_context.get("mood", "neutral")
    energy = song_context.get("energy", "medium")
    
    # Costruisci contesto righe precedenti
    previous_context = ""
    if previous_lines and len(previous_lines) > 0:
        previous_context = f"\n\nPREVIOUS LINES (for narrative coherence):\n" + "\n".join([f"Line {i+1}: {line}" for i, line in enumerate(previous_lines)])
    
    line_position = ""
    if total_lines > 0:
        if line_index == 0:
            line_position = "This is the FIRST line of the song (opening/intro)"
        elif line_index == total_lines - 1:
            line_position = "This is the LAST line of the song (ending/conclusion)"
        elif line_index < total_lines // 2:
            line_position = f"This is line {line_index + 1} of {total_lines} (early in the song)"
        else:
            line_position = f"This is line {line_index + 1} of {total_lines} (later in the song)"
    
    # Estrai caratteristiche del CANTO (non parlato!)
    line_slot_data_first = line_slot_data[0] if line_slot_data else {}
    pitch_info = line_slot_data_first.get("pitch")
    
    # Usa caratteristiche del canto se passate
    melody_info = ""
    vocalization_note = ""
    if singing_features:
        has_melody = singing_features.get("has_melody", False)
        pitch_variation = singing_features.get("pitch_variation", "medium")
        melody_info = f"\n- Melody: {'Present with ' + pitch_variation + ' variation' if has_melody else 'Following musical contour'}"
        
        # Aggiungi nota sui vocalizzi se presenti
        if singing_features.get("has_vocalizations"):
            vocalization_note = "\n- NOTE: The transcribed line contains vocalizations (la-la-la, oh-oh-oh, etc.) - replace them with meaningful English words that fit the melody and theme."
        
        # Aggiungi info pitch se disponibile
        if singing_features.get("pitch_range"):
            avg_pitch = sum(singing_features["pitch_range"]) / len(singing_features["pitch_range"]) if singing_features["pitch_range"] else 0
            if avg_pitch > 0:
                melody_info += f" (average pitch: {avg_pitch:.0f} Hz)"
    else:
        melody_info = f"\n- Melody: {'Present' if pitch_info else 'Following musical contour'}"
    
    prompt = f"""You are listening to a SONG (SINGING VOICE, not speech) and writing the English lyrics that match what you hear.

CRITICAL: This is SINGING, not spoken words!
- The voice is SUNG with melody, pitch variations, and musical phrasing
- Syllables can be extended, held, or modified to fit the melody
- The singer uses vocal techniques (vibrato, portamento, vocal extensions)
- Words flow with the music, not like normal speech

MUSICAL CONTEXT - What you're hearing:
- Song theme: {song_theme}
- Musical tempo: {tempo} BPM ({song_context.get('tempo_category', 'medium')} speed)
- Mood/emotion: {mood}
- Energy level: {energy}
- This line duration: {duration:.2f} seconds{melody_info}{vocalization_note}
{line_position}{previous_context}

YOUR TASK:
Write ONE line of English SONG LYRICS (for SINGING, not speaking) that:
1. Has EXACTLY {target_syllables} syllables (CRITICAL - count carefully, this determines if it fits the melody)
2. Matches what you HEAR being SUNG in this {song_theme} song
3. Fits the tempo and rhythm perfectly ({tempo} BPM, {duration:.2f}s duration)
4. Expresses the {mood} mood with {energy} energy
5. Sounds like actual song lyrics someone would SING to this music (not speak!)
6. Is part of a coherent {song_theme} song
7. {"Follows naturally from the previous lines" if previous_lines else "Opens the song appropriately"}
8. DO NOT repeat words or phrases - write ONE unique line with NO repetitions
9. Consider that syllables can be extended or held when sung (singing allows more flexibility than speech)

CRITICAL: You are WRITING THE LYRICS FOR THE SONG YOU'RE LISTENING TO.
This is SINGING VOICE, not speech recognition!
The lyrics must match:
- The MELODY (pitch and notes you hear - this is SUNG, not spoken)
- The RHYTHM (timing and beat - musical phrasing)
- The EMOTION (how it's being sung - vocal expression)
- The THEME ({song_theme})
- The SINGING STYLE (melodic, expressive, following the music)

IMPORTANT: 
- Write for SINGING, not speaking
- Syllables can be extended to fit the melody
- The text flows with the music
- Write ONE unique line - NO repetitions, NO duplicate words/phrases within the line

Write ONLY the line (no explanations, no quotes, no line numbers):"""
    
    # Prova DeepSeek (priorità 1)
    if DEEPSEEK_AVAILABLE:
        try:
            import requests
            response = requests.post(
                f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": DEEPSEEK_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a professional songwriter. Write song lyrics that match the exact syllable count and musical context."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.8,
                    "max_tokens": 50
                },
                timeout=30
            )
            if response.status_code == 200:
                generated = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if generated:
                    cleaned = clean_generated_text(generated.split('\n')[0].strip())
                    return cleaned
        except Exception as e:
            logger.warning(f"DeepSeek fallito: {e}, provo altra AI")
    
    # Prova Claude (priorità 2)
    if CLAUDE_AVAILABLE:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
            message = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=50,
                temperature=0.8,
                system="You are a professional songwriter. Write song lyrics that match the exact syllable count and musical context.",
                messages=[{"role": "user", "content": prompt}]
            )
            if message.content:
                cleaned = clean_generated_text(message.content[0].text.strip().split('\n')[0])
                return cleaned
        except Exception as e:
            logger.warning(f"Claude fallito: {e}, provo altra AI")
    
    # Prova OpenAI (priorità 3)
    if OPENAI_AVAILABLE:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional songwriter. Write song lyrics that match the exact syllable count and musical context."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.8
            )
            if response.choices:
                cleaned = clean_generated_text(response.choices[0].message.content.strip().split('\n')[0])
                return cleaned
        except Exception as e:
            logger.warning(f"OpenAI fallito: {e}, provo altra AI")
    
    # Prova Ollama (priorità 4)
    if OLLAMA_AVAILABLE:
        try:
            import requests
            response = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.8,
                        "num_predict": 50
                    }
                },
                timeout=30
            )
            if response.status_code == 200:
                generated = response.json().get("response", "").strip()
                lines = [l.strip() for l in generated.split('\n') if l.strip()]
                if lines:
                    cleaned = clean_generated_text(lines[0])
                    return cleaned
        except Exception as e:
            logger.warning(f"Ollama fallito: {e}")
    
    # Se nessuna AI disponibile, usa fallback
    raise Exception("Nessuna AI disponibile")


def _generate_line_fallback(song_context: Dict, song_theme: str, target_syllables: int, previous_lines: List[str] = None, line_index: int = 0) -> str:
    """Genera riga senza AI basandosi su tema e sillabe."""
    import random
    
    # Template per tema
    templates = {
        "love": [
            "I love you more each day",
            "You are my heart and soul",
            "Together we will stay",
            "Love is all I know"
        ],
        "loss": [
            "You're gone but not forgotten",
            "I miss you every day",
            "The pain will never fade",
            "Without you I'm lost"
        ],
        "hope": [
            "Tomorrow brings new light",
            "I dream of better days",
            "Hope will guide the way",
            "The future's bright ahead"
        ],
        "freedom": [
            "I'm free to fly away",
            "Breaking all the chains",
            "Nothing can hold me down",
            "I'll soar into the sky"
        ],
        "struggle": [
            "I fight through all the pain",
            "The struggle makes me strong",
            "I won't give up today",
            "I'll rise above it all"
        ],
        "celebration": [
            "Let's dance the night away",
            "Music fills the air",
            "We celebrate tonight",
            "The party's just begun"
        ]
    }
    
    # Scegli template appropriato
    theme_templates = templates.get(song_theme, templates["love"])
    
    # Scegli template più vicino al numero di sillabe
    best_template = None
    min_diff = float('inf')
    
    for template in theme_templates:
        template_syllables = _count_syllables_simple(template)
        diff = abs(template_syllables - target_syllables)
        if diff < min_diff:
            min_diff = diff
            best_template = template
    
    if best_template:
        return best_template
    
    # Fallback: genera semplice
    words_1 = ["love", "time", "way", "day", "night", "light"]
    words_2 = ["music", "dancing", "feeling", "dreaming"]
    
    line = []
    syllables = 0
    while syllables < target_syllables:
        remaining = target_syllables - syllables
        if remaining >= 2:
            word = random.choice(words_2)
            syllables += 2
        else:
            word = random.choice(words_1)
            syllables += 1
        line.append(word)
    
    return " ".join(line)


def _find_english_replacement(slot: Dict, use_ai: bool = True) -> Dict:
    """
    Trova frase inglese che sostituisce slot non valido.
    
    Criteri:
    - Stesso numero di sillabe
    - Durata simile (veloce/lento)
    - Accento rispettato
    """
    syllable_count = slot.get("syllable_count", 1)
    duration = slot.get("duration", 0.25)
    accent = slot.get("accent", 0)
    
    # Per ora: usa parole comuni che si adattano
    # In futuro: usa AI per generare frasi più creative
    
    # Parole per numero di sillabe
    words_by_syllables = {
        1: ["love", "time", "way", "day", "night", "light", "heart", "soul", "dream", "hope", "life", "home"],
        2: ["music", "dancing", "feeling", "dreaming", "singing", "calling", "falling", "rising", "coming", "going"],
        3: ["beautiful", "wonderful", "together", "forever", "remember", "believe", "complete"],
        4: ["imagination", "celebration", "generation", "situation", "destination"]
    }
    
    # Scegli parola appropriata
    import random
    if syllable_count in words_by_syllables:
        candidates = words_by_syllables[syllable_count]
    else:
        # Usa parola più vicina
        closest = min(words_by_syllables.keys(), key=lambda x: abs(x - syllable_count))
        candidates = words_by_syllables[closest]
    
    replacement_word = random.choice(candidates)
    
    # Se accento forte, capitalizza
    if accent == 1:
        replacement_word = replacement_word.capitalize()
    
    return {
        "text": replacement_word,
        "syllable_match": True,
        "duration_match": True  # Approssimativo
    }

