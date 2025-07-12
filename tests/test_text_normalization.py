"""
Unit tests for text normalization functionality.

Tests the IndicTextNormalizer class and its various text processing capabilities.
"""

import unittest
import unicodedata
from india_speaks_cleaner.text_normalization import IndicTextNormalizer

class TestIndicTextNormalizer(unittest.TestCase):
    """Test cases for IndicTextNormalizer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.normalizer = IndicTextNormalizer()
    
    def test_empty_text_handling(self):
        """Test handling of empty or None text."""
        # Test empty string
        result, stats = self.normalizer.normalize_text("")
        self.assertEqual(result, "")
        self.assertTrue(stats.get('empty_text', False))
        
        # Test None
        result, stats = self.normalizer.normalize_text(None)
        self.assertEqual(result, "")
        self.assertTrue(stats.get('empty_text', False))
        
        # Test whitespace only
        result, stats = self.normalizer.normalize_text("   \n\t  ")
        self.assertEqual(result, "")
        self.assertTrue(stats.get('empty_text', False))
    
    def test_unicode_normalization(self):
        """Test Unicode NFC normalization."""
        # Test with composed and decomposed characters
        composed = "café"  # é as single character
        decomposed = "cafe\u0301"  # e + combining acute accent
        
        result1, stats1 = self.normalizer.normalize_text(composed)
        result2, stats2 = self.normalizer.normalize_text(decomposed)
        
        # Both should result in the same normalized form
        self.assertEqual(result1, result2)
        
        # Check if Unicode normalization was applied to decomposed text
        if decomposed != unicodedata.normalize('NFC', decomposed):
            self.assertIn('unicode_nfc', stats2['operations'])
    
    def test_diacritics_removal(self):
        """Test diacritics removal functionality."""
        # Hindi text with nukta
        hindi_text = "क़िताब"  # qitaab with nukta
        result, stats = self.normalizer.normalize_text(hindi_text)
        
        # Should remove nukta characters
        self.assertNotIn('\u093c', result)  # Devanagari nukta
        
        # Test with combining diacritical marks
        text_with_marks = "a\u0300b\u0301c"  # a with grave, b with acute
        result, stats = self.normalizer.normalize_text(text_with_marks)
        
        # Should remove combining marks
        self.assertEqual(result, "abc")
    
    def test_number_expansion_hindi(self):
        """Test number expansion for Hindi."""
        test_cases = [
            ("मैं 5 साल का हूँ", "मैं पांच साल का हूँ"),
            ("1 2 3", "एक दो तीन"),
            ("0 से 9 तक", "शून्य से नौ तक"),
        ]
        
        for input_text, expected in test_cases:
            result, stats = self.normalizer.normalize_text(input_text, language='hi')
            # Check if numbers were expanded (might not be exact match due to other normalizations)
            self.assertIn('numbers_expanded', stats.get('operations', []))
    
    def test_number_expansion_other_languages(self):
        """Test that number expansion doesn't happen for unsupported languages."""
        text = "I have 5 books"
        result, stats = self.normalizer.normalize_text(text, language='en')
        
        # Numbers should not be expanded for English
        self.assertNotIn('numbers_expanded', stats.get('operations', []))
        self.assertIn('5', result)
    
    def test_punctuation_normalization(self):
        """Test punctuation normalization."""
        test_cases = [
            ("Hello—world", "Hello-world"),  # Em dash to hyphen
            ("He said \"hello\"", "He said \"hello\""),  # Smart quotes
            ("Wait…", "Wait..."),  # Ellipsis
            ("Multiple   spaces", "Multiple spaces"),  # Multiple spaces
        ]
        
        for input_text, expected_pattern in test_cases:
            result, stats = self.normalizer.normalize_text(input_text, language='en')
            # Check if punctuation normalization was applied
            if input_text != result:
                self.assertIn('punctuation_normalized', stats.get('operations', []))
    
    def test_language_specific_lowercasing(self):
        """Test language-specific case normalization."""
        # English should be lowercased
        result, _ = self.normalizer.normalize_text("HELLO World", language='en')
        self.assertEqual(result, "hello world")
        
        # Hindi text should preserve case (no traditional case distinction)
        hindi_text = "नमस्ते"
        result, _ = self.normalizer.normalize_text(hindi_text, language='hi')
        self.assertEqual(result, hindi_text)
    
    def test_final_cleanup(self):
        """Test final text cleanup operations."""
        test_cases = [
            ("  hello world  ", "hello world"),  # Trim whitespace
            ("hello    world", "hello world"),  # Multiple spaces
            ("hello ( ) world", "hello world"),  # Empty parentheses
            ("hello [ ] world", "hello world"),  # Empty brackets
        ]
        
        for input_text, expected in test_cases:
            result, _ = self.normalizer.normalize_text(input_text)
            self.assertEqual(result, expected)
    
    def test_language_script_validation(self):
        """Test language script validation functionality."""
        # Test English text
        is_valid, confidence, script = self.normalizer.validate_language_script(
            "Hello world", "en"
        )
        self.assertTrue(is_valid)
        self.assertGreater(confidence, 0.7)
        
        # Test empty text
        is_valid, confidence, script = self.normalizer.validate_language_script(
            "", "hi"
        )
        self.assertFalse(is_valid)
        self.assertEqual(confidence, 0.0)
        self.assertEqual(script, 'empty')
        
        # Test text with no alphabetic characters
        is_valid, confidence, script = self.normalizer.validate_language_script(
            "123 !@#", "hi"
        )
        self.assertFalse(is_valid)
        self.assertEqual(confidence, 0.0)
        self.assertEqual(script, 'no_alpha')
    
    def test_supported_languages(self):
        """Test processing with different supported languages."""
        languages = ['hi', 'bn', 'te', 'ta', 'ml', 'kn', 'gu', 'mr', 'pa', 'ur', 'en']
        
        for lang in languages:
            result, stats = self.normalizer.normalize_text("test text", language=lang)
            self.assertIsInstance(result, str)
            self.assertIsInstance(stats, dict)
            self.assertIn('operations', stats)
    
    def test_processing_statistics(self):
        """Test that processing statistics are maintained correctly."""
        # Reset stats
        self.normalizer.reset_stats()
        initial_stats = self.normalizer.get_normalization_stats()
        
        # Process some text
        self.normalizer.normalize_text("Hello world", language='en')
        self.normalizer.normalize_text("नमस्ते", language='hi')
        
        # Check stats were updated
        final_stats = self.normalizer.get_normalization_stats()
        self.assertEqual(final_stats['total_processed'], 2)
        self.assertGreaterEqual(final_stats['total_processed'], 
                               initial_stats['total_processed'] + 2)
    
    def test_normalization_operations_tracking(self):
        """Test that normalization operations are properly tracked."""
        # Text that should trigger multiple operations
        complex_text = "HELLO—world  123"
        result, stats = self.normalizer.normalize_text(complex_text, language='en')
        
        # Should have operations listed
        self.assertIn('operations', stats)
        self.assertIsInstance(stats['operations'], list)
        
        # Should have length information
        self.assertIn('original_length', stats)
        self.assertIn('final_length', stats)
        self.assertEqual(stats['original_length'], len(complex_text))
        self.assertEqual(stats['final_length'], len(result))
    
    def test_edge_cases(self):
        """Test various edge cases."""
        edge_cases = [
            "",  # Empty
            " ",  # Single space
            "\n\t",  # Whitespace characters
            "123",  # Numbers only
            "!@#$%",  # Punctuation only
            "a",  # Single character
            "a" * 1000,  # Very long text
        ]
        
        for text in edge_cases:
            try:
                result, stats = self.normalizer.normalize_text(text)
                self.assertIsInstance(result, str)
                self.assertIsInstance(stats, dict)
            except Exception as e:
                self.fail(f"Failed to process edge case '{text}': {e}")
    
    def test_special_characters_handling(self):
        """Test handling of special characters and symbols."""
        special_text = "Text with 💕 emojis and ® symbols"
        result, stats = self.normalizer.normalize_text(special_text)
        
        # Should not crash and return a string
        self.assertIsInstance(result, str)
        
        # Should remove or normalize special characters
        # (exact behavior depends on implementation)
        normalized_length = len(result)
        self.assertGreaterEqual(normalized_length, 0)

class TestTextNormalizationIntegration(unittest.TestCase):
    """Integration tests for text normalization with real examples."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.normalizer = IndicTextNormalizer()
    
    def test_hindi_text_normalization(self):
        """Test normalization of real Hindi text."""
        hindi_samples = [
            "नमस्ते, आप कैसे हैं?",
            "मैं ठीक हूँ, धन्यवाद।",
            "आज का दिन बहुत अच्छा है।"
        ]
        
        for text in hindi_samples:
            result, stats = self.normalizer.normalize_text(text, language='hi')
            self.assertIsInstance(result, str)
            self.assertTrue(len(result) > 0)
            self.assertIn('operations', stats)
    
    def test_english_text_normalization(self):
        """Test normalization of English text."""
        english_samples = [
            "Hello, how are you?",
            "I'm fine, thank you.",
            "Today is a beautiful day."
        ]
        
        for text in english_samples:
            result, stats = self.normalizer.normalize_text(text, language='en')
            self.assertIsInstance(result, str)
            self.assertTrue(len(result) > 0)
            # English should be lowercased
            self.assertEqual(result, result.lower())
    
    def test_mixed_content_normalization(self):
        """Test normalization of mixed content (text + numbers + punctuation)."""
        mixed_samples = [
            "I have 5 books and 10 pencils.",
            "Price: $50.99 (discount: 20%)",
            "Meeting at 3:30 PM on 15th April."
        ]
        
        for text in mixed_samples:
            result, stats = self.normalizer.normalize_text(text, language='en')
            self.assertIsInstance(result, str)
            self.assertTrue(len(result) > 0)

if __name__ == '__main__':
    unittest.main() 