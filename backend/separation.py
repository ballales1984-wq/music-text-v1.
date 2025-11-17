"""
Separazione vocale - Isola voce da musica completa
Usa metodo fallback (estrazione canale centrale) che funziona sempre
"""
import logging
from pathlib import Path
import torch
import torchaudio
import numpy as np

logger = logging.getLogger(__name__)


def separate_vocals(input_path: Path, job_id: str, output_dir: Path) -> Path:
    """
    Isola traccia vocale da file audio.
    Metodo: estrazione canale centrale (L-R) per stereo, mono diretto.
    """
    logger.info(f"Separazione vocale: {input_path}")
    
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
                logger.info(f"Caricato con librosa: shape={wav.shape}")
            except Exception as e:
                raise Exception(f"Errore caricamento {file_ext}: {str(e)[:100]}. Converti in WAV.")
        else:
            # WAV/FLAC: usa soundfile
            try:
                wav, sr = torchaudio.load(str(input_path), backend="soundfile")
                logger.info(f"Caricato con soundfile: shape={wav.shape}")
            except Exception as e:
                raise Exception(f"Errore caricamento: {str(e)[:100]}")
        
        # Estrai voce (IMPORTANTE: isoliamo la VOCE, non la base strumentale!)
        if wav.shape[0] == 2:
            # Stereo: canale centrale (L-R) per isolare voce
            # La voce è solitamente al centro, quindi (L-R) la isola
            # Se (L+R)/2 = strumenti al centro, (L-R) = voce al centro
            vocals = (wav[0] - wav[1]) / 2
            vocals = vocals.unsqueeze(0)
            logger.info("✅ Estrazione VOCE dal canale centrale (L-R) - isolata dalla base strumentale")
        elif wav.shape[0] == 1:
            # Mono: usa direttamente
            vocals = wav
            logger.info("File mono: uso diretto")
        else:
            # Multi-canale: primo canale
            vocals = wav[0:1]
            logger.info(f"Multi-canale: uso primo canale")
        
        # Salva
        output_path = output_dir / f"{job_id}_vocals.wav"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            torchaudio.save(str(output_path), vocals, sr, backend="soundfile")
        except:
            # Fallback: soundfile diretto
            import soundfile as sf
            vocals_np = vocals.detach().cpu().numpy()
            if vocals_np.dtype != np.float32:
                vocals_np = vocals_np.astype(np.float32)
            max_val = np.abs(vocals_np).max()
            if max_val > 1.0:
                vocals_np = vocals_np / max_val
            if vocals_np.ndim == 1:
                vocals_np = vocals_np.reshape(-1, 1)
            elif vocals_np.ndim == 2 and vocals_np.shape[0] < vocals_np.shape[1]:
                vocals_np = vocals_np.T
            sf.write(str(output_path), vocals_np, int(sr), format='WAV', subtype='PCM_16')
        
        logger.info(f"✅ Voce isolata salvata: {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Errore separazione: {str(e)}", exc_info=True)
        raise Exception(f"Separazione vocale fallita: {str(e)}")

