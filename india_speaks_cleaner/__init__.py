"""
India Speaks Cleaner - Audio-Text Preprocessing Pipeline for Indic Languages

A comprehensive preprocessing pipeline for cleaning and validating audio-text pairs
for ASR/TTS model training with support for 12+ Indic languages.
"""

__version__ = "1.0.0"
__author__ = "India Speaks Team"

from .core import AudioTextPreprocessor
from .text_normalization import IndicTextNormalizer
from .audio_validation import AudioValidator

__all__ = [
    "AudioTextPreprocessor",
    "IndicTextNormalizer", 
    "AudioValidator"
] 