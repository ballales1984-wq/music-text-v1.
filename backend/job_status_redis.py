"""
Job status manager usando Redis per persistenza.
Sopravvive ai riavvii del server.
"""
import json
import logging
import os
from typing import Dict, Optional

import redis

logger = logging.getLogger(__name__)

# Configurazione Redis
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_KEY_PREFIX = os.getenv("REDIS_KEY_PREFIX", "musictext:job:")

# TTL per i job (7 giorni)
JOB_TTL_SECONDS = 7 * 24 * 60 * 60


class JobStatusRedis:
    """Manager per job status con Redis."""
    
    def __init__(self):
        self._redis: Optional[redis.Redis] = None
        self._fallback: Dict[str, Dict] = {}
        self._use_redis = False
    
    def _get_redis(self) -> redis.Redis:
        """Ottiene connessione Redis (lazy initialization)."""
        if self._redis is None:
            try:
                self._redis = redis.Redis(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    db=REDIS_DB,
                    password=REDIS_PASSWORD,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                # Testa connessione
                self._redis.ping()
                self._use_redis = True
                logger.info(f"✅ Redis connesso: {REDIS_HOST}:{REDIS_PORT}")
            except redis.ConnectionError as e:
                logger.warning(f"⚠️ Redis non disponibile: {e}")
                logger.warning("   Uso fallback in memoria (i job NON sopravviveranno ai riavvii)")
                self._use_redis = False
            except Exception as e:
                logger.error(f"❌ Errore connessione Redis: {e}")
                self._use_redis = False
    
    def _key(self, job_id: str) -> str:
        """Genera chiave Redis per job."""
        return f"{REDIS_KEY_PREFIX}{job_id}"
    
    def set(self, job_id: str, status: Dict) -> None:
        """Salva stato job."""
        self._get_redis()
        
        if self._use_redis:
            try:
                self._redis.setex(
                    self._key(job_id),
                    JOB_TTL_SECONDS,
                    json.dumps(status)
                )
            except Exception as e:
                logger.error(f"Errore salvataggio Redis: {e}")
                # Fallback a memoria
                self._fallback[job_id] = status
        else:
            self._fallback[job_id] = status
    
    def get(self, job_id: str) -> Optional[Dict]:
        """Ottiene stato job."""
        self._get_redis()
        
        if self._use_redis:
            try:
                data = self._redis.get(self._key(job_id))
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Errore lettura Redis: {e}")
        
        # Fallback a memoria
        return self._fallback.get(job_id)
    
    def update(self, job_id: str, updates: Dict) -> None:
        """Aggiorna parte dello stato job."""
        current = self.get(job_id)
        if current:
            current.update(updates)
            self.set(job_id, current)
        else:
            self.set(job_id, updates)
    
    def delete(self, job_id: str) -> None:
        """Elimina stato job."""
        self._get_redis()
        
        if self._use_redis:
            try:
                self._redis.delete(self._key(job_id))
            except Exception as e:
                logger.error(f"Errore eliminazione Redis: {e}")
        
        self._fallback.pop(job_id, None)
    
    def list_jobs(self) -> Dict[str, Dict]:
        """Lista tutti i job (solo dalla memoria, Redis richiede SCAN)."""
        # Per semplicità, restituisce solo fallback
        # In produzione, usare SCAN o chiave set separata
        return self._fallback.copy()
    
    def exists(self, job_id: str) -> bool:
        """Verifica se job esiste."""
        return self.get(job_id) is not None


# Istanza globale
job_status = JobStatusRedis()
