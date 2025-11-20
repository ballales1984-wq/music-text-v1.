"""
Script per analizzare i dati del processo di generazione testo
Mostra statistiche, risultati e stato dei job
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import sys

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("outputs")

def get_latest_jobs(limit: int = 10) -> List[str]:
    """Ottiene gli ultimi job_id dai file caricati."""
    if not UPLOAD_DIR.exists():
        return []
    
    files = sorted(UPLOAD_DIR.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    job_ids = [f.stem for f in files[:limit]]
    return job_ids

def analyze_job(job_id: str) -> Dict:
    """Analizza un singolo job."""
    result = {
        "job_id": job_id,
        "has_original": False,
        "has_vocals": False,
        "has_instrumental": False,
        "has_vocals_clean": False,
        "file_size_mb": 0,
        "timestamp": None
    }
    
    # Controlla file originale
    for ext in [".mp3", ".wav", ".m4a", ".flac"]:
        original = UPLOAD_DIR / f"{job_id}{ext}"
        if original.exists():
            result["has_original"] = True
            result["file_size_mb"] = original.stat().st_size / (1024 * 1024)
            result["timestamp"] = datetime.fromtimestamp(original.stat().st_mtime)
            break
    
    # Controlla file generati
    vocals = OUTPUT_DIR / f"{job_id}_vocals.wav"
    instrumental = OUTPUT_DIR / f"{job_id}_instrumental.wav"
    vocals_clean = OUTPUT_DIR / f"{job_id}_vocals_clean.wav"
    
    result["has_vocals"] = vocals.exists()
    result["has_instrumental"] = instrumental.exists()
    result["has_vocals_clean"] = vocals_clean.exists()
    
    # Dimensione file generati
    if result["has_vocals"]:
        result["vocals_size_mb"] = vocals.stat().st_size / (1024 * 1024)
    if result["has_instrumental"]:
        result["instrumental_size_mb"] = instrumental.stat().st_size / (1024 * 1024)
    
    return result

def get_statistics() -> Dict:
    """Ottiene statistiche generali."""
    stats = {
        "total_jobs": 0,
        "jobs_with_vocals": 0,
        "jobs_with_instrumental": 0,
        "total_size_mb": 0,
        "latest_jobs": []
    }
    
    if not UPLOAD_DIR.exists():
        return stats
    
    # Conta file originali
    original_files = list(UPLOAD_DIR.glob("*.mp3")) + list(UPLOAD_DIR.glob("*.wav")) + \
                     list(UPLOAD_DIR.glob("*.m4a")) + list(UPLOAD_DIR.glob("*.flac"))
    stats["total_jobs"] = len(original_files)
    
    # Calcola dimensione totale
    for f in original_files:
        stats["total_size_mb"] += f.stat().st_size / (1024 * 1024)
    
    # Conta file generati
    vocals_files = list(OUTPUT_DIR.glob("*_vocals.wav"))
    instrumental_files = list(OUTPUT_DIR.glob("*_instrumental.wav"))
    
    stats["jobs_with_vocals"] = len(vocals_files)
    stats["jobs_with_instrumental"] = len(instrumental_files)
    
    # Analizza ultimi job
    latest_job_ids = get_latest_jobs(5)
    stats["latest_jobs"] = [analyze_job(job_id) for job_id in latest_job_ids]
    
    return stats

def print_analysis():
    """Stampa analisi completa."""
    print("=" * 60)
    print("📊 ANALISI PROCESSO - Music Text Generator")
    print("=" * 60)
    print()
    
    stats = get_statistics()
    
    print("📈 STATISTICHE GENERALI")
    print("-" * 60)
    print(f"Totale job processati: {stats['total_jobs']}")
    print(f"Job con voce isolata: {stats['jobs_with_vocals']}")
    print(f"Job con base strumentale: {stats['jobs_with_instrumental']}")
    print(f"Dimensione totale file: {stats['total_size_mb']:.2f} MB")
    print()
    
    if stats["latest_jobs"]:
        print("🕐 ULTIMI 5 JOB")
        print("-" * 60)
        for job in stats["latest_jobs"]:
            print(f"\nJob ID: {job['job_id'][:8]}...")
            if job['timestamp']:
                print(f"  Timestamp: {job['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  File originale: {'✅' if job['has_original'] else '❌'} ({job['file_size_mb']:.2f} MB)")
            print(f"  Voce isolata: {'✅' if job['has_vocals'] else '❌'}", end="")
            if job['has_vocals']:
                print(f" ({job.get('vocals_size_mb', 0):.2f} MB)")
            else:
                print()
            print(f"  Base strumentale: {'✅' if job['has_instrumental'] else '❌'}", end="")
            if job['has_instrumental']:
                print(f" ({job.get('instrumental_size_mb', 0):.2f} MB)")
            else:
                print()
            print(f"  Voce pulita: {'✅' if job['has_vocals_clean'] else '❌'}")
    
    print()
    print("=" * 60)
    print("💡 Per vedere i dettagli di un job specifico:")
    print("   python analyze_process.py <job_id>")
    print("=" * 60)

def analyze_specific_job(job_id: str):
    """Analizza un job specifico in dettaglio."""
    print("=" * 60)
    print(f"📋 ANALISI JOB: {job_id}")
    print("=" * 60)
    print()
    
    job = analyze_job(job_id)
    
    print("📁 FILE DISPONIBILI")
    print("-" * 60)
    print(f"File originale: {'✅' if job['has_original'] else '❌'}")
    if job['has_original']:
        print(f"  Dimensione: {job['file_size_mb']:.2f} MB")
        print(f"  Timestamp: {job['timestamp']}")
    
    print(f"Voce isolata: {'✅' if job['has_vocals'] else '❌'}")
    if job['has_vocals']:
        print(f"  Dimensione: {job.get('vocals_size_mb', 0):.2f} MB")
        vocals_path = OUTPUT_DIR / f"{job_id}_vocals.wav"
        print(f"  Path: {vocals_path}")
    
    print(f"Base strumentale: {'✅' if job['has_instrumental'] else '❌'}")
    if job['has_instrumental']:
        print(f"  Dimensione: {job.get('instrumental_size_mb', 0):.2f} MB")
        instrumental_path = OUTPUT_DIR / f"{job_id}_instrumental.wav"
        print(f"  Path: {instrumental_path}")
    
    print(f"Voce pulita: {'✅' if job['has_vocals_clean'] else '❌'}")
    if job['has_vocals_clean']:
        vocals_clean_path = OUTPUT_DIR / f"{job_id}_vocals_clean.wav"
        print(f"  Path: {vocals_clean_path}")
    
    print()
    print("🔗 URL API")
    print("-" * 60)
    print(f"Audio originale: http://localhost:8001/audio/{job_id}")
    if job['has_vocals']:
        print(f"Voce isolata: http://localhost:8001/audio/{job_id}/vocals")
    if job['has_instrumental']:
        print(f"Base strumentale: http://localhost:8001/audio/{job_id}/instrumental")
    print(f"Stato job: http://localhost:8001/status/{job_id}")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        job_id = sys.argv[1]
        analyze_specific_job(job_id)
    else:
        print_analysis()

