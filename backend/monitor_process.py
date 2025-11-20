"""
Script per monitorare in tempo reale lo stato di un processo
Mostra progress, step corrente e attende completamento
"""
import requests
import time
import sys
from datetime import datetime

API_URL = "http://localhost:8001"

def monitor_job(job_id: str, poll_interval: float = 0.5):
    """Monitora un job in tempo reale."""
    print("=" * 70)
    print(f"🔍 MONITORAGGIO JOB: {job_id}")
    print("=" * 70)
    print(f"⏰ Inizio monitoraggio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    start_time = time.time()
    last_step = -1
    last_progress = -1
    
    try:
        while True:
            try:
                response = requests.get(f"{API_URL}/status/{job_id}", timeout=5)
                
                if response.status_code == 404:
                    print("❌ Job non trovato. Verifica che il job_id sia corretto.")
                    break
                
                if response.status_code != 200:
                    print(f"⚠️  Errore HTTP {response.status_code}: {response.text}")
                    time.sleep(poll_interval)
                    continue
                
                status = response.json()
                current_status = status.get("status", "unknown")
                current_step = status.get("step", 0)
                total_steps = status.get("total_steps", 4)
                current_progress = status.get("progress", 0)
                current_step_name = status.get("current_step", "Sconosciuto")
                
                # Mostra solo se cambia qualcosa
                if current_step != last_step or current_progress != last_progress:
                    elapsed = time.time() - start_time
                    
                    # Progress bar
                    bar_width = 50
                    filled = int(bar_width * current_progress / 100)
                    bar = "█" * filled + "░" * (bar_width - filled)
                    
                    print(f"\r[{bar}] {current_progress:3d}% | Step {current_step}/{total_steps} | {elapsed:6.1f}s", end="", flush=True)
                    
                    # Dettagli step
                    if current_step != last_step:
                        print(f"\n📋 {current_step_name}")
                    
                    last_step = current_step
                    last_progress = current_progress
                
                # Controlla se completato
                if current_status == "completed":
                    elapsed = time.time() - start_time
                    print(f"\n\n✅ PROCESSO COMPLETATO!")
                    print(f"⏱️  Tempo totale: {elapsed:.1f} secondi ({elapsed/60:.1f} minuti)")
                    print()
                    
                    # Mostra risultato se disponibile
                    if "result" in status:
                        result = status["result"]
                        print("📊 RISULTATI:")
                        print("-" * 70)
                        
                        if "lyrics_variants" in result:
                            variants = result["lyrics_variants"]
                            print(f"Varianti testo generate: {variants.get('total', 0)}")
                        
                        if "raw_transcription" in result:
                            trans = result["raw_transcription"]
                            text_len = len(trans.get("text", ""))
                            print(f"Testo trascritto: {text_len} caratteri")
                        
                        if "processing_info" in result:
                            info = result["processing_info"]
                            print(f"Metodo usato: {info.get('method_used', 'unknown')}")
                            if info.get("warnings"):
                                print(f"⚠️  Warning: {len(info['warnings'])}")
                            if info.get("errors"):
                                print(f"❌ Errori: {len(info['errors'])}")
                    
                    print()
                    print("🔗 URL Risultati:")
                    print(f"  Audio originale: {API_URL}/audio/{job_id}")
                    if status.get("result", {}).get("vocal_audio_url"):
                        print(f"  Voce isolata: {API_URL}{status['result']['vocal_audio_url']}")
                    if status.get("result", {}).get("instrumental_audio_url"):
                        print(f"  Base strumentale: {API_URL}{status['result']['instrumental_audio_url']}")
                    
                    break
                
                # Controlla se errore
                if current_status == "error":
                    elapsed = time.time() - start_time
                    print(f"\n\n❌ PROCESSO FALLITO!")
                    print(f"⏱️  Tempo prima dell'errore: {elapsed:.1f} secondi")
                    if "error" in status:
                        print(f"💥 Errore: {status['error']}")
                    break
                
                time.sleep(poll_interval)
                
            except requests.exceptions.ConnectionError:
                print("\n⚠️  Impossibile connettersi al backend. Verifica che sia attivo su http://localhost:8001")
                break
            except requests.exceptions.Timeout:
                print("\n⚠️  Timeout connessione. Riprovo...")
                time.sleep(poll_interval)
                continue
            except KeyboardInterrupt:
                print("\n\n⏸️  Monitoraggio interrotto dall'utente")
                break
            except Exception as e:
                print(f"\n⚠️  Errore: {str(e)}")
                time.sleep(poll_interval)
                continue
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Monitoraggio interrotto")
    
    print("\n" + "=" * 70)

def find_latest_job():
    """Trova l'ultimo job_id dai file caricati."""
    from pathlib import Path
    
    upload_dir = Path("uploads")
    if not upload_dir.exists():
        return None
    
    files = sorted(upload_dir.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    if files:
        return files[0].stem
    return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        job_id = sys.argv[1]
    else:
        # Cerca ultimo job
        job_id = find_latest_job()
        if not job_id:
            print("❌ Nessun job trovato. Fornisci un job_id:")
            print("   python monitor_process.py <job_id>")
            sys.exit(1)
        print(f"🔍 Job ID non specificato, uso l'ultimo: {job_id}\n")
    
    monitor_job(job_id)

