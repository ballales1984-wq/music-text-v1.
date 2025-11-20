"""
Timing Analysis - stima distanza tra parole, ripetizioni e tempi

Usa i segmenti vocali (start/end) + testo per segmento per:
- stimare inizio/fine di ogni parola
- calcolare ripetizioni e frequenze
- creare una "base" di dati temporali da usare dopo
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


def build_word_timing(transcription: Dict) -> Dict[str, Any]:
    """
    Costruisce una struttura con timing per parola a partire dalla trascrizione per segmenti.

    transcription["segments"] deve contenere una lista di:
        {"start": float, "end": float, "duration": float, "text": str}
    """
    segments: List[Dict[str, Any]] = transcription.get("segments") or []

    all_words: List[Dict[str, Any]] = []
    word_counts: Dict[str, int] = {}

    for seg_idx, seg in enumerate(segments):
        text = (seg.get("text") or "").strip()
        if not text:
            continue

        start = float(seg.get("start", 0.0))
        end = float(seg.get("end", 0.0))
        duration = max(float(seg.get("duration", end - start)), 0.0)

        if duration <= 0 or end <= start:
            continue

        words = text.split()
        if not words:
            continue

        # Durata media per parola nel segmento
        word_dur = duration / len(words)

        for w_idx, word in enumerate(words):
            w_start = start + w_idx * word_dur
            w_end = min(end, w_start + word_dur)

            word_lower = word.lower()
            word_counts[word_lower] = word_counts.get(word_lower, 0) + 1

            all_words.append(
                {
                    "word": word,
                    "word_lower": word_lower,
                    "segment_index": seg_idx,
                    "index_in_segment": w_idx,
                    "start": w_start,
                    "end": w_end,
                    "duration": w_end - w_start,
                }
            )

    # Ordina le parole per tempo di inizio (ordine reale di ascolto)
    all_words.sort(key=lambda w: w["start"])

    # Trova ripetizioni globali (stessa parola ripetuta molte volte)
    repeated_words = [
        {"word": w, "count": c} for w, c in sorted(word_counts.items(), key=lambda x: -x[1]) if c > 1
    ]

    logger.info(
        f"✅ Timing parole: {len(all_words)} parole totali, "
        f"{len(repeated_words)} parole con ripetizioni"
    )

    return {
        "words": all_words,
        "repeated_words": repeated_words,
        "total_words": len(all_words),
    }


