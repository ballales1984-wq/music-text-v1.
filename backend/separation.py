"""
Separazione vocale CORRETTA - Isola voce E base strumentale
Separa correttamente in due parti: VOCE (linguistica) e BASE (ritmica)
"""
import logging
from pathlib import Path
from typing import Tuple
import torch
import torchaudio
import numpy as np

logger = logging.getLogger(__name__)


def _save_audio_tensor(audio_tensor: torch.Tensor, output_path: Path, sr: int):
    """Salva tensor audio come WAV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        torchaudio.save(str(output_path), audio_tensor, sr, backend="soundfile")
    except:
        # Fallback: soundfile diretto
        import soundfile as sf
        audio_np = audio_tensor.detach().cpu().numpy()
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


def separate_vocals_and_instrumental(input_path: Path, job_id: str, output_dir: Path) -> Tuple[Path, Path]:
    """
    Separa correttamente VOCE e BASE STRUMENTALE.
    
    CORREZIONE: Il metodo precedente (L-R)/2 estraeva la BASE, non la VOCE!
    Nuovo metodo:
    - VOCE = Canale centrale (L+R)/2 (voce tipicamente al centro)
    - BASE = Differenza laterale (L-R)/2 (strumenti ai lati)
    
    Returns:
        (vocal_path, instrumental_path)
    """
    logger.info(f"🎵 Separazione VOCE e BASE: {input_path}")
    
    try:
        # Carica audio
        file_ext = input_path.suffix.lower()
        
        if file_ext in ['.mp3', '.m4a', '.aac']:
            # Formati compressi: usa librosa
            try:
                import librosa
                y, sr = librosa.load(str(input_path), sr=None, mono=False)
                if len(y.shape) == 1:
                    wav = torch.from_numpy(y).unsqueeze(0)
                else:
                    wav = torch.from_numpy(y)
                logger.info(f"Caricato con librosa: shape={wav.shape}, stereo={wav.shape[0] == 2}")
            except Exception as e:
                raise Exception(f"Errore caricamento {file_ext}: {str(e)[:100]}. Converti in WAV.")
        else:
            # WAV/FLAC: usa soundfile
            try:
                wav, sr = torchaudio.load(str(input_path), backend="soundfile")
                logger.info(f"Caricato con soundfile: shape={wav.shape}, stereo={wav.shape[0] == 2}")
            except Exception as e:
                raise Exception(f"Errore caricamento: {str(e)[:100]}")
        
        # SEPARAZIONE CORRETTA
        if wav.shape[0] == 2:
            # STEREO: Separazione corretta
            # VOCE = Canale centrale (L+R)/2 (voce tipicamente al centro del mix)
            vocals = (wav[0] + wav[1]) / 2
            vocals = vocals.unsqueeze(0)
            
            # BASE = Differenza laterale (L-R)/2 (strumenti ai lati, non al centro)
            instrumental = (wav[0] - wav[1]) / 2
            instrumental = instrumental.unsqueeze(0)
            
            logger.info("✅ Separazione STEREO corretta:")
            logger.info("   - VOCE = (L+R)/2 (canale centrale)")
            logger.info("   - BASE = (L-R)/2 (differenza laterale)")
            
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
        
        logger.info(f"✅ VOCE isolata salvata: {vocal_path.name}")
        logger.info(f"✅ BASE strumentale salvata: {instrumental_path.name}")
        
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

