"""
Security middleware per rate limiting e autenticazione
"""
import time
import hashlib
from typing import Dict, Optional
from fastapi import Request, HTTPException, Header
from fastapi.security import APIKeyHeader
import logging
import os

logger = logging.getLogger(__name__)

# Configurazione
API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))  # Richieste per finestra
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))  # Secondi
ENABLE_AUTH = os.getenv("ENABLE_AUTH", "false").lower() == "true"
VALID_API_KEYS = set(os.getenv("API_KEYS", "").split(",")) if os.getenv("API_KEYS") else set()

# Storage in-memory per rate limiting (in produzione usare Redis)
rate_limit_storage: Dict[str, list] = {}


class RateLimiter:
    """Rate limiter semplice basato su IP"""
    
    def __init__(self, requests: int = RATE_LIMIT_REQUESTS, window: int = RATE_LIMIT_WINDOW):
        self.requests = requests
        self.window = window
    
    def _get_client_id(self, request: Request) -> str:
        """Ottiene identificatore client (IP o API key)"""
        # Prova a ottenere IP reale (dietro proxy)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def check_rate_limit(self, request: Request) -> bool:
        """
        Verifica se il client ha superato il rate limit.
        Returns True se OK, False se limite superato.
        """
        client_id = self._get_client_id(request)
        current_time = time.time()
        
        # Inizializza storage per client
        if client_id not in rate_limit_storage:
            rate_limit_storage[client_id] = []
        
        # Rimuovi richieste vecchie (fuori dalla finestra)
        rate_limit_storage[client_id] = [
            req_time for req_time in rate_limit_storage[client_id]
            if current_time - req_time < self.window
        ]
        
        # Verifica limite
        if len(rate_limit_storage[client_id]) >= self.requests:
            logger.warning(f"Rate limit exceeded for {client_id}")
            return False
        
        # Aggiungi richiesta corrente
        rate_limit_storage[client_id].append(current_time)
        return True
    
    async def __call__(self, request: Request):
        """Middleware callable"""
        if not self.check_rate_limit(request):
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {self.requests} requests per {self.window} seconds."
            )


class APIKeyAuth:
    """Autenticazione tramite API key"""
    
    def __init__(self, enabled: bool = ENABLE_AUTH):
        self.enabled = enabled
        if enabled and not VALID_API_KEYS:
            logger.warning("⚠️  Autenticazione abilitata ma nessuna API key configurata!")
    
    def verify_api_key(self, api_key: Optional[str]) -> bool:
        """Verifica validità API key"""
        if not self.enabled:
            return True  # Auth disabilitata
        
        if not api_key:
            return False
        
        # Hash API key per sicurezza (confronto hash invece di plaintext)
        api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # In produzione, confrontare con hash salvati in DB
        # Per ora confronto diretto
        return api_key in VALID_API_KEYS
    
    async def __call__(self, api_key: Optional[str] = Header(None, alias="X-API-Key")):
        """Middleware callable"""
        if not self.enabled:
            return  # Auth disabilitata
        
        if not self.verify_api_key(api_key):
            logger.warning(f"Invalid API key attempt: {api_key[:10] if api_key else 'None'}...")
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key. Include X-API-Key header."
            )


# Istanze globali
rate_limiter = RateLimiter()
api_key_auth = APIKeyAuth()


def get_rate_limiter() -> RateLimiter:
    """Dependency injection per rate limiter"""
    return rate_limiter


def get_api_key_auth() -> APIKeyAuth:
    """Dependency injection per auth"""
    return api_key_auth

# Made with Bob
