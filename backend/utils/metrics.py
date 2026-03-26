"""
Prometheus metrics per monitoring
"""
import time
from typing import Optional, Callable
from functools import wraps
import os

# Check disponibilità prometheus_client
PROMETHEUS_AVAILABLE = False
try:
    from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, REGISTRY
    PROMETHEUS_AVAILABLE = True
except ImportError:
    # Fallback: mock classes
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def time(self): return self
        def labels(self, *args, **kwargs): return self
        def __enter__(self): return self
        def __exit__(self, *args): pass
    
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Info:
        def __init__(self, *args, **kwargs): pass
        def info(self, *args, **kwargs): pass
    
    def generate_latest():
        return b"# Prometheus not available"
    
    REGISTRY = None


# ============================================
# METRICS DEFINITIONS
# ============================================

# Request metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

# Job metrics
jobs_total = Counter(
    'jobs_total',
    'Total jobs processed',
    ['status']  # completed, error, processing
)

jobs_duration_seconds = Histogram(
    'jobs_duration_seconds',
    'Job processing duration in seconds',
    ['status']
)

jobs_active = Gauge(
    'jobs_active',
    'Number of active jobs'
)

# File metrics
files_uploaded_total = Counter(
    'files_uploaded_total',
    'Total files uploaded',
    ['format']  # mp3, wav, etc.
)

files_uploaded_bytes = Counter(
    'files_uploaded_bytes_total',
    'Total bytes uploaded'
)

files_storage_bytes = Gauge(
    'files_storage_bytes',
    'Current storage usage in bytes',
    ['directory']  # uploads, outputs, temp
)

# AI metrics
ai_requests_total = Counter(
    'ai_requests_total',
    'Total AI requests',
    ['provider', 'status']  # ollama/openai/etc, success/error
)

ai_request_duration_seconds = Histogram(
    'ai_request_duration_seconds',
    'AI request duration in seconds',
    ['provider']
)

# System metrics
system_info = Info(
    'system_info',
    'System information'
)


# ============================================
# HELPER FUNCTIONS
# ============================================

def track_request(method: str, endpoint: str, status: int, duration: float):
    """Track HTTP request metrics"""
    if not PROMETHEUS_AVAILABLE:
        return
    
    http_requests_total.labels(
        method=method,
        endpoint=endpoint,
        status=str(status)
    ).inc()
    
    http_request_duration_seconds.labels(
        method=method,
        endpoint=endpoint
    ).observe(duration)


def track_job(status: str, duration: Optional[float] = None):
    """Track job metrics"""
    if not PROMETHEUS_AVAILABLE:
        return
    
    jobs_total.labels(status=status).inc()
    
    if duration is not None:
        jobs_duration_seconds.labels(status=status).observe(duration)


def track_file_upload(file_format: str, file_size: int):
    """Track file upload metrics"""
    if not PROMETHEUS_AVAILABLE:
        return
    
    files_uploaded_total.labels(format=file_format).inc()
    files_uploaded_bytes.inc(file_size)


def track_ai_request(provider: str, status: str, duration: float):
    """Track AI request metrics"""
    if not PROMETHEUS_AVAILABLE:
        return
    
    ai_requests_total.labels(
        provider=provider,
        status=status
    ).inc()
    
    ai_request_duration_seconds.labels(
        provider=provider
    ).observe(duration)


def update_storage_metrics(uploads_bytes: int, outputs_bytes: int, temp_bytes: int):
    """Update storage metrics"""
    if not PROMETHEUS_AVAILABLE:
        return
    
    files_storage_bytes.labels(directory="uploads").set(uploads_bytes)
    files_storage_bytes.labels(directory="outputs").set(outputs_bytes)
    files_storage_bytes.labels(directory="temp").set(temp_bytes)


def set_system_info(version: str, python_version: str):
    """Set system info"""
    if not PROMETHEUS_AVAILABLE:
        return
    
    system_info.info({
        'version': version,
        'python_version': python_version
    })


# ============================================
# DECORATORS
# ============================================

def track_time(metric: Histogram, **labels):
    """
    Decorator per tracciare tempo esecuzione.
    
    Usage:
        @track_time(ai_request_duration_seconds, provider="ollama")
        def call_ollama():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not PROMETHEUS_AVAILABLE:
                return func(*args, **kwargs)
            
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                if labels:
                    metric.labels(**labels).observe(duration)
                else:
                    metric.observe(duration)
        
        return wrapper
    return decorator


def count_calls(metric: Counter, **labels):
    """
    Decorator per contare chiamate.
    
    Usage:
        @count_calls(ai_requests_total, provider="ollama", status="success")
        def call_ollama():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            if PROMETHEUS_AVAILABLE:
                if labels:
                    metric.labels(**labels).inc()
                else:
                    metric.inc()
            
            return result
        
        return wrapper
    return decorator


# ============================================
# METRICS ENDPOINT
# ============================================

def get_metrics() -> bytes:
    """
    Ottieni metrics in formato Prometheus.
    
    Returns:
        Metrics in formato text/plain
    """
    if not PROMETHEUS_AVAILABLE:
        return b"# Prometheus client not installed\n# Install with: pip install prometheus-client\n"
    
    return generate_latest(REGISTRY)


# ============================================
# INITIALIZATION
# ============================================

def init_metrics(app_version: str = "3.1.0"):
    """Inizializza metrics con info sistema"""
    import sys
    
    set_system_info(
        version=app_version,
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    )
    
    if PROMETHEUS_AVAILABLE:
        print("✅ Prometheus metrics enabled")
        print("   Endpoint: GET /metrics")
    else:
        print("⚠️  Prometheus client not available")
        print("   Install with: pip install prometheus-client")


# Esempio utilizzo
if __name__ == "__main__":
    # Simula alcune metriche
    track_request("POST", "/upload", 200, 0.5)
    track_request("POST", "/upload", 200, 0.3)
    track_request("GET", "/status/123", 200, 0.1)
    
    track_job("completed", 45.2)
    track_job("error", 10.5)
    
    track_file_upload("mp3", 5_000_000)
    track_file_upload("wav", 10_000_000)
    
    track_ai_request("ollama", "success", 2.5)
    
    # Output metrics
    print(get_metrics().decode())

# Made with Bob
