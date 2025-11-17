"""
Modulo per generare testo creativo da trascrizioni e fonemi.
Usa modelli NLP per trasformare input vocali in testo coerente.
"""
import logging
import os
import re
import random
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Flag per controllare se OpenAI API è disponibile
OPENAI_AVAILABLE = False
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI non disponibile. Installare con: pip install openai")

# Flag per controllare se modelli locali sono disponibili
LOCAL_MODEL_AVAILABLE = False
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    import torch
    LOCAL_MODEL_AVAILABLE = True
    logger.info("✅ Modelli locali disponibili (GPT-2)")
except ImportError:
    logger.warning("Modelli locali non disponibili. Installare con: pip install transformers torch")

# Flag per controllare se Ollama è disponibile
OLLAMA_AVAILABLE = False
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
try:
    import requests
    # Test se Ollama è in esecuzione
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            OLLAMA_AVAILABLE = True
            logger.info("✅ Ollama disponibile per generazione testo")
    except:
        pass
except ImportError:
    pass

# Modello Ollama da usare (default: llama3.2, buono per inglese)
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


def generate_lyrics(
    transcription_data: Dict,
    use_creative_mode: bool = True,
    style: str = "song_lyrics"
) -> str:
    """
    Genera testo creativo basato su trascrizione e fonemi.
    Usa informazioni sulle sezioni vocali rilevate per migliorare la generazione.
    
    Args:
        transcription_data: Dizionario con trascrizione da transcription.py
        use_creative_mode: Se True, usa NLP creativo per trasformare fonemi
        style: Stile del testo (song_lyrics, poem, prose)
    
    Returns:
        Testo finale generato
    """
    raw_text = transcription_data.get("text", "")
    phonemes = transcription_data.get("phonemes", "")
    has_clear_words = transcription_data.get("has_clear_words", False)
    
    # Informazioni sulle sezioni vocali (se disponibili)
    vocal_segments = transcription_data.get("vocal_segments", [])
    vocal_segments_count = transcription_data.get("vocal_segments_count", 0)
    vocal_percentage = transcription_data.get("vocal_percentage", 0)
    
    # Features audio avanzate (pitch, timing, envelope, melodia)
    audio_features = transcription_data.get("audio_features", {})
    audio_features_str = transcription_data.get("audio_features_str", "")
    
    # Prepara contesto aggiuntivo dalle sezioni vocali
    vocal_context = ""
    if vocal_segments_count > 0:
        vocal_context = f"Rilevate {vocal_segments_count} sezioni vocali ({vocal_percentage:.1f}% del brano). "
        if vocal_segments_count <= 5:
            vocal_context += f"Sezioni: {', '.join([f'{s:.1f}-{e:.1f}s' for s, e in vocal_segments[:5]])}. "
    
    # Aggiungi contesto audio avanzato
    if audio_features_str:
        vocal_context += f"\n\nAudio Analysis:\n{audio_features_str}"
    
    # Se ci sono parole chiare, usa direttamente o migliora
    if has_clear_words and raw_text:
        logger.info(f"Parole chiare rilevate, miglioramento testo... {vocal_context}")
        if use_creative_mode:
            return _enhance_text_with_ai(raw_text, style, vocal_context)
        else:
            return raw_text
    
    # Se non ci sono parole chiare, trasforma fonemi in testo creativo
    logger.info(f"Nessuna parola chiara, generazione da fonemi... {vocal_context}")
    if use_creative_mode:
        return _generate_from_phonemes(phonemes, raw_text, style, vocal_context)
    else:
        return f"[Fonemi rilevati: {phonemes}]"


def _enhance_text_with_ai(text: str, style: str, vocal_context: str = "") -> str:
    """
    Migliora un testo esistente usando AI.
    """
    if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
        try:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            context_info = f"\n\nContesto: {vocal_context}" if vocal_context else ""
            prompt = f"""Trasforma questo testo trascritto da una canzone in un testo di canzone coerente e poetico.
Mantieni il significato e lo stile originale, ma migliora la fluidità e la coerenza.

Testo originale:
{text}{context_info}

Genera un testo di canzone migliorato:"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Sei un esperto scrittore di testi musicali."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Errore OpenAI API: {str(e)}")
            return _fallback_enhancement(text)
    else:
        return _fallback_enhancement(text)


def _generate_from_phonemes(phonemes: str, raw_text: str, style: str, vocal_context: str = "") -> str:
    """
    Genera testo creativo da fonemi usando AI.
    """
    if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
        try:
            client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            context_info = f"\n\nContesto: {vocal_context}" if vocal_context else ""
            prompt = f"""Genera un testo di canzone creativo basato su questi suoni vocali.
I suoni rilevati sono: {phonemes}
Trascrizione grezza (possibilmente imprecisa): {raw_text}{context_info}

Crea un testo di canzone coerente e poetico che potrebbe corrispondere a questi suoni vocali.
Il testo deve essere fluido, emotivo e adatto a una canzone."""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Sei un creativo scrittore di testi musicali che trasforma suoni vocali in poesia."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.8
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Errore OpenAI API: {str(e)}")
            return _fallback_phoneme_generation(phonemes, raw_text)
    else:
        return _fallback_phoneme_generation(phonemes, raw_text)


def _fallback_enhancement(text: str) -> str:
    """
    Metodo fallback per miglioramento testo senza AI.
    Prova prima con Ollama, poi GPT-2 locale, poi formattazione base.
    """
    # Prova prima Ollama (migliore per inglese)
    if OLLAMA_AVAILABLE:
        try:
            # Estrai audio_context se disponibile
            audio_context = ""  # Sarà passato dalla funzione chiamante
            return _enhance_with_ollama(text, task="enhance", audio_context=audio_context)
        except Exception as e:
            logger.warning(f"Ollama fallito, provo GPT-2: {str(e)[:100]}")
    
    # Prova GPT-2 locale
    if LOCAL_MODEL_AVAILABLE:
        try:
            return _enhance_with_local_model(text, task="enhance")
        except Exception as e:
            logger.warning(f"Modello locale fallito, uso formattazione base: {str(e)[:100]}")
    
    logger.info("Uso metodo fallback base per miglioramento testo")
    # Semplice pulizia e formattazione
    text = text.strip()
    # Aggiungi line breaks ogni ~40 caratteri per sembrare più una canzone
    words = text.split()
    lines = []
    current_line = []
    char_count = 0
    
    for word in words:
        if char_count + len(word) > 40 and current_line:
            lines.append(" ".join(current_line))
            current_line = [word]
            char_count = len(word)
        else:
            current_line.append(word)
            char_count += len(word) + 1
    
    if current_line:
        lines.append(" ".join(current_line))
    
    return "\n".join(lines)


def _fallback_phoneme_generation(phonemes: str, raw_text: str) -> str:
    """
    Metodo fallback per generazione da fonemi senza AI.
    Prova prima con Ollama, poi GPT-2 locale, poi formattazione base.
    """
    # Usa raw_text se disponibile, altrimenti fonemi
    # Questo è il caso "la la la" - canto senza parole
    input_text = raw_text if raw_text and len(raw_text.strip()) > 5 else f"Vocal sounds (humming like 'la la la'): {phonemes[:200]}"
    
    # Estrai audio_context dal vocal_context
    audio_context = ""
    if "Audio Analysis:" in vocal_context:
        audio_context = vocal_context.split("Audio Analysis:")[1].strip()
    
    # Prova prima Ollama (migliore per inglese)
    if OLLAMA_AVAILABLE:
        try:
            return _enhance_with_ollama(input_text, task="generate", audio_context=audio_context)
        except Exception as e:
            logger.warning(f"Ollama fallito, provo GPT-2: {str(e)[:100]}")
    
    # Prova GPT-2 locale
    if LOCAL_MODEL_AVAILABLE:
        try:
            return _enhance_with_local_model(input_text, task="generate")
        except Exception as e:
            logger.warning(f"Modello locale fallito, uso formattazione base: {str(e)[:100]}")
    
    logger.info("Uso metodo fallback base per generazione da fonemi")
    
    if raw_text and len(raw_text.strip()) > 5:
        # Se c'è almeno un testo grezzo, usalo come base
        return _fallback_enhancement(raw_text)
    else:
        # Altrimenti, genera un messaggio descrittivo migliorato
        return _generate_creative_text_from_sounds(phonemes, raw_text)


# Cache globale per il modello locale (evita ricaricarlo ogni volta)
_local_model_cache = None
_local_tokenizer_cache = None


def _enhance_with_ollama(text: str, task: str = "enhance", audio_context: str = "") -> str:
    """
    Migliora o genera testo usando Ollama (modello locale in inglese).
    
    Args:
        text: Testo di input
        task: "enhance" per migliorare testo esistente, "generate" per generare da zero
    """
    try:
        import requests
        
        # Prepara prompt in inglese per generazione testo canzone
        # Include informazioni audio (pitch, timing, melodia) per adattare il testo alla melodia
        audio_info = f"\n\nMusical Information:\n{audio_context}" if audio_context else ""
        
        if task == "enhance":
            prompt = f"""Transform this transcribed song text into coherent and poetic song lyrics in English.
The lyrics must fit perfectly with the melody, rhythm, and musical structure provided below.

Original text:
{text}{audio_info}

IMPORTANT: The generated lyrics must:
- Match the pitch contour and rhythm
- Fit the tempo and timing
- Follow the melody structure
- Be in English
- Be poetic and emotional

Generate improved song lyrics that fit the melody:"""
        else:
            prompt = f"""Generate creative English song lyrics based on these vocal sounds (like "la la la" humming).
The lyrics must fit perfectly with the melody, rhythm, and musical structure provided below.

Vocal sounds detected:
{text}{audio_info}

IMPORTANT: The generated lyrics must:
- Match the pitch contour and rhythm exactly
- Fit the tempo ({audio_context.split('Tempo:')[1].split('BPM')[0].strip() if 'Tempo:' in audio_context else 'unknown'} BPM)
- Follow the melody structure and notes
- Match the timing and beat pattern
- Be in English
- Be poetic, emotional, and suitable for a song

Create coherent song lyrics that fit the melody perfectly:"""
        
        # Chiama Ollama API
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.8,
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            },
            timeout=60  # Timeout 60 secondi
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama API error: {response.status_code}")
        
        result = response.json()
        generated_text = result.get("response", "").strip()
        
        if not generated_text:
            raise Exception("Empty response from Ollama")
        
        # Pulisci il testo generato
        # Rimuovi eventuali prefissi comuni
        prefixes = ["Here are", "Here's", "The lyrics", "Song lyrics:"]
        for prefix in prefixes:
            if generated_text.lower().startswith(prefix.lower()):
                generated_text = generated_text[len(prefix):].strip()
                if generated_text.startswith(":"):
                    generated_text = generated_text[1:].strip()
        
        # Rimuovi ripetizioni eccessive
        lines = generated_text.split('\n')
        seen = set()
        unique_lines = []
        for line in lines:
            line_clean = line.strip().lower()
            if line_clean and line_clean not in seen and len(line_clean) > 3:
                seen.add(line_clean)
                unique_lines.append(line.strip())
        
        result_text = '\n'.join(unique_lines[:20])  # Max 20 righe
        
        if not result_text or len(result_text) < 20:
            # Se il risultato è troppo corto, usa formattazione base
            return _fallback_enhancement(text)
        
        logger.info(f"✅ Testo generato con Ollama ({len(result_text)} caratteri)")
        return result_text
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Errore connessione Ollama: {str(e)}")
        raise Exception(f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. Make sure Ollama is running.")
    except Exception as e:
        logger.error(f"Errore generazione con Ollama: {str(e)}")
        raise


def _get_local_model():
    """
    Carica il modello GPT-2 locale (con cache per evitare ricaricamenti).
    """
    global _local_model_cache, _local_tokenizer_cache
    
    if not LOCAL_MODEL_AVAILABLE:
        raise ImportError("Transformers non disponibile")
    
    if _local_model_cache is None:
        logger.info("📥 Caricamento modello GPT-2 locale (prima volta, ~500MB)...")
        try:
            # Usa GPT-2 small (più leggero e veloce)
            model_name = "gpt2"
            _local_tokenizer_cache = AutoTokenizer.from_pretrained(model_name)
            _local_model_cache = AutoModelForCausalLM.from_pretrained(model_name)
            
            # Imposta padding token se non esiste
            if _local_tokenizer_cache.pad_token is None:
                _local_tokenizer_cache.pad_token = _local_tokenizer_cache.eos_token
            
            logger.info("✅ Modello GPT-2 caricato con successo")
        except Exception as e:
            logger.error(f"Errore caricamento modello: {str(e)}")
            raise
    
    return _local_model_cache, _local_tokenizer_cache


def _enhance_with_local_model(text: str, task: str = "enhance") -> str:
    """
    Migliora o genera testo usando GPT-2 locale.
    
    Args:
        text: Testo di input
        task: "enhance" per migliorare testo esistente, "generate" per generare da zero
    """
    try:
        model, tokenizer = _get_local_model()
        
        # Prepara prompt in base al task
        if task == "enhance":
            # Migliora testo esistente
            prompt = f"Testo di una canzone:\n{text}\n\nVersione migliorata:\n"
        else:
            # Genera da suoni/input
            prompt = f"Testo di una canzone basato su:\n{text}\n\nTesto della canzone:\n"
        
        # Tokenizza
        inputs = tokenizer.encode(prompt, return_tensors="pt", max_length=512, truncation=True)
        
        # Genera (usa CPU per compatibilità, ma può usare GPU se disponibile)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = model.to(device)
        inputs = inputs.to(device)
        
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_length=inputs.shape[1] + 150,  # Aggiungi ~150 token
                num_return_sequences=1,
                temperature=0.8,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                repetition_penalty=1.2
            )
        
        # Decodifica
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Estrai solo la parte generata (dopo il prompt)
        if prompt in generated_text:
            generated_text = generated_text.split(prompt, 1)[1]
        
        # Pulisci e formatta
        generated_text = generated_text.strip()
        
        # Rimuovi ripetizioni eccessive
        lines = generated_text.split('\n')
        seen = set()
        unique_lines = []
        for line in lines:
            line_clean = line.strip().lower()
            if line_clean and line_clean not in seen and len(line_clean) > 3:
                seen.add(line_clean)
                unique_lines.append(line.strip())
        
        result = '\n'.join(unique_lines[:15])  # Max 15 righe
        
        if not result or len(result) < 20:
            # Se il risultato è troppo corto, usa formattazione base
            return _fallback_enhancement(text)
        
        logger.info(f"✅ Testo generato con modello locale ({len(result)} caratteri)")
        return result
        
    except Exception as e:
        logger.error(f"Errore generazione con modello locale: {str(e)}")
        raise


def _generate_creative_text_from_sounds(phonemes: str, raw_text: str) -> str:
    """
    Genera testo creativo dai suoni vocali usando pattern e trasformazioni intelligenti.
    """
    logger.info("Generazione testo creativo da suoni vocali")
    
    # Pattern comuni di fonemi -> parole italiane
    phoneme_patterns = {
        r'[aeiou]+': 'melodia',
        r'[mn]+': 'momento',
        r'[lr]+': 'amore',
        r'[st]+': 'stella',
        r'[kd]+': 'cuore',
    }
    
    # Se c'è raw_text, prova a estrarre parole
    if raw_text and len(raw_text.strip()) > 3:
        # Pulisci e migliora il testo grezzo
        cleaned = re.sub(r'[^\w\s]', '', raw_text.lower())
        words = cleaned.split()
        
        # Filtra parole troppo corte o comuni
        meaningful_words = [w for w in words if len(w) > 3 and w not in ['the', 'and', 'or', 'but', 'che', 'per', 'con']]
        
        if meaningful_words:
            # Crea versi basati sulle parole trovate
            verses = []
            for i in range(0, len(meaningful_words), 4):
                verse_words = meaningful_words[i:i+4]
                if verse_words:
                    verse = ' '.join(verse_words).capitalize()
                    verses.append(verse)
            
            if verses:
                result = '\n'.join(verses[:8])  # Max 8 versi
                return result
    
    # Altrimenti, genera testo poetico basato su pattern
    poetic_templates = [
        "Nel silenzio della notte\nsi alza una voce\nche canta l'amore",
        "Senti questa melodia\nche parla al cuore\ncon dolce armonia",
        "Una canzone nasce\ndai suoni del cuore\nche vibrano nell'aria",
        "Cantiamo insieme\nquesta melodia\nche unisce le anime",
    ]
    
    # Scegli template basato su lunghezza fonemi
    if len(phonemes) > 50:
        template = poetic_templates[0]
    elif len(phonemes) > 20:
        template = poetic_templates[1]
    else:
        template = poetic_templates[2]
    
    # Aggiungi info sui suoni rilevati
    result = f"{template}\n\n[Basato sui suoni vocali rilevati]"
    
    return result

