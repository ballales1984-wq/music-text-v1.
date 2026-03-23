"""
Text generation infrastructure adapters.
"""
import logging
import os
from pathlib import Path
from typing import Dict, Protocol, Optional

from domain.errors import TextGenerationError

logger = logging.getLogger(__name__)


class TextGenerator(Protocol):
    """Protocol for text generation implementations."""
    def generate(self, transcription: str, mood: str = None, style: str = None) -> str:
        """Generate lyrics from transcription."""
        ...


class OllamaGenerator:
    """Ollama-based text generator."""
    
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3")
        self._available = self._check_availability()
    
    def _check_availability(self) -> bool:
        """Check if Ollama is available."""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                # Find best model
                models = response.json().get("models", [])
                for m in models:
                    name = m.get("name", "")
                    if "llama3" in name and "coder" not in name.lower():
                        self.model = name.split(":")[0]
                        break
                    elif "mistral" in name.lower():
                        self.model = name.split(":")[0]
                logger.info(f"Ollama available with model: {self.model}")
                return True
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")
        return False
    
    def generate(self, transcription: str, mood: str = None, style: str = None) -> str:
        """Generate lyrics using Ollama."""
        if not self._available:
            raise TextGenerationError("Ollama not available")
        
        import requests
        
        # Mood and style mapping
        mood_map = {
            "happy": "upbeat, joyful, optimistic",
            "sad": "melancholic, emotional, reflective",
            "angry": "intense, powerful, rebellious",
            "romantic": "love, passionate, tender",
            "dreamy": "atmospheric, ethereal, peaceful",
            "energetic": "dynamic, exciting, high-energy"
        }
        
        style_map = {
            "pop": "Verse + Chorus structure",
            "rock": "Intro + Verse + Pre-Chorus + Chorus + Bridge",
            "rap": "Verse + Hook pattern",
            "ballad": "slow, emotional verses",
            "electronic": "drop and build sections",
            "folk": "acoustic verse + chorus"
        }
        
        mood_str = mood_map.get(mood, "poetic and meaningful") if mood else "poetic and meaningful"
        style_str = style_map.get(style, "verse and chorus") if style else "verse and chorus"
        
        prompt = f"""You are a professional songwriter.

Write clean, natural, and emotionally coherent English song lyrics based on this rough vocal transcription.

RULES:
- Always write lyrics (never explanations)
- Never mention AI or refuse
- Fix incorrect or broken words
- Keep it singable and rhythmic
- Follow the {style_str} structure

MOOD: {mood_str}

INPUT:
{transcription}

OUTPUT:"""
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": 400
                    }
                },
                timeout=120
            )
            
            if response.status_code != 200:
                raise Exception(f"Ollama error: {response.status_code}")
            
            result = response.json().get("response", "").strip()
            
            # Validate
            if not result or len(result.split()) < 20:
                raise TextGenerationError("Generated text too short")
            if "ai model" in result.lower() or "i'm sorry" in result.lower():
                raise TextGenerationError("AI refused to generate lyrics")
            
            return result
            
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise TextGenerationError(f"Generation failed: {e}")


class OpenAIGenerator:
    """OpenAI-based text generator."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._available = bool(self.api_key)
    
    def generate(self, transcription: str, mood: str = None, style: str = None) -> str:
        """Generate lyrics using OpenAI."""
        if not self._available:
            raise TextGenerationError("OpenAI not available")
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            mood_str = mood or "emotional"
            style_str = style or "pop"
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional songwriter."},
                    {"role": "user", "content": f"Write song lyrics based on: {transcription}. Mood: {mood_str}. Style: {style_str}"}
                ],
                temperature=0.7,
                max_tokens=500
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise TextGenerationError(f"Generation failed: {e}")


class FallbackGenerator:
    """Fallback generator when no AI is available."""
    
    def generate(self, transcription: str, mood: str = None, style: str = None) -> str:
        """Generate basic lyrics from transcription keywords."""
        words = transcription.lower().split()
        keywords = [w.strip('.,!?;:"()[]{}') for w in words if len(w) > 3][:5]
        
        if keywords:
            theme = keywords[0]
        else:
            theme = "feelings"
        
        return f"""[Verse 1]
{theme.capitalize()} in the air tonight
Something feels so right
Through the music we share
Every moment takes us there

[Chorus]
In the rhythm of our hearts
We can make new starts
Following the sound
Where love can be found"""


# Factory function
def create_text_generator() -> TextGenerator:
    """Create the appropriate text generator based on availability."""
    # Try Ollama first (local, free)
    try:
        return OllamaGenerator()
    except Exception:
        pass
    
    # Try OpenAI
    try:
        return OpenAIGenerator()
    except Exception:
        pass
    
    # Fallback
    return FallbackGenerator()
