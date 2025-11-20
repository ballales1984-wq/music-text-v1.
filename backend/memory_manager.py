"""
Memory Manager - Salva testi generati in video memoria usando memvid
Permette ricerca semantica nei testi generati
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime

logger = logging.getLogger(__name__)

MEMVID_AVAILABLE = False
try:
    from memvid import MemvidEncoder, MemvidRetriever, MemvidChat
    MEMVID_AVAILABLE = True
    logger.info("✅ Memvid disponibile - memoria video abilitata")
except ImportError:
    logger.warning("⚠️ Memvid non disponibile - installa con: pip install memvid")

# Directory per memoria
MEMORY_DIR = Path("memory")
MEMORY_DIR.mkdir(exist_ok=True)

MEMORY_VIDEO = MEMORY_DIR / "lyrics_memory.mp4"
MEMORY_INDEX = MEMORY_DIR / "lyrics_index.json"


class LyricsMemoryManager:
    """Gestisce memoria video dei testi generati."""
    
    def __init__(self):
        self.encoder = None
        self.retriever = None
        self.chat = None
        self._initialize()
    
    def _initialize(self):
        """Inizializza encoder/retriever se memvid disponibile."""
        if not MEMVID_AVAILABLE:
            return
        
        try:
            # Se esiste già memoria, carica retriever
            if MEMORY_VIDEO.exists() and MEMORY_INDEX.exists():
                self.retriever = MemvidRetriever(str(MEMORY_VIDEO), str(MEMORY_INDEX))
                self.chat = MemvidChat(str(MEMORY_VIDEO), str(MEMORY_INDEX))
                logger.info("✅ Memoria video esistente caricata")
        except Exception as e:
            logger.warning(f"⚠️ Errore caricamento memoria: {e}")
    
    def save_lyrics(self, job_id: str, transcription: Dict, final_text: str, metadata: Optional[Dict] = None):
        """
        Salva testo generato nella memoria video.
        
        Args:
            job_id: ID del job
            transcription: Dati trascrizione
            final_text: Testo finale generato
            metadata: Metadati aggiuntivi (nome file, data, etc.)
        """
        if not MEMVID_AVAILABLE:
            logger.warning("⚠️ Memvid non disponibile - testo non salvato in memoria")
            return False
        
        try:
            # Prepara chunks da salvare
            chunks = []
            
            # Chunk 1: Testo finale generato
            if final_text:
                chunk_text = f"Generated lyrics for job {job_id}:\n{final_text}"
                chunks.append(chunk_text)
            
            # Chunk 2: Trascrizione originale
            raw_text = transcription.get("text", "")
            if raw_text:
                chunk_text = f"Original transcription for job {job_id}:\n{raw_text}"
                chunks.append(chunk_text)
            
            if not chunks:
                logger.warning("⚠️ Nessun testo da salvare")
                return False
            
            # Prepara metadata
            save_metadata = {
                "job_id": job_id,
                "timestamp": datetime.now().isoformat(),
                "language": transcription.get("language", "en"),
                "has_clear_words": transcription.get("has_clear_words", False)
            }
            if metadata:
                save_metadata.update(metadata)
            
            # Crea encoder se non esiste
            if not self.encoder:
                self.encoder = MemvidEncoder(chunk_size=512)
            
            # Aggiungi chunks con metadata
            for chunk in chunks:
                self.encoder.add_text(chunk, metadata=save_metadata)
            
            logger.info(f"✅ Testo salvato in memoria per job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore salvataggio in memoria: {e}")
            return False
    
    def build_memory(self):
        """Costruisce/aggiorna il video memoria."""
        if not MEMVID_AVAILABLE or not self.encoder:
            logger.warning("⚠️ Memvid non disponibile o encoder non inizializzato")
            return False
        
        try:
            logger.info("🎬 Costruzione video memoria...")
            self.encoder.build_video(str(MEMORY_VIDEO), str(MEMORY_INDEX))
            logger.info(f"✅ Memoria video costruita: {MEMORY_VIDEO.name}")
            
            # Ricarica retriever dopo build
            self.retriever = MemvidRetriever(str(MEMORY_VIDEO), str(MEMORY_INDEX))
            self.chat = MemvidChat(str(MEMORY_VIDEO), str(MEMORY_INDEX))
            
            return True
        except Exception as e:
            logger.error(f"❌ Errore costruzione memoria: {e}")
            return False
    
    def search_lyrics(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Cerca nei testi generati usando ricerca semantica.
        
        Args:
            query: Query di ricerca
            top_k: Numero di risultati
            
        Returns:
            Lista di risultati con testo e metadata
        """
        if not MEMVID_AVAILABLE or not self.retriever:
            logger.warning("⚠️ Memvid non disponibile o retriever non inizializzato")
            return []
        
        try:
            results = self.retriever.search(query, top_k=top_k)
            logger.info(f"✅ Trovati {len(results)} risultati per query: {query}")
            return results
        except Exception as e:
            logger.error(f"❌ Errore ricerca: {e}")
            return []
    
    def chat_with_memory(self, query: str) -> str:
        """
        Chat con la memoria usando memvid.
        
        Args:
            query: Domanda/query
            
        Returns:
            Risposta basata sulla memoria
        """
        if not MEMVID_AVAILABLE or not self.chat:
            logger.warning("⚠️ Memvid non disponibile o chat non inizializzato")
            return "Memoria non disponibile"
        
        try:
            response = self.chat.chat(query)
            return response
        except Exception as e:
            logger.error(f"❌ Errore chat: {e}")
            return f"Errore: {str(e)}"


# Istanza globale
memory_manager = LyricsMemoryManager()


def save_lyrics_to_memory(job_id: str, transcription: Dict, final_text: str, metadata: Optional[Dict] = None):
    """Helper per salvare testo in memoria."""
    return memory_manager.save_lyrics(job_id, transcription, final_text, metadata)


def build_memory_video():
    """Helper per costruire video memoria."""
    return memory_manager.build_memory()


def search_in_memory(query: str, top_k: int = 5):
    """Helper per cercare nella memoria."""
    return memory_manager.search_lyrics(query, top_k)


def chat_with_memory(query: str):
    """Helper per chat con memoria."""
    return memory_manager.chat_with_memory(query)


# Directory per knowledge base
KNOWLEDGE_VIDEO = MEMORY_DIR / "knowledge_base.mp4"
KNOWLEDGE_INDEX = MEMORY_DIR / "knowledge_index.json"


def save_knowledge_base_to_memory(knowledge_data: Dict) -> bool:
    """
    Salva database conoscenza (pattern, frasi comuni, regole metriche) in memvid.
    
    Args:
        knowledge_data: Dati da get_knowledge_base_for_memvid()
        
    Returns:
        True se salvato con successo
    """
    if not MEMVID_AVAILABLE:
        logger.warning("⚠️ Memvid non disponibile - knowledge base non salvata")
        return False
    
    try:
        chunks = knowledge_data.get("chunks", [])
        if not chunks:
            logger.warning("⚠️ Nessun chunk da salvare")
            return False
        
        logger.info(f"🎬 Costruzione knowledge base: {len(chunks)} chunks...")
        
        # Crea encoder per knowledge base
        encoder = MemvidEncoder(chunk_size=512)
        
        # Aggiungi tutti i chunks
        for chunk in chunks:
            encoder.add_text(chunk, metadata={"type": "knowledge_base", "source": "pattern_analysis"})
        
        # Costruisci video
        encoder.build_video(str(KNOWLEDGE_VIDEO), str(KNOWLEDGE_INDEX))
        
        logger.info(f"✅ Knowledge base salvata: {KNOWLEDGE_VIDEO.name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Errore salvataggio knowledge base: {e}")
        return False


def search_knowledge_base(query: str, top_k: int = 5) -> List[Dict]:
    """
    Cerca nel database conoscenza (pattern, regole metriche).
    
    Args:
        query: Query di ricerca
        top_k: Numero di risultati
        
    Returns:
        Lista di risultati
    """
    if not MEMVID_AVAILABLE:
        return []
    
    try:
        if not KNOWLEDGE_VIDEO.exists() or not KNOWLEDGE_INDEX.exists():
            logger.warning("⚠️ Knowledge base non costruita ancora")
            return []
        
        retriever = MemvidRetriever(str(KNOWLEDGE_VIDEO), str(KNOWLEDGE_INDEX))
        results = retriever.search(query, top_k=top_k)
        return results
    except Exception as e:
        logger.error(f"❌ Errore ricerca knowledge base: {e}")
        return []

