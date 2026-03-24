"""
Test per lyrics_generator_simple.py
"""
import pytest
from unittest.mock import Mock, patch


class TestCleanText:
    """Test per pulizia testo."""
    
    def test_clean_text_basic(self):
        """Test pulizia base testo."""
        from lyrics_generator_simple import clean_text
        
        result = clean_text("  HELLO World  ")
        
        assert result is not None
        assert "hello" in result
        assert "world" in result
    
    def test_clean_text_empty(self):
        """Test pulizia testo vuoto."""
        from lyrics_generator_simple import clean_text
        
        result = clean_text("")
        
        assert result == ""


class TestIsValidLyrics:
    """Test validazione lyrics."""
    
    def test_is_valid_lyrics_empty(self):
        """Test lyrics vuoto."""
        from lyrics_generator_simple import is_valid_lyrics
        
        assert is_valid_lyrics("") is False
    
    def test_is_valid_lyrics_only_spaces(self):
        """Test lyrics con solo spazi."""
        from lyrics_generator_simple import is_valid_lyrics
        
        assert is_valid_lyrics("   ") is False
    
    def test_is_valid_lyrics_none(self):
        """Test lyrics None."""
        from lyrics_generator_simple import is_valid_lyrics
        
        assert is_valid_lyrics(None) is False


class TestGenerateLyricsRobust:
    """Test generazione lyrics robusta."""
    
    @patch('lyrics_generator_simple.OPENAI_AVAILABLE', False)
    @patch('lyrics_generator_simple.OLLAMA_AVAILABLE', False)
    def test_generate_fallback(self):
        """Test fallback quando nessun AI disponibile."""
        from lyrics_generator_simple import generate_lyrics_robust
        
        result = generate_lyrics_robust(
            transcription="hello world test",
            mood="neutral",
            style="pop"
        )
        
        assert result is not None
        assert isinstance(result, str)


class TestFallbackEnhance:
    """Test fallback enhancement."""
    
    def test_fallback_enhance(self):
        """Test fallback miglioramento."""
        from lyrics_generator_simple import _fallback_enhance
        
        result = _fallback_enhance("Original text")
        
        assert result is not None
        assert isinstance(result, str)


class TestFallbackGenerateImproved:
    """Test fallback generazione migliorata."""
    
    def test_fallback_generate_improved(self):
        """Test generazione fallback migliorata."""
        from lyrics_generator_simple import _fallback_generate_improved
        
        result = _fallback_generate_improved("test sounds", "pop")
        
        assert result is not None
        assert isinstance(result, str)
    
    def test_fallback_generate_with_context(self):
        """Test generazione con context."""
        from lyrics_generator_simple import _fallback_generate_improved
        
        result = _fallback_generate_improved("hello", "ballad")
        
        assert result is not None


class TestGenerateEnglishTextFromVocals:
    """Test generazione testo da vocals."""
    
    @patch('lyrics_generator_simple.OPENAI_AVAILABLE', False)
    @patch('lyrics_generator_simple.OLLAMA_AVAILABLE', False)
    def test_generate_from_vocals(self):
        """Test generazione da vocals."""
        from lyrics_generator_simple import generate_english_text_from_vocals
        
        transcription_data = {
            "text": "hello world",
            "segments": [
                {"start": 0, "end": 2, "text": "hello"},
                {"start": 2, "end": 4, "text": "world"}
            ]
        }
        
        result = generate_english_text_from_vocals(
            transcription_data=transcription_data,
            mood="happy",
            style="pop"
        )
        
        assert result is not None
        assert isinstance(result, str)
