"""
File Manager per gestione e cleanup file temporanei
"""
import logging
import os
import shutil
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
import tempfile
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Configurazione
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploads"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "outputs"))
TEMP_DIR = Path(os.getenv("TEMP_DIR", tempfile.gettempdir())) / "music_text_temp"
FILE_MAX_AGE_HOURS = int(os.getenv("FILE_MAX_AGE_HOURS", "24"))
CLEANUP_ENABLED = os.getenv("CLEANUP_ENABLED", "true").lower() == "true"

# Crea directory se non esistono
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)


class FileManager:
    """
    Gestisce file temporanei e permanenti con cleanup automatico.
    """
    
    def __init__(self):
        self.upload_dir = UPLOAD_DIR
        self.output_dir = OUTPUT_DIR
        self.temp_dir = TEMP_DIR
        self.max_age_hours = FILE_MAX_AGE_HOURS
        self.cleanup_enabled = CLEANUP_ENABLED
        
        logger.info(f"FileManager inizializzato:")
        logger.info(f"  - Upload: {self.upload_dir}")
        logger.info(f"  - Output: {self.output_dir}")
        logger.info(f"  - Temp: {self.temp_dir}")
        logger.info(f"  - Max age: {self.max_age_hours}h")
        logger.info(f"  - Cleanup: {'enabled' if self.cleanup_enabled else 'disabled'}")
    
    @contextmanager
    def temp_file(self, suffix: str = "", prefix: str = "tmp_"):
        """
        Context manager per file temporaneo con cleanup automatico.
        
        Usage:
            with file_manager.temp_file(suffix=".wav") as temp_path:
                # Usa temp_path
                pass
            # File automaticamente eliminato
        """
        temp_path = None
        try:
            # Crea file temporaneo
            fd, temp_path = tempfile.mkstemp(
                suffix=suffix,
                prefix=prefix,
                dir=str(self.temp_dir)
            )
            os.close(fd)  # Chiudi file descriptor
            
            temp_path = Path(temp_path)
            logger.debug(f"Temp file creato: {temp_path.name}")
            
            yield temp_path
            
        finally:
            # Cleanup automatico
            if temp_path and temp_path.exists():
                try:
                    temp_path.unlink()
                    logger.debug(f"Temp file eliminato: {temp_path.name}")
                except Exception as e:
                    logger.warning(f"Errore eliminazione temp file {temp_path.name}: {e}")
    
    @contextmanager
    def temp_directory(self, prefix: str = "tmpdir_"):
        """
        Context manager per directory temporanea con cleanup automatico.
        
        Usage:
            with file_manager.temp_directory() as temp_dir:
                # Usa temp_dir
                pass
            # Directory automaticamente eliminata
        """
        temp_dir = None
        try:
            # Crea directory temporanea
            temp_dir = Path(tempfile.mkdtemp(
                prefix=prefix,
                dir=str(self.temp_dir)
            ))
            logger.debug(f"Temp directory creata: {temp_dir.name}")
            
            yield temp_dir
            
        finally:
            # Cleanup automatico
            if temp_dir and temp_dir.exists():
                try:
                    shutil.rmtree(temp_dir)
                    logger.debug(f"Temp directory eliminata: {temp_dir.name}")
                except Exception as e:
                    logger.warning(f"Errore eliminazione temp directory {temp_dir.name}: {e}")
    
    def get_file_age_hours(self, file_path: Path) -> float:
        """
        Calcola età file in ore.
        """
        if not file_path.exists():
            return 0.0
        
        mtime = file_path.stat().st_mtime
        age_seconds = datetime.now().timestamp() - mtime
        return age_seconds / 3600
    
    def cleanup_old_files(self, directory: Path, max_age_hours: Optional[int] = None) -> int:
        """
        Elimina file più vecchi di max_age_hours.
        Returns numero file eliminati.
        """
        if not self.cleanup_enabled:
            logger.debug("Cleanup disabilitato")
            return 0
        
        if not directory.exists():
            return 0
        
        max_age = max_age_hours or self.max_age_hours
        deleted = 0
        
        try:
            for file_path in directory.iterdir():
                if file_path.is_file():
                    age = self.get_file_age_hours(file_path)
                    if age > max_age:
                        try:
                            file_path.unlink()
                            deleted += 1
                            logger.debug(f"File vecchio eliminato: {file_path.name} (età: {age:.1f}h)")
                        except Exception as e:
                            logger.warning(f"Errore eliminazione {file_path.name}: {e}")
        except Exception as e:
            logger.error(f"Errore cleanup directory {directory}: {e}")
        
        if deleted > 0:
            logger.info(f"Cleanup {directory.name}: eliminati {deleted} file (>{max_age}h)")
        
        return deleted
    
    def cleanup_all(self) -> dict:
        """
        Cleanup completo di tutte le directory.
        Returns statistiche.
        """
        stats = {
            "uploads": self.cleanup_old_files(self.upload_dir),
            "outputs": self.cleanup_old_files(self.output_dir),
            "temp": self.cleanup_old_files(self.temp_dir, max_age_hours=1),  # Temp: 1h
        }
        
        total = sum(stats.values())
        if total > 0:
            logger.info(f"Cleanup totale: {total} file eliminati")
        
        return stats
    
    def get_directory_stats(self, directory: Path) -> dict:
        """
        Statistiche directory (numero file, dimensione totale).
        """
        if not directory.exists():
            return {"files": 0, "size_mb": 0.0}
        
        files = 0
        total_size = 0
        
        try:
            for file_path in directory.iterdir():
                if file_path.is_file():
                    files += 1
                    total_size += file_path.stat().st_size
        except Exception as e:
            logger.error(f"Errore stats directory {directory}: {e}")
        
        return {
            "files": files,
            "size_mb": round(total_size / (1024 * 1024), 2)
        }
    
    def get_all_stats(self) -> dict:
        """
        Statistiche complete di tutte le directory.
        """
        return {
            "uploads": self.get_directory_stats(self.upload_dir),
            "outputs": self.get_directory_stats(self.output_dir),
            "temp": self.get_directory_stats(self.temp_dir),
        }
    
    def cleanup_job_files(self, job_id: str) -> int:
        """
        Elimina tutti i file associati a un job specifico.
        Returns numero file eliminati.
        """
        deleted = 0
        
        # Pattern file da cercare
        patterns = [
            f"{job_id}*",  # File con job_id come prefisso
            f"*{job_id}*",  # File con job_id nel nome
        ]
        
        for directory in [self.upload_dir, self.output_dir, self.temp_dir]:
            if not directory.exists():
                continue
            
            try:
                for file_path in directory.iterdir():
                    if file_path.is_file() and job_id in file_path.name:
                        try:
                            file_path.unlink()
                            deleted += 1
                            logger.debug(f"File job eliminato: {file_path.name}")
                        except Exception as e:
                            logger.warning(f"Errore eliminazione {file_path.name}: {e}")
            except Exception as e:
                logger.error(f"Errore cleanup job {job_id} in {directory}: {e}")
        
        if deleted > 0:
            logger.info(f"Cleanup job {job_id}: eliminati {deleted} file")
        
        return deleted
    
    def validate_file_path(self, file_path: Path, allowed_dir: Path) -> bool:
        """
        Valida che il file path sia all'interno della directory consentita.
        Previene path traversal attacks.
        """
        try:
            # Risolvi path assoluti
            file_abs = file_path.resolve()
            dir_abs = allowed_dir.resolve()
            
            # Verifica che file sia dentro directory
            return str(file_abs).startswith(str(dir_abs))
        except Exception as e:
            logger.error(f"Errore validazione path: {e}")
            return False


# Istanza globale singleton
_file_manager: Optional[FileManager] = None


def get_file_manager() -> FileManager:
    """
    Dependency injection per FileManager.
    Crea istanza singleton.
    """
    global _file_manager
    if _file_manager is None:
        _file_manager = FileManager()
    return _file_manager

# Made with Bob
