"""
Generatore di testo in inglese semplificato
Genera testo in inglese ascoltando la traccia vocale della canzone
"""
import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

# Check AI disponibili
OLLAMA_AVAILABLE = False
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
# Usa llama3 se disponibile (migliore qualità), altrimenti llama3.2
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

def _check_ollama():
    """Verifica Ollama e seleziona il miglior modello disponibile."""
    global OLLAMA_AVAILABLE, OLLAMA_MODEL
    
    try:
        import requests
        # Verifica Ollama con retry (più affidabile)
        for attempt in range(3):
            try:
                response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
                if response.status_code == 200:
                    OLLAMA_AVAILABLE = True
                    # Verifica quale modello è disponibile
                    models = response.json().get("models", [])
                    available_models = [m.get("name", "") for m in models]
                    
                    # Preferisci llama3 se disponibile (migliore qualità)
                    if any("llama3:" in m and "llama3.2" not in m for m in available_models):
                        OLLAMA_MODEL = "llama3"
                        logger.info(f"✅ Ollama disponibile - Usando llama3 (migliore qualità)")
                    elif any("llama3.2:" in m for m in available_models):
                        OLLAMA_MODEL = "llama3.2"
                        logger.info(f"✅ Ollama disponibile - Usando llama3.2")
                    elif any("gemma" in m.lower() for m in available_models):
                        OLLAMA_MODEL = "gemma3:1b"
                        logger.info(f"✅ Ollama disponibile - Usando gemma3:1b")
                    else:
                        # Usa il primo modello disponibile
                        if available_models:
                            OLLAMA_MODEL = available_models[0].split(":")[0]
                            logger.info(f"✅ Ollama disponibile - Usando {OLLAMA_MODEL}")
                    
                    return True
            except Exception as e:
                if attempt < 2:
                    import time
                    time.sleep(1)
                else:
                    logger.warning(f"⚠️ Ollama non raggiungibile dopo 3 tentativi: {e}")
                    return False
    except ImportError:
        logger.warning("⚠️ requests non disponibile - Ollama non può essere usato")
        return False
    except Exception as e:
        logger.warning(f"⚠️ Errore verifica Ollama: {e}")
        return False
    
    return False

# Verifica Ollama all'avvio
_check_ollama()

OPENAI_AVAILABLE = False
try:
    import openai
    if os.getenv("OPENAI_API_KEY"):
        OPENAI_AVAILABLE = True
        logger.info("✅ OpenAI disponibile")
except:
    pass


def generate_english_text_from_vocals(transcription_data: Dict) -> str:
    """
    Genera testo in inglese ascoltando la traccia vocale.
    
    Args:
        transcription_data: Dati dalla trascrizione Whisper della voce
        
    Returns:
        Testo in inglese generato
    """
    raw_text = transcription_data.get("text", "").strip()
    phonemes = transcription_data.get("phonemes", "").strip()
    has_clear_words = transcription_data.get("has_clear_words", False)
    language = transcription_data.get("language", "en")
    segments = transcription_data.get("segments", [])
    
    logger.info(f"🎵 Generazione testo inglese da voce: {len(raw_text)} caratteri, parole chiare: {has_clear_words}, lingua: {language}")
    
    # Prepara input per AI - usa tutto il contesto disponibile
    input_text = raw_text if raw_text else phonemes
    if not input_text or len(input_text.strip()) < 3:
        logger.warning("⚠️ Testo trascritto troppo breve o vuoto")
        input_text = "vocal melody and sounds"
    
    # Estrai informazioni dai segmenti per più contesto
    context_info = ""
    if segments:
        # Prendi prime e ultime parole per contesto
        first_words = " ".join([s.get("text", "").strip() for s in segments[:3] if s.get("text")])
        last_words = " ".join([s.get("text", "").strip() for s in segments[-3:] if s.get("text")])
        if first_words and last_words:
            context_info = f"\nFirst part: {first_words}\nLast part: {last_words}"
    
    # RI-verifica Ollama prima di usarlo (potrebbe essere stato avviato dopo)
    if not OLLAMA_AVAILABLE:
        _check_ollama()
    
    # Prova sempre con AI prima (Ollama o OpenAI) - FORZA l'uso di AI
    result = None
    max_retries = 2
    
    if OLLAMA_AVAILABLE:
        for retry in range(max_retries):
            try:
                logger.info(f"🤖 Tentativo generazione con Ollama ({OLLAMA_MODEL}) - tentativo {retry+1}/{max_retries}...")
                if has_clear_words and raw_text:
                    result = _enhance_with_ollama(raw_text + context_info, language)
                else:
                    result = _generate_with_ollama(input_text + context_info, language)
                
                if result and len(result) > 50:  # Almeno 50 caratteri per essere valido
                    logger.info(f"✅ Testo generato con Ollama: {len(result)} caratteri")
                    return result
                else:
                    logger.warning(f"⚠️ Ollama ha generato testo troppo corto: {len(result) if result else 0} caratteri, riprovo...")
                    if retry < max_retries - 1:
                        import time
                        time.sleep(2)  # Aspetta prima di ritentare
            except Exception as e:
                logger.error(f"❌ Errore Ollama (tentativo {retry+1}): {e}")
                if retry < max_retries - 1:
                    import time
                    time.sleep(2)
    
    if OPENAI_AVAILABLE and not result:
        try:
            logger.info("🤖 Tentativo generazione con OpenAI...")
            if has_clear_words and raw_text:
                result = _enhance_with_openai(raw_text + context_info)
            else:
                result = _generate_with_openai(input_text + context_info)
            
            if result and len(result) > 50:
                logger.info(f"✅ Testo generato con OpenAI: {len(result)} caratteri")
                return result
        except Exception as e:
            logger.error(f"❌ Errore OpenAI: {e}")
    
    # Fallback SOLO se AI completamente non disponibile o fallita dopo tutti i tentativi
    if not result or len(result) < 20:
        logger.warning("⚠️ AI non disponibile o completamente fallita dopo tutti i tentativi - uso fallback migliorato")
        result = _fallback_generate_improved(input_text, context_info)
    
    logger.info(f"✅ Testo finale generato: {len(result)} caratteri")
    return result


def _enhance_text_with_ai(text: str) -> str:
    """Migliora testo esistente con AI - non usato più, tutto in generate_english_text_from_vocals."""
    # Questa funzione non è più usata, ma la mantengo per compatibilità
    return _enhance_with_ollama(text) if OLLAMA_AVAILABLE else _fallback_enhance(text)


def _generate_from_vocal_sounds(sounds: str) -> str:
    """Genera testo da suoni vocali - non usato più, tutto in generate_english_text_from_vocals."""
    # Questa funzione non è più usata, ma la mantengo per compatibilità
    return _generate_with_ollama(sounds) if OLLAMA_AVAILABLE else _fallback_generate_improved(sounds)


def _enhance_with_ollama(text: str, language: str = "en") -> str:
    """Migliora testo con Ollama - prompt migliorato per testi unici basati sul contenuto specifico."""
    import requests
    
    # Estrai parole chiave dal testo per personalizzare
    words = text.lower().split()[:30]  # Prime 30 parole per più contesto
    key_words = [w.strip('.,!?;:"()[]{}') for w in words if len(w) > 3][:8]  # Più parole significative
    
    # Estrai tema/emozione dal testo
    theme_hints = []
    if any(w in text.lower() for w in ['love', 'heart', 'feel', 'emotion']):
        theme_hints.append("emotional and heartfelt")
    if any(w in text.lower() for w in ['time', 'come', 'going', 'future', 'past']):
        theme_hints.append("reflective about time and change")
    if any(w in text.lower() for w in ['night', 'dark', 'light', 'day']):
        theme_hints.append("atmospheric and moody")
    if any(w in text.lower() for w in ['dream', 'hope', 'wish', 'believe']):
        theme_hints.append("hopeful and dreamy")
    
    theme_desc = ", ".join(theme_hints) if theme_hints else "poetic and meaningful"
    
    prompt = f"""You are a professional song lyricist. Transform this SPECIFIC transcribed vocal text into beautiful, UNIQUE, poetic English song lyrics.

CRITICAL INSTRUCTIONS:
1. Generate COMPLETELY UNIQUE lyrics based on THIS EXACT transcription
2. Do NOT use generic templates or repetitive phrases
3. Each song must be DIFFERENT based on the specific words and meaning
4. Use the actual words and themes from the transcription

Original transcribed text from the vocal track (THIS IS WHAT WAS ACTUALLY SUNG/HEARD):
{text}

Key words and themes detected: {', '.join(key_words) if key_words else 'melodic patterns'}
Mood and style: {theme_desc}
Original language: {language}

Requirements:
- Generate UNIQUE lyrics that reflect THIS SPECIFIC song and its meaning
- Be in English
- Be poetic, emotional, and meaningful
- Sound natural and singable
- Keep the core meaning, emotions, and themes from the original transcription
- Create 2-3 verses and a memorable chorus
- Make it personal and specific to THIS song - NOT generic
- Use variations of the key words detected above
- Each line should be different and meaningful

IMPORTANT: Do NOT repeat the same generic lyrics. Make it unique to THIS transcription.

Generate the complete, unique English song lyrics now:"""

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.9,  # Massima creatività per testi unici
                    "top_p": 0.95,
                    "num_predict": 1000,  # Più testo generato
                    "repeat_penalty": 1.3,  # Evita ripetizioni
                    "top_k": 40  # Più varietà
                }
            },
            timeout=120  # Timeout aumentato
        )
        
        if response.status_code != 200:
            error_text = response.text[:200] if hasattr(response, 'text') else ""
            raise Exception(f"Ollama error {response.status_code}: {error_text}")
        
        generated = response.json().get("response", "").strip()
        
        if not generated:
            raise Exception("Risposta Ollama vuota")
        
        # Pulisci output più aggressivamente
        prefixes = ["Here are", "Here's", "The lyrics", "Song lyrics:", "Lyrics:", "Lyrics", "Here"]
        for prefix in prefixes:
            if generated.lower().startswith(prefix.lower()):
                generated = generated[len(prefix):].strip()
                if generated.startswith(":"):
                    generated = generated[1:].strip()
        
        # Rimuovi eventuali prefissi rimasti
        lines = generated.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not any(line.lower().startswith(p.lower()) for p in prefixes):
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        
        if result and len(result) > 30:
            return result
        else:
            raise Exception(f"Testo generato troppo corto: {len(result) if result else 0} caratteri")
            
    except requests.exceptions.Timeout:
        raise Exception("Ollama timeout - il modello potrebbe essere troppo lento")
    except requests.exceptions.ConnectionError:
        raise Exception("Ollama non raggiungibile - verifica che sia in esecuzione")
    except Exception as e:
        raise Exception(f"Errore Ollama: {str(e)}")


def _generate_with_ollama(sounds: str, language: str = "en") -> str:
    """Genera testo da suoni vocali con Ollama - prompt migliorato per testi unici basati sui suoni specifici."""
    import requests
    
    # Analizza i suoni per estrarre pattern
    sound_words = sounds.lower().split() if sounds else []
    unique_sounds = list(set([w.strip('.,!?;:"()[]{}') for w in sound_words if len(w) > 2]))[:15]
    
    # Analizza il pattern ritmico (la la la, na na na, etc.)
    pattern_type = "melodic humming"
    if any("la" in s for s in unique_sounds):
        pattern_type = "melodic 'la' patterns"
    elif any("na" in s for s in unique_sounds):
        pattern_type = "rhythmic 'na' patterns"
    elif any("da" in s or "do" in s for s in unique_sounds):
        pattern_type = "percussive vocal patterns"
    
    prompt = f"""You are a creative song lyricist. Generate beautiful, COMPLETELY UNIQUE, poetic English song lyrics based on these SPECIFIC vocal sounds and melodies.

CRITICAL INSTRUCTIONS:
1. Generate COMPLETELY UNIQUE lyrics that are SPECIFIC to THESE vocal sounds
2. Do NOT use generic templates or the same lyrics for every song
3. Each song must be DIFFERENT based on the specific sounds and patterns
4. Use the rhythm, flow, and mood suggested by these sounds

Vocal sounds and melodies detected (THIS IS WHAT WAS ACTUALLY HEARD):
{sounds}

Unique sound patterns: {', '.join(unique_sounds) if unique_sounds else 'melodic patterns'}
Pattern type: {pattern_type}
Original language: {language}

Requirements:
- Generate COMPLETELY UNIQUE lyrics based on THESE specific sounds
- Be in English
- Be poetic, emotional, and meaningful
- Sound natural and singable
- Create a complete song with 2-3 verses and a memorable chorus
- Tell a story or express emotions that match the mood and rhythm of the sounds
- Make it personal and specific - NOT generic
- Use the rhythm and flow suggested by the vocal sounds
- Each song should be DIFFERENT - vary the themes, emotions, and words

IMPORTANT: Do NOT repeat generic lyrics. Make it unique to THESE sounds.

Generate the complete, unique English song lyrics now:"""

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.9,  # Massima creatività per testi unici
                    "top_p": 0.95,
                    "num_predict": 1000,  # Più testo generato
                    "repeat_penalty": 1.3,  # Evita ripetizioni
                    "top_k": 40  # Più varietà
                }
            },
            timeout=120  # Timeout aumentato
        )
        
        if response.status_code != 200:
            error_text = response.text[:200] if hasattr(response, 'text') else ""
            raise Exception(f"Ollama error {response.status_code}: {error_text}")
        
        generated = response.json().get("response", "").strip()
        
        if not generated:
            raise Exception("Risposta Ollama vuota")
        
        # Pulisci output
        prefixes = ["Here are", "Here's", "The lyrics", "Song lyrics:", "Lyrics:", "Lyrics", "Here"]
        for prefix in prefixes:
            if generated.lower().startswith(prefix.lower()):
                generated = generated[len(prefix):].strip()
                if generated.startswith(":"):
                    generated = generated[1:].strip()
        
        # Rimuovi prefissi rimasti
        lines = generated.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if line and not any(line.lower().startswith(p.lower()) for p in prefixes):
                cleaned_lines.append(line)
        
        result = '\n'.join(cleaned_lines).strip()
        
        if result and len(result) > 30:
            return result
        else:
            raise Exception(f"Testo generato troppo corto: {len(result) if result else 0} caratteri")
            
    except requests.exceptions.Timeout:
        raise Exception("Ollama timeout - il modello potrebbe essere troppo lento")
    except requests.exceptions.ConnectionError:
        raise Exception("Ollama non raggiungibile - verifica che sia in esecuzione")
    except Exception as e:
        raise Exception(f"Errore Ollama: {str(e)}")


def _enhance_with_openai(text: str) -> str:
    """Migliora testo con OpenAI."""
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert song lyricist. Transform transcribed vocal text into beautiful, poetic English song lyrics."},
            {"role": "user", "content": f"Transform this into English song lyrics:\n{text}"}
        ],
        max_tokens=500,
        temperature=0.7
    )
    
    return response.choices[0].message.content.strip()


def _generate_with_openai(sounds: str) -> str:
    """Genera testo da suoni vocali con OpenAI."""
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a creative song lyricist. Generate beautiful English song lyrics from vocal sounds."},
            {"role": "user", "content": f"Generate English song lyrics from these vocal sounds:\n{sounds}"}
        ],
        max_tokens=500,
        temperature=0.8
    )
    
    return response.choices[0].message.content.strip()


def _fallback_enhance(text: str) -> str:
    """Fallback: migliora testo base."""
    if not text:
        return ""
    
    # Capitalizza e formatta
    lines = text.split('\n')
    formatted = []
    for line in lines:
        line = line.strip()
        if line:
            # Capitalizza prima lettera
            if len(line) > 1:
                line = line[0].upper() + line[1:]
            formatted.append(line)
    
    return '\n'.join(formatted) if formatted else text


def _fallback_generate_improved(sounds: str, context: str = "") -> str:
    """Fallback migliorato: genera testo basato sul contenuto specifico invece di template fisso."""
    if not sounds:
        sounds = "vocal melody"
    
    # Estrai parole chiave dal testo per personalizzare il fallback
    words = sounds.lower().split()
    meaningful_words = [w.strip('.,!?;:"()[]{}') for w in words if len(w) > 3][:5]
    
    # Usa le parole chiave per creare testo più personalizzato
    if meaningful_words:
        # Crea testo basato sulle parole trovate
        first_word = meaningful_words[0].capitalize()
        theme = meaningful_words[0] if meaningful_words else "melody"
        
        # Genera variazioni basate sul tema
        if "time" in theme or "come" in theme or "going" in theme:
            lyrics = [
                f"Time is {theme}ing",
                "Through the days we're living",
                "Every moment brings",
                "Something new to sing",
                "",
                "In the rhythm of our hearts",
                "We find where it starts",
                "Moving forward, never back",
                "On this endless track"
            ]
        elif "love" in theme or "heart" in theme or "feel" in theme:
            lyrics = [
                f"In my {theme} I feel",
                "Something that is real",
                "Every beat reminds me",
                "Of what I want to be",
                "",
                "With the music in my soul",
                "I'll reach my goal",
                "Following the sound",
                "Where love can be found"
            ]
        elif "night" in theme or "dark" in theme or "light" in theme:
            lyrics = [
                f"Through the {theme} I see",
                "What's meant to be",
                "In the shadows and the light",
                "Everything feels right",
                "",
                "In the silence of the night",
                "I find my inner light",
                "Guiding me along",
                "In this endless song"
            ]
        else:
            # Testo generico ma personalizzato con la prima parola
            lyrics = [
                f"{first_word} is calling me",
                "Through the melody",
                "Every note I hear",
                "Brings me something near",
                "",
                "In the rhythm of the sound",
                "I know I'll be found",
                "Following the beat",
                "Making life complete"
            ]
    else:
        # Se non ci sono parole significative, usa testo più generico ma variato
        import hashlib
        # Usa hash del testo per variare il fallback
        text_hash = int(hashlib.md5(sounds.encode()).hexdigest()[:8], 16)
        variant = text_hash % 5
        
        variants = [
            [
                "In the melody I hear",
                "A story drawing near",
                "Every note tells a tale",
                "That will never fail",
                "",
                "Through the rhythm and the rhyme",
                "I'll find my way in time",
                "With the music in my heart",
                "A brand new start"
            ],
            [
                "Following the sound",
                "Wherever it may lead",
                "In every word I find",
                "A piece of my mind",
                "",
                "The melody flows free",
                "Just like it should be",
                "Carrying me along",
                "In this endless song"
            ],
            [
                "Voices in the air",
                "Singing everywhere",
                "Every sound I hear",
                "Brings me something near",
                "",
                "In the harmony",
                "I find what I need",
                "Moving with the beat",
                "Making life complete"
            ],
            [
                "Through the music's call",
                "I'll give it my all",
                "Every moment counts",
                "As the rhythm mounts",
                "",
                "In the song I see",
                "What I want to be",
                "Following the tune",
                "Underneath the moon"
            ],
            [
                "The sound begins to rise",
                "Right before my eyes",
                "Every note so clear",
                "Dispelling every fear",
                "",
                "In the melody's flow",
                "I know where to go",
                "With the beat so strong",
                "I know I belong"
            ]
        ]
        
        lyrics = variants[variant]
    
    return '\n'.join(lyrics)

