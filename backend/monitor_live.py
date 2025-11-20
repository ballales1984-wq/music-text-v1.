"""
Monitora automaticamente i nuovi processi in corso
Rileva quando viene caricato un nuovo file e monitora il suo processamento
"""
import requests
import time
from pathlib import Path
from datetime import datetime
import sys

API_URL = "http://localhost:8001"
UPLOAD_DIR = Path("uploads")
POLL_INTERVAL = 1.0  # Controlla ogni secondo

def get_latest_job_id():
    """Ottiene l'ultimo job_id dai file caricati."""
    if not UPLOAD_DIR.exists():
        return None
    
    files = sorted(UPLOAD_DIR.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    if files:
        return files[0].stem
    return None

def check_job_status(job_id: str):
    """Controlla lo stato di un job."""
    try:
        response = requests.get(f"{API_URL}/status/{job_id}", timeout=2)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def monitor_live():
    """Monitora continuamente i nuovi processi."""
    print("=" * 70)
    print("🔍 MONITORAGGIO LIVE - Music Text Generator")
    print("=" * 70)
    print("⏰ In attesa di nuovi processi...")
    print("💡 Carica un file audio dal frontend per iniziare")
    print("⏸️  Premi Ctrl+C per interrompere")
    print("=" * 70)
    print()
    
    last_job_id = None
    monitored_jobs = set()
    
    try:
        while True:
            # Controlla nuovo job
            current_job_id = get_latest_job_id()
            
            if current_job_id and current_job_id != last_job_id:
                # Nuovo job rilevato
                last_job_id = current_job_id
                
                if current_job_id not in monitored_jobs:
                    monitored_jobs.add(current_job_id)
                    print(f"\n🆕 NUOVO JOB RILEVATO: {current_job_id}")
                    print("-" * 70)
                    
                    # Monitora questo job
                    monitor_single_job(current_job_id)
            
            # Controlla job già monitorati che potrebbero essere ancora in corso
            for job_id in list(monitored_jobs):
                status = check_job_status(job_id)
                if status:
                    current_status = status.get("status", "unknown")
                    if current_status == "processing":
                        # Job ancora in corso, mostra progress
                        progress = status.get("progress", 0)
                        step = status.get("step", 0)
                        total_steps = status.get("total_steps", 4)
                        step_name = status.get("current_step", "")
                        
                        bar_width = 30
                        filled = int(bar_width * progress / 100)
                        bar = "█" * filled + "░" * (bar_width - filled)
                        
                        print(f"\r[{bar}] {progress:3d}% | Step {step}/{total_steps} | {step_name[:40]}", end="", flush=True)
            
            time.sleep(POLL_INTERVAL)
            
    except KeyboardInterrupt:
        print("\n\n⏸️  Monitoraggio interrotto")
    except Exception as e:
        print(f"\n⚠️  Errore: {str(e)}")

def monitor_single_job(job_id: str):
    """Monitora un singolo job fino al completamento."""
    start_time = time.time()
    last_progress = -1
    last_step = -1
    
    print(f"📊 Monitoraggio job: {job_id[:8]}...")
    
    while True:
        try:
            status = check_job_status(job_id)
            
            if not status:
                print("⚠️  Job non trovato nello stato (potrebbe essere completato)")
                break
            
            current_status = status.get("status", "unknown")
            current_progress = status.get("progress", 0)
            current_step = status.get("step", 0)
            total_steps = status.get("total_steps", 4)
            step_name = status.get("current_step", "")
            
            # Mostra progress solo se cambia
            if current_progress != last_progress or current_step != last_step:
                elapsed = time.time() - start_time
                bar_width = 50
                filled = int(bar_width * current_progress / 100)
                bar = "█" * filled + "░" * (bar_width - filled)
                
                print(f"\r[{bar}] {current_progress:3d}% | Step {current_step}/{total_steps} | {elapsed:6.1f}s | {step_name[:30]}", end="", flush=True)
                
                last_progress = current_progress
                last_step = current_step
            
            # Controlla completamento
            if current_status == "completed":
                elapsed = time.time() - start_time
                print(f"\n\n✅ PROCESSO COMPLETATO!")
                print(f"⏱️  Tempo totale: {elapsed:.1f}s ({elapsed/60:.1f} minuti)")
                
                if "result" in status:
                    result = status["result"]
                    print(f"📝 Varianti generate: {result.get('lyrics_variants', {}).get('total', 0)}")
                    print(f"🎵 Metodo: {result.get('processing_info', {}).get('method_used', 'unknown')}")
                
                print()
                break
            
            if current_status == "error":
                elapsed = time.time() - start_time
                print(f"\n\n❌ PROCESSO FALLITO dopo {elapsed:.1f}s")
                if "error" in status:
                    print(f"💥 Errore: {status['error']}")
                break
            
            time.sleep(0.5)
            
        except KeyboardInterrupt:
            print("\n⏸️  Monitoraggio interrotto")
            break
        except Exception as e:
            print(f"\n⚠️  Errore monitoraggio: {str(e)}")
            time.sleep(1)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Monitora job specifico
        job_id = sys.argv[1]
        monitor_single_job(job_id)
    else:
        # Monitora live tutti i nuovi job
        monitor_live()

