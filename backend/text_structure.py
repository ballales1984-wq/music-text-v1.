"""
Estrae struttura (strofe/ritornello) dal testo trascritto
Semplice analisi del testo per identificare pattern ripetitivi
"""
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def extract_structure(text: str) -> Dict:
    """
    Estrae struttura base dal testo trascritto:
    - Divide in righe/frasi
    - Identifica pattern ripetitivi (ritornello)
    - Conta righe per strofa
    
    Restituisce struttura semplice con:
    - lines: lista di righe
    - verses: lista di strofe (ogni strofa è lista di righe)
    - chorus: ritornello (se identificato)
    """
    if not text or len(text.strip()) < 5:
        return {
            "lines": [],
            "verses": [],
            "chorus": None,
            "total_lines": 0
        }
    
    # Dividi in righe (usa \n o punti come separatori)
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if line:
            lines.append(line)
    
    # Se non ci sono \n, prova a dividere per punti o virgole
    if len(lines) == 1:
        # Dividi per punti, virgole, o punti esclamativi/interrogativi
        import re
        sentences = re.split(r'[.!?]\s+', lines[0])
        lines = [s.strip() for s in sentences if s.strip()]
    
    # Se ancora una sola riga, dividi per virgole
    if len(lines) == 1:
        parts = lines[0].split(',')
        lines = [p.strip() for p in parts if p.strip()]
    
    # Identifica ritornello: cerca righe ripetute
    chorus = None
    verses = []
    
    # Conta occorrenze di ogni riga
    line_counts = {}
    for line in lines:
        line_lower = line.lower()
        line_counts[line_lower] = line_counts.get(line_lower, 0) + 1
    
    # Righe che appaiono 2+ volte sono probabili ritornelli
    repeated_lines = [line for line, count in line_counts.items() if count >= 2]
    
    if repeated_lines:
        # Prendi la riga più ripetuta come ritornello
        most_repeated = max(repeated_lines, key=lambda l: line_counts[l])
        # Trova la versione originale (con maiuscole/minuscole)
        for orig_line in lines:
            if orig_line.lower() == most_repeated:
                chorus = orig_line
                break
    
    # Dividi in strofe: ogni 4-6 righe = una strofa
    current_verse = []
    for line in lines:
        # Salta il ritornello se già identificato
        if chorus and line.lower() == chorus.lower():
            if current_verse:
                verses.append(current_verse)
                current_verse = []
            continue
        
        current_verse.append(line)
        # Ogni 4-6 righe, inizia nuova strofa
        if len(current_verse) >= 4:
            verses.append(current_verse)
            current_verse = []
    
    if current_verse:
        verses.append(current_verse)
    
    # Se non abbiamo trovato strofe, crea una singola strofa
    if not verses and lines:
        verses = [lines]
    
    logger.info(f"✅ Struttura estratta: {len(lines)} righe, {len(verses)} strofe, chorus={'sì' if chorus else 'no'}")
    
    return {
        "lines": lines,
        "verses": verses,
        "chorus": chorus,
        "total_lines": len(lines)
    }

