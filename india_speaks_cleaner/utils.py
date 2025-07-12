"""
Utility functions for the India Speaks preprocessing pipeline.

Contains helper functions for data validation, file handling, and common operations.
"""

import os
import re
import csv
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

class DataValidationUtils:
    """Utilities for data validation and quality checks."""
    
    @staticmethod
    def validate_csv_structure(filepath: str, required_columns: List[str]) -> Tuple[bool, Dict]:
        """Validate CSV file structure and required columns."""
        try:
            df = pd.read_csv(filepath)
            
            missing_columns = []
            for col in required_columns:
                if col not in df.columns:
                    missing_columns.append(col)
            
            result = {
                'valid': len(missing_columns) == 0,
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'missing_columns': missing_columns,
                'available_columns': list(df.columns)
            }
            
            return result['valid'], result
            
        except Exception as e:
            logger.error(f"Error validating CSV structure: {str(e)}")
            return False, {'error': str(e)}
    
    @staticmethod
    def check_data_completeness(df: pd.DataFrame, critical_columns: List[str]) -> Dict:
        """Check data completeness for critical columns."""
        completeness = {}
        
        for col in critical_columns:
            if col in df.columns:
                null_count = df[col].isnull().sum()
                empty_count = (df[col] == '').sum() if df[col].dtype == 'object' else 0
                total_missing = null_count + empty_count
                
                completeness[col] = {
                    'total_rows': len(df),
                    'missing_count': total_missing,
                    'completeness_ratio': 1 - (total_missing / len(df)),
                    'null_count': null_count,
                    'empty_count': empty_count
                }
        
        return completeness
    
    @staticmethod
    def detect_language_path_mismatch(audio_path: str, language_label: str) -> bool:
        """Detect mismatch between audio file path language and language label."""
        if not audio_path:
            return False
        
        # Extract language from path (e.g., s3://bucket/raw/hi/file.wav -> hi)
        path_parts = audio_path.split('/')
        path_language = None
        
        for i, part in enumerate(path_parts):
            if part == 'raw' and i + 1 < len(path_parts):
                path_language = path_parts[i + 1]
                break
        
        if path_language and language_label:
            return path_language.lower() != language_label.lower()
        
        return False
    
    @staticmethod
    def calculate_text_quality_score(text: str) -> Dict:
        """Calculate text quality metrics."""
        if not text or not text.strip():
            return {
                'quality_score': 0.0,
                'word_count': 0,
                'char_count': 0,
                'avg_word_length': 0.0,
                'repeated_word_ratio': 1.0,
                'punctuation_ratio': 0.0
            }
        
        words = text.split()
        unique_words = set(words)
        
        # Calculate punctuation ratio
        punctuation_count = sum(1 for char in text if not char.isalnum() and not char.isspace())
        
        metrics = {
            'quality_score': 0.0,  # Will be calculated
            'word_count': len(words),
            'char_count': len(text),
            'avg_word_length': sum(len(word) for word in words) / len(words) if words else 0,
            'repeated_word_ratio': (len(words) - len(unique_words)) / len(words) if words else 0,
            'punctuation_ratio': punctuation_count / len(text) if text else 0
        }
        
        # Simple quality score calculation
        score = 1.0
        if metrics['repeated_word_ratio'] > 0.7:  # Too many repeated words
            score *= 0.3
        if metrics['word_count'] < 3:  # Too few words
            score *= 0.5
        if metrics['avg_word_length'] < 2:  # Words too short
            score *= 0.7
        
        metrics['quality_score'] = score
        
        return metrics

class FileUtils:
    """Utilities for file operations."""
    
    @staticmethod
    def ensure_directory(filepath: str):
        """Ensure directory exists for the given filepath."""
        directory = os.path.dirname(filepath)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
    
    @staticmethod
    def safe_filename(text: str, max_length: int = 50) -> str:
        """Create a safe filename from text."""
        # Remove special characters
        safe_text = re.sub(r'[^\w\s-]', '', text)
        # Replace spaces with underscores
        safe_text = re.sub(r'\s+', '_', safe_text)
        # Truncate if too long
        if len(safe_text) > max_length:
            safe_text = safe_text[:max_length]
        
        return safe_text
    
    @staticmethod
    def generate_file_hash(filepath: str) -> str:
        """Generate MD5 hash for file content."""
        hash_md5 = hashlib.md5()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Error generating hash for {filepath}: {str(e)}")
            return ""

class ReportUtils:
    """Utilities for generating reports and statistics."""
    
    @staticmethod
    def generate_processing_summary(stats_dict: Dict) -> str:
        """Generate a human-readable processing summary."""
        lines = ["Processing Summary", "=" * 40]
        
        for category, stats in stats_dict.items():
            lines.append(f"\n{category.upper()}:")
            for key, value in stats.items():
                if isinstance(value, float):
                    lines.append(f"  {key}: {value:.2f}")
                else:
                    lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)
    
    @staticmethod
    def create_rejection_reasons_summary(rejected_data: List[Dict]) -> Dict:
        """Create summary of rejection reasons."""
        reason_counts = {}
        
        for item in rejected_data:
            reasons = item.get('reason', '').split(';')
            for reason in reasons:
                reason = reason.strip()
                if reason:
                    reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        return reason_counts
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in seconds to human-readable format."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}m"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}h"

class ConfigUtils:
    """Utilities for configuration management."""
    
    DEFAULT_CONFIG = {
        'audio_validation': {
            'min_duration': 0.5,
            'max_duration': 15.0,
            'min_sample_rate': 8000,
            'max_sample_rate': 48000,
            'preferred_sample_rate': 16000
        },
        'text_normalization': {
            'remove_diacritics': True,
            'expand_numbers': True,
            'normalize_punctuation': True,
            'apply_unicode_nfc': True
        },
        'quality_filtering': {
            'min_text_quality_score': 0.3,
            'max_repeated_word_ratio': 0.8,
            'min_word_count': 2,
            'check_language_mismatch': True
        },
        'output': {
            'train_ready_filename': 'train_ready.csv',
            'rejected_filename': 'rejected.csv',
            'include_stats': True
        }
    }
    
    @staticmethod
    def load_config(config_path: Optional[str] = None) -> Dict:
        """Load configuration from file or return default."""
        if config_path and os.path.exists(config_path):
            try:
                import json
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                
                # Merge with default config
                config = ConfigUtils.DEFAULT_CONFIG.copy()
                config.update(user_config)
                return config
            except Exception as e:
                logger.warning(f"Error loading config from {config_path}: {str(e)}")
        
        return ConfigUtils.DEFAULT_CONFIG.copy()
    
    @staticmethod
    def save_config(config: Dict, config_path: str):
        """Save configuration to file."""
        try:
            import json
            FileUtils.ensure_directory(config_path)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving config to {config_path}: {str(e)}")

class LanguageUtils:
    """Utilities for language detection and validation."""
    
    # Supported Indic languages
    SUPPORTED_LANGUAGES = {
        'hi': {'name': 'Hindi', 'script': 'Devanagari'},
        'bn': {'name': 'Bengali', 'script': 'Bengali'},
        'te': {'name': 'Telugu', 'script': 'Telugu'},
        'ta': {'name': 'Tamil', 'script': 'Tamil'},
        'ml': {'name': 'Malayalam', 'script': 'Malayalam'},
        'kn': {'name': 'Kannada', 'script': 'Kannada'},
        'gu': {'name': 'Gujarati', 'script': 'Gujarati'},
        'mr': {'name': 'Marathi', 'script': 'Devanagari'},
        'pa': {'name': 'Punjabi', 'script': 'Gurmukhi'},
        'ur': {'name': 'Urdu', 'script': 'Arabic'},
        'en': {'name': 'English', 'script': 'Latin'}
    }
    
    @staticmethod
    def is_supported_language(language_code: str) -> bool:
        """Check if language code is supported."""
        return language_code.lower() in LanguageUtils.SUPPORTED_LANGUAGES
    
    @staticmethod
    def get_language_info(language_code: str) -> Optional[Dict]:
        """Get language information."""
        return LanguageUtils.SUPPORTED_LANGUAGES.get(language_code.lower())
    
    @staticmethod
    def validate_language_consistency(text: str, expected_language: str) -> Tuple[bool, float]:
        """Simple language consistency check based on character scripts."""
        if not text or not expected_language:
            return False, 0.0
        
        lang_info = LanguageUtils.get_language_info(expected_language)
        if not lang_info:
            return False, 0.0
        
        # Simple heuristic based on character ranges
        # This is a basic implementation; real-world would use proper language detection
        script_name = lang_info['script']
        
        if script_name == 'Latin':
            latin_chars = sum(1 for c in text if ord(c) < 128 and c.isalpha())
            total_alpha = sum(1 for c in text if c.isalpha())
            if total_alpha > 0:
                confidence = latin_chars / total_alpha
                return confidence > 0.7, confidence
        
        # For other scripts, this would need proper Unicode range checking
        # For now, return moderate confidence
        return True, 0.6 