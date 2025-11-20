"""
Separazione vocale AVANZATA - Isola voce E base strumentale

METODI DISPONIBILI:
1. Spleeter (ML model) - MIGLIORE QUALITÀ
   - Richiede 30-60 secondi per file
   - Separazione molto precisa
   - NOTA: Spleeter ha problemi di compatibilità con Python 3.11+
   - Installazione: pip install spleeter (può fallire su Python 3.11+)

2. Metodi semplici (fallback) - VELOCE MA MENO PRECISO
   - Richiede 1-3 secondi per file
   - Usa filtri frequenza + differenza canali stereo
   - Separazione meno precisa ma funziona sempre
   - Questo è il metodo usato se Spleeter non è disponibile

Il sistema prova prima Spleeter, poi usa i metodi semplici se non disponibile.
"""
import logging
from pathlib import Path
from typing import Tuple, Optional
import numpy as np
import os
import shutil

# Import opzionali per torch/torchaudio
try:
    import torch
    import torchaudio
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("torch/torchaudio non disponibile - alcune funzionalità saranno limitate")

logger = logging.getLogger(__name__)

# Check disponibilità modelli ML
SPLEETER_AVAILABLE = False
USE_SPLEETER = os.getenv("USE_SPLEETER", "true").lower() == "true"  # Variabile ambiente per disabilitare
SPLEETER_VENV_PATH = None  # Path al venv_spleeter se disponibile

# Prova prima con il venv_spleeter (Python 3.10)
venv_spleeter_python = Path(__file__).parent / "venv_spleeter" / "Scripts" / "python.exe"
if venv_spleeter_python.exists():
    try:
        import subprocess
        result = subprocess.run(
            [str(venv_spleeter_python), "-c", "from spleeter.separator import Separator; print('OK')"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            SPLEETER_VENV_PATH = str(venv_spleeter_python.parent.parent)
            SPLEETER_AVAILABLE = True
            logger.info(f"✅ Spleeter trovato in venv_spleeter (Python 3.10)")
    except:
        pass

# Prova import normale (se Spleeter è nel venv corrente)
if not SPLEETER_VENV_PATH:
    try:
        from spleeter.separator import Separator
        from spleeter.audio.adapter import AudioAdapter
        SPLEETER_AVAILABLE = True
        if USE_SPLEETER:
            logger.info("✅ Spleeter disponibile - userà modello ML per separazione")
        else:
            logger.info("⚠️  Spleeter disponibile ma DISABILITATO (USE_SPLEETER=false) - userà metodi veloci")
    except ImportError:
        if SPLEETER_VENV_PATH:
            SPLEETER_AVAILABLE = True
            logger.info("✅ Spleeter disponibile in venv_spleeter - userà modello ML per separazione")
        else:
            logger.warning("Spleeter non disponibile - userà metodi semplici")


def _separate_with_spleeter_subprocess(input_path: Path, job_id: str, output_dir: Path) -> Optional[Tuple[Path, Path]]:
    """
    Separa usando Spleeter tramite subprocess dal venv_spleeter.
    Usato quando Spleeter è installato in un venv separato (Python 3.10).
    """
    import subprocess
    import json
    import tempfile
    
    venv_python = Path(SPLEETER_VENV_PATH) / "Scripts" / "python.exe"
    if not venv_python.exists():
        logger.error("venv_spleeter Python non trovato")
        return None
    
    try:
        # Crea script temporaneo per eseguire Spleeter
        script_content = f"""
import sys
from pathlib import Path
from spleeter.separator import Separator
from spleeter.audio.adapter import AudioAdapter
import json

input_path = r"{input_path}"
output_dir = r"{output_dir}"
job_id = "{job_id}"

try:
    separator = Separator('spleeter:2stems', multiprocess=False)
    audio_adapter = AudioAdapter.default()
    
    waveform, sample_rate = audio_adapter.load(input_path)
    prediction = separator.separate(waveform)
    
    vocals = prediction['vocals']
    accompaniment = prediction['accompaniment']
    
    vocal_path = Path(output_dir) / f"{{job_id}}_vocals.wav"
    instrumental_path = Path(output_dir) / f"{{job_id}}_instrumental.wav"
    
    audio_adapter.save(str(vocal_path), vocals, sample_rate)
    audio_adapter.save(str(instrumental_path), accompaniment, sample_rate)
    
    result = {{
        "success": True,
        "vocal_path": str(vocal_path),
        "instrumental_path": str(instrumental_path)
    }}
    print(json.dumps(result))
except Exception as e:
    result = {{"success": False, "error": str(e)}}
    print(json.dumps(result))
    sys.exit(1)
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            script_path = f.name
        
        # Esegui script con venv_spleeter
        result = subprocess.run(
            [str(venv_python), script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minuti timeout
        )
        
        # Pulisci script temporaneo
        try:
            os.unlink(script_path)
        except:
            pass
        
        if result.returncode != 0:
            logger.error(f"Spleeter subprocess fallito: {result.stderr}")
            return None
        
        # Parse risultato JSON
        try:
            output = result.stdout.strip().split('\n')[-1]  # Ultima riga (JSON)
            data = json.loads(output)
            if data.get("success"):
                vocal_path = Path(data["vocal_path"])
                instrumental_path = Path(data["instrumental_path"])
                logger.info("✅ Separazione Spleeter completata con successo!")
                logger.info(f"   📁 VOCE: {vocal_path.name}")
                logger.info(f"   📁 BASE: {instrumental_path.name}")
                return vocal_path, instrumental_path
            else:
                logger.error(f"Spleeter errore: {data.get('error', 'Unknown')}")
                return None
        except json.JSONDecodeError:
            logger.error(f"Spleeter output non valido: {result.stdout}")
            return None
            
    except subprocess.TimeoutExpired:
        logger.error("Spleeter timeout (oltre 5 minuti)")
        return None
    except Exception as e:
        logger.error(f"Errore esecuzione Spleeter subprocess: {e}")
        return None


def _save_audio_tensor(audio_tensor, output_path: Path, sr: int):
    """Salva tensor audio come WAV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if TORCH_AVAILABLE:
        try:
            torchaudio.save(str(output_path), audio_tensor, sr, backend="soundfile")
            return
        except:
            pass
    
    # Fallback: soundfile diretto o numpy
    import soundfile as sf
    if TORCH_AVAILABLE:
        audio_np = audio_tensor.detach().cpu().numpy()
    else:
        # Se non è un tensor, assumiamo che sia già numpy
        audio_np = np.array(audio_tensor)
    
    if audio_np.dtype != np.float32:
        audio_np = audio_np.astype(np.float32)
    max_val = np.abs(audio_np).max()
    if max_val > 1.0:
        audio_np = audio_np / max_val
    if audio_np.ndim == 1:
        audio_np = audio_np.reshape(-1, 1)
    elif audio_np.ndim == 2 and audio_np.shape[0] < audio_np.shape[1]:
        audio_np = audio_np.T
    sf.write(str(output_path), audio_np, int(sr), format='WAV', subtype='PCM_16')


def _separate_with_spleeter(input_path: Path, job_id: str, output_dir: Path) -> Optional[Tuple[Path, Path]]:
    """
    Separa usando Spleeter (modello ML pre-addestrato).
    Metodo migliore disponibile per separazione vocale.
    """
    if not SPLEETER_AVAILABLE or not USE_SPLEETER:
        if not USE_SPLEETER:
            logger.info("⏭️  Spleeter disabilitato (USE_SPLEETER=false) - salto a metodi veloci")
        return None
    
    try:
        logger.info("🎯 Tentativo separazione con Spleeter (ML model)...")
        logger.info("   ⏳ Questo può richiedere 30-60 secondi (scarica modello al primo uso)")
        
        # Se Spleeter è nel venv_spleeter, usa subprocess
        if SPLEETER_VENV_PATH:
            logger.info("   🔧 Uso Spleeter da venv_spleeter (Python 3.10)")
            return _separate_with_spleeter_subprocess(input_path, job_id, output_dir)
        
        # Altrimenti usa import diretto
        from spleeter.separator import Separator
        from spleeter.audio.adapter import AudioAdapter
        
        # Usa modello 2stems (vocals + accompaniment)
        # Nota: al primo uso scarica il modello (~100MB)
        # multiprocess=False per evitare problemi e migliorare stabilità
        separator = Separator('spleeter:2stems', multiprocess=False)
        audio_adapter = AudioAdapter.default()
        
        # Carica audio
        logger.info("   📥 Caricamento audio...")
        waveform, sample_rate = audio_adapter.load(str(input_path))
        logger.info(f"   ✅ Audio caricato: shape={waveform.shape}, {sample_rate}Hz")
        
        # Separa (operazione ML - può richiedere tempo)
        logger.info("   ⏳ Separazione in corso (modello ML)...")
        prediction = separator.separate(waveform)
        
        # Estrai tracce
        vocals = prediction['vocals']
        accompaniment = prediction['accompaniment']
        logger.info(f"   ✅ Separazione completata: vocals shape={vocals.shape}, accompaniment shape={accompaniment.shape}")
        
        # Salva tracce
        vocal_path = output_dir / f"{job_id}_vocals.wav"
        instrumental_path = output_dir / f"{job_id}_instrumental.wav"
        
        logger.info("   💾 Salvataggio tracce...")
        audio_adapter.save(str(vocal_path), vocals, sample_rate)
        audio_adapter.save(str(instrumental_path), accompaniment, sample_rate)
        
        logger.info("✅ Separazione Spleeter completata con successo!")
        logger.info(f"   📁 VOCE: {vocal_path.name}")
        logger.info(f"   📁 BASE: {instrumental_path.name}")
        return vocal_path, instrumental_path
        
    except Exception as e:
        logger.warning(f"Spleeter fallito: {str(e)[:100]}, uso fallback")
        # Pulisci directory temporanea se esiste
        temp_dir = output_dir / f"{job_id}_spleeter_temp"
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except:
            pass
        return None


def separate_vocals_and_instrumental(input_path: Path, job_id: str, output_dir: Path) -> Tuple[Path, Path]:
    """
    Separa correttamente VOCE e BASE STRUMENTALE.
    
    Ordine di tentativi:
    1. Spleeter (ML model) - migliore qualità (richiede 30-60 secondi)
    2. Metodi semplici (filtri frequenza + differenza canali) - fallback (veloce ma meno accurato)
    
    Returns:
        (vocal_path, instrumental_path)
    """
    import time
    start_time = time.time()
    
    logger.info(f"🎵 Separazione VOCE e BASE: {input_path.name}")
    logger.info(f"📊 Spleeter disponibile: {SPLEETER_AVAILABLE}, Abilitato: {USE_SPLEETER}")
    
    # TENTATIVO 1: Spleeter (ML model) - migliore qualità
    if SPLEETER_AVAILABLE and USE_SPLEETER:
        logger.info("🎯 Tentativo con Spleeter (ML model) - richiede 30-60 secondi...")
        result = _separate_with_spleeter(input_path, job_id, output_dir)
        if result:
            elapsed = time.time() - start_time
            logger.info(f"✅ Separazione Spleeter completata in {elapsed:.1f} secondi")
            return result
        else:
            logger.warning("⚠️  Spleeter fallito o non disponibile, passo a metodi semplici")
    else:
        if not SPLEETER_AVAILABLE:
            logger.warning("⚠️  Spleeter NON INSTALLATO - uso metodi semplici (veloce ma meno accurato)")
            logger.warning("   💡 Per installare: pip install spleeter")
        elif not USE_SPLEETER:
            logger.warning("⚠️  Spleeter DISABILITATO (USE_SPLEETER=false) - uso metodi semplici")
    
    # TENTATIVO 2: Metodi semplici (fallback)
    logger.info("⚡ Uso metodi semplici (fallback) - veloce ma meno accurato")
    logger.info("   ⚠️  Questo metodo è VELOCE ma la separazione sarà MENO PRECISA")
    
    try:
        # Carica audio
        file_ext = input_path.suffix.lower()
        
        if file_ext in ['.mp3', '.m4a', '.aac']:
            # Formati compressi: usa librosa
            try:
                import librosa
                y, sr = librosa.load(str(input_path), sr=None, mono=False)
                if TORCH_AVAILABLE:
                    if len(y.shape) == 1:
                        wav = torch.from_numpy(y).unsqueeze(0)
                    else:
                        wav = torch.from_numpy(y)
                    logger.info(f"Caricato con librosa: shape={wav.shape}, stereo={wav.shape[0] == 2}")
                else:
                    # Usa numpy direttamente
                    wav = y
                    logger.info(f"Caricato con librosa: shape={wav.shape}, stereo={len(wav.shape) > 1 and wav.shape[0] == 2}")
            except Exception as e:
                raise Exception(f"Errore caricamento {file_ext}: {str(e)[:100]}. Converti in WAV.")
        else:
            # WAV/FLAC: usa soundfile
            try:
                if TORCH_AVAILABLE:
                    wav, sr = torchaudio.load(str(input_path), backend="soundfile")
                    logger.info(f"Caricato con soundfile: shape={wav.shape}, stereo={wav.shape[0] == 2}")
                else:
                    # Fallback: usa soundfile direttamente
                    import soundfile as sf
                    wav, sr = sf.read(str(input_path), always_2d=False)
                    if wav.ndim == 1:
                        wav = wav.reshape(1, -1)  # Mono -> (1, samples)
                    else:
                        wav = wav.T  # (samples, channels) -> (channels, samples)
                    logger.info(f"Caricato con soundfile: shape={wav.shape}, stereo={wav.shape[0] == 2}")
            except Exception as e:
                raise Exception(f"Errore caricamento: {str(e)[:100]}")
        
        # SEPARAZIONE CORRETTA
        if wav.shape[0] == 2:
            # STEREO: Metodo migliorato per isolare VOCE
            # Il problema: (L+R)/2 contiene TUTTO il mix centrale (voce + base)
            # Soluzione: usiamo filtri frequenza + differenza canali
            
            try:
                import librosa
                # Carica con librosa per avere accesso ai filtri
                y, sr = librosa.load(str(input_path), sr=None, mono=False)
                if len(y.shape) == 1:
                    y = y.reshape(1, -1)
                
                # Metodo 1: Filtro frequenza per isolare voce (80-8000 Hz)
                # La voce umana è tipicamente in questa banda
                y_mono = (y[0] + y[1]) / 2 if y.shape[0] == 2 else y[0]
                
                # Applica filtro passa-banda per frequenze vocali
                # Usa librosa per filtrare
                from scipy import signal
                try:
                    # Filtro passa-banda 80-8000 Hz per voce
                    nyquist = sr / 2
                    low = 80 / nyquist
                    high = 8000 / nyquist
                    b, a = signal.butter(4, [low, high], btype='band')
                    vocals_filtered = signal.filtfilt(b, a, y_mono)
                    
                    # CORREZIONE: I risultati erano invertiti!
                    # Il filtro 80-8000 Hz estrae principalmente la BASE (strumenti)
                    # La VOCE è meglio estratta con differenza canali o metodo inverso
                    
                    # Metodo corretto: usa differenza canali per voce
                    # VOCE = Differenza canali (L-R)/2 (voce spesso panata al centro ma con differenze)
                    # Oppure: inverso del filtro - tutto tranne 80-8000 Hz
                    mix_mono = (y[0] + y[1]) / 2 if y.shape[0] == 2 else y[0]
                    
                    # VOCE: Prova metodo differenza canali (più affidabile per voce)
                    if y.shape[0] == 2:
                        vocals_diff = (y[0] - y[1]) / 2
                        # Combina: differenza canali + filtro frequenza per migliorare
                        vocals_combined = vocals_filtered * 0.3 + vocals_diff * 0.7
                    else:
                        vocals_combined = vocals_filtered
                    
                    vocals = torch.from_numpy(vocals_combined).unsqueeze(0)
                    
                    # BASE = mix completo - voce (sottrazione)
                    instrumental_raw = mix_mono - vocals_combined
                    instrumental = torch.from_numpy(instrumental_raw).unsqueeze(0)
                    
                    logger.info("✅ Separazione STEREO con metodo combinato:")
                    logger.info("   - VOCE = Differenza canali (L-R)/2 + filtro frequenza")
                    logger.info("   - BASE = Mix completo - voce")
                except ImportError:
                    # Fallback se scipy non disponibile: usa metodo differenza canali
                    logger.warning("scipy non disponibile, uso metodo differenza canali")
                    # CORREZIONE: VOCE = Differenza canali (L-R)/2
                    vocals = (wav[0] - wav[1]) / 2
                    vocals = vocals.unsqueeze(0)
                    # BASE = Canale centrale (L+R)/2 - voce (sottrazione)
                    mix_center = (wav[0] + wav[1]) / 2
                    instrumental = mix_center - vocals
                    instrumental = instrumental.unsqueeze(0)
                    logger.info("✅ Separazione STEREO (fallback differenza canali):")
                    logger.info("   - VOCE = (L-R)/2 (differenza canali)")
                    logger.info("   - BASE = (L+R)/2 - voce")
            except Exception as e:
                # Fallback semplice: differenza canali
                logger.warning(f"Errore filtri frequenza: {str(e)[:50]}, uso metodo semplice")
                # CORREZIONE: VOCE = Differenza canali (L-R)/2
                vocals = (wav[0] - wav[1]) / 2
                vocals = vocals.unsqueeze(0)
                # BASE = Canale centrale (L+R)/2 - voce
                mix_center = (wav[0] + wav[1]) / 2
                instrumental = mix_center - vocals
                instrumental = instrumental.unsqueeze(0)
                logger.info("✅ Separazione STEREO (metodo semplice):")
                logger.info("   - VOCE = (L-R)/2 (differenza canali)")
                logger.info("   - BASE = (L+R)/2 - voce")
            
        elif wav.shape[0] == 1:
            # MONO: Usa filtri frequenza per separare
            logger.warning("File MONO: separazione per frequenze (meno precisa)")
            
            # Per mono, usa tutto come voce e crea base vuota
            # (oppure applica filtri frequenza se disponibile)
            vocals = wav
            # Base vuota o molto attenuata
            instrumental = wav * 0.1  # Base molto attenuata per mono
            
            logger.info("⚠️  File mono: voce=completo, base=attenuata")
        else:
            # Multi-canale: usa primi due canali
            vocals = (wav[0] + wav[1]) / 2 if wav.shape[0] >= 2 else wav[0]
            vocals = vocals.unsqueeze(0)
            instrumental = (wav[0] - wav[1]) / 2 if wav.shape[0] >= 2 else wav[0] * 0.1
            instrumental = instrumental.unsqueeze(0)
            logger.info(f"Multi-canale: uso primi 2 canali")
        
        # Normalizza per evitare clipping
        for audio in [vocals, instrumental]:
            max_val = torch.abs(audio).max()
            if max_val > 1.0:
                audio.data = audio / max_val
        
        # Salva entrambi i file
        vocal_path = output_dir / f"{job_id}_vocals.wav"
        instrumental_path = output_dir / f"{job_id}_instrumental.wav"
        
        _save_audio_tensor(vocals, vocal_path, sr)
        _save_audio_tensor(instrumental, instrumental_path, sr)
        
        elapsed = time.time() - start_time
        logger.info(f"✅ Separazione completata in {elapsed:.1f} secondi (metodo semplice)")
        logger.info(f"   📁 VOCE isolata: {vocal_path.name}")
        logger.info(f"   📁 BASE strumentale: {instrumental_path.name}")
        logger.warning(f"   ⚠️  NOTA: Metodo semplice usato - separazione meno precisa di Spleeter")
        
        return vocal_path, instrumental_path
        
    except Exception as e:
        logger.error(f"Errore separazione: {str(e)}", exc_info=True)
        raise Exception(f"Separazione vocale fallita: {str(e)}")


def separate_vocals(input_path: Path, job_id: str, output_dir: Path) -> Path:
    """
    Wrapper per compatibilità: restituisce solo la voce.
    Usa la nuova funzione separate_vocals_and_instrumental internamente.
    """
    vocal_path, _ = separate_vocals_and_instrumental(input_path, job_id, output_dir)
    return vocal_path

