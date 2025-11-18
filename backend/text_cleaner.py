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
    
    # Conta occorrenze
    sentence_counts = {}
    for sent in sentences:
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
    
    for sent in sentences:
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
        "total_unique_sentences": len(set(s.lower() for s in sentences)),
        "repeated_sentences": len(repeated),
        "total_repetitions": total_repetitions,
        "chorus_candidates": len(chorus_candidates),
        "final_sentences": len(unique_sentences)
    }
    
    return unique_sentences, stats


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

