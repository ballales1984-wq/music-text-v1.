"""
Denoise e restoration vocale professionale
Rimuove rumore, click, hum dalla traccia vocale isolata
"""
import logging
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

NOISEREDUCE_AVAILABLE = False
try:
    import noisereduce as nr
    NOISEREDUCE_AVAILABLE = True
    logger.info("✅ noisereduce disponibile per denoise")
except ImportError:
    logger.warning("noisereduce non disponibile - salto denoise")


def denoise_vocals(vocals_path: Path, output_path: Path) -> Path:
    """
    Applica denoise professionale alla traccia vocale.
    Rimuove rumore, click, hum, migliora qualità.
    """
    logger.info(f"🔇 Denoise vocale: {vocals_path.name}")
    
    if not NOISEREDUCE_AVAILABLE:
        logger.warning("noisereduce non disponibile - salto denoise")
        # Copia file originale
        import shutil
        shutil.copy2(vocals_path, output_path)
        return output_path
    
    try:
        import librosa
        import soundfile as sf
        
        # Carica audio
        y, sr = librosa.load(str(vocals_path), sr=None, mono=True)
        logger.info(f"   Audio caricato: {len(y)/sr:.2f}s, {sr}Hz")
        
        # Denoise con noisereduce
        logger.info("   ⏳ Applicazione denoise...")
        y_denoised = nr.reduce_noise(
            y=y,
            sr=sr,
            stationary=False,  # Rumore non stazionario (voce)
            prop_decrease=0.8  # Rimuove 80% del rumore
        )
        
        # Normalizza
        max_val = np.abs(y_denoised).max()
        if max_val > 1.0:
            y_denoised = y_denoised / max_val
        
        # Salva
        output_path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output_path), y_denoised, sr)
        
        logger.info(f"✅ Denoise completato: {output_path.name}")
        return output_path
        
    except Exception as e:
        logger.error(f"Errore denoise: {str(e)[:100]}")
        # Fallback: copia originale
        import shutil
        shutil.copy2(vocals_path, output_path)
        return output_path

