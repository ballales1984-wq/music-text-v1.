"""
Pulizia e filtraggio del testo trascritto
Rimuove ripetizioni eccessive, migliora grammatica, valida qualità
"""
import logging
import re
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def clean_and_filter_text(text: str) -> Dict:
    """
    Pulisce e filtra il testo trascritto.
    Restituisce:
    - cleaned_text: testo pulito
    - removed_repetitions: numero di ripetizioni rimosse
    - original_length: lunghezza originale
    - cleaned_length: lunghezza dopo pulizia
    - statistics: statistiche dettagliate
    """
    if not text or len(text.strip()) < 5:
        return {
            "cleaned_text": text,
            "removed_repetitions": 0,
            "original_length": len(text) if text else 0,
            "cleaned_length": len(text) if text else 0,
            "statistics": {}
        }
    
    original_length = len(text)
    original_sentences = _split_into_sentences(text)
    
    logger.info(f"🧹 Pulizia testo: {len(original_sentences)} frasi originali, {original_length} caratteri")
    
    # Rimuovi ripetizioni eccessive
    cleaned_sentences, stats = _remove_excessive_repetitions(original_sentences)
    
    # Migliora grammatica base
    improved_sentences = _improve_grammar(cleaned_sentences)
    
    # Ricostruisci testo
    cleaned_text = "\n".join(improved_sentences)
    cleaned_length = len(cleaned_text)
    
    removed_repetitions = len(original_sentences) - len(cleaned_sentences)
    reduction_percent = (removed_repetitions / len(original_sentences) * 100) if original_sentences else 0
    
    statistics = {
        "original_sentences": len(original_sentences),
        "cleaned_sentences": len(cleaned_sentences),
        "removed_sentences": removed_repetitions,
        "reduction_percent": round(reduction_percent, 1),
        "original_length": original_length,
        "cleaned_length": cleaned_length,
        "length_reduction": original_length - cleaned_length,
        **stats
    }
    
    logger.info(f"✅ Testo pulito: {len(cleaned_sentences)} frasi finali ({removed_repetitions} rimosse, {reduction_percent:.1f}% riduzione)")
    
    return {
        "cleaned_text": cleaned_text,
        "removed_repetitions": removed_repetitions,
        "original_length": original_length,
        "cleaned_length": cleaned_length,
        "statistics": statistics
    }


def _split_into_sentences(text: str) -> List[str]:
    """Divide il testo in frasi."""
    # Prima prova punti/virgole
    sentences = re.split(r'[.!?]\s+', text)
    if len(sentences) == 1:
        # Dividi per virgole
        sentences = re.split(r',\s+', text)
        # Dividi anche quando c'è una maiuscola dopo una minuscola
        new_sentences = []
        for sent in sentences:
            parts = re.split(r'([a-z])\s+([A-Z])', sent)
            if len(parts) > 1:
                current = parts[0]
                for i in range(1, len(parts), 3):
                    if i+1 < len(parts):
                        new_sentences.append(current + parts[i])
                        current = parts[i+1] + (parts[i+2] if i+2 < len(parts) else '')
                if current:
                    new_sentences.append(current)
            else:
                new_sentences.append(sent)
        sentences = new_sentences
    
    # Pulisci
    cleaned = []
    for sent in sentences:
        sent = sent.strip()
        if sent and len(sent) > 3:
            cleaned.append(sent)
    
    return cleaned


def _remove_excessive_repetitions(sentences: List[str]) -> Tuple[List[str], Dict]:
    """Rimuove ripetizioni eccessive mantenendo struttura."""
    if not sentences:
        return [], {}
    
    # Prima pulisci ogni frase da ripetizioni di parole/frasi brevi
    cleaned_sentences = []
    for sent in sentences:
        cleaned_sent = _remove_word_repetitions(sent)
        cleaned_sentences.append(cleaned_sent)
    
    # Conta occorrenze
    sentence_counts = {}
    for sent in cleaned_sentences:
        sent_lower = sent.lower().strip()
        sentence_counts[sent_lower] = sentence_counts.get(sent_lower, 0) + 1
    
    # Identifica ripetizioni
    repeated = {k: v for k, v in sentence_counts.items() if v > 1}
    total_repetitions = sum(v - 1 for v in repeated.values())  # Numero di ripetizioni da rimuovere
    
    # Strategia: mantieni prima occorrenza + max 1 ripetizione se è probabile chorus
    # Se una frase appare 3+ volte, è probabile un chorus - mantienila 2 volte
    # Se appare 2 volte, mantienila 1 volta (o 2 se è breve e potrebbe essere chorus)
    
    seen = {}
    unique_sentences = []
    chorus_candidates = []
    
    for sent in cleaned_sentences:
        sent_lower = sent.lower().strip()
        count = sentence_counts[sent_lower]
        
        if sent_lower not in seen:
            # Prima occorrenza - sempre mantieni
            seen[sent_lower] = 1
            unique_sentences.append(sent)
            if count >= 3:
                chorus_candidates.append(sent_lower)
        elif count >= 3 and seen[sent_lower] < 2:
            # Chorus probabile - mantieni seconda occorrenza
            seen[sent_lower] += 1
            unique_sentences.append(sent)
        elif count == 2 and len(sent) < 50:
            # Frase breve ripetuta 2 volte - potrebbe essere chorus, mantieni
            seen[sent_lower] += 1
            unique_sentences.append(sent)
        # Altrimenti scarta (ripetizione eccessiva)
    
    stats = {
        "total_unique_sentences": len(set(s.lower() for s in cleaned_sentences)),
        "repeated_sentences": len(repeated),
        "total_repetitions": total_repetitions,
        "chorus_candidates": len(chorus_candidates),
        "final_sentences": len(unique_sentences)
    }
    
    return unique_sentences, stats


def _remove_word_repetitions(text: str) -> str:
    """
    Rimuove ripetizioni eccessive di parole/frasi all'interno di una singola frase.
    Es: "I'm coming from I'm coming from I'm coming from" -> "I'm coming from"
    """
    if not text or len(text) < 10:
        return text
    
    # Pattern per trovare ripetizioni consecutive della stessa parola/frase
    #Cerca sequenze come "word word word" o "phrase phrase phrase"
    
    # Pattern 1: Ripetizioni esatte consecutive (case insensitive)
    # "I'm coming from I'm coming from" -> "I'm coming from"
    pattern1 = r'(\b\S+(?:\s+\S+){0,5})\s+\1\b(\s+\1\b)+'
    
    # Iterazione finché non ci sono più ripetizioni
    prev_text = ""
    current_text = text
    max_iterations = 10
    iteration = 0
    
    while prev_text != current_text and iteration < max_iterations:
        prev_text = current_text
        # Rimuovi ripetizioni consecutive identiche
        current_text = re.sub(pattern1, r'\1', current_text, flags=re.IGNORECASE)
        # Pulisci spazi multipli
        current_text = re.sub(r'\s+', ' ', current_text).strip()
        iteration += 1
    
    # Pattern 2: Rimuovi parole singole ripetute 3+ volte
    # "yeah yeah yeah yeah" -> "yeah"
    pattern2 = r'\b(\w+)(?:\s+\1){2,}\b'
    current_text = re.sub(pattern2, r'\1', current_text, flags=re.IGNORECASE)
    
    # Pattern 3: Rimuovi_pattern ripetuto (per "I'm coming from coming from coming from")
    # Trova le ultime 2-4 parole e cerca se sono ripetute
    words = current_text.split()
    if len(words) >= 4:
        # Prova con le ultime 2-3 parole
        for phrase_len in [3, 2]:
            if len(words) >= phrase_len * 2:
                phrase = ' '.join(words[-phrase_len:])
                pattern = re.escape(phrase) + r'(?:\s+' + re.escape(phrase) + r')+'
                current_text = re.sub(pattern, phrase, current_text, flags=re.IGNORECASE)
    
    return current_text.strip()


def _improve_grammar(sentences: List[str]) -> List[str]:
    """Migliora grammatica base delle frasi."""
    improved = []
    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        
        # Capitalizza prima lettera
        if len(sent) > 1:
            sent = sent[0].upper() + sent[1:]
        else:
            sent = sent.upper()
        
        # Rimuovi punteggiatura eccessiva alla fine
        sent = re.sub(r'[.!?]+$', '', sent)
        
        # Aggiungi punto finale se manca (opzionale, per canzoni potrebbe non servire)
        # sent = sent + '.' if not sent.endswith(('.', '!', '?')) else sent
        
        improved.append(sent)
    
    return improved


def validate_text_quality(original: str, cleaned: str) -> Dict:
    """
    Valida la qualità del testo pulito.
    Restituisce metriche di qualità.
    """
    original_sentences = _split_into_sentences(original)
    cleaned_sentences = _split_into_sentences(cleaned)
    
    # Calcola metriche
    repetition_ratio = len(original_sentences) / len(cleaned_sentences) if cleaned_sentences else 1
    length_ratio = len(cleaned) / len(original) if original else 1
    
    # Qualità: 0-100
    quality_score = 100
    if repetition_ratio > 2:
        quality_score -= min(30, (repetition_ratio - 2) * 10)  # Penalizza ripetizioni eccessive
    if length_ratio < 0.3:
        quality_score -= 20  # Penalizza se troppo corto
    
    return {
        "quality_score": round(quality_score, 1),
        "repetition_ratio": round(repetition_ratio, 2),
        "length_ratio": round(length_ratio, 2),
        "is_good_quality": quality_score >= 70
    }


def clean_generated_text(text: str) -> str:
    """
    Pulisce testo generato dall'AI rimuovendo:
    - Ripetizioni eccessive di parole singole (es: "a a a a", "time time time")
    - Parole spezzate o isolate
    - Testo malformato
    - Ripetizioni di frasi intere eccessive
    
    Args:
        text: Testo generato dall'AI
        
    Returns:
        Testo pulito e coerente
    """
    if not text or len(text.strip()) < 3:
        return text
    
    logger.info(f"🧹 Pulizia testo generato: {len(text)} caratteri")
    
    # 0. Correggi parole spezzate comuni PRIMA di tutto (contrazioni rotte)
    # Pattern: "It' " (con spazio) o "It'" (fine parola) -> "It's "
    text = re.sub(r"\bIt'\s+", "It's ", text)  # "It' " -> "It's "
    text = re.sub(r"\bIt'$", "It's", text)  # "It'" fine riga -> "It's"
    text = re.sub(r"\bI'\s+", "I'm ", text)  # "I' " -> "I'm "
    text = re.sub(r"\bI'$", "I'm", text)  # "I'" fine riga -> "I'm"
    text = re.sub(r"\bWe'\s+", "We're ", text)  # "We' " -> "We're "
    text = re.sub(r"\bWe'$", "We're", text)  # "We'" fine riga -> "We're"
    text = re.sub(r"\bYou'\s+", "You're ", text)  # "You' " -> "You're "
    text = re.sub(r"\bYou'$", "You're", text)  # "You'" fine riga -> "You're"
    text = re.sub(r"\bThey'\s+", "They're ", text)  # "They' " -> "They're "
    text = re.sub(r"\bThey'$", "They're", text)  # "They'" fine riga -> "They're"
    text = re.sub(r"\bHe'\s+", "He's ", text)  # "He' " -> "He's "
    text = re.sub(r"\bHe'$", "He's", text)  # "He'" fine riga -> "He's"
    text = re.sub(r"\bShe'\s+", "She's ", text)  # "She' " -> "She's "
    text = re.sub(r"\bShe'$", "She's", text)  # "She'" fine riga -> "She's"
    
    # 1. Rimuovi ripetizioni eccessive di parole singole (es: "a a a a" -> "a")
    # Pattern: parola ripetuta 3+ volte consecutivamente
    text = re.sub(r'\b(\w+)(\s+\1){2,}\b', r'\1', text, flags=re.IGNORECASE)
    
    # 2. Rimuovi parole isolate molto corte ripetute (es: "a a a time" -> "a time")
    words = text.split()
    cleaned_words = []
    prev_word = None
    prev_count = 0
    
    for word in words:
        word_clean = word.strip().lower()
        # Se è una parola molto corta (1-2 caratteri) e ripetuta
        if len(word_clean) <= 2 and word_clean == prev_word:
            prev_count += 1
            if prev_count <= 1:  # Mantieni max 2 ripetizioni
                cleaned_words.append(word)
        else:
            prev_word = word_clean
            prev_count = 1
            cleaned_words.append(word)
    
    text = " ".join(cleaned_words)
    
    # 3. Rimuovi ripetizioni di frasi intere (mantieni max 1 occorrenza per evitare duplicati)
    # Prima controlla anche senza newline (per testo su una riga)
    words = text.split()
    if len(words) > 0:
        # Controlla se l'intero testo è una ripetizione
        if len(words) > 3:
            # Controlla se le prime N parole si ripetono
            first_half = " ".join(words[:len(words)//2]).lower()
            second_half = " ".join(words[len(words)//2:]).lower()
            if first_half == second_half:
                # È una ripetizione completa, mantieni solo la prima metà
                text = " ".join(words[:len(words)//2])
    
    # Poi controlla per righe
    lines = text.split('\n')
    
    # IMPORTANTE: Se il testo ha più di 2 righe, potrebbe essere una canzone con chorus
    # In questo caso, mantieni tutte le righe anche se simili (potrebbero essere intenzionali)
    # Rimuovi solo se ci sono 3+ righe identiche consecutive
    if len(lines) > 2:
        # Per canzoni: rimuovi solo ripetizioni consecutive eccessive (3+ volte)
        cleaned_lines = []
        prev_line = None
        consecutive_count = 0
        
        for line in lines:
            line_clean = line.strip().lower()
            if not line_clean or len(line_clean) < 3:
                continue
            
            if line_clean == prev_line:
                consecutive_count += 1
                if consecutive_count < 2:  # Mantieni max 2 righe consecutive identiche (chorus)
                    cleaned_lines.append(line.strip())
            else:
                consecutive_count = 0
                cleaned_lines.append(line.strip())
                prev_line = line_clean
        
        text = "\n".join(cleaned_lines)
    else:
        # Per testo corto (1-2 righe): rimuovi duplicati come prima
        seen_lines = {}
        unique_lines = []
        
        for line in lines:
            line_clean = line.strip().lower()
            if not line_clean or len(line_clean) < 3:
                continue
            
            count = seen_lines.get(line_clean, 0)
            if count < 1:  # Mantieni max 1 occorrenza (rimuovi duplicati)
                seen_lines[line_clean] = count + 1
                unique_lines.append(line.strip())
        
        text = "\n".join(unique_lines)
    
    # 4. Rimuovi parole spezzate o isolate strane (es: "Together" isolato in mezzo a ripetizioni)
    # Se una parola è isolata e circondata da ripetizioni, potrebbe essere un errore
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        words = line.split()
        if len(words) <= 1:
            cleaned_lines.append(line)
            continue
        
        # Rimuovi parole isolate che sembrano errori (parole lunghe isolate tra ripetizioni)
        filtered_words = []
        for i, word in enumerate(words):
            word_clean = word.strip().lower()
            # Se è una parola lunga (>5 caratteri) isolata tra parole corte ripetute, potrebbe essere errore
            if len(word_clean) > 5 and i > 0 and i < len(words) - 1:
                prev_word = words[i-1].strip().lower()
                next_word = words[i+1].strip().lower() if i+1 < len(words) else ""
                # Se le parole adiacenti sono corte e ripetute, potrebbe essere un errore
                if len(prev_word) <= 3 and len(next_word) <= 3 and prev_word == next_word:
                    continue  # Salta questa parola
            filtered_words.append(word)
        
        if filtered_words:
            cleaned_lines.append(" ".join(filtered_words))
    
    text = "\n".join(cleaned_lines)
    
    # 5. Rimuovi spazi multipli
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Max 2 newline consecutivi
    
    # 6. Rimuovi caratteri strani o isolati
    text = re.sub(r'\b\w{1}\b(?=\s|$)', '', text)  # Rimuovi parole di 1 carattere isolate
    text = re.sub(r'\s+', ' ', text)  # Rimuovi spazi multipli di nuovo
    
    # 7. Rimuovi ripetizioni di frasi molto corte (1-3 parole) ripetute più di 2 volte
    words = text.split()
    if len(words) > 0:
        cleaned_words = []
        seen_phrases = {}
        window_size = 3  # Controlla frasi di max 3 parole
        
        for i in range(len(words)):
            # Controlla frase corrente (1-3 parole)
            phrase_found = False
            for size in range(1, min(window_size + 1, len(words) - i + 1)):
                phrase = " ".join(words[i:i+size]).lower()
                count = seen_phrases.get(phrase, 0)
                
                if count >= 2 and size <= 2:  # Se frase corta ripetuta 2+ volte, salta
                    phrase_found = True
                    # Salta le parole di questa frase
                    for _ in range(size - 1):
                        if i + 1 < len(words):
                            i += 1
                    break
                else:
                    seen_phrases[phrase] = count + 1
            
            if not phrase_found:
                cleaned_words.append(words[i])
        
        text = " ".join(cleaned_words)
    
    # 9. Rimuovi spazi multipli finali
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Max 2 newline consecutivi
    
    logger.info(f"✅ Testo generato pulito: {len(text)} caratteri")
    
    return text.strip()