"""
Orchestratore per il processo completo di generazione testo
Coordina tutte le funzioni, gestisce errori e implementa retry automatico
"""
import logging
from pathlib import Path
from typing import Dict, Optional, Callable, Any, Tuple
import time
from functools import wraps

logger = logging.getLogger(__name__)


class ProcessingOrchestrator:
    """
    Orchestratore che coordina tutto il processo di generazione testo.
    Gestisce errori, retry, fallback e coordinamento tra funzioni.
    """
    
    def __init__(self, job_id: str, input_path: Path, output_dir: Path, upload_dir: Path):
        self.job_id = job_id
        self.input_path = input_path
        self.output_dir = output_dir
        self.upload_dir = upload_dir
        self.state = {
            "vocal_path": None,
            "instrumental_path": None,
            "transcription": None,
            "audio_features": None,
            "instrumental_features": None,
            "metric_grid": None,
            "final_result": None,
            "errors": [],
            "warnings": []
        }
    
    def execute_pipeline(self, status_callback: Optional[Callable] = None) -> Dict:
        """
        Esegue l'intera pipeline con gestione errori e retry.
        
        Args:
            status_callback: Funzione chiamata per aggiornare lo stato (progress, step, etc.)
        
        Returns:
            Dict con risultati completi o None se fallito
        """
        logger.info(f"[{self.job_id}] 🎼 Avvio orchestratore pipeline...")
        
        try:
            # STEP 0: Separazione vocale
            self._update_status(status_callback, 0, 4, "Separazione vocale", 10)
            self._execute_with_retry(
                self._step_separation,
                max_retries=2,
                step_name="Separazione vocale"
            )
            
            # STEP 1: Trascrizione
            self._update_status(status_callback, 1, 4, "Trascrizione Whisper", 20)
            self._execute_with_retry(
                self._step_transcription,
                max_retries=2,
                step_name="Trascrizione"
            )
            
            # STEP 1.5: Pulizia testo
            self._update_status(status_callback, 1.5, 4, "Pulizia testo", 30)
            self._execute_with_retry(
                self._step_text_cleaning,
                max_retries=1,
                step_name="Pulizia testo"
            )
            
            # STEP 1.7: Analisi audio avanzata
            self._update_status(status_callback, 1.7, 4, "Analisi audio avanzata", 35)
            self._execute_with_retry(
                self._step_audio_analysis,
                max_retries=2,
                step_name="Analisi audio",
                can_skip=True  # Può essere saltato se fallisce
            )
            
            # STEP 2: Estrazione struttura
            self._update_status(status_callback, 2, 4, "Estrazione struttura", 60)
            self._execute_with_retry(
                self._step_structure_extraction,
                max_retries=1,
                step_name="Estrazione struttura"
            )
            
            # STEP 3: Generazione testo
            self._update_status(status_callback, 3, 4, "Generazione testo", 80)
            self._execute_with_retry(
                self._step_text_generation,
                max_retries=2,
                step_name="Generazione testo"
            )
            
            # Completato
            self._update_status(status_callback, 4, 4, "Completato", 100)
            logger.info(f"[{self.job_id}] ✅ Pipeline completata con successo")
            
            return self._build_final_result()
            
        except Exception as e:
            logger.error(f"[{self.job_id}] ❌ Pipeline fallita: {str(e)}", exc_info=True)
            self.state["errors"].append(str(e))
            return None
    
    def _execute_with_retry(self, func: Callable, max_retries: int = 2, 
                           step_name: str = "", can_skip: bool = False, **kwargs):
        """
        Esegue una funzione con retry automatico.
        
        Args:
            func: Funzione da eseguire
            max_retries: Numero massimo di tentativi
            step_name: Nome dello step per logging
            can_skip: Se True, può essere saltato se fallisce
            **kwargs: Argomenti da passare alla funzione
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"[{self.job_id}] 🔄 {step_name} - Tentativo {attempt + 1}/{max_retries + 1}")
                result = func(**kwargs)
                logger.info(f"[{self.job_id}] ✅ {step_name} completato")
                return result
                
            except Exception as e:
                last_error = e
                error_msg = str(e)
                logger.warning(f"[{self.job_id}] ⚠️  {step_name} fallito (tentativo {attempt + 1}/{max_retries + 1}): {error_msg}")
                
                if attempt < max_retries:
                    # Aspetta prima di ritentare (backoff esponenziale)
                    wait_time = 2 ** attempt
                    logger.info(f"[{self.job_id}] ⏳ Attendo {wait_time}s prima di ritentare...")
                    time.sleep(wait_time)
                else:
                    # Ultimo tentativo fallito
                    if can_skip:
                        logger.warning(f"[{self.job_id}] ⚠️  {step_name} fallito ma può essere saltato, continuo...")
                        self.state["warnings"].append(f"{step_name} saltato: {error_msg}")
                        return None
                    else:
                        logger.error(f"[{self.job_id}] ❌ {step_name} fallito dopo {max_retries + 1} tentativi")
                        self.state["errors"].append(f"{step_name}: {error_msg}")
                        raise Exception(f"{step_name} fallito: {error_msg}")
        
        # Non dovrebbe mai arrivare qui, ma per sicurezza
        if can_skip:
            return None
        raise last_error
    
    def _step_separation(self):
        """Step 0: Separazione vocale."""
        import time
        from separation import separate_vocals_and_instrumental, SPLEETER_AVAILABLE, USE_SPLEETER
        
        start_time = time.time()
        
        logger.info(f"[{self.job_id}] 🎵 Inizio separazione vocale...")
        logger.info(f"[{self.job_id}] 📊 Spleeter disponibile: {SPLEETER_AVAILABLE}, Abilitato: {USE_SPLEETER}")
        
        if not SPLEETER_AVAILABLE:
            logger.warning(f"[{self.job_id}] ⚠️  Spleeter NON INSTALLATO - separazione sarà veloce ma MENO PRECISA")
            logger.warning(f"[{self.job_id}]    💡 Per installare: pip install spleeter")
        elif not USE_SPLEETER:
            logger.warning(f"[{self.job_id}] ⚠️  Spleeter DISABILITATO - uso metodi semplici (veloce)")
        else:
            logger.info(f"[{self.job_id}] 🎯 Uso Spleeter (ML) - richiede 30-60 secondi...")
        
        vocal_path, instrumental_path = separate_vocals_and_instrumental(
            self.input_path, 
            self.job_id, 
            self.output_dir
        )
        
        elapsed = time.time() - start_time
        self.state["vocal_path"] = vocal_path
        self.state["instrumental_path"] = instrumental_path
        
        logger.info(f"[{self.job_id}] ✅ Separazione completata in {elapsed:.1f}s: voce={vocal_path.name}, base={instrumental_path.name}")
        
        if elapsed < 5:
            logger.warning(f"[{self.job_id}] ⚠️  Separazione troppo veloce ({elapsed:.1f}s) - probabilmente usato metodo semplice")
            logger.warning(f"[{self.job_id}]    💡 Per separazione migliore, installa Spleeter: pip install spleeter")
        
        return True
    
    def _step_transcription(self):
        """Step 1: Trascrizione Whisper."""
        from transcription import transcribe_audio
        
        audio_for_transcription = self.state["vocal_path"] or self.input_path
        transcription = transcribe_audio(audio_for_transcription)
        
        if not transcription.get("text") or len(transcription.get("text", "").strip()) < 3:
            raise Exception("Trascrizione vuota o troppo corta")
        
        self.state["transcription"] = transcription
        logger.info(f"[{self.job_id}] ✅ Trascrizione: {len(transcription.get('text', ''))} caratteri")
        return True
    
    def _step_text_cleaning(self):
        """
        Step 1.5: Pulizia e filtraggio testo (SOLO per statistiche/display).
        
        IMPORTANTE: NON rimuove ripetizioni dalla trascrizione originale!
        La trascrizione originale deve essere preservata INTATTA per la generazione del testo.
        L'IA ha bisogno di vedere TUTTA la trascrizione (anche con ripetizioni) per:
        - Capire la struttura della canzone (chorus, versi)
        - Generare testo corretto basato su tutti i suoni/vocalizzi
        - Rispettare la metrica completa della canzone
        
        La pulizia viene fatta SOLO sul testo FINALE generato, non sulla trascrizione originale.
        """
        from text_cleaner import clean_and_filter_text, validate_text_quality
        
        raw_text = self.state["transcription"].get("text", "")
        if not raw_text:
            raise Exception("Nessun testo da pulire")
        
        # Calcola statistiche di pulizia (per display), ma NON modifica la trascrizione originale
        cleaning_result = clean_and_filter_text(raw_text)
        self.state["cleaned_text"] = cleaning_result.get("cleaned_text", raw_text)
        self.state["cleaning_stats"] = cleaning_result.get("statistics", {})
        
        logger.info(f"[{self.job_id}] ✅ Statistiche pulizia: {cleaning_result.get('removed_repetitions', 0)} ripetizioni (solo per display)")
        logger.info(f"[{self.job_id}] 📝 IMPORTANTE: Trascrizione originale preservata INTATTA per generazione testo")
        return True
    
    def _step_audio_analysis(self):
        """Step 1.7: Analisi audio avanzata."""
        from audio_analysis import analyze_audio_features
        from rhythmic_analysis import analyze_rhythmic_features
        
        # Analizza voce
        audio_for_analysis = self.state["vocal_path"] or self.input_path
        audio_features = analyze_audio_features(audio_for_analysis)
        self.state["audio_features"] = audio_features
        
        # Analizza base strumentale se disponibile
        if self.state["instrumental_path"] and self.state["instrumental_path"] != self.input_path:
            try:
                instrumental_features = analyze_rhythmic_features(self.state["instrumental_path"])
                self.state["instrumental_features"] = instrumental_features
                logger.info(f"[{self.job_id}] ✅ Analisi base: BPM={instrumental_features.get('tempo', 0):.1f}")
            except Exception as e:
                logger.warning(f"[{self.job_id}] ⚠️  Analisi base fallita: {e}")
        
        logger.info(f"[{self.job_id}] ✅ Analisi audio: {len(audio_features.get('rhythm', {}).get('onset_times', []))} onset")
        return True
    
    def _step_structure_extraction(self):
        """Step 2: Estrazione struttura e sillabe."""
        from text_structure import extract_structure
        from syllable_counter import count_syllables_in_text, get_key_words
        from audio_structure_analysis import analyze_audio_structure
        
        # IMPORTANTE: Usa SEMPRE la trascrizione originale, non quella pulita
        # L'IA ha bisogno di vedere TUTTA la trascrizione per capire la struttura completa
        text_to_process = self.state["transcription"].get("text", "")
        if not text_to_process:
            raise Exception("Nessun testo per estrazione struttura")
        
        # Struttura testo
        text_structure = extract_structure(text_to_process)
        
        # Struttura audio
        audio_structure = analyze_audio_structure(self.input_path)
        
        # Sillabe
        syllables_info = count_syllables_in_text(text_to_process)
        
        # Parole chiave
        key_words = get_key_words(text_to_process, max_words=10)
        
        self.state["structure"] = text_structure
        self.state["audio_structure"] = audio_structure
        self.state["syllables_info"] = syllables_info
        self.state["key_words"] = key_words
        
        logger.info(f"[{self.job_id}] ✅ Struttura: {text_structure.get('total_lines', 0)} righe, {syllables_info.get('total_syllables', 0)} sillabe")
        return True
    
    def _step_text_generation(self):
        """
        Step 3: Generazione testo.
        
        PROCESSO:
        1. PRIMA: Trascrizione vocale (già fatto in _step_transcription)
           - Trascrive la traccia vocale isolata (anche se sono solo suoni/vocalizzi)
           - Estrae timing, durata, pitch dalla voce
           
        2. POI: Crea schema metrico dalla trascrizione vocale
           - Usa la trascrizione vocale per creare una griglia metrica
           - La griglia contiene: timing, durata sillabe, accenti, pitch
           - Identifica quali parole/frasi trascritte sono valide in inglese
           
        3. INFINE: Genera testo basato sullo schema
           - Sostituisce parole non inglesi con frasi inglesi che si adattano alla metrica
           - Genera testo coerente che rispetta timing, sillabe, accenti della voce originale
        """
        from metric_grid_generator import create_metric_grid_from_vocal, generate_text_from_grid
        from lyrics_generator import generate_lyrics_simple
        
        # Verifica che abbiamo la trascrizione vocale (necessaria per creare lo schema)
        if not self.state.get("transcription"):
            raise Exception("Trascrizione vocale mancante - necessario per creare schema metrico")
        
        # Prova approccio griglia metrica se possibile
        use_metric_grid = (
            self.state.get("audio_features") and 
            self.state["audio_features"].get("tempo") and 
            self.state["audio_features"].get("rhythm", {}).get("onset_times")
        )
        
        if use_metric_grid:
            try:
                logger.info(f"[{self.job_id}] 🎯 Uso approccio GRIGLIA METRICA")
                logger.info(f"[{self.job_id}] 📝 Creazione schema metrico dalla trascrizione vocale...")
                
                # Crea griglia metrica dalla trascrizione vocale
                # La trascrizione vocale (anche se sbagliata/non ha significato) viene usata
                # per creare lo schema metrico (timing, durata, sillabe, accenti)
                metric_grid = create_metric_grid_from_vocal(
                    self.state["audio_features"],  # Features audio dalla voce (tempo, pitch, ritmo)
                    self.state["transcription"]     # Trascrizione vocale (anche se sono solo suoni)
                )
                self.state["metric_grid"] = metric_grid
                
                logger.info(f"[{self.job_id}] ✅ Schema metrico creato: {metric_grid.get('total_slots', 0)} slot, {metric_grid.get('total_lines', 0)} righe")
                
                # Genera testo
                grid_result = generate_text_from_grid(
                    metric_grid,
                    use_ai=True,
                    instrumental_features=self.state.get("instrumental_features"),
                    transcription=self.state["transcription"]
                )
                
                # Converti in formato compatibile
                grid_lines = grid_result.get("lines", [])
                if grid_lines:
                    # IMPORTANTE: NON rimuovere righe! L'IA ha già generato testo corretto per ogni riga.
                    # Usa le righe generate così come sono (solo pulizia formattazione minima)
                    grid_lines_cleaned = [line.strip() for line in grid_lines if line and len(line.strip()) >= 3]
                    
                    # Se la pulizia ha rimosso righe, ripristina TUTTE
                    if len(grid_lines_cleaned) < len(grid_lines):
                        logger.warning(f"[{self.job_id}] ⚠️  Righe rimosse durante pulizia: {len(grid_lines)} -> {len(grid_lines_cleaned)}, ripristino TUTTE")
                        grid_lines_cleaned = [line.strip() for line in grid_lines if line and len(line.strip()) >= 3]
                    
                    variants = []
                    for i, line in enumerate(grid_lines_cleaned):
                        variants.append({
                            "id": i + 1,
                            "full_text": "\n".join(grid_lines_cleaned),
                            "verses": grid_lines_cleaned[:-1] if len(grid_lines_cleaned) > 1 else grid_lines_cleaned,
                            "chorus": [grid_lines_cleaned[-1]] if len(grid_lines_cleaned) > 1 else [],
                            "preview": "\n".join(grid_lines_cleaned[:2]) if len(grid_lines_cleaned) >= 2 else grid_lines_cleaned[0] if grid_lines_cleaned else ""
                        })
                    
                    self.state["final_result"] = {
                        "variants": variants[:3],
                        "selected": 0,
                        "total": min(3, len(variants)),
                        "method": "metric_grid",
                        "replacements": grid_result.get("replacements", []),
                        "song_context": grid_result.get("song_context", {}),
                        "song_theme": grid_result.get("song_theme", "unknown")
                    }
                    logger.info(f"[{self.job_id}] ✅ Testo generato con griglia metrica")
                    return True
                    
            except Exception as e:
                logger.warning(f"[{self.job_id}] ⚠️  Griglia metrica fallita: {e}, uso metodo tradizionale")
                self.state["warnings"].append(f"Griglia metrica fallita, uso metodo tradizionale: {str(e)}")
        
        # Approccio tradizionale (fallback)
        logger.info(f"[{self.job_id}] 🎯 Uso approccio TRADIZIONALE")
        
        # IMPORTANTE: Usa SEMPRE la trascrizione originale, non quella pulita
        # L'IA ha bisogno di vedere TUTTA la trascrizione (anche con ripetizioni) per generare il testo corretto
        generation_data = {
            "text": self.state["transcription"].get("text", ""),  # Trascrizione ORIGINALE, non pulita
            "structure": self.state["structure"],
            "syllables": self.state["syllables_info"],
            "key_words": self.state["key_words"],
            "audio_structure": self.state["audio_structure"]
        }
        
        lyrics_result = generate_lyrics_simple(generation_data, num_variants=3)
        lyrics_result["method"] = "traditional_ai"
        
        self.state["final_result"] = lyrics_result
        logger.info(f"[{self.job_id}] ✅ Testo generato con metodo tradizionale")
        return True
    
    def _build_final_result(self) -> Dict:
        """Costruisce risultato finale completo."""
        if not self.state["final_result"]:
            raise Exception("Nessun risultato generato")
        
        lyrics_result = self.state["final_result"].copy()
        
        # Costruisci risultato nel formato atteso
        result = {
            "job_id": self.job_id,
            "lyrics_variants": lyrics_result,
            "raw_transcription": {
                "text": self.state["transcription"].get("text", ""),
                "cleaned_text": self.state.get("cleaned_text"),
                "cleaning_stats": self.state.get("cleaning_stats", {}),
                "language": self.state["transcription"].get("language", "unknown"),
                "confidence": self.state["transcription"].get("confidence", 0.5)
            },
            "structure": self.state.get("structure", {}),
            "syllables": {
                "total": self.state.get("syllables_info", {}).get("total_syllables", 0),
                "per_line": self.state.get("syllables_info", {}).get("lines_syllables", [])
            },
            "key_words": self.state.get("key_words", []),
            "original_audio_url": f"/audio/{self.job_id}",
            "vocal_audio_url": f"/audio/{self.job_id}/vocals" if self.state.get("vocal_path") else None,
            "instrumental_audio_url": f"/audio/{self.job_id}/instrumental" if self.state.get("instrumental_path") else None,
            "processing_info": {
                "method_used": lyrics_result.get("method", "unknown"),
                "warnings": self.state["warnings"],
                "errors": self.state["errors"]
            }
        }
        
        return result
    
    def _update_status(self, callback: Optional[Callable], step: float, total_steps: int, 
                      current_step: str, progress: int):
        """Aggiorna stato se callback disponibile."""
        if callback:
            try:
                callback({
                    "status": "processing",
                    "step": step,
                    "total_steps": total_steps,
                    "current_step": current_step,
                    "progress": progress
                })
            except:
                pass


def retry_on_failure(max_retries: int = 2, can_skip: bool = False, delay: float = 1.0):
    """
    Decorator per retry automatico su funzioni.
    
    Args:
        max_retries: Numero massimo di tentativi
        can_skip: Se True, può essere saltato se fallisce
        delay: Delay tra tentativi (secondi)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries:
                        time.sleep(delay * (2 ** attempt))  # Backoff esponenziale
                    elif can_skip:
                        logger.warning(f"Funzione {func.__name__} fallita ma può essere saltata")
                        return None
            
            if can_skip:
                return None
            raise last_error
        
        return wrapper
    return decorator

