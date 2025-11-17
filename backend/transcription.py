"""
Modulo per la trascrizione audio usando Whisper.
Gestisce sia parole chiare che fonemi.
"""
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Flag per controllare se Whisper è disponibile
WHISPER_AVAILABLE = False
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    logger.warning("Whisper non disponibile. Installare con: pip install openai-whisper")


def transcribe_audio(
    audio_path: Path,
    model_name: str = "tiny",  # Cambiato da "base" a "tiny" per velocità
    language: Optional[str] = None
) -> Dict[str, any]:
    """
    Trascrive un file audio usando Whisper.
    
    Args:
        audio_path: Path del file audio
        model_name: Nome del modello Whisper (tiny, base, small, medium, large)
        language: Lingua del audio (None = auto-detect)
    
    Returns:
        Dizionario con trascrizione grezza, fonemi, e metadati
    """
    if not WHISPER_AVAILABLE:
        logger.warning("Whisper non disponibile, restituisco trascrizione mock")
        return {
            "text": "[Whisper non disponibile] Trascrizione mock per test",
            "phonemes": "[mock]",
            "language": "it",
            "confidence": 0.5,
            "segments": []
        }
    
    try:
        import torch
        
        # Determina device (prova GPU: CUDA, DirectML, poi CPU)
        device = "cpu"
        device_name = "CPU"
        
        # Prova CUDA (NVIDIA)
        if torch.cuda.is_available():
            device = "cuda"
            device_name = torch.cuda.get_device_name(0)
            logger.info("🚀 GPU NVIDIA rilevata!")
        else:
            # Su Windows, AMD GPU non è facilmente supportata da Whisper
            # Whisper supporta solo CUDA (NVIDIA) nativamente
            # Per AMD su Windows, usiamo CPU ottimizzata
            device = "cpu"
            device_name = "CPU"
            logger.info("ℹ️  GPU AMD rilevata ma Whisper supporta solo CUDA (NVIDIA)")
            logger.info("ℹ️  Usando CPU ottimizzata (modello 'tiny' per velocità)")
        
        logger.info(f"Caricamento modello Whisper: {model_name}")
        logger.info(f"🚀 Device: {device_name}")
        if device != "cpu":
            logger.info("⚡ GPU rilevata! Il processamento sarà più veloce!")
        else:
            logger.warning("⚠️  GPU non disponibile. Usando CPU (più lento)")
        
        logger.info("⚠️  NOTA: Se è la prima volta, il modello verrà scaricato (~39MB per 'tiny')")
        import time
        start_load = time.time()
        
        # Whisper supporta solo "cuda" (NVIDIA) o "cpu"
        whisper_device = device if device == "cuda" else "cpu"
        model = whisper.load_model(model_name, device=whisper_device)
        
        load_time = time.time() - start_load
        if load_time > 5:
            logger.info(f"✅ Modello caricato/scaricato in {load_time:.1f} secondi")
        else:
            logger.info(f"✅ Modello caricato in {load_time:.1f} secondi")
        
        logger.info(f"Trascrizione audio: {audio_path}")
        logger.info(f"⏳ Trascrizione in corso su {device_name}...")
        if device != "cpu":
            logger.info("⚡ GPU attiva - processamento accelerato!")
        
        # Trascrivi con Whisper (ottimizzato per velocità)
        start_transcribe = time.time()
        result = model.transcribe(
            str(audio_path),
            language=language,
            task="transcribe",
            verbose=False,
            # Ottimizzazioni per velocità
            fp16=(device != "cpu"),  # Usa fp16 su GPU (se supportato), fp32 su CPU
            beam_size=1,  # Beam size minimo per velocità (default è 5)
            best_of=1,  # Numero di tentativi minimo
            temperature=0,  # Temperatura 0 per velocità (più deterministica)
            compression_ratio_threshold=2.4,  # Threshold per compressione
            logprob_threshold=-1.0,  # Threshold per probabilità
            no_speech_threshold=0.6,  # Threshold per rilevamento voce
        )
        transcribe_time = time.time() - start_transcribe
        speedup = "⚡" if device != "cpu" else ""
        logger.info(f"✅ Trascrizione completata in {transcribe_time:.1f} secondi {speedup}")
        
        # Estrai informazioni
        text = result.get("text", "").strip()
        language_detected = result.get("language", "unknown")
        segments = result.get("segments", [])
        
        # Calcola confidence media dai segmenti
        confidences = [seg.get("no_speech_prob", 0) for seg in segments]
        avg_confidence = 1 - (sum(confidences) / len(confidences)) if confidences else 0.5
        
        # Estrai fonemi approssimati (usando caratteri fonetici semplici)
        # Nota: Whisper non restituisce fonemi direttamente, quindi usiamo una
        # rappresentazione semplificata basata sul testo
        phonemes = _extract_phonemes_approximation(text)
        
        logger.info(f"Trascrizione completata. Lingua: {language_detected}, Testo: {text[:50]}...")
        
        return {
            "text": text,
            "phonemes": phonemes,
            "language": language_detected,
            "confidence": avg_confidence,
            "segments": segments,
            "has_clear_words": len(text.split()) > 3 and avg_confidence > 0.3
        }
        
    except Exception as e:
        logger.error(f"Errore durante trascrizione: {str(e)}")
        return {
            "text": f"[Errore trascrizione: {str(e)}]",
            "phonemes": "[errore]",
            "language": "unknown",
            "confidence": 0.0,
            "segments": [],
            "has_clear_words": False
        }


def _extract_phonemes_approximation(text: str) -> str:
    """
    Approssimazione semplice di fonemi dal testo.
    In una versione avanzata, si potrebbe usare un modello fonetico dedicato.
    """
    # Semplificazione: rimuovi spazi e converti in rappresentazione fonetica base
    # Questo è solo un placeholder - un sistema reale userebbe IPA o un modello fonetico
    phonemes = text.lower().replace(" ", "-")
    return phonemes

