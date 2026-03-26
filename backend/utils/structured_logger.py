"""
Structured logging con supporto JSON
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict, Optional
import traceback
import os


class StructuredLogger:
    """
    Logger strutturato che emette log in formato JSON.
    Utile per aggregazione log (ELK, Splunk, CloudWatch, etc.)
    """
    
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))
        
        # Rimuovi handler esistenti
        self.logger.handlers.clear()
        
        # Formato JSON o text based su env
        use_json = os.getenv("LOG_FORMAT", "json").lower() == "json"
        
        if use_json:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JSONFormatter())
        else:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.propagate = False
    
    def _log(self, level: str, message: str, **kwargs):
        """Log interno con context"""
        extra = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            **kwargs
        }
        
        log_method = getattr(self.logger, level.lower())
        log_method(message, extra={"structured": extra})
    
    def debug(self, message: str, **kwargs):
        """Log debug"""
        self._log("DEBUG", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info"""
        self._log("INFO", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning"""
        self._log("WARNING", message, **kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error con traceback opzionale"""
        if error:
            kwargs["error_type"] = type(error).__name__
            kwargs["error_message"] = str(error)
            kwargs["traceback"] = traceback.format_exc()
        
        self._log("ERROR", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical"""
        self._log("CRITICAL", message, **kwargs)


class JSONFormatter(logging.Formatter):
    """
    Formatter che converte log in JSON.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """Formatta record come JSON"""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Aggiungi context strutturato se presente
        if hasattr(record, "structured"):
            log_data.update(record.structured)
        
        # Aggiungi exception info se presente
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        return json.dumps(log_data, default=str)


# Factory function
def get_logger(name: str, level: Optional[str] = None) -> StructuredLogger:
    """
    Ottieni logger strutturato.
    
    Args:
        name: Nome logger (solitamente __name__)
        level: Livello log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        StructuredLogger instance
    """
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")
    
    return StructuredLogger(name, level)


# Esempio utilizzo
if __name__ == "__main__":
    logger = get_logger(__name__)
    
    # Log semplici
    logger.info("Application started")
    logger.debug("Debug message", user_id=123, action="login")
    
    # Log con context
    logger.info(
        "User action",
        user_id=456,
        action="upload_file",
        file_size=1024000,
        duration_ms=1500
    )
    
    # Log errore
    try:
        1 / 0
    except Exception as e:
        logger.error("Division error", error=e, user_id=789)
    
    # Output JSON:
    # {"timestamp": "2026-03-26T16:45:00Z", "level": "INFO", "message": "Application started", ...}

# Made with Bob
