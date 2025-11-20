"""
Generazione testo in inglese da trascrizione e analisi audio
Usa Ollama (llama2/3, mistral, gpt-j, gpt-neox) con prompt avanzato
che include pitch, timing, metrica per adattare testo alla melodia
"""
import logging
import os
from typing import Dict
import numpy as np

logger = logging.getLogger(__name__)

# ============================================
# RILEVAMENTO AUTOMATICO AI DISPONIBILI
# ============================================

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

# Check OpenAI
OPENAI_AVAILABLE = False
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
try:
    import openai
    if os.getenv("OPENAI_API_KEY"):
        OPENAI_AVAILABLE = True
        logger.info("✅ OpenAI disponibile")
except:
    pass

# Check DeepSeek
DEEPSEEK_AVAILABLE = False
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

if DEEPSEEK_API_KEY:
    try:
        import requests
        # Test connessione (opzionale)
        DEEPSEEK_AVAILABLE = True
        logger.info("✅ DeepSeek disponibile (API key configurata)")
    except:
        pass

# Check Claude (Anthropic)
CLAUDE_AVAILABLE = False
CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-3-5-sonnet-20241022")

if CLAUDE_API_KEY:
    try:
        import anthropic
        CLAUDE_AVAILABLE = True
        logger.info("✅ Claude (Anthropic) disponibile")
    except ImportError:
        # Prova senza import (potrebbe non essere installato)
        if CLAUDE_API_KEY:
            logger.info("⚠️  Claude API key trovata ma libreria 'anthropic' non installata. Installa con: pip install anthropic")
    except:
        pass

# Riepilogo AI disponibili
AVAILABLE_AIS = []
if OLLAMA_AVAILABLE:
    AVAILABLE_AIS.append("Ollama")
if OPENAI_AVAILABLE:
    AVAILABLE_AIS.append("OpenAI")
if DEEPSEEK_AVAILABLE:
    AVAILABLE_AIS.append("DeepSeek")
if CLAUDE_AVAILABLE:
    AVAILABLE_AIS.append("Claude")

if AVAILABLE_AIS:
    logger.info(f"🤖 AI disponibili: {', '.join(AVAILABLE_AIS)}")
else:
    logger.warning("⚠️  Nessuna AI disponibile - userà solo fallback locale")



def generate_lyrics(transcription_data: Dict, num_variants: int = 3) -> Dict:
    """
    Genera più varianti di testo in inglese che si adattano alla melodia.
    Restituisce un dizionario con varianti e versi/chorus separati.
    Ora usa struttura dettagliata per riga dalla voce.
    """
    raw_text = transcription_data.get("text", "")
    phonemes = transcription_data.get("phonemes", "")
    has_clear_words = transcription_data.get("has_clear_words", False)
    audio_features_str = transcription_data.get("audio_features_str", "")
    rhythmic_features_str = transcription_data.get("rhythmic_features_str", "")
    metric_pattern = transcription_data.get("metric_pattern", {})
    
    # Estrai struttura dettagliata per riga
    detailed_structure = metric_pattern.get('detailed_structure', {})
    
    # Combina features linguistiche, ritmiche e metriche
    metric_info = ""
    if metric_pattern:
        syllable_count = metric_pattern.get('syllable_count', 0)
        strong_beats = metric_pattern.get('strong_beats', 0)
        time_sig = metric_pattern.get('time_signature', '4/4')
        accents = metric_pattern.get('accents', [])
        
        # NUOVO: Usa struttura dettagliata per riga se disponibile
        if detailed_structure and detailed_structure.get('lines'):
            lines_info = []
            for line in detailed_structure['lines']:
                line_num = line.get('line_number', 0)
                syl_count = line.get('syllable_count', 0)
                strong_syl = line.get('strong_syllables', [])
                accents_line = line.get('accents', [])
                duration = line.get('duration', 0)
                
                lines_info.append(
                    f"Line {line_num}: {syl_count} syllables, "
                    f"strong accents at positions {strong_syl}, "
                    f"duration {duration:.2f}s, "
                    f"accent pattern: {accents_line}"
                )
            
            metric_info = f"\nVOCAL STRUCTURE (CRITICAL - must follow EXACTLY):\n"
            metric_info += f"Total lines: {detailed_structure.get('total_lines', 0)}\n"
            metric_info += f"Total syllables: {syllable_count}\n"
            metric_info += f"Time signature: {time_sig}\n"
            metric_info += f"Tempo: {metric_pattern.get('tempo', 120):.1f} BPM\n\n"
            metric_info += "LINE-BY-LINE STRUCTURE:\n"
            metric_info += "\n".join(lines_info)
            metric_info += f"\n\nCRITICAL REQUIREMENTS:\n"
            metric_info += f"1. Generate EXACTLY {detailed_structure.get('total_lines', 0)} lines\n"
            metric_info += f"2. Each line must have the EXACT syllable count specified above\n"
            metric_info += f"3. Place strong accents (stressed syllables) at the positions specified for each line\n"
            metric_info += f"4. Follow the rhythm and timing of each line (duration specified)\n"
            metric_info += f"5. The lyrics must fit the melody perfectly - match the vocal structure\n"
            metric_info += f"6. Sound natural, poetic, and emotional in English\n"
        else:
            # Fallback: usa pattern generico
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
    """Migliora testo esistente usando AI (priorità: DeepSeek > Claude > OpenAI > Ollama)."""
    if DEEPSEEK_AVAILABLE:
        try:
            return _enhance_with_deepseek(text, audio_context)
        except Exception as e:
            logger.warning(f"DeepSeek fallito: {e}, provo altra AI")
    
    if CLAUDE_AVAILABLE:
        try:
            return _enhance_with_claude(text, audio_context)
        except Exception as e:
            logger.warning(f"Claude fallito: {e}, provo altra AI")
    
    if OPENAI_AVAILABLE:
        try:
            return _enhance_with_openai(text, audio_context)
        except Exception as e:
            logger.warning(f"OpenAI fallito: {e}, provo altra AI")
    
    if OLLAMA_AVAILABLE:
        return _enhance_with_ollama(text, "enhance", audio_context)
    
    return _fallback_enhancement(text)


def _generate_from_sounds(text: str, audio_context: str) -> str:
    """Genera testo da suoni vocali (la la la) usando AI (priorità: DeepSeek > Claude > OpenAI > Ollama)."""
    # Prova DeepSeek
    if DEEPSEEK_AVAILABLE:
        try:
            result = _generate_with_deepseek(text, audio_context)
            if result and len(result) > 50:
                return result
        except Exception as e:
            logger.warning(f"DeepSeek fallito: {e}, provo altra AI")
    
    # Prova Claude
    if CLAUDE_AVAILABLE:
        try:
            result = _generate_with_claude(text, audio_context)
            if result and len(result) > 50:
                return result
        except Exception as e:
            logger.warning(f"Claude fallito: {e}, provo altra AI")
    
    # Prova OpenAI
    if OPENAI_AVAILABLE:
        try:
            result = _generate_with_openai(text, audio_context)
            if result and len(result) > 50:
                return result
        except Exception as e:
            logger.warning(f"OpenAI fallito: {e}, provo altra AI")
    
    # Prova Ollama
    if OLLAMA_AVAILABLE:
        result = _enhance_with_ollama(text, "generate", audio_context)
        if result and len(result) > 50:
            return result
    
    # Fallback
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
            model=OPENAI_MODEL,
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
        return _fallback_generation(text, audio_context)


def _enhance_with_deepseek(text: str, audio_context: str) -> str:
    """Migliora testo con DeepSeek API."""
    try:
        import requests
        
        audio_info = f"\n\nMusical Information:\n{audio_context}" if audio_context else ""
        
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
        
        response = requests.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": "You are an expert song lyricist. Generate lyrics in English that fit perfectly with the melody, rhythm, and musical structure."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=60
        )
        
        if response.status_code != 200:
            raise Exception(f"DeepSeek error: {response.status_code} - {response.text}")
        
        result = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        
        if not result or len(result) < 50:
            raise Exception("DeepSeek generato testo troppo corto")
        
        logger.info(f"✅ Testo generato con DeepSeek ({len(result)} caratteri)")
        return result
        
    except Exception as e:
        logger.error(f"Errore DeepSeek: {str(e)}")
        raise


def _generate_with_deepseek(text: str, audio_context: str) -> str:
    """Genera testo da suoni vocali con DeepSeek API."""
    try:
        import requests
        
        audio_info = f"\n\nMusical Information:\n{audio_context}" if audio_context else ""
        
        prompt = f"""You are a professional song lyricist. Generate creative, poetic English song lyrics based on vocal sounds (like "la la la" humming).
The lyrics MUST fit perfectly with the melody, rhythm, and musical structure provided.

Vocal sounds detected:
{text}{audio_info}

CRITICAL REQUIREMENTS:
- Generate FULL song lyrics (at least 8-12 lines, verses and chorus)
- Match the pitch contour and rhythm EXACTLY
- Fit the tempo perfectly
- Follow the melody structure and notes provided
- Match the beat pattern and timing
- Be in English
- Be poetic, emotional, and suitable for a song
- Create COHERENT lyrics that tell a story or express emotions
- DO NOT just say "vocal sounds" or "humming" - CREATE ACTUAL LYRICS

Generate the complete song lyrics now:"""
        
        response = requests.post(
            f"{DEEPSEEK_BASE_URL}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a creative song lyricist. Generate English lyrics from vocal sounds that fit perfectly with the melody, rhythm, and musical structure."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.8,
                "max_tokens": 500
            },
            timeout=60
        )
        
        if response.status_code != 200:
            raise Exception(f"DeepSeek error: {response.status_code} - {response.text}")
        
        result = response.json().get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        
        if not result or len(result) < 50:
            raise Exception("DeepSeek generato testo troppo corto")
        
        logger.info(f"✅ Testo generato con DeepSeek ({len(result)} caratteri)")
        return result
        
    except Exception as e:
        logger.error(f"Errore DeepSeek: {str(e)}")
        raise


def _enhance_with_claude(text: str, audio_context: str) -> str:
    """Migliora testo con Claude (Anthropic) API."""
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        audio_info = f"\n\nMusical Information:\n{audio_context}" if audio_context else ""
        
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=500,
            temperature=0.7,
            system="You are an expert song lyricist. Generate lyrics in English that fit perfectly with the melody, rhythm, and musical structure.",
            messages=[
                {
                    "role": "user",
                    "content": f"Transform this into English song lyrics that fit the melody:\n{text}{audio_info}"
                }
            ]
        )
        
        result = message.content[0].text.strip()
        
        if not result or len(result) < 50:
            raise Exception("Claude generato testo troppo corto")
        
        logger.info(f"✅ Testo generato con Claude ({len(result)} caratteri)")
        return result
        
    except Exception as e:
        logger.error(f"Errore Claude: {str(e)}")
        raise


def _generate_with_claude(text: str, audio_context: str) -> str:
    """Genera testo da suoni vocali con Claude (Anthropic) API."""
    try:
        import anthropic
        
        client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
        audio_info = f"\n\nMusical Information:\n{audio_context}" if audio_context else ""
        
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=500,
            temperature=0.8,
            system="You are a creative song lyricist. Generate English lyrics from vocal sounds that fit perfectly with the melody, rhythm, and musical structure.",
            messages=[
                {
                    "role": "user",
                    "content": f"Generate English song lyrics from these vocal sounds that fit the melody:\n{text}{audio_info}"
                }
            ]
        )
        
        result = message.content[0].text.strip()
        
        if not result or len(result) < 50:
            raise Exception("Claude generato testo troppo corto")
        
        logger.info(f"✅ Testo generato con Claude ({len(result)} caratteri)")
        return result
        
    except Exception as e:
        logger.error(f"Errore Claude: {str(e)}")
        raise


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


# ============================================================================
# VERSIONE SEMPLIFICATA: Solo testo, sillabe e struttura
# ============================================================================

def generate_lyrics_simple(generation_data: Dict, num_variants: int = 3) -> Dict:
    """
    Genera testo in inglese da trascrizione e analisi.
    Versione semplificata che usa:
    - Testo trascritto (parole/fonemi)
    - Struttura (strofe/ritornello) - da testo O da audio (intensità)
    - Sillabe
    - Parole chiave
    - Analisi audio (intensità, intervalli) - NUOVO
    """
    raw_text = generation_data.get("text", "")
    structure = generation_data.get("structure", {})
    syllables_info = generation_data.get("syllables", {})
    key_words = generation_data.get("key_words", [])
    audio_structure = generation_data.get("audio_structure", {})
    
    logger.info(f"📊 Dati per generazione: {len(raw_text)} caratteri, {structure.get('total_lines', 0)} righe, {syllables_info.get('total_syllables', 0)} sillabe, {len(key_words)} parole chiave")
    
    # Prepara informazioni per il prompt
    total_syllables = syllables_info.get("total_syllables", 0)
    lines_syllables = syllables_info.get("lines_syllables", [])
    verses = structure.get("verses", [])
    chorus = structure.get("chorus", "")
    total_lines = structure.get("total_lines", 0)
    
    # Prepara versi per il prompt
    verses_text = ""
    if verses:
        for i, verse in enumerate(verses):
            verses_text += f"\nVerse {i+1}:\n" + "\n".join(verse)
    
    # Aggiungi informazioni audio se disponibili
    audio_info = ""
    if audio_structure.get("available"):
        audio_chorus = audio_structure.get("structure", {}).get("chorus")
        audio_verses = audio_structure.get("structure", {}).get("verses", [])
        word_intervals = audio_structure.get("word_intervals", [])
        
        audio_info = "\n\nAUDIO STRUCTURE ANALYSIS (based on intensity changes):"
        if audio_chorus:
            audio_info += f"\n- Chorus detected at: {audio_chorus['start']:.1f}s - {audio_chorus['end']:.1f}s (intensity: {audio_chorus['intensity']:.2f}, confidence: {audio_chorus['confidence']:.2f})"
        if audio_verses:
            audio_info += f"\n- Verses detected: {len(audio_verses)} sections"
            for i, v in enumerate(audio_verses[:3]):
                audio_info += f"\n  Verse {i+1}: {v['start']:.1f}s - {v['end']:.1f}s (intensity: {v['intensity']:.2f})"
        if word_intervals:
            avg_interval = np.mean([w['duration'] for w in word_intervals[:20]]) if word_intervals else 0
            audio_info += f"\n- Word intervals analyzed: {len(word_intervals)} detected, average duration: {avg_interval:.2f}s"
            audio_info += "\n  (This helps understand the rhythm and phrasing of the original song)"
    
    # Crea contesto semplice per AI
    context = f"""You are a professional song lyricist. Your task is to REMODEL and IMPROVE the transcribed text below into proper, poetic English song lyrics.

ORIGINAL TRANSCRIBED TEXT (this is what was heard/sung):
{raw_text}

STRUCTURE ANALYSIS:
- Total lines: {total_lines}
- Number of verses: {len(verses)}
- Chorus identified: {chorus if chorus else "Not identified"}
- Total syllables: {total_syllables}
- Syllables per line: {', '.join(map(str, lines_syllables)) if lines_syllables else 'N/A'}
- Key words detected: {', '.join(key_words[:10]) if key_words else 'N/A'}
{verses_text if verses_text else ''}{audio_info}

CRITICAL REQUIREMENTS (IN ORDER OF PRIORITY):
1. SYLLABLE COUNT IS ABSOLUTELY CRITICAL - You MUST match the syllable count per line EXACTLY as specified above
   - If syllables per line are: {', '.join(map(str, lines_syllables)) if lines_syllables else 'N/A'}, you MUST generate lines with these EXACT counts
   - Total syllables MUST be EXACTLY {total_syllables} (or very close, within 5%)
   - Count syllables carefully - this determines if the lyrics fit the melody
2. REMODEL the original text - keep the meaning, emotions, and structure but fix grammar and make it poetic
3. Keep the same number of lines and verses as the original ({total_lines} lines total)
4. If there are repetitions in the original, keep them but improve the wording
5. Use the key words from the original text: {', '.join(key_words[:10]) if key_words else 'N/A'}
6. Make it sound natural and poetic in English
7. If a chorus was identified, improve it and make it memorable
8. DO NOT create completely new lyrics - REMODEL what was transcribed

SYLLABLE VALIDATION:
- After generating, count syllables in each line
- If a line doesn't match the target syllable count, adjust it by:
  * Adding short words (1-2 syllables) if too few
  * Removing non-essential words if too many
  * Replacing words with shorter/longer synonyms

Generate improved lyrics that are based on the original transcription:"""
    
    # Genera varianti
    variants = []
    from text_cleaner import clean_generated_text
    
    for i in range(num_variants):
        variant = _generate_simple_variant(raw_text, context, variant_num=i, target_syllables=total_syllables, target_lines_syllables=lines_syllables)
        
        # Pulisci il testo generato per rimuovere ripetizioni eccessive
        variant = clean_generated_text(variant)
        
        # Valida sillabe generate
        from syllable_counter import count_syllables_in_text
        generated_syllables = count_syllables_in_text(variant)
        generated_total = generated_syllables.get("total_syllables", 0)
        generated_lines = generated_syllables.get("lines_syllables", [])
        
        # Calcola differenza
        syllable_diff = abs(generated_total - total_syllables) if total_syllables > 0 else 0
        syllable_accuracy = (1 - (syllable_diff / total_syllables)) * 100 if total_syllables > 0 else 100
        
        logger.info(f"📊 Variante {i+1}: {generated_total} sillabe generate (target: {total_syllables}, differenza: {syllable_diff}, accuratezza: {syllable_accuracy:.1f}%)")
        
        # Estrai versi e chorus
        parsed = _parse_lyrics(variant)
        variants.append({
            "id": i + 1,
            "full_text": variant,
            "verses": parsed["verses"],
            "chorus": parsed["chorus"],
            "preview": parsed["preview"],
            "syllable_validation": {
                "target_syllables": total_syllables,
                "generated_syllables": generated_total,
                "difference": syllable_diff,
                "accuracy_percent": round(syllable_accuracy, 1),
                "target_lines_syllables": lines_syllables,
                "generated_lines_syllables": generated_lines
            }
        })
    
    return {
        "variants": variants,
        "selected": 0,
        "total": len(variants)
    }


def _generate_simple_variant(text: str, context: str, variant_num: int = 0, target_syllables: int = 0, target_lines_syllables: list = None) -> str:
    """Genera una variante semplice usando AI linguistica."""
    logger.info(f"🔄 Generazione variante {variant_num+1} - Ollama disponibile: {OLLAMA_AVAILABLE}, OpenAI disponibile: {OPENAI_AVAILABLE}")
    
    # Aggiungi informazioni sillabe al contesto se disponibili
    if target_syllables > 0:
        context += f"\n\nCRITICAL SYLLABLE REQUIREMENTS:\n"
        context += f"- Total syllables MUST be EXACTLY {target_syllables} (current target)\n"
        if target_lines_syllables:
            context += f"- Syllables per line: {', '.join(map(str, target_lines_syllables))}\n"
            context += f"- You MUST generate {len(target_lines_syllables)} lines with these exact syllable counts\n"
        context += f"- This is CRITICAL for the lyrics to fit the melody perfectly\n"
    
    # Prova Ollama prima
    if OLLAMA_AVAILABLE:
        try:
            logger.info(f"🤖 Tentativo con Ollama per variante {variant_num+1}...")
            result = _generate_simple_with_ollama(text, context, variant_num)
            if result and len(result) > 50:
                logger.info(f"✅ Variante {variant_num+1} generata con Ollama ({len(result)} caratteri)")
                # Valida sillabe se target disponibile
                if target_syllables > 0:
                    result = _validate_and_adjust_syllables(result, target_syllables, target_lines_syllables)
                return result
            else:
                logger.warning(f"⚠️ Ollama ha generato testo troppo corto per variante {variant_num+1}, uso fallback")
        except Exception as e:
            logger.warning(f"❌ Ollama fallito per variante {variant_num+1}: {e}")
    
    # Prova OpenAI
    if OPENAI_AVAILABLE:
        try:
            logger.info(f"🤖 Tentativo con OpenAI per variante {variant_num+1}...")
            result = _generate_simple_with_openai(text, context, variant_num)
            if result and len(result) > 50:
                logger.info(f"✅ Variante {variant_num+1} generata con OpenAI ({len(result)} caratteri)")
                # Valida sillabe se target disponibile
                if target_syllables > 0:
                    result = _validate_and_adjust_syllables(result, target_syllables, target_lines_syllables)
                return result
            else:
                logger.warning(f"⚠️ OpenAI ha generato testo troppo corto per variante {variant_num+1}, uso fallback")
        except Exception as e:
            logger.warning(f"❌ OpenAI fallito per variante {variant_num+1}: {e}")
    
    # Fallback: migliora testo esistente
    logger.info(f"📝 Uso fallback per variante {variant_num+1} (AI non disponibile o fallita)")
    result = _fallback_simple_generation(text, context, variant_num)
    # Valida sillabe se target disponibile
    if target_syllables > 0:
        result = _validate_and_adjust_syllables(result, target_syllables, target_lines_syllables)
    return result


def _generate_simple_with_ollama(text: str, context: str, variant_num: int = 0) -> str:
    """Genera con Ollama usando solo informazioni linguistiche."""
    import time
    import requests
    from requests.exceptions import RequestException, Timeout, ConnectionError as RequestsConnectionError
    
    # Verifica disponibilità Ollama prima di chiamare
    try:
        check_response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if check_response.status_code != 200:
            raise Exception(f"Ollama non disponibile: status {check_response.status_code}")
    except (RequestsConnectionError, Timeout, RequestException) as e:
        raise Exception(f"Ollama non raggiungibile: {str(e)}")
    
    try:
        style_hints = [
            "energetic and powerful",
            "emotional and deep",
            "romantic and tender",
            "mysterious and intriguing",
            "hopeful and uplifting"
        ]
        style = style_hints[variant_num % len(style_hints)]
        
        prompt = f"""You are a professional song lyricist. REMODEL and IMPROVE the transcribed text below into {style} English song lyrics.

{context}

IMPORTANT: 
- REMODEL the original text, don't create completely new lyrics
- Keep the same structure, number of lines, and syllable count
- Fix grammar and make it poetic while preserving the original meaning
- If the original has repetitions, keep them but improve the wording
- Use the key words from the original transcription

Generate the remodeled lyrics now:"""
        
        # Retry logic con timeout progressivo
        max_retries = 2
        timeouts = [90, 120]  # Timeout progressivi
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Tentativo Ollama {attempt + 1}/{max_retries} (timeout: {timeouts[attempt]}s)...")
                
                response = requests.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.8 + (variant_num * 0.1),
                            "top_p": 0.9,
                            "num_predict": 600  # Usa num_predict invece di max_tokens per Ollama
                        }
                    },
                    timeout=timeouts[attempt],
                    headers={"Content-Type": "application/json"}
                )
                
                if response.status_code == 200:
                    generated = response.json().get("response", "").strip()
                    
                    if not generated:
                        raise Exception("Risposta Ollama vuota")
                    
                    # Pulisci output
                    prefixes = ["Here are", "Here's", "The lyrics", "Song lyrics:", "Lyrics:"]
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
                    
                    result = '\n'.join(unique[:30])
                    
                    if result and len(result) >= 50:
                        logger.info(f"✅ Testo generato con Ollama ({len(result)} caratteri)")
                        return result
                    else:
                        raise Exception(f"Testo generato troppo corto: {len(result) if result else 0} caratteri")
                else:
                    error_text = response.text[:200] if response.text else "Nessun dettaglio"
                    raise Exception(f"Ollama error {response.status_code}: {error_text}")
                    
            except Timeout as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⏱️ Timeout Ollama (tentativo {attempt + 1}/{max_retries}), riprovo...")
                    time.sleep(2)  # Aspetta prima di ritentare
                    continue
                else:
                    raise Exception(f"Ollama timeout dopo {max_retries} tentativi: {str(e)}")
                    
            except RequestsConnectionError as e:
                raise Exception(f"Ollama connessione fallita: {str(e)}")
                
            except RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Errore Ollama (tentativo {attempt + 1}/{max_retries}): {str(e)}, riprovo...")
                    time.sleep(2)
                    continue
                else:
                    raise Exception(f"Errore Ollama dopo {max_retries} tentativi: {str(e)}")
        
        raise Exception("Ollama fallito dopo tutti i tentativi")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Errore Ollama semplice: {error_msg}")
        raise Exception(f"Ollama fallito: {error_msg}")


def _generate_simple_with_openai(text: str, context: str, variant_num: int = 0) -> str:
    """Genera con OpenAI usando solo informazioni linguistiche."""
    import time
    from openai import OpenAI, APIError, APIConnectionError, APITimeoutError
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.strip() == "":
        raise Exception("OPENAI_API_KEY non configurata")
    
    # Verifica formato API key
    if not api_key.startswith("sk-") or len(api_key) < 20:
        raise Exception(f"OPENAI_API_KEY non valida (formato errato)")
    
    try:
        client = OpenAI(api_key=api_key, timeout=60.0)
        
        style_hints = [
            "energetic and powerful",
            "emotional and deep",
            "romantic and tender"
        ]
        style = style_hints[variant_num % len(style_hints)]
        
        # Retry logic per OpenAI
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                logger.info(f"🔄 Tentativo OpenAI {attempt + 1}/{max_retries}...")
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": f"You are a {style} song lyricist. Your task is to REMODEL and IMPROVE transcribed text into proper English lyrics, keeping the original meaning and structure."},
                        {"role": "user", "content": f"REMODEL this transcribed text into {style} English song lyrics. Keep the same structure and meaning, but fix grammar and make it poetic:\n\n{context}"}
                    ],
                    max_tokens=600,
                    temperature=0.7 + (variant_num * 0.1),
                    timeout=60.0
                )
                
                if response.choices and len(response.choices) > 0:
                    result = response.choices[0].message.content.strip()
                    if result and len(result) >= 50:
                        logger.info(f"✅ Testo generato con OpenAI ({len(result)} caratteri)")
                        return result
                    else:
                        raise Exception(f"Testo generato troppo corto: {len(result) if result else 0} caratteri")
                else:
                    raise Exception("Risposta OpenAI vuota")
                    
            except APITimeoutError as e:
                if attempt < max_retries - 1:
                    logger.warning(f"⏱️ Timeout OpenAI (tentativo {attempt + 1}/{max_retries}), riprovo...")
                    time.sleep(2)
                    continue
                else:
                    raise Exception(f"OpenAI timeout dopo {max_retries} tentativi: {str(e)}")
                    
            except APIConnectionError as e:
                raise Exception(f"OpenAI connessione fallita: {str(e)}")
                
            except APIError as e:
                error_code = getattr(e, 'code', None)
                error_msg = str(e)
                
                # Se è un errore di API key, non ritentare
                if error_code == 'invalid_api_key' or '401' in error_msg or 'authentication' in error_msg.lower():
                    raise Exception(f"OpenAI API key non valida: verifica la chiave in .env")
                    
                if attempt < max_retries - 1:
                    logger.warning(f"⚠️ Errore OpenAI (tentativo {attempt + 1}/{max_retries}): {error_msg}, riprovo...")
                    time.sleep(2)
                    continue
                else:
                    raise Exception(f"Errore OpenAI dopo {max_retries} tentativi: {error_msg}")
        
        raise Exception("OpenAI fallito dopo tutti i tentativi")
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Errore OpenAI semplice: {error_msg}")
        raise Exception(f"OpenAI fallito: {error_msg}")


def _fallback_simple_generation(text: str, context: str, variant_num: int = 0) -> str:
    """Fallback: rimodella il testo originale invece di usare template generici."""
    logger.info(f"📝 Fallback: rimodellamento testo (variante {variant_num+1})")
    
    if not text or len(text.strip()) < 10:
        return _fallback_enhancement(text)
    
    # Estrai informazioni dal contesto se disponibili
    total_syllables = 0
    lines_syllables = []
    total_lines = 0
    
    for line in context.split('\n'):
        if 'Total syllables:' in line:
            try:
                total_syllables = int(line.split('Total syllables:')[1].strip())
            except:
                pass
        if 'Syllables per line:' in line:
            try:
                syl_str = line.split('Syllables per line:')[1].strip()
                if syl_str != 'N/A':
                    lines_syllables = [int(x.strip()) for x in syl_str.split(',') if x.strip().isdigit()]
            except:
                pass
        if 'Total lines:' in line:
            try:
                total_lines = int(line.split('Total lines:')[1].strip())
            except:
                pass
    
    logger.info(f"📊 Fallback usa: {total_syllables} sillabe totali, {total_lines} righe, {len(lines_syllables)} righe con conteggio sillabe")
    
    # Dividi il testo in frasi (usa punti, virgole, o pattern comuni)
    import re
    # Prima prova a dividere per punti/virgole
    sentences = re.split(r'[.!?]\s+', text)
    if len(sentences) == 1:
        # Se non ci sono punti, dividi per virgole
        sentences = re.split(r',\s+', text)
        # Dopo ogni virgola, controlla se c'è una maiuscola (nuova frase)
        # Pattern: minuscola + spazio + maiuscola = nuova frase
        new_sentences = []
        for sent in sentences:
            # Dividi anche quando c'è una maiuscola dopo una minuscola (es: "fine We get")
            parts = re.split(r'([a-z])\s+([A-Z])', sent)
            if len(parts) > 1:
                # Ricostruisci le frasi
                current = parts[0]
                for i in range(1, len(parts), 3):
                    if i+1 < len(parts):
                        new_sentences.append(current + parts[i])
                        current = parts[i+1] + (parts[i+2] if i+2 < len(parts) else '')
                if current:
                    new_sentences.append(current)
            else:
                new_sentences.append(sent)
        sentences = [s.strip() for s in new_sentences if s.strip()]
        
        # Se ancora poche frasi, dividi per pattern comuni
        if len(sentences) <= 2:
            sentences = re.split(r'\s+(We\'re|we\'re|I\'m|i\'m|We get|we get|We\'re getting|we\'re getting|and)\s+', text)
            sentences = [s.strip() for s in sentences if s.strip() and s.lower() not in ["we're", "i'm", "we get", "we're getting", "and"]]
    
    # Pulisci e capitalizza
    cleaned_sentences = []
    for sent in sentences:
        sent = sent.strip()
        if sent and len(sent) > 3:
            # Capitalizza prima lettera
            sent = sent[0].upper() + sent[1:] if len(sent) > 1 else sent.upper()
            # Rimuovi punteggiatura finale eccessiva
            sent = re.sub(r'[.!?]+$', '', sent)
            cleaned_sentences.append(sent)
    
    # Rimuovi ripetizioni eccessive
    seen = {}
    unique_sentences = []
    for sent in cleaned_sentences:
        sent_lower = sent.lower()
        if sent_lower not in seen:
            seen[sent_lower] = 1
            unique_sentences.append(sent)
        elif seen[sent_lower] < 2:  # Permetti 2 ripetizioni max
            seen[sent_lower] += 1
            unique_sentences.append(sent)
    
    # Se il testo è troppo breve, espandilo con variazioni poetiche
    if len(unique_sentences) < 2:
        return _expand_short_text(text, context, variant_num, total_syllables, total_lines)
    
    # Crea varianti diverse basate su variant_num
    # Usa hash del testo per variare l'ordine in modo determinista ma diverso per ogni variante
    import hashlib
    text_hash = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
    
    # Variante 0: Mantieni struttura originale, migliora grammatica, ordine originale
    # Variante 1: Riorganizza in strofe, ordine variato
    # Variante 2: Enfatizza il chorus, ordine diverso
    
    if variant_num == 0:
        # Variante base: migliora grammatica, mantieni ordine originale
        result = "\n".join(unique_sentences[:min(8, len(unique_sentences))])
    elif variant_num == 1:
        # Variante 2: organizza in strofe con ordine variato
        # Mescola leggermente l'ordine basandosi su variant_num e hash
        shuffled = list(unique_sentences[:min(8, len(unique_sentences))])
        # Mescola in modo determinista
        seed = (text_hash + variant_num) % 1000
        for i in range(len(shuffled) - 1, 0, -1):
            j = (seed + i) % (i + 1)
            shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
        
        verses = []
        chorus_line = None
        
        # Identifica la frase più ripetuta come chorus
        sentence_counts = {}
        for sent in cleaned_sentences:
            sent_lower = sent.lower()
            sentence_counts[sent_lower] = sentence_counts.get(sent_lower, 0) + 1
        
        if sentence_counts:
            most_repeated = max(sentence_counts.items(), key=lambda x: x[1])
            if most_repeated[1] >= 2:
                # Trova la versione originale
                for sent in cleaned_sentences:
                    if sent.lower() == most_repeated[0]:
                        chorus_line = sent
                        break
        
        # Dividi in versi (ogni 2-3 frasi), escludi chorus
        current_verse = []
        for sent in shuffled:
            if not chorus_line or sent.lower() != chorus_line.lower():
                current_verse.append(sent)
                if len(current_verse) >= 2:
                    verses.append("\n".join(current_verse))
                    current_verse = []
        if current_verse:
            verses.append("\n".join(current_verse))
        
        result = "\n\n".join(verses[:3])  # Max 3 versi
        if chorus_line:
            result += f"\n\n(Chorus)\n{chorus_line}"
    else:
        # Variante 2: Enfatizza struttura con ordine diverso
        # Prendi frasi in ordine diverso
        selected = list(unique_sentences[:min(6, len(unique_sentences))])
        # Ordine alternativo: prima, ultima, seconda, penultima, ecc.
        reordered = []
        for i in range(len(selected) // 2):
            reordered.append(selected[i])
            if i < len(selected) - 1 - i:
                reordered.append(selected[len(selected) - 1 - i])
        if len(selected) % 2 == 1 and len(selected) > 1:
            reordered.append(selected[len(selected) // 2])
        
        verses_text = "\n".join(reordered[:4])
        # Identifica chorus (frasi ripetute)
        repeated = [s for s in cleaned_sentences if cleaned_sentences.count(s) >= 2]
        if repeated:
            chorus = repeated[0]
            result = f"{verses_text}\n\n(Chorus)\n{chorus}"
        else:
            # Se non c'è chorus, usa l'ultima frase ripetuta come chorus
            if len(unique_sentences) > 4:
                result = f"{verses_text}\n\n(Chorus)\n{unique_sentences[-1]}"
            else:
                result = verses_text
    
    # Se il risultato è troppo breve (meno di 3 righe), espandilo
    if result.count('\n') < 2:
        result = _expand_short_text(text, context, variant_num, total_syllables, total_lines)
    
    return result


def _expand_short_text(text: str, context: str, variant_num: int, total_syllables: int, total_lines: int) -> str:
    """
    Espande testo breve (1-2 righe) in più righe poetiche mantenendo tema e sillabe.
    """
    if not text or len(text.strip()) < 5:
        return _fallback_enhancement(text)
    
    # Pulisci testo base
    base_text = text.strip()
    # Rimuovi ripetizioni alla fine
    base_text = base_text.split('\n')[0].strip()
    
    # Estrai parole chiave
    words = base_text.lower().split()
    key_words = [w.strip('.,!?;:"()[]{}') for w in words if len(w) > 2]
    
    # Estrai tema/soggetto dalla frase
    theme = None
    if 'time' in base_text.lower():
        theme = 'time'
    elif 'come' in base_text.lower() or 'coming' in base_text.lower():
        theme = 'coming'
    elif 'going' in base_text.lower() or 'go' in base_text.lower():
        theme = 'journey'
    elif 'feel' in base_text.lower() or 'feeling' in base_text.lower():
        theme = 'emotions'
    elif 'pain' in base_text.lower() or 'hurt' in base_text.lower():
        theme = 'pain'
    elif 'love' in base_text.lower():
        theme = 'love'
    else:
        # Usa la prima parola sostantiva come tema
        theme = key_words[0] if key_words else 'life'
    
    # Crea variazioni poetiche basate sul tema e variant_num
    # Ogni variante ha un tono diverso ma mantiene il tema originale
    
    expansions = {
        0: {  # Variante 1: Diretta ed espansiva
            'time': [
                "It's a time to come",
                "A moment we've been waiting for",
                "The future is calling",
                "We can't ignore"
            ],
            'coming': [
                "It's a time to come",
                "Through the darkness we will run",
                "Finding light in every step",
                "Never giving up"
            ],
            'journey': [
                "It's a time to come",
                "On this road we're traveling on",
                "Every step a new beginning",
                "Until we find our way"
            ],
            'emotions': [
                "It's a time to come",
                "Feeling everything we've known",
                "Letting go of what we had",
                "Moving forward now"
            ],
            'pain': [
                "It's a time to come",
                "Leaving all the pain behind",
                "Finding strength within ourselves",
                "Starting fresh again"
            ],
            'love': [
                "It's a time to come",
                "Love is calling out to us",
                "Opening our hearts again",
                "Believing in tomorrow"
            ],
            'default': [
                "It's a time to come",
                "Changing everything we know",
                "Moving forward in the light",
                "Seeing where we go"
            ]
        },
        1: {  # Variante 2: Emotiva
            'time': [
                "It's a time to come",
                "When all the waiting's done",
                "We'll see what's ahead",
                "No need to fear instead"
            ],
            'coming': [
                "It's a time to come",
                "Overcoming what we've known",
                "Breaking free from yesterday",
                "In a brand new way"
            ],
            'journey': [
                "It's a time to come",
                "Walking roads we've never seen",
                "Every moment is a chance",
                "To learn and to advance"
            ],
            'emotions': [
                "It's a time to come",
                "All the feelings rushing in",
                "Every heartbeat tells a tale",
                "That we cannot fail"
            ],
            'pain': [
                "It's a time to come",
                "Healing wounds that we have felt",
                "Rising up from where we fell",
                "Our story we will tell"
            ],
            'love': [
                "It's a time to come",
                "Love will find us where we are",
                "In the silence of the night",
                "Everything feels right"
            ],
            'default': [
                "It's a time to come",
                "Everything is changing now",
                "In the rhythm of our hearts",
                "A brand new start"
            ]
        },
        2: {  # Variante 3: Narrativa
            'time': [
                "It's a time to come",
                "The clock is ticking on",
                "We've been waiting for so long",
                "Now the moment's here"
            ],
            'coming': [
                "It's a time to come",
                "From the shadows we emerge",
                "Standing tall and feeling strong",
                "This is where we belong"
            ],
            'journey': [
                "It's a time to come",
                "On this path we're walking through",
                "Every mile brings something new",
                "Seeing life anew"
            ],
            'emotions': [
                "It's a time to come",
                "All emotions flow like streams",
                "In our hearts and in our dreams",
                "Nothing's what it seems"
            ],
            'pain': [
                "It's a time to come",
                "Leaving sorrow far behind",
                "In our hearts and in our mind",
                "Peace we'll finally find"
            ],
            'love': [
                "It's a time to come",
                "Love is in the air we breathe",
                "In every moment we receive",
                "Something to believe"
            ],
            'default': [
                "It's a time to come",
                "Everything begins again",
                "In the sun and in the rain",
                "Nothing feels the same"
            ]
        }
    }
    
    theme_expansions = expansions.get(variant_num, expansions[0])
    lines = theme_expansions.get(theme, theme_expansions['default'])
    
    # Adatta il numero di righe se total_lines è specificato
    if total_lines > 0 and total_lines < len(lines):
        lines = lines[:total_lines]
    elif total_lines > len(lines):
        # Aggiungi più righe se necessario
        while len(lines) < total_lines and len(lines) < 8:
            lines.append(lines[-1])  # Ripeti ultima riga
    
    # Se total_syllables è specificato, cerca di adattare
    # (semplificato: se le righe sono troppo poche, aggiungi chorus)
    if len(lines) >= 4:
        # Formatta come versi + chorus
        verses = lines[:2] if len(lines) >= 4 else lines[:1]
        chorus = lines[2] if len(lines) >= 3 else lines[-1]
        result = "\n".join(verses)
        if len(lines) >= 3:
            result += f"\n\n(Chorus)\n{chorus}"
            if len(lines) > 3:
                result += f"\n\n{lines[3]}"
    else:
        result = "\n".join(lines[:4])
    
    logger.info(f"📝 Testo breve espanso: {len(lines)} righe da '{base_text}'")
    
    return result


def _validate_and_adjust_syllables(text: str, target_syllables: int, target_lines_syllables: list = None) -> str:
    """
    Valida e aggiusta sillabe nel testo generato.
    Se la differenza è troppo grande, prova a correggere.
    """
    from syllable_counter import count_syllables_in_text
    
    if not text or target_syllables <= 0:
        return text
    
    # Conta sillabe generate
    generated_syllables = count_syllables_in_text(text)
    generated_total = generated_syllables.get("total_syllables", 0)
    generated_lines = generated_syllables.get("lines_syllables", [])
    
    # Calcola differenza
    diff = abs(generated_total - target_syllables)
    diff_percent = (diff / target_syllables * 100) if target_syllables > 0 else 0
    
    # Se la differenza è accettabile (<20%), ritorna testo originale
    if diff_percent < 20:
        logger.info(f"✅ Sillabe validate: {generated_total}/{target_syllables} (diff: {diff}, {diff_percent:.1f}%) - OK")
        return text
    
    # Se la differenza è grande, prova a correggere
    logger.warning(f"⚠️  Sillabe non corrispondono: {generated_total}/{target_syllables} (diff: {diff}, {diff_percent:.1f}%) - provo correzione")
    
    # Strategia: se il testo ha troppe poche sillabe, aggiungi parole brevi
    # Se ha troppe, rimuovi parole non essenziali
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    if generated_total < target_syllables:
        # Aggiungi sillabe: inserisci parole brevi (1-2 sillabe) dove appropriato
        needed = target_syllables - generated_total
        logger.info(f"📝 Aggiungo ~{needed} sillabe mancanti")
        # Per ora, solo log - correzione automatica complessa
        # In futuro: inserire parole brevi semanticamente appropriate
    elif generated_total > target_syllables:
        # Rimuovi sillabe: rimuovi parole non essenziali
        excess = generated_total - target_syllables
        logger.info(f"📝 Rimuovo ~{excess} sillabe in eccesso")
        # Per ora, solo log - correzione automatica complessa
        # In futuro: rimuovere parole non essenziali
    
    # Per ora ritorna testo originale con warning
    # In futuro: implementare correzione automatica più sofisticata
    return text


