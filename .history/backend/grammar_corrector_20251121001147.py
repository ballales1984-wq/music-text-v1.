"""
Grammar / Lyric Corrector

Data una frase "grezza" (trascritta da Whisper), propone:
- una versione grammaticalmente corretta
- alcune alternative con metrica simile, adatte a essere cantate

Usa Ollama se disponibile; altrimenti restituisce un fallback molto semplice.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

REQUESTS_AVAILABLE = False
try:
    import requests  # type: ignore

    REQUESTS_AVAILABLE = True
except Exception:
    logger.warning("⚠️ requests non disponibile: il correttore userà solo fallback locali")


def _call_ollama(prompt: str, max_tokens: int = 256) -> Optional[str]:
    """Chiama Ollama /api/generate con un prompt e restituisce la risposta (stringa)."""
    if not REQUESTS_AVAILABLE:
        return None

    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "max_tokens": max_tokens,
            },
            timeout=60,
        )
        if resp.status_code != 200:
            logger.warning(f"⚠️ Ollama ha restituito status {resp.status_code}")
            return None
        data = resp.json()
        return data.get("response") or data.get("text")
    except Exception as e:
        logger.warning(f"⚠️ Errore chiamata Ollama nel correttore: {e}")
        return None


def _simple_fallback(text: str) -> Dict[str, Any]:
    """Fallback minimale: restituisce la frase originale come 'fixed'."""
    cleaned = text.strip()
    # prima lettera maiuscola, punto finale opzionale
    if cleaned and not cleaned[0].isupper():
        cleaned = cleaned[0].upper() + cleaned[1:]
    if cleaned and cleaned[-1] not in ".!?":
        cleaned = cleaned + "."

    return {
        "text_raw": text,
        "fixed": cleaned,
        "alternatives": [],
        "used_ai": False,
    }


def suggest_corrections(
    text: str,
    target_syllables: Optional[int] = None,
    n_alternatives: int = 4,
) -> Dict[str, Any]:
    """
    Suggerisce correzioni per una singola riga/frase.

    Args:
        text: frase grezza (da Whisper)
        target_syllables: stima sillabe/word count desiderato (opzionale)
        n_alternatives: quante alternative proporre
    """
    text = (text or "").strip()
    if not text:
        return {
            "text_raw": "",
            "fixed": "",
            "alternatives": [],
            "used_ai": False,
        }

    # Stima lunghezza se non fornita
    approx_words = len(text.split())
    if target_syllables is None:
        target_syllables = approx_words

    # Prompt per Ollama: chiediamo un JSON ben strutturato
    prompt = f"""
You are a professional songwriter and English grammar expert.

TASK:
- Take the following raw lyric line (possibly with grammatical errors or odd phrasing).
- Produce:
  1) A grammatically correct version that keeps as much of the meaning as possible.
  2) {n_alternatives} alternative lines that:
     - fit in approximately the same number of syllables/words
     - sound natural in a song
     - keep similar emotional tone and imagery.

IMPORTANT:
- Target approximate length: about {target_syllables} words.
- Do NOT return explanations, only JSON.

Return JSON with this exact structure:
{{
  "fixed": "...",
  "alternatives": ["...", "...", "..."]
}}

RAW LINE:
\"\"\"{text}\"\"\"
""".strip()

    ai_response = _call_ollama(prompt) if REQUESTS_AVAILABLE else None

    if not ai_response:
        logger.info("ℹ️ Corrections: uso fallback semplice (nessuna risposta AI)")
        return _simple_fallback(text)

    # Prova a fare il parsing del JSON dalla risposta
    json_str = ai_response.strip()
    # Se Ollama ha aggiunto testo extra, prova a trovare il blocco JSON
    if "{" in json_str:
        json_str = json_str[json_str.find("{") :]
    if "}" in json_str:
        json_str = json_str[: json_str.rfind("}") + 1]

    try:
        data = json.loads(json_str)
        fixed = (data.get("fixed") or "").strip()
        alts = data.get("alternatives") or []
        if not isinstance(alts, list):
            alts = []
        alts = [str(a).strip() for a in alts if str(a).strip()]

        if not fixed:
            # se qualcosa è andato storto, usa fallback
            return _simple_fallback(text)

        return {
            "text_raw": text,
            "fixed": fixed,
            "alternatives": alts,
            "used_ai": True,
        }
    except Exception as e:
        logger.warning(f"⚠️ Errore parsing JSON da Ollama nel correttore: {e}")
        return _simple_fallback(text)


