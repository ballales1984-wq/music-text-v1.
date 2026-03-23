"""
Tests for infrastructure adapters.
"""
import pytest
from pathlib import Path
import tempfile
import shutil

from infrastructure.text_generation import (
    FallbackGenerator,
    TextGenerator
)


class TestFallbackGenerator:
    """Test FallbackGenerator."""
    
    def test_generate_basic_lyrics(self):
        """Test basic lyrics generation."""
        generator = FallbackGenerator()
        
        result = generator.generate("dark night feelings")
        
        assert len(result) > 0
        assert "[Verse" in result or "[Chorus" in result
    
    def test_generate_with_keywords(self):
        """Test generation with specific keywords."""
        generator = FallbackGenerator()
        
        result = generator.generate("love heart feeling")
        
        # Should use keywords
        assert "love" in result.lower() or "heart" in result.lower()
    
    def test_generate_returns_structure(self):
        """Test that output has verse/chorus structure."""
        generator = FallbackGenerator()
        
        result = generator.generate("test transcription")
        
        # Should have verse and chorus markers
        assert "[" in result
        assert "Verse" in result or "Chorus" in result


class TestTextGeneratorProtocol:
    """Test TextGenerator protocol compliance."""
    
    def test_fallback_conforms_to_protocol(self):
        """Test FallbackGenerator conforms to TextGenerator protocol."""
        generator = FallbackGenerator()
        
        # Should have generate method
        assert hasattr(generator, "generate")
        assert callable(generator.generate)
        
        # Should be callable with transcription
        result = generator.generate("test text")
        assert isinstance(result, str)
        assert len(result) > 0
