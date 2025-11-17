"""
Modulo per la separazione della traccia vocale dagli strumenti.
Usa Demucs per la source separation.
"""
import os
import subprocess
import logging
from pathlib import Path
import torch
import torchaudio
from typing import Optional
import shutil

logger = logging.getLogger(__name__)

# Flag per controllare se Demucs è disponibile e funzionante
DEMUCS_AVAILABLE = False

# Disabilita Demucs se FFmpeg non è disponibile o se torchcodec non funziona
# Per semplicità, disabilitiamo Demucs se FFmpeg non è disponibile
ffmpeg_path = shutil.which("ffmpeg")
if not ffmpeg_path:
    logger.warning("FFmpeg non trovato nel sistema. Disabilito Demucs, userò metodo fallback.")
    DEMUCS_AVAILABLE = False
else:
    # FFmpeg è disponibile, ma torchcodec potrebbe non funzionare
    # Disabilitiamo Demucs per evitare errori con torchcodec
    logger.warning("FFmpeg trovato ma torchcodec potrebbe non funzionare. Uso metodo fallback per sicurezza.")
    DEMUCS_AVAILABLE = False
    # Se vuoi provare Demucs, decommenta il codice sotto (ma potrebbe fallire)
    # try:
    #     import demucs
    #     DEMUCS_AVAILABLE = True
    #     logger.info("Demucs disponibile")
    # except Exception as e:
    #     logger.warning(f"Demucs non disponibile: {str(e)[:100]}")
    #     DEMUCS_AVAILABLE = False


def separate_vocals(
    input_path: Path,
    job_id: str,
    output_dir: Path,
    model_name: str = "htdemucs"
) -> Path:
    """
    Isola la traccia vocale da un file audio usando Demucs.
    
    Args:
        input_path: Path del file audio originale
        job_id: ID univoco del job
        output_dir: Directory dove salvare l'output
        model_name: Nome del modello Demucs da usare
    
    Returns:
        Path del file vocale isolato
    """
    # Se Demucs non è disponibile o non funziona, usa direttamente il fallback
    if not DEMUCS_AVAILABLE:
        logger.info("Demucs non disponibile o non funzionante. Uso metodo fallback.")
        return _fallback_separation(input_path, job_id, output_dir)
    
    try:
        logger.info(f"Separazione vocale con Demucs (modello: {model_name})")
        
        # Prepara directory temporanea per Demucs
        temp_dir = output_dir / f"temp_{job_id}"
        temp_dir.mkdir(exist_ok=True)
        
        # Usa Demucs tramite CLI (metodo più affidabile)
        # Demucs separa in: drums, bass, other, vocals
        try:
            cmd = [
                "python", "-m", "demucs.separate",
                "-n", model_name,
                "-o", str(temp_dir),
                str(input_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True,
                timeout=600  # Timeout di 10 minuti
            )
            
            logger.info("Demucs CLI eseguito con successo")
            
            # Trova il file vocale generato
            # Demucs crea: temp_dir/model_name/filename/vocals.wav
            audio_name = input_path.stem
            vocals_path = temp_dir / model_name / audio_name / "vocals.wav"
            
            if not vocals_path.exists():
                # Prova varianti del nome
                for possible_name in [audio_name, input_path.name.replace(input_path.suffix, "")]:
                    possible_path = temp_dir / model_name / possible_name / "vocals.wav"
                    if possible_path.exists():
                        vocals_path = possible_path
                        break
            
            if not vocals_path.exists():
                raise FileNotFoundError(f"File vocale non trovato in {temp_dir}")
            
            # Copia il file vocale nella directory di output
            output_path = output_dir / f"{job_id}_vocals.wav"
            shutil.copy2(vocals_path, output_path)
            
            logger.info(f"Traccia vocale salvata: {output_path}")
            
            # Pulisci directory temporanea
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            
            return output_path
            
        except subprocess.CalledProcessError as e:
            error_output = e.stderr or e.stdout or str(e)
            logger.error(f"Errore esecuzione Demucs CLI: {error_output}")
            
            # Se l'errore è relativo a torchcodec/FFmpeg, usa fallback
            if any(keyword in error_output.lower() for keyword in ["torchcodec", "ffmpeg", "libtorchcodec"]):
                logger.warning("Demucs richiede FFmpeg/torchcodec. Uso metodo fallback.")
                return _fallback_separation(input_path, job_id, output_dir)
            
            # Per altri errori, prova fallback
            logger.warning("Errore con Demucs, uso metodo fallback.")
            return _fallback_separation(input_path, job_id, output_dir)
            
        except FileNotFoundError as e:
            logger.error(f"File non trovato: {str(e)}")
            return _fallback_separation(input_path, job_id, output_dir)
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Errore durante separazione Demucs: {error_msg}")
        
        # Se l'errore è relativo a torchcodec/FFmpeg, usa direttamente il fallback
        if any(keyword in error_msg.lower() for keyword in ["torchcodec", "ffmpeg", "libtorchcodec"]):
            logger.warning("Demucs richiede FFmpeg/torchcodec non disponibile. Uso metodo fallback.")
            return _fallback_separation(input_path, job_id, output_dir)
        
        logger.info("Tentativo con metodo fallback...")
        return _fallback_separation(input_path, job_id, output_dir)


def _fallback_separation(
    input_path: Path,
    job_id: str,
    output_dir: Path
) -> Path:
    """
    Metodo fallback per separazione vocale.
    Estrae il canale centrale (L-R) che spesso contiene la voce.
    """
    try:
        logger.info("Uso metodo fallback: estrazione canale centrale")
        logger.info(f"Caricamento file: {input_path}")
        
        # Determina device (GPU se disponibile)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        if device == "cuda":
            logger.info(f"⚡ GPU disponibile per processamento audio")
        
        # Carica il file audio senza usare torchcodec
        # Usa backend="soundfile" che non richiede torchcodec
        wav = None
        sr = None
        
        # Prova prima con soundfile (non richiede torchcodec, funziona con WAV)
        file_ext = input_path.suffix.lower()
        
        # Se è MP3 o formato compresso, prova direttamente con librosa
        if file_ext in ['.mp3', '.m4a', '.aac', '.ogg', '.wma']:
            logger.info(f"File {file_ext} rilevato. Uso librosa per caricare (supporta formati compressi)...")
            try:
                import librosa
                import numpy as np
                # Librosa può caricare MP3 e altri formati
                # NOTA: Potrebbe richiedere FFmpeg, ma gestisce meglio gli errori
                y, sr = librosa.load(str(input_path), sr=None, mono=False)
                logger.info(f"File caricato con librosa: shape={y.shape}, sample_rate={sr}")
                
                # Converti in formato torchaudio
                if len(y.shape) == 1:
                    # Mono
                    wav = torch.from_numpy(y).unsqueeze(0)
                else:
                    # Multi-canale (stereo)
                    wav = torch.from_numpy(y)
                
                logger.info(f"Convertito in tensor: shape={wav.shape}")
            except Exception as e_librosa:
                error_str = str(e_librosa).lower()
                logger.error(f"Librosa fallito: {str(e_librosa)[:200]}")
                
                # Se librosa fallisce per FFmpeg, suggerisci installazione
                if "ffmpeg" in error_str or "no backend" in error_str:
                    raise Exception(
                        f"Impossibile caricare file MP3 '{input_path.name}'. "
                        f"Librosa richiede FFmpeg per formati compressi. "
                        f"SOLUZIONI: "
                        f"1) Converti il file in WAV (consigliato - più veloce), "
                        f"2) Installa FFmpeg (vedi INSTALLA_FFMPEG.md). "
                        f"Errore: {str(e_librosa)[:100]}"
                    )
                else:
                    raise Exception(
                        f"Errore durante caricamento file MP3: {str(e_librosa)[:150]}"
                    )
        else:
            # Per WAV/FLAC, prova con soundfile
            try:
                wav, sr = torchaudio.load(str(input_path), backend="soundfile")
                logger.info(f"File caricato con soundfile: shape={wav.shape}, sample_rate={sr}")
            except Exception as e1:
                logger.warning(f"Errore con soundfile: {str(e1)[:100]}")
                # Se soundfile fallisce, prova backend default
                try:
                    logger.info("Tento con backend default di torchaudio")
                    wav, sr = torchaudio.load(str(input_path))
                    logger.info(f"File caricato con backend default: shape={wav.shape}, sample_rate={sr}")
                except Exception as e_default:
                    logger.error(f"Tutti i metodi falliti: soundfile={str(e1)[:50]}, default={str(e_default)[:50]}")
                    raise Exception(
                        f"Impossibile caricare file audio '{input_path.name}'. "
                        f"Formato: {file_ext}. "
                        f"Prova a convertire il file in WAV. "
                        f"Errore: {str(e_default)[:100]}"
                    )
        
        if wav is None or sr is None:
            raise Exception("Impossibile caricare file audio")
        
        # Se stereo, estrai canale centrale (L-R) che spesso contiene la voce
        if wav.shape[0] == 2:
            logger.info("File stereo: estrazione canale centrale (L-R)")
            # Canale centrale = differenza tra L e R (spesso contiene la voce)
            vocals = (wav[0] - wav[1]) / 2
            vocals = vocals.unsqueeze(0)  # Aggiungi dimensione canale per mono
        elif wav.shape[0] == 1:
            # Se mono, usa direttamente
            logger.info("File mono: uso direttamente")
            vocals = wav
        else:
            # Se multi-canale, usa il primo canale
            logger.info(f"File multi-canale ({wav.shape[0]} canali): uso primo canale")
            vocals = wav[0:1]
        
        # Assicurati che vocals sia mono (1 canale)
        if vocals.shape[0] > 1:
            vocals = vocals[0:1]
        
        # Salva la traccia vocale isolata
        output_path = output_dir / f"{job_id}_vocals.wav"
        logger.info(f"Salvataggio traccia vocale in: {output_path}")
        
        # Crea la directory se non esiste
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Salva il file usando soundfile backend (non richiede torchcodec)
        try:
            torchaudio.save(str(output_path), vocals, sr, backend="soundfile")
            logger.info(f"File salvato con soundfile backend")
        except Exception as e_save:
            logger.warning(f"Errore salvataggio con soundfile: {str(e_save)[:100]}")
            # Se soundfile fallisce, prova con sox
            try:
                torchaudio.save(str(output_path), vocals, sr, backend="sox")
                logger.info(f"File salvato con sox backend")
            except Exception as e_sox:
                logger.warning(f"Errore salvataggio con sox: {str(e_sox)[:100]}")
                # Ultimo tentativo: salva direttamente con soundfile (libreria Python)
                try:
                    import soundfile as sf
                    import numpy as np
                    
                    # Converti tensor in numpy
                    if isinstance(vocals, torch.Tensor):
                        vocals_np = vocals.detach().cpu().numpy()
                    else:
                        vocals_np = np.array(vocals)
                    
                    # Assicurati che sia float32 e normalizzato tra -1.0 e 1.0
                    if vocals_np.dtype != np.float32:
                        vocals_np = vocals_np.astype(np.float32)
                    
                    # Normalizza se necessario (dovrebbe già essere normalizzato, ma controlliamo)
                    max_val = np.abs(vocals_np).max()
                    if max_val > 1.0:
                        vocals_np = vocals_np / max_val
                    
                    # Gestisci la forma: soundfile vuole (samples, channels)
                    if vocals_np.ndim == 1:
                        # Mono: (samples,) -> (samples, 1)
                        vocals_np = vocals_np.reshape(-1, 1)
                    elif vocals_np.ndim == 2:
                        if vocals_np.shape[0] < vocals_np.shape[1]:
                            # Probabilmente (channels, samples) -> trasponi a (samples, channels)
                            vocals_np = vocals_np.T
                        # Se già (samples, channels), va bene
                    else:
                        raise ValueError(f"Forma audio non supportata: {vocals_np.shape}")
                    
                    logger.info(f"Salvataggio con soundfile: shape={vocals_np.shape}, dtype={vocals_np.dtype}, sr={sr}")
                    sf.write(str(output_path), vocals_np, int(sr), format='WAV', subtype='PCM_16')
                    logger.info(f"File salvato con soundfile (libreria Python)")
                except Exception as e_sf:
                    logger.error(f"Errore dettagliato soundfile: {str(e_sf)}", exc_info=True)
                    raise Exception(
                        f"Impossibile salvare file vocale. "
                        f"Tutti i metodi falliti. Errore: {str(e_sf)[:150]}"
                    )
        
        # Verifica che il file sia stato salvato
        if not output_path.exists():
            raise FileNotFoundError(f"File vocale non salvato: {output_path}")
        
        file_size = output_path.stat().st_size
        logger.info(f"Traccia vocale (fallback) salvata con successo: {output_path} ({file_size} bytes)")
        
        return output_path
        
    except Exception as e:
        logger.error(f"Errore metodo fallback: {str(e)}", exc_info=True)
        raise Exception(f"Impossibile separare traccia vocale: {str(e)}")

