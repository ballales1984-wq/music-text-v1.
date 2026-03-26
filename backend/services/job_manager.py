"""
Job Manager con persistenza Redis
Gestisce lo stato dei job in modo persistente
"""
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

# Configurazione Redis
REDIS_AVAILABLE = False
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
JOB_EXPIRY_HOURS = int(os.getenv("JOB_EXPIRY_HOURS", "24"))

try:
    import redis
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=2
    )
    # Test connessione
    redis_client.ping()
    REDIS_AVAILABLE = True
    logger.info(f"✅ Redis connesso: {REDIS_HOST}:{REDIS_PORT}")
except Exception as e:
    logger.warning(f"⚠️  Redis non disponibile: {e}. Uso storage in-memory (non persistente)")
    redis_client = None


class JobManager:
    """
    Gestisce lo stato dei job con persistenza Redis.
    Fallback automatico a storage in-memory se Redis non disponibile.
    """
    
    def __init__(self):
        self.redis_available = REDIS_AVAILABLE
        self.redis = redis_client
        # Fallback in-memory
        self._memory_storage: Dict[str, Dict] = {}
        
        if self.redis_available:
            logger.info("JobManager: usando Redis per persistenza")
        else:
            logger.warning("JobManager: usando storage in-memory (non persistente)")
    
    def _get_key(self, job_id: str) -> str:
        """Genera chiave Redis per job"""
        return f"job:{job_id}"
    
    def create_job(self, job_id: str, initial_data: Optional[Dict] = None) -> Dict:
        """
        Crea nuovo job con stato iniziale.
        """
        job_data = {
            "job_id": job_id,
            "status": "processing",
            "progress": 0,
            "step": "Inizializzazione...",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            **(initial_data or {})
        }
        
        self.update_job(job_id, job_data)
        logger.info(f"Job creato: {job_id}")
        return job_data
    
    def get_job(self, job_id: str) -> Optional[Dict]:
        """
        Recupera stato job.
        Returns None se job non trovato.
        """
        if self.redis_available:
            try:
                data = self.redis.get(self._get_key(job_id))
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Errore lettura Redis per {job_id}: {e}")
                # Fallback a memory
                return self._memory_storage.get(job_id)
        
        return self._memory_storage.get(job_id)
    
    def update_job(self, job_id: str, data: Dict) -> bool:
        """
        Aggiorna stato job.
        Returns True se successo.
        """
        # Aggiungi timestamp update
        data["updated_at"] = datetime.utcnow().isoformat()
        
        if self.redis_available:
            try:
                key = self._get_key(job_id)
                # Salva con expiry
                expiry_seconds = JOB_EXPIRY_HOURS * 3600
                self.redis.setex(
                    key,
                    expiry_seconds,
                    json.dumps(data)
                )
                # Salva anche in memory per fallback
                self._memory_storage[job_id] = data
                return True
            except Exception as e:
                logger.error(f"Errore scrittura Redis per {job_id}: {e}")
                # Fallback a memory
                self._memory_storage[job_id] = data
                return True
        
        # Storage in-memory
        self._memory_storage[job_id] = data
        return True
    
    def delete_job(self, job_id: str) -> bool:
        """
        Elimina job.
        Returns True se successo.
        """
        if self.redis_available:
            try:
                self.redis.delete(self._get_key(job_id))
            except Exception as e:
                logger.error(f"Errore eliminazione Redis per {job_id}: {e}")
        
        if job_id in self._memory_storage:
            del self._memory_storage[job_id]
        
        logger.info(f"Job eliminato: {job_id}")
        return True
    
    def list_jobs(self, status: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """
        Lista job (opzionalmente filtrati per status).
        """
        jobs = []
        
        if self.redis_available:
            try:
                # Scan tutte le chiavi job:*
                cursor = 0
                while True:
                    cursor, keys = self.redis.scan(cursor, match="job:*", count=100)
                    for key in keys:
                        data = self.redis.get(key)
                        if data:
                            job = json.loads(data)
                            if status is None or job.get("status") == status:
                                jobs.append(job)
                    
                    if cursor == 0:
                        break
                    
                    if len(jobs) >= limit:
                        break
            except Exception as e:
                logger.error(f"Errore listing Redis: {e}")
                # Fallback a memory
                jobs = [
                    job for job in self._memory_storage.values()
                    if status is None or job.get("status") == status
                ]
        else:
            # Memory storage
            jobs = [
                job for job in self._memory_storage.values()
                if status is None or job.get("status") == status
            ]
        
        # Ordina per data creazione (più recenti prima)
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return jobs[:limit]
    
    def cleanup_old_jobs(self, hours: int = JOB_EXPIRY_HOURS) -> int:
        """
        Pulisce job più vecchi di N ore.
        Returns numero job eliminati.
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        deleted = 0
        
        jobs = self.list_jobs(limit=1000)
        for job in jobs:
            created_at = job.get("created_at")
            if created_at:
                try:
                    job_date = datetime.fromisoformat(created_at)
                    if job_date < cutoff:
                        self.delete_job(job["job_id"])
                        deleted += 1
                except Exception as e:
                    logger.error(f"Errore parsing data per {job['job_id']}: {e}")
        
        if deleted > 0:
            logger.info(f"Cleanup: eliminati {deleted} job vecchi (>{hours}h)")
        
        return deleted
    
    def get_stats(self) -> Dict:
        """
        Statistiche job.
        """
        jobs = self.list_jobs(limit=10000)
        
        stats = {
            "total": len(jobs),
            "by_status": {},
            "redis_available": self.redis_available
        }
        
        for job in jobs:
            status = job.get("status", "unknown")
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1
        
        return stats


# Istanza globale singleton
_job_manager: Optional[JobManager] = None


def get_job_manager() -> JobManager:
    """
    Dependency injection per JobManager.
    Crea istanza singleton.
    """
    global _job_manager
    if _job_manager is None:
        _job_manager = JobManager()
    return _job_manager

# Made with Bob
