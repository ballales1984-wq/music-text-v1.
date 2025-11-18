"""
Generazione testo in inglese da trascrizione e analisi audio
Usa Ollama (llama2/3, mistral, gpt-j, gpt-neox) con prompt avanzato
che include pitch, timing, metrica per adattare testo alla melodia
"""
import logging
import os
from typing import Dict

logger = logging.getLogger(__name__)

# Check Ollama
OLLAMA_AVAILABLE = False
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

try:
    import requests
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        if response.status_code == 200:
            OLLAMA_AVAILABLE = True
            logger.info("✅ Ollama disponibile")
    except:
        pass
except ImportError:
    pass

# Check OpenAI (opzionale)
OPENAI_AVAILABLE = False
try:
    import openai
    if os.getenv("OPENAI_API_KEY"):
        OPENAI_AVAILABLE = True
        logger.info("✅ OpenAI disponibile")
except:
    pass


def generate_lyrics(transcription_data: Dict, num_variants: int = 3) -> Dict:
    """
    Genera più varianti di testo in inglese che si adattano alla melodia.
    Restituisce un dizionario con varianti e versi/chorus separati.
    """
    raw_text = transcription_data.get("text", "")
    phonemes = transcription_data.get("phonemes", "")
    has_clear_words = transcription_data.get("has_clear_words", False)
    audio_features_str = transcription_data.get("audio_features_str", "")
    rhythmic_features_str = transcription_data.get("rhythmic_features_str", "")
    metric_pattern = transcription_data.get("metric_pattern", {})
    
    # Combina features linguistiche, ritmiche e metriche
    metric_info = ""
    if metric_pattern:
        syllable_count = metric_pattern.get('syllable_count', 0)
        strong_beats = metric_pattern.get('strong_beats', 0)
        time_sig = metric_pattern.get('time_signature', '4/4')
        accents = metric_pattern.get('accents', [])
        metric_info = f"\nMETRIC PATTERN (CRITICAL - must follow exactly):\n- Total syllables: {syllable_count}\n- Strong accents: {strong_beats} (positions: {[i for i, a in enumerate(accents[:20]) if a == 1]})\n- Time signature: {time_sig}\n- Accent pattern: {accents[:30] if len(accents) > 0 else 'N/A'}\n\nIMPORTANT: Generate English lyrics that:\n1. Have EXACTLY {syllable_count} syllables total\n2. Place strong accents on syllables at positions {[i for i, a in enumerate(accents[:20]) if a == 1]}\n3. Follow the rhythm and phrasing of the original melody\n4. Sound natural and poetic in English"
    
    combined_context = f"{audio_features_str}\n{rhythmic_features_str}{metric_info}" if rhythmic_features_str else audio_features_str + metric_info
    
    # Genera varianti
    variants = []
    input_text = raw_text if raw_text and len(raw_text.strip()) > 5 else f"Vocal sounds (humming): {phonemes[:200]}"
    
    for i in range(num_variants):
        if has_clear_words and raw_text:
            variant = _enhance_with_ai_variant(raw_text, combined_context, variant_num=i)
        else:
            variant = _generate_from_sounds_variant(input_text, combined_context, variant_num=i)
        
        # Estrai versi e chorus
        parsed = _parse_lyrics(variant)
        variants.append({
            "id": i + 1,
            "full_text": variant,
            "verses": parsed["verses"],
            "chorus": parsed["chorus"],
            "preview": parsed["preview"]
        })
    
    return {
        "variants": variants,
        "selected": 0,  # Prima variante selezionata di default
        "total": len(variants)
    }


def _enhance_with_ai(text: str, audio_context: str) -> str:
    """Migliora testo esistente usando AI."""
    if OLLAMA_AVAILABLE:
        return _enhance_with_ollama(text, "enhance", audio_context)
    elif OPENAI_AVAILABLE:
        return _enhance_with_openai(text, audio_context)
    else:
        return _fallback_enhancement(text)


def _generate_from_sounds(text: str, audio_context: str) -> str:
    """Genera testo da suoni vocali (la la la) usando AI."""
    if OLLAMA_AVAILABLE:
        result = _enhance_with_ollama(text, "generate", audio_context)
        if result and len(result) > 50:  # Verifica che sia testo valido
            return result
        # Se Ollama fallisce, usa fallback migliorato
        return _fallback_generation(text, audio_context)
    elif OPENAI_AVAILABLE:
        result = _generate_with_openai(text, audio_context)
        if result and len(result) > 50:
            return result
        return _fallback_generation(text, audio_context)
    else:
        return _fallback_generation(text, audio_context)


def _generate_from_sounds_variant(text: str, audio_context: str, variant_num: int = 0) -> str:
    """Genera una variante di testo da suoni vocali."""
    # Prova Ollama con timeout breve, se fallisce usa fallback veloce
    if OLLAMA_AVAILABLE:
        try:
            result = _enhance_with_ollama_variant(text, "generate", audio_context, variant_num)
            if result and len(result) > 50:
                return result
        except Exception as e:
            logger.warning(f"Ollama timeout per variante {variant_num+1}, uso fallback veloce")
    
    if OPENAI_AVAILABLE:
        try:
            result = _generate_with_openai_variant(text, audio_context, variant_num)
            if result and len(result) > 50:
                return result
        except:
            pass
    
    # Fallback con varianti (veloce e funzionante)
    return _fallback_generation_variant(text, audio_context, variant_num)


def _enhance_with_ai_variant(text: str, audio_context: str, variant_num: int = 0) -> str:
    """Genera una variante migliorando testo esistente."""
    if OLLAMA_AVAILABLE:
        try:
            result = _enhance_with_ollama_variant(text, "enhance", audio_context, variant_num)
            if result and len(result) > 50:
                return result
        except Exception as e:
            logger.warning(f"Ollama timeout per variante {variant_num+1}, uso fallback")
    
    if OPENAI_AVAILABLE:
        try:
            result = _enhance_with_openai_variant(text, audio_context, variant_num)
            if result and len(result) > 50:
                return result
        except:
            pass
    
    # Fallback veloce
    return _fallback_generation_variant(text, audio_context, variant_num)


def _enhance_with_ollama(text: str, task: str, audio_context: str) -> str:
    """Genera/migliora testo con Ollama usando pitch, timing, metrica."""
    try:
        import requests
        
        audio_info = f"\n\nMusical Information:\n{audio_context}" if audio_context else ""
        
        if task == "enhance":
            prompt = f"""Transform this transcribed song text into coherent and poetic song lyrics in English.
The lyrics must fit perfectly with the melody, rhythm, and musical structure.

Original text:
{text}{audio_info}

IMPORTANT: The generated lyrics must:
- Match the pitch contour and rhythm exactly
- Fit the tempo and timing
- Follow the melody structure and notes
- Follow the METRIC PATTERN (syllable count and accents) EXACTLY as specified
- Be in English
- Be poetic and emotional

Generate improved song lyrics that fit the melody:"""
        else:
            prompt = f"""You are a professional song lyricist. Generate creative, poetic English song lyrics based on vocal sounds (like "la la la" humming).
The lyrics MUST fit perfectly with the melody, rhythm, and musical structure provided.

Vocal sounds detected:
{text}{audio_info}

CRITICAL REQUIREMENTS:
- Generate FULL song lyrics (at least 8-12 lines, verses and chorus)
- Match the pitch contour and rhythm EXACTLY
- Fit the tempo ({audio_context.split('Tempo:')[1].split('BPM')[0].strip() if 'Tempo:' in audio_context else 'unknown'} BPM) perfectly
- Follow the melody structure and notes provided
- Match the beat pattern and timing
- Be in English
- Be poetic, emotional, and suitable for a song
- Create COHERENT lyrics that tell a story or express emotions
- DO NOT just say "vocal sounds" or "humming" - CREATE ACTUAL LYRICS

Generate the complete song lyrics now:"""
        
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
            timeout=60
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama error: {response.status_code}")
        
        generated = response.json().get("response", "").strip()
        
        # Pulisci
        prefixes = ["Here are", "Here's", "The lyrics", "Song lyrics:"]
        for prefix in prefixes:
            if generated.lower().startswith(prefix.lower()):
                generated = generated[len(prefix):].strip()
                if generated.startswith(":"):
                    generated = generated[1:].strip()
        
        # Rimuovi ripetizioni
        lines = generated.split('\n')
        seen = set()
        unique = []
        for line in lines:
            clean = line.strip().lower()
            if clean and clean not in seen and len(clean) > 3:
                seen.add(clean)
                unique.append(line.strip())
        
        result = '\n'.join(unique[:20])
        
        if not result or len(result) < 50:
            # Se il risultato è troppo corto, usa fallback migliorato
            logger.warning("Ollama generato testo troppo corto, uso fallback")
            return _fallback_generation(text, audio_context)
        
        logger.info(f"✅ Testo generato con Ollama ({len(result)} caratteri)")
        return result
        
    except Exception as e:
        logger.error(f"Errore Ollama: {str(e)}")
        return _fallback_enhancement(text)


def _enhance_with_openai(text: str, audio_context: str) -> str:
    """Migliora con OpenAI."""
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        audio_info = f"\n\nMusical Information:\n{audio_context}" if audio_context else ""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert song lyricist. Generate lyrics in English that fit perfectly with the melody, rhythm, and musical structure."},
                {"role": "user", "content": f"Transform this into English song lyrics that fit the melody:\n{text}{audio_info}"}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Errore OpenAI: {str(e)}")
        return _fallback_enhancement(text)


def _generate_with_openai(text: str, audio_context: str) -> str:
    """Genera da suoni con OpenAI."""
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        audio_info = f"\n\nMusical Information:\n{audio_context}" if audio_context else ""
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a creative song lyricist. Generate English lyrics from vocal sounds that fit perfectly with the melody, rhythm, and musical structure."},
                {"role": "user", "content": f"Generate English song lyrics from these vocal sounds that fit the melody:\n{text}{audio_info}"}
            ],
            max_tokens=500,
            temperature=0.8
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Errore OpenAI: {str(e)}")
        return _fallback_generation(text)


def _fallback_enhancement(text: str) -> str:
    """Fallback: formattazione base."""
    text = text.strip()
    words = text.split()
    lines = []
    current = []
    char_count = 0
    
    for word in words:
        if char_count + len(word) > 40 and current:
            lines.append(" ".join(current))
            current = [word]
            char_count = len(word)
        else:
            current.append(word)
            char_count += len(word) + 1
    
    if current:
        lines.append(" ".join(current))
    
    return "\n".join(lines)


def _fallback_generation(text: str, audio_context: str = "") -> str:
    """Fallback: genera testo creativo basato su features audio."""
    # Estrai informazioni audio dal contesto
    tempo = None
    notes = []
    melody = []
    
    if audio_context:
        for line in audio_context.split('\n'):
            if 'Tempo:' in line:
                try:
                    tempo = float(line.split('Tempo:')[1].split('BPM')[0].strip())
                except:
                    pass
            if 'Musical notes:' in line:
                notes_str = line.split('Musical notes:')[1].strip()
                notes = [n.strip() for n in notes_str.split(',')[:10]]
            if 'Melody:' in line:
                melody_str = line.split('Melody:')[1].strip()
                melody = [m.strip() for m in melody_str.split('->')[:8]]
    
    # Genera testo creativo basato su features
    lyrics = []
    
    # Intro basato su tempo
    if tempo:
        if tempo > 140:
            lyrics.append("Running fast through the night")
            lyrics.append("Heartbeat racing, feeling alive")
        elif tempo > 100:
            lyrics.append("Dancing in the moonlight")
            lyrics.append("Feeling the rhythm in my soul")
        else:
            lyrics.append("Walking slowly through the day")
            lyrics.append("Taking time to feel the way")
    
    # Versi basati su note/melodia
    if notes:
        # Usa pattern melodico per creare versi
        if 'D' in str(notes[:3]):
            lyrics.append("Down the road I go")
            lyrics.append("Dreaming of what I know")
        if 'E' in str(notes[:3]) or 'F' in str(notes[:3]):
            lyrics.append("Every moment feels so right")
            lyrics.append("Flying high into the light")
    
    # Versi generici se non ci sono info specifiche
    if not lyrics:
        lyrics = [
            "In the silence of the night",
            "A melody begins to rise",
            "Carrying emotions deep inside",
            "Through the rhythm of the sound"
        ]
    
    # Aggiungi chorus basato su melodia
    if melody:
        lyrics.append("")
        lyrics.append("(Chorus)")
        lyrics.append("Following the melody line")
        lyrics.append("Every note feels so divine")
    else:
        lyrics.append("")
        lyrics.append("(Chorus)")
        lyrics.append("Singing with the melody")
        lyrics.append("Feeling free, feeling free")
    
    result = "\n".join(lyrics)
    
    if text and len(text.strip()) > 5:
        # Se c'è qualche testo, prova a migliorarlo
        return _fallback_enhancement(text) + "\n\n" + result
    
    return result


def _parse_lyrics(lyrics_text: str) -> Dict:
    """Estrae versi e chorus dal testo."""
    lines = [l.strip() for l in lyrics_text.split('\n') if l.strip()]
    verses = []
    chorus = []
    current_section = verses
    
    for line in lines:
        if '(Chorus)' in line or 'Chorus:' in line.lower():
            current_section = chorus
            continue
        if '(Verse)' in line or 'Verse:' in line.lower():
            current_section = verses
            continue
        if line:
            current_section.append(line)
    
    # Se non c'è chorus esplicito, prendi le ultime 2-3 righe come chorus
    if not chorus and verses:
        chorus = verses[-3:] if len(verses) > 3 else verses[-2:]
        verses = verses[:-len(chorus)] if len(verses) > len(chorus) else verses
    
    preview = "\n".join(verses[:2] + (chorus[:1] if chorus else []))
    
    return {
        "verses": verses,
        "chorus": chorus,
        "preview": preview
    }


def _fallback_generation_variant(text: str, audio_context: str = "", variant_num: int = 0) -> str:
    """Genera variante di testo creativo basato su features audio."""
    # Estrai informazioni audio
    tempo = None
    notes = []
    melody = []
    
    if audio_context:
        for line in audio_context.split('\n'):
            if 'Tempo:' in line:
                try:
                    tempo = float(line.split('Tempo:')[1].split('BPM')[0].strip())
                except:
                    pass
            if 'Musical notes:' in line:
                notes_str = line.split('Musical notes:')[1].strip()
                notes = [n.strip() for n in notes_str.split(',')[:10]]
            if 'Melody:' in line:
                melody_str = line.split('Melody:')[1].strip()
                melody = [m.strip() for m in melody_str.split('->')[:8]]
    
    # Varianti diverse basate su variant_num
    variants_templates = [
        # Variante 1: Energica
        {
            "fast": ["Running fast through the night", "Heartbeat racing, feeling alive", "Chasing dreams with all my might", "Never stopping, always drive"],
            "medium": ["Dancing in the moonlight", "Feeling the rhythm in my soul", "Moving to the beat so right", "Letting the music take control"],
            "slow": ["Walking slowly through the day", "Taking time to feel the way", "Every moment has its say", "In the rhythm I will stay"],
            "chorus": ["Following the melody line", "Every note feels so divine", "This is my time to shine"]
        },
        # Variante 2: Emotiva
        {
            "fast": ["Flying high above the clouds", "Breaking free from all the crowds", "Singing loud, singing proud", "Standing tall, standing strong"],
            "medium": ["In the silence I can hear", "All the voices drawing near", "Every word becomes so clear", "Dispelling every fear"],
            "slow": ["Softly whispering in the dark", "Leaving behind a single mark", "Like a spark in the night", "Everything will be alright"],
            "chorus": ["This melody tells my story", "Of pain and also glory", "Every line, every verse"]
        },
        # Variante 3: Romantica
        {
            "fast": ["Love is running through my veins", "Nothing else remains the same", "Calling out your precious name", "Setting my heart aflame"],
            "medium": ["In your eyes I see the light", "Everything feels so right", "Holding you so close tonight", "Everything will be alright"],
            "slow": ["Gentle touch upon my heart", "Never wanting us to part", "You're the music, I'm the art", "Together we will start"],
            "chorus": ["You are my melody", "The song inside of me", "Forever you'll be"]
        }
    ]
    
    template = variants_templates[variant_num % len(variants_templates)]
    
    lyrics = []
    
    # Scegli versi basati su tempo
    if tempo:
        if tempo > 140:
            lyrics.extend(template["fast"][:4])
        elif tempo > 100:
            lyrics.extend(template["medium"][:4])
        else:
            lyrics.extend(template["slow"][:4])
    else:
        lyrics.extend(template["medium"][:4])
    
    # Aggiungi chorus
    lyrics.append("")
    lyrics.append("(Chorus)")
    lyrics.extend(template["chorus"])
    
    return "\n".join(lyrics)


def _enhance_with_ollama_variant(text: str, task: str, audio_context: str, variant_num: int = 0) -> str:
    """Genera variante con Ollama."""
    try:
        import requests
        
        audio_info = f"\n\nMusical Information:\n{audio_context}" if audio_context else ""
        
        # Varia il prompt per ogni variante
        style_hints = [
            "energetic and powerful",
            "emotional and deep",
            "romantic and tender",
            "mysterious and intriguing",
            "hopeful and uplifting"
        ]
        style = style_hints[variant_num % len(style_hints)]
        
        if task == "enhance":
            prompt = f"""Transform this into {style} English song lyrics. Generate a complete song with verses and chorus.
Original: {text}{audio_info}
Generate {style} lyrics:"""
        else:
            prompt = f"""Generate {style} English song lyrics from vocal sounds. Create a complete song (verses + chorus).
Vocal sounds: {text}{audio_info}
Generate {style} lyrics:"""
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.8 + (variant_num * 0.1),
                    "top_p": 0.9,
                    "max_tokens": 500
                }
            },
            timeout=30  # Timeout ridotto: se Ollama è lento, usa fallback più veloce
        )
        
        if response.status_code != 200:
            return _fallback_generation_variant(text, audio_context, variant_num)
        
        generated = response.json().get("response", "").strip()
        
        # Pulisci
        prefixes = ["Here are", "Here's", "The lyrics", "Song lyrics:"]
        for prefix in prefixes:
            if generated.lower().startswith(prefix.lower()):
                generated = generated[len(prefix):].strip()
                if generated.startswith(":"):
                    generated = generated[1:].strip()
        
        lines = generated.split('\n')
        seen = set()
        unique = []
        for line in lines:
            clean = line.strip().lower()
            if clean and clean not in seen and len(clean) > 3:
                seen.add(clean)
                unique.append(line.strip())
        
        result = '\n'.join(unique[:20])
        
        if not result or len(result) < 50:
            return _fallback_generation_variant(text, audio_context, variant_num)
        
        return result
        
    except Exception as e:
        logger.error(f"Errore Ollama variante: {str(e)}")
        return _fallback_generation_variant(text, audio_context, variant_num)


def _enhance_with_openai_variant(text: str, audio_context: str, variant_num: int = 0) -> str:
    """Genera variante con OpenAI."""
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        audio_info = f"\n\nMusical Information:\n{audio_context}" if audio_context else ""
        
        style_hints = [
            "energetic and powerful",
            "emotional and deep", 
            "romantic and tender"
        ]
        style = style_hints[variant_num % len(style_hints)]
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": f"You are a {style} song lyricist. Generate complete English lyrics with verses and chorus."},
                {"role": "user", "content": f"Generate {style} song lyrics:\n{text}{audio_info}"}
            ],
            max_tokens=500,
            temperature=0.7 + (variant_num * 0.1)
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"Errore OpenAI variante: {str(e)}")
        return _fallback_generation_variant(text, audio_context, variant_num)


def _generate_with_openai_variant(text: str, audio_context: str, variant_num: int = 0) -> str:
    """Genera variante da suoni con OpenAI."""
    return _enhance_with_openai_variant(text, audio_context, variant_num)

