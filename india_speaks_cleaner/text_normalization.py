"""
Text normalization utilities for Indic languages.

Handles diacritics removal, number expansion, punctuation handling,
language-specific lowercasing, and Unicode normalization (NFC).
"""

import re
import unicodedata
from typing import Dict, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class IndicTextNormalizer:
    """Text normalizer for Indic languages following India Speaks data standards."""
    
    # Language-specific mappings
    LANGUAGE_SCRIPTS = {
        'hi': 'Devanagari',    # Hindi
        'bn': 'Bengali',       # Bengali  
        'te': 'Telugu',        # Telugu
        'ta': 'Tamil',         # Tamil
        'ml': 'Malayalam',     # Malayalam
        'kn': 'Kannada',       # Kannada
        'gu': 'Gujarati',      # Gujarati
        'mr': 'Devanagari',    # Marathi
        'pa': 'Gurmukhi',      # Punjabi
        'ur': 'Arabic',        # Urdu
        'en': 'Latin'          # English
    }
    
    # Common Indic diacritics patterns
    DIACRITIC_PATTERNS = [
        (r'[\u0300-\u036f]', ''),  # Combining diacritical marks
        (r'[\u093c]', ''),         # Devanagari nukta
        (r'[\u09bc]', ''),         # Bengali nukta
        (r'[\u0a3c]', ''),         # Gurmukhi nukta
        (r'[\u0abc]', ''),         # Gujarati nukta
        (r'[\u0b3c]', ''),         # Oriya nukta
        (r'[\u0c3c]', ''),         # Telugu nukta
    ]
    
    # Number expansion mappings (Hindi numerals to words)
    NUMBER_WORDS_HI = {
        '0': 'शून्य', '1': 'एक', '2': 'दो', '3': 'तीन', '4': 'चार',
        '5': 'पांच', '6': 'छह', '7': 'सात', '8': 'आठ', '9': 'नौ'
    }
    
    # Common punctuation to remove or normalize
    PUNCTUATION_PATTERNS = [
        (r'[।॥]', '.'),           # Devanagari danda to period
        (r'[\u2018\u2019\u201B]', "'"),          # Smart single quotes to straight
        (r'[\u201C\u201D\u201E]', '"'),          # Smart double quotes to straight
        (r'[–—]', '-'),           # Em/en dash to hyphen
        (r'[…]', '...'),          # Ellipsis normalization
        (r'\s+', ' '),            # Multiple spaces to single
        (r'[^\w\s\.\,\!\?\-\'\"]', ''),  # Remove special chars
    ]
    
    def __init__(self):
        self.stats = {
            'total_processed': 0,
            'diacritics_removed': 0,
            'numbers_expanded': 0,
            'punctuation_normalized': 0,
            'unicode_normalized': 0
        }
    
    def normalize_text(self, text: str, language: str = 'hi') -> Tuple[str, Dict]:
        """
        Normalize text according to India Speaks standards.
        
        Args:
            text: Input text to normalize
            language: Language code (hi, bn, te, etc.)
            
        Returns:
            Tuple of (normalized_text, normalization_stats)
        """
        if not text or not text.strip():
            return '', {'empty_text': True}
        
        original_text = text
        stats = {'operations': []}
        
        # Step 1: Unicode normalization (NFC)
        text = unicodedata.normalize('NFC', text)
        if text != original_text:
            stats['operations'].append('unicode_nfc')
            self.stats['unicode_normalized'] += 1
        
        # Step 2: Remove diacritics
        text, diac_removed = self._remove_diacritics(text)
        if diac_removed:
            stats['operations'].append('diacritics_removed')
            self.stats['diacritics_removed'] += 1
        
        # Step 3: Expand numbers (for supported languages)
        if language in ['hi', 'mr']:  # Languages where we expand numbers
            text, num_expanded = self._expand_numbers(text, language)
            if num_expanded:
                stats['operations'].append('numbers_expanded')
                self.stats['numbers_expanded'] += 1
        
        # Step 4: Language-specific lowercasing
        text = self._language_specific_lowercase(text, language)
        
        # Step 5: Normalize punctuation
        text, punct_normalized = self._normalize_punctuation(text)
        if punct_normalized:
            stats['operations'].append('punctuation_normalized')
            self.stats['punctuation_normalized'] += 1
        
        # Step 6: Final cleanup
        text = self._final_cleanup(text)
        
        self.stats['total_processed'] += 1
        stats['original_length'] = len(original_text)
        stats['final_length'] = len(text)
        stats['reduction_ratio'] = 1 - (len(text) / len(original_text)) if original_text else 0
        
        return text.strip(), stats
    
    def _remove_diacritics(self, text: str) -> Tuple[str, bool]:
        """Remove diacritical marks from text."""
        original = text
        
        # Apply diacritic removal patterns
        for pattern, replacement in self.DIACRITIC_PATTERNS:
            text = re.sub(pattern, replacement, text)
        
        # Additional Unicode category-based removal
        text = ''.join(
            char for char in text 
            if unicodedata.category(char) != 'Mn'  # Mark, nonspacing
        )
        
        return text, text != original
    
    def _expand_numbers(self, text: str, language: str) -> Tuple[str, bool]:
        """Expand numeric digits to words."""
        original = text
        
        if language == 'hi':
            # Expand single digits to Hindi words
            for digit, word in self.NUMBER_WORDS_HI.items():
                text = re.sub(r'\b' + digit + r'\b', word, text)
        
        # For multi-digit numbers, we could add more sophisticated expansion
        # For now, just handle simple cases
        
        return text, text != original
    
    def _language_specific_lowercase(self, text: str, language: str) -> str:
        """Apply language-specific case normalization."""
        if language == 'en':
            return text.lower()
        
        # For Indic scripts, lowercasing is more complex
        # Most Indic scripts don't have case, but we normalize Latin chars
        return re.sub(r'[A-Z]', lambda m: m.group().lower(), text)
    
    def _normalize_punctuation(self, text: str) -> Tuple[str, bool]:
        """Normalize punctuation marks."""
        original = text
        
        for pattern, replacement in self.PUNCTUATION_PATTERNS:
            text = re.sub(pattern, replacement, text)
        
        return text, text != original
    
    def _final_cleanup(self, text: str) -> str:
        """Final text cleanup and formatting."""
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Ensure single spaces between words
        text = re.sub(r'\s+', ' ', text)
        
        # Remove empty parentheses, brackets
        text = re.sub(r'\(\s*\)', '', text)
        text = re.sub(r'\[\s*\]', '', text)
        text = re.sub(r'\{\s*\}', '', text)
        
        return text
    
    def validate_language_script(self, text: str, expected_language: str) -> Tuple[bool, float, str]:
        """
        Validate if text matches expected language script.
        
        Returns:
            Tuple of (is_valid, confidence_score, detected_script)
        """
        if not text or not text.strip():
            return False, 0.0, 'empty'
        
        # Count characters by script
        script_counts = {}
        total_chars = 0
        
        for char in text:
            if char.isalpha():
                script = unicodedata.name(char, '').split()[0] if unicodedata.name(char, '') else 'UNKNOWN'
                script_counts[script] = script_counts.get(script, 0) + 1
                total_chars += 1
        
        if total_chars == 0:
            return False, 0.0, 'no_alpha'
        
        # Find dominant script
        dominant_script = max(script_counts.items(), key=lambda x: x[1]) if script_counts else ('UNKNOWN', 0)
        dominant_script_name = dominant_script[0]
        confidence = dominant_script[1] / total_chars
        
        # Map detected script to expected
        expected_script = self.LANGUAGE_SCRIPTS.get(expected_language, 'UNKNOWN')
        
        # Simple validation logic
        is_valid = False
        if expected_language == 'en' and 'LATIN' in dominant_script_name:
            is_valid = confidence > 0.7
        elif expected_script in dominant_script_name.upper() or dominant_script_name in expected_script.upper():
            is_valid = confidence > 0.5
        
        return is_valid, confidence, dominant_script_name
    
    def get_normalization_stats(self) -> Dict:
        """Get processing statistics."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset processing statistics."""
        self.stats = {
            'total_processed': 0,
            'diacritics_removed': 0,
            'numbers_expanded': 0,
            'punctuation_normalized': 0,
            'unicode_normalized': 0
        } 