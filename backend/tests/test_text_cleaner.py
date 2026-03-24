"""
Test per text_cleaner.py
"""
import pytest
from unittest.mock import Mock, patch


class TestCleanAndFilterText:
    """Test per pulizia e filtaggio testo."""
    
    def test_clean_and_filter_text_basic(self):
        """Test pulizia base."""
        from text_cleaner import clean_and_filter_text
        
        result = clean_and_filter_text("  Hello   World  ")
        
        assert result is not None
        assert isinstance(result, dict)
        assert "cleaned_text" in result
    
    def test_clean_and_filter_text_with_repetitions(self):
        """Test con ripetizioni."""
        from text_cleaner import clean_and_filter_text
        
        result = clean_and_filter_text("la la la la hello")
        
        assert result is not None
    
    def test_clean_and_filter_text_empty(self):
        """Test con testo vuoto."""
        from text_cleaner import clean_and_filter_text
        
        result = clean_and_filter_text("")
        
        assert result is not None


class TestSplitIntoSentences:
    """Test divisione in frasi."""
    
    def test_split_into_sentences(self):
        """Test divisione frasi."""
        from text_cleaner import _split_into_sentences
        
        result = _split_into_sentences("Hello world. Test sentence.")
        
        assert result is not None
        assert isinstance(result, list)
        assert len(result) >= 1


class TestRemoveExcessiveRepetitions:
    """Test rimozione ripetizioni eccessive."""
    
    def test_remove_excessive_repetitions(self):
        """Test rimozione ripetizioni."""
        from text_cleaner import _remove_excessive_repetitions
        
        sentences = ["hello", "hello", "hello", "world"]
        
        result, stats = _remove_excessive_repetitions(sentences)
        
        assert result is not None
        assert stats is not None
        assert isinstance(result, list)
        assert isinstance(stats, dict)


class TestImproveGrammar:
    """Test miglioramento grammatica."""
    
    def test_improve_grammar(self):
        """Test miglioramento grammatica."""
        from text_cleaner import _improve_grammar
        
        sentences = ["hello world", "test sentence"]
        
        result = _improve_grammar(sentences)
        
        assert result is not None
        assert isinstance(result, list)


class TestValidateTextQuality:
    """Test validazione qualità testo."""
    
    def test_validate_text_quality(self):
        """Test validazione qualità."""
        from text_cleaner import validate_text_quality
        
        result = validate_text_quality("Original", "Cleaned")
        
        assert result is not None
        assert isinstance(result, dict)
    
    def test_validate_empty_texts(self):
        """Test con testi vuoti."""
        from text_cleaner import validate_text_quality
        
        result = validate_text_quality("", "")
        
        assert result is not None


class TestCleanGeneratedText:
    """Test pulizia testo generato."""
    
    def test_clean_generated_text(self):
        """Test pulizia testo generato."""
        from text_cleaner import clean_generated_text
        
        result = clean_generated_text("  Generated   Text  ")
        
        assert result is not None
        assert isinstance(result, str)
    
    def test_clean_generated_text_with_repetitions(self):
        """Test con ripetizioni."""
        from text_cleaner import clean_generated_text
        
        result = clean_generated_text("la la la test")
        
        assert result is not None
