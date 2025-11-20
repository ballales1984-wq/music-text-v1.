"""
Analizzatore di Pattern delle Canzoni
Estrae struttura metrica, frasi comuni, pattern verse/chorus dalle canzoni processate
Per creare database di conoscenza con memvid
"""
import logging
import re
from typing import Dict, List, Tuple
from collections import Counter, defaultdict
import json

logger = logging.getLogger(__name__)

# Pattern comuni nelle canzoni (da analizzare e aggiornare)
COMMON_PHRASES_PATTERNS = [
    # Pattern emotivi
    r"I (love|want|need|feel|know|see|hear|think|believe)",
    r"You (are|were|will|can|should|must|have|know)",
    r"In the (night|day|dark|light|rain|sun|wind|storm)",
    r"Through the (night|day|dark|light|rain|storm|fire|water)",
    r"All (I|you|we|they) (want|need|know|see|feel|have)",
    r"Every (time|day|night|moment|step|beat|word|note)",
    r"Never (stop|give|leave|forget|know|see|feel)",
    r"Always (there|here|with|for|in|on|at)",
    
    # Pattern temporali
    r"It's (time|a time|the time|my time|your time)",
    r"When (I|you|we|they) (come|go|see|feel|know|think)",
    r"Now (I|you|we|they) (know|see|feel|understand|believe)",
    r"Tonight (I|you|we|they) (will|can|must|should)",
    
    # Pattern spaziali
    r"Here (I|you|we|they) (am|are|stand|sit|wait|come)",
    r"There (is|are|was|were|will be)",
    r"Where (I|you|we|they) (go|come|stand|sit|wait)",
    
    # Pattern relazionali
    r"With (you|me|us|them|him|her|love|hope|faith)",
    r"Without (you|me|us|them|love|hope|faith|fear)",
    r"Together (we|they|you and I) (are|will|can|must)",
    
    # Pattern azione
    r"Let (me|us|it|them) (go|be|see|feel|know|try)",
    r"Don't (stop|give|leave|forget|worry|cry)",
    r"Can't (stop|give|leave|forget|see|feel|know)",
    r"Won't (stop|give|leave|forget|see|feel|know)",
    
    # Pattern esistenziali
    r"I'm (here|there|alive|free|lost|found|yours|mine)",
    r"You're (here|there|mine|yours|alive|free|lost|found)",
    r"We're (here|there|alive|free|together|apart)",
    
    # Pattern desiderio
    r"I (wish|hope|dream|pray|want|need) (you|it|that|this)",
    r"If (I|you|we|they) (could|would|should|might)",
    r"Maybe (I|you|we|they) (can|will|should|could)",
]

# Strutture comuni verse/chorus
COMMON_STRUCTURES = [
    "Verse-Chorus-Verse-Chorus-Bridge-Chorus",
    "Verse-Verse-Chorus-Verse-Chorus",
    "Verse-Chorus-Verse-Chorus",
    "Intro-Verse-Chorus-Verse-Chorus-Outro",
    "Verse-PreChorus-Chorus-Verse-PreChorus-Chorus-Bridge-Chorus",
]


class SongPatternsAnalyzer:
    """Analizza pattern e struttura delle canzoni."""
    
    def __init__(self):
        self.all_lyrics = []  # Tutti i testi processati
        self.all_structures = []  # Tutte le strutture analizzate
        self.all_metrics = []  # Tutte le metriche analizzate
        self.common_phrases = Counter()  # Frasi comuni
        self.structure_patterns = Counter()  # Pattern strutturali
        self.metric_patterns = defaultdict(list)  # Pattern metrici
    
    def analyze_song(self, transcription: Dict, final_text: str, structure: Dict = None, metrics: Dict = None):
        """
        Analizza una canzone e estrae pattern.
        
        Args:
            transcription: Dati trascrizione
            final_text: Testo finale generato
            structure: Struttura verse/chorus (opzionale)
            metrics: Metriche sillabe/accenti (opzionale)
        """
        if not final_text:
            return
        
        # Salva testo
        self.all_lyrics.append({
            "text": final_text,
            "raw": transcription.get("text", ""),
            "language": transcription.get("language", "en")
        })
        
        # Analizza frasi comuni
        self._extract_common_phrases(final_text)
        
        # Analizza struttura
        if structure:
            self.all_structures.append(structure)
            self._analyze_structure(structure)
        
        # Analizza metriche
        if metrics:
            self.all_metrics.append(metrics)
            self._analyze_metrics(metrics)
        
        logger.info(f"✅ Canzone analizzata: {len(self.all_lyrics)} totali")
    
    def _extract_common_phrases(self, text: str):
        """Estrae frasi comuni dal testo."""
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            # Cerca pattern comuni
            for pattern in COMMON_PHRASES_PATTERNS:
                matches = re.findall(pattern, line, re.IGNORECASE)
                if matches:
                    # Normalizza la frase
                    phrase = line[:60].strip()  # Prime 60 caratteri
                    self.common_phrases[phrase.lower()] += 1
    
    def _analyze_structure(self, structure: Dict):
        """Analizza struttura verse/chorus."""
        verses = structure.get("verses", [])
        chorus = structure.get("chorus", "")
        total_lines = structure.get("total_lines", 0)
        
        # Identifica pattern strutturale
        if verses and chorus:
            pattern = f"Verse({len(verses)})-Chorus"
        elif verses:
            pattern = f"Verse({len(verses)})"
        else:
            pattern = "Unknown"
        
        self.structure_patterns[pattern] += 1
        
        # Analizza lunghezza versi
        if verses:
            verse_lengths = [len(v) for v in verses if isinstance(v, list)]
            if verse_lengths:
                avg_length = sum(verse_lengths) / len(verse_lengths)
                self.metric_patterns["verse_lengths"].append(avg_length)
    
    def _analyze_metrics(self, metrics: Dict):
        """Analizza pattern metrici."""
        syllable_count = metrics.get("syllable_count", 0)
        lines_syllables = metrics.get("lines_syllables", [])
        accents = metrics.get("accents", [])
        
        if syllable_count > 0:
            self.metric_patterns["syllable_counts"].append(syllable_count)
        
        if lines_syllables:
            self.metric_patterns["lines_syllables"].extend(lines_syllables)
        
        if accents:
            # Analizza pattern accenti
            accent_pattern = "".join([str(a) for a in accents[:20]])  # Prime 20 posizioni
            self.metric_patterns["accent_patterns"].append(accent_pattern)
    
    def get_knowledge_base_data(self) -> Dict:
        """
        Genera dati per database conoscenza con memvid.
        Include:
        - Frasi comuni più frequenti
        - Pattern strutturali
        - Regole metriche
        - Esempi di struttura verse/chorus
        """
        knowledge_chunks = []
        
        # 1. Frasi comuni (top 50)
        knowledge_chunks.append("=== COMMON SONG PHRASES ===")
        top_phrases = self.common_phrases.most_common(50)
        for phrase, count in top_phrases:
            knowledge_chunks.append(f"Phrase: '{phrase}' (appears {count} times)")
        
        # 2. Pattern strutturali
        knowledge_chunks.append("\n=== SONG STRUCTURE PATTERNS ===")
        for pattern, count in self.structure_patterns.most_common(10):
            knowledge_chunks.append(f"Structure: {pattern} (used {count} times)")
        
        # 3. Regole metriche
        knowledge_chunks.append("\n=== METRIC RULES ===")
        
        if self.metric_patterns.get("syllable_counts"):
            avg_syllables = sum(self.metric_patterns["syllable_counts"]) / len(self.metric_patterns["syllable_counts"])
            knowledge_chunks.append(f"Average total syllables per song: {avg_syllables:.1f}")
        
        if self.metric_patterns.get("lines_syllables"):
            all_line_syllables = self.metric_patterns["lines_syllables"]
            if all_line_syllables:
                avg_line_syllables = sum(all_line_syllables) / len(all_line_syllables)
                knowledge_chunks.append(f"Average syllables per line: {avg_line_syllables:.1f}")
                knowledge_chunks.append(f"Common line syllable counts: {Counter(all_line_syllables).most_common(10)}")
        
        if self.metric_patterns.get("accent_patterns"):
            accent_counter = Counter(self.metric_patterns["accent_patterns"])
            top_accents = accent_counter.most_common(5)
            knowledge_chunks.append(f"Common accent patterns: {top_accents}")
        
        # 4. Esempi struttura verse/chorus
        knowledge_chunks.append("\n=== VERSE/CHORUS STRUCTURE EXAMPLES ===")
        for i, structure in enumerate(self.all_structures[:5]):  # Prime 5 strutture
            verses = structure.get("verses", [])
            chorus = structure.get("chorus", "")
            knowledge_chunks.append(f"\nExample {i+1}:")
            knowledge_chunks.append(f"  Verses: {len(verses)}")
            if verses:
                knowledge_chunks.append(f"  Verse length: {len(verses[0]) if verses[0] else 0} lines")
            if chorus:
                knowledge_chunks.append(f"  Chorus: {len(chorus) if isinstance(chorus, list) else 1} lines")
        
        # 5. Regole generali
        knowledge_chunks.append("\n=== SONGWRITING RULES ===")
        knowledge_chunks.append("1. Verses typically have 4-8 lines")
        knowledge_chunks.append("2. Chorus is usually 2-4 lines, repeated")
        knowledge_chunks.append("3. Each line typically has 8-12 syllables")
        knowledge_chunks.append("4. Strong accents usually on beats 1 and 3 in 4/4 time")
        knowledge_chunks.append("5. Verse tells story, Chorus repeats main message")
        
        if self.all_lyrics:
            # Statistiche reali
            total_songs = len(self.all_lyrics)
            knowledge_chunks.append(f"\nBased on {total_songs} analyzed songs:")
            
            if self.metric_patterns.get("verse_lengths"):
                avg_verse = sum(self.metric_patterns["verse_lengths"]) / len(self.metric_patterns["verse_lengths"])
                knowledge_chunks.append(f"- Average verse length: {avg_verse:.1f} lines")
        
        return {
            "chunks": knowledge_chunks,
            "stats": {
                "total_songs": len(self.all_lyrics),
                "total_phrases": len(self.common_phrases),
                "total_structures": len(self.all_structures),
                "total_metrics": len(self.all_metrics)
            }
        }


# Istanza globale
patterns_analyzer = SongPatternsAnalyzer()


def analyze_song_patterns(transcription: Dict, final_text: str, structure: Dict = None, metrics: Dict = None):
    """Helper per analizzare pattern canzone."""
    return patterns_analyzer.analyze_song(transcription, final_text, structure, metrics)


def get_knowledge_base_for_memvid() -> Dict:
    """Helper per ottenere dati per memvid."""
    return patterns_analyzer.get_knowledge_base_data()

