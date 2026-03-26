"""
Validazione file upload con MIME type detection
"""
import logging
from pathlib import Path
from typing import Optional, Set
import os

logger = logging.getLogger(__name__)

# Import opzionale python-magic
try:
    import magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False
    logger.warning("⚠️  python-magic non disponibile. Installa con: pip install python-magic-bin")

# Configurazione
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg"}
ALLOWED_MIME_TYPES = {
    "audio/mpeg",       # MP3
    "audio/wav",        # WAV
    "audio/x-wav",      # WAV alternativo
    "audio/wave",       # WAV alternativo
    "audio/mp4",        # M4A
    "audio/x-m4a",      # M4A alternativo
    "audio/flac",       # FLAC
    "audio/x-flac",     # FLAC alternativo
    "audio/ogg",        # OGG
    "audio/vorbis",     # OGG Vorbis
}
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE_MB", "100")) * 1024 * 1024  # Default 100MB
MIN_FILE_SIZE = 1024  # 1KB minimo

# MAGIC_AVAILABLE già definito sopra
if MAGIC_AVAILABLE:
    logger.info("✅ python-magic disponibile per MIME detection")


class FileValidator:
    """
    Validatore file con controlli di sicurezza.
    """
    
    def __init__(self):
        self.allowed_extensions = ALLOWED_EXTENSIONS
        self.allowed_mime_types = ALLOWED_MIME_TYPES
        self.max_size = MAX_FILE_SIZE
        self.min_size = MIN_FILE_SIZE
        self.magic_available = MAGIC_AVAILABLE
        
        if self.magic_available:
            try:
                # Inizializza magic
                self.magic = magic.Magic(mime=True)
                logger.info("MIME detector inizializzato")
            except Exception as e:
                logger.warning(f"Errore init magic: {e}")
                self.magic_available = False
    
    def validate_extension(self, filename: str) -> bool:
        """
        Valida estensione file.
        """
        ext = Path(filename).suffix.lower()
        return ext in self.allowed_extensions
    
    def validate_size(self, file_size: int) -> tuple[bool, Optional[str]]:
        """
        Valida dimensione file.
        Returns (is_valid, error_message)
        """
        if file_size < self.min_size:
            return False, f"File troppo piccolo ({file_size} bytes). Minimo: {self.min_size} bytes"
        
        if file_size > self.max_size:
            size_mb = file_size / (1024 * 1024)
            max_mb = self.max_size / (1024 * 1024)
            return False, f"File troppo grande ({size_mb:.1f}MB). Massimo: {max_mb:.0f}MB"
        
        return True, None
    
    def detect_mime_type(self, file_path: Path) -> Optional[str]:
        """
        Rileva MIME type reale del file.
        Returns None se non disponibile.
        """
        if not self.magic_available:
            return None
        
        try:
            mime_type = self.magic.from_file(str(file_path))
            logger.debug(f"MIME type rilevato: {mime_type} per {file_path.name}")
            return mime_type
        except Exception as e:
            logger.warning(f"Errore rilevamento MIME per {file_path.name}: {e}")
            return None
    
    def validate_mime_type(self, file_path: Path) -> tuple[bool, Optional[str]]:
        """
        Valida MIME type reale del file.
        Returns (is_valid, error_message)
        """
        if not self.magic_available:
            # Se magic non disponibile, salta validazione MIME
            logger.debug("MIME validation skipped (magic non disponibile)")
            return True, None
        
        mime_type = self.detect_mime_type(file_path)
        
        if mime_type is None:
            # Errore rilevamento, permetti comunque (fallback)
            logger.warning(f"MIME detection fallita per {file_path.name}, permetto comunque")
            return True, None
        
        if mime_type not in self.allowed_mime_types:
            return False, f"Tipo file non supportato: {mime_type}. File potrebbe essere corrotto o non audio."
        
        return True, None
    
    def validate_file(self, filename: str, file_size: int, file_path: Optional[Path] = None) -> tuple[bool, Optional[str]]:
        """
        Validazione completa file.
        Returns (is_valid, error_message)
        """
        # 1. Valida estensione
        if not self.validate_extension(filename):
            ext = Path(filename).suffix.lower()
            allowed = ", ".join(sorted(self.allowed_extensions))
            return False, f"Estensione '{ext}' non supportata. Formati supportati: {allowed}"
        
        # 2. Valida dimensione
        is_valid, error = self.validate_size(file_size)
        if not is_valid:
            return False, error
        
        # 3. Valida MIME type (se file_path fornito e magic disponibile)
        if file_path and file_path.exists():
            is_valid, error = self.validate_mime_type(file_path)
            if not is_valid:
                return False, error
        
        return True, None
    
    def is_safe_filename(self, filename: str) -> bool:
        """
        Verifica che il filename sia sicuro (no path traversal).
        """
        # Rimuovi path, mantieni solo nome file
        safe_name = Path(filename).name
        
        # Check caratteri pericolosi
        dangerous_chars = ["../", "..\\", "/", "\\", "\0"]
        for char in dangerous_chars:
            if char in filename:
                logger.warning(f"Filename pericoloso rilevato: {filename}")
                return False
        
        return True
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitizza filename rimuovendo caratteri pericolosi.
        """
        # Mantieni solo nome file (no path)
        safe_name = Path(filename).name
        
        # Rimuovi caratteri speciali pericolosi
        dangerous_chars = ["/", "\\", "\0", ":", "*", "?", '"', "<", ">", "|"]
        for char in dangerous_chars:
            safe_name = safe_name.replace(char, "_")
        
        return safe_name


# Istanza globale
_file_validator: Optional[FileValidator] = None


def get_file_validator() -> FileValidator:
    """
    Dependency injection per FileValidator.
    """
    global _file_validator
    if _file_validator is None:
        _file_validator = FileValidator()
    return _file_validator

# Made with Bob
