"""
Conteggio sillabe semplice per parole inglesi
Usa pronouncing se disponibile, altrimenti euristica
"""
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

PRONOUNCING_AVAILABLE = False
try:
    import pronouncing
    PRONOUNCING_AVAILABLE = True
    logger.info("✅ pronouncing disponibile per conteggio sillabe")
except ImportError:
    logger.warning("pronouncing non disponibile - uso euristica per sillabe")


def count_syllables(word: str) -> int:
    """
    Conta sillabe in una parola.
    Usa pronouncing se disponibile, altrimenti euristica.
    """
    if not word:
        return 0
    
    # Pulisci parola (rimuovi punteggiatura)
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
    word = word.lower()
    count = 0
    prev_was_vowel = False
    
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_was_vowel:
            count += 1
        prev_was_vowel = is_vowel
    
    # Regole speciali
    if word.endswith('e'):
        count -= 1  # "e" muta alla fine
    if word.endswith('le') and len(word) > 2:
        count += 1  # "le" finale conta come sillaba
    
    return max(1, count)  # Minimo 1 sillaba


def count_syllables_in_text(text: str) -> Dict:
    """
    Conta sillabe in tutto il testo.
    Restituisce:
    - total_syllables: totale sillabe
    - words: lista di parole con conteggio sillabe
    - lines_syllables: sillabe per riga
    """
    if not text:
        return {
            "total_syllables": 0,
            "words": [],
            "lines_syllables": []
        }
    
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    words_info = []
    lines_syllables = []
    total = 0
    
    for line in lines:
        words = line.split()
        line_syllables = 0
        
        for word in words:
            syl_count = count_syllables(word)
            words_info.append({
                "word": word,
                "syllables": syl_count
            })
            line_syllables += syl_count
            total += syl_count
        
        lines_syllables.append(line_syllables)
    
    logger.info(f"✅ Conteggio sillabe: {total} totali, {len(words_info)} parole")
    
    return {
        "total_syllables": total,
        "words": words_info,
        "lines_syllables": lines_syllables
    }


def get_key_words(text: str, max_words: int = 10) -> List[str]:
    """
    Estrae parole chiave dal testo (parole più comuni, esclusi stopwords).
    """
    if not text:
        return []
    
    # Stopwords comuni
    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that',
        'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me',
        'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our',
        'their', 'la', 'la la', 'la la la'  # Suoni vocali comuni
    }
    
    # Estrai parole
    import re
    words = re.findall(r'\b\w+\b', text.lower())
    
    # Filtra stopwords e conta
    word_counts = {}
    for word in words:
        if word not in stopwords and len(word) > 2:
            word_counts[word] = word_counts.get(word, 0) + 1
    
    # Ordina per frequenza
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Prendi le prime max_words
    key_words = [word for word, count in sorted_words[:max_words]]
    
    logger.info(f"✅ Parole chiave estratte: {len(key_words)}")
    
    return key_words

