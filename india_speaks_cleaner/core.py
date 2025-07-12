"""
Core preprocessing pipeline for India Speaks audio-text data.

Orchestrates audio validation, text normalization, and quality filtering
to produce clean training data and reject problematic samples.
"""

import os
import time
import logging
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
from dataclasses import dataclass

from .text_normalization import IndicTextNormalizer
from .audio_validation import AudioValidator
from .utils import (
    DataValidationUtils, FileUtils, ReportUtils, 
    ConfigUtils, LanguageUtils
)

logger = logging.getLogger(__name__)

@dataclass
class ProcessingResult:
    """Result of processing a single audio-text pair."""
    utterance_id: str
    is_valid: bool
    reasons: List[str]
    normalized_text: str
    original_text: str
    audio_properties: Dict
    text_metrics: Dict
    processing_time: float

class AudioTextPreprocessor:
    """Main preprocessing pipeline for audio-text pairs."""
    
    REQUIRED_COLUMNS = [
        'utterance_id', 'audio_path', 'language', 
        'transcription_raw', 'duration_sec'
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize preprocessor with configuration."""
        self.config = config or ConfigUtils.DEFAULT_CONFIG
        
        # Initialize components
        self.text_normalizer = IndicTextNormalizer()
        self.audio_validator = AudioValidator()
        
        # Processing statistics
        self.stats = {
            'total_processed': 0,
            'valid_samples': 0,
            'rejected_samples': 0,
            'processing_time': 0.0,
            'rejection_reasons': {},
            'text_normalization': {},
            'audio_validation': {}
        }
        
        # Data storage
        self.valid_samples = []
        self.rejected_samples = []
    
    def process_dataset(self, input_csv: str, output_dir: str = '.') -> Dict:
        """
        Process entire dataset from CSV file.
        
        Args:
            input_csv: Path to input CSV file
            output_dir: Directory for output files
            
        Returns:
            Processing summary dictionary
        """
        start_time = time.time()
        
        logger.info(f"Starting dataset processing: {input_csv}")
        
        try:
            # Validate input file structure
            is_valid, validation_info = DataValidationUtils.validate_csv_structure(
                input_csv, self.REQUIRED_COLUMNS
            )
            
            if not is_valid:
                raise ValueError(f"Invalid CSV structure: {validation_info}")
            
            # Load dataset
            df = pd.read_csv(input_csv)
            logger.info(f"Loaded dataset with {len(df)} samples")
            
            # Process each sample
            results = []
            for idx, row in df.iterrows():
                try:
                    result = self.process_single_sample(row.to_dict())
                    results.append(result)
                    
                    if (idx + 1) % 100 == 0:
                        logger.info(f"Processed {idx + 1}/{len(df)} samples")
                        
                except Exception as e:
                    logger.error(f"Error processing sample {idx}: {str(e)}")
                    # Create failed result
                    result = ProcessingResult(
                        utterance_id=row.get('utterance_id', f'row_{idx}'),
                        is_valid=False,
                        reasons=[f'processing_error: {str(e)}'],
                        normalized_text='',
                        original_text=row.get('transcription_raw', ''),
                        audio_properties={},
                        text_metrics={},
                        processing_time=0.0
                    )
                    results.append(result)
            
            # Separate valid and rejected samples
            self._separate_results(results, df)
            
            # Generate output files
            output_files = self._save_results(output_dir)
            
            # Calculate final statistics
            processing_time = time.time() - start_time
            self.stats['processing_time'] = processing_time
            
            # Generate summary
            summary = self._generate_summary(output_files, processing_time)
            
            logger.info(f"Processing completed in {ReportUtils.format_duration(processing_time)}")
            logger.info(f"Valid samples: {self.stats['valid_samples']}")
            logger.info(f"Rejected samples: {self.stats['rejected_samples']}")
            
            return summary
            
        except Exception as e:
            logger.error(f"Dataset processing failed: {str(e)}")
            raise
    
    def process_single_sample(self, sample: Dict) -> ProcessingResult:
        """Process a single audio-text sample."""
        start_time = time.time()
        
        # Helper function to safely extract string values (handles NaN)
        def safe_get_string(key: str, default: str = '') -> str:
            value = sample.get(key, default)
            if pd.isna(value) or value is None:
                return default
            return str(value)
        
        utterance_id = safe_get_string('utterance_id')
        audio_path = safe_get_string('audio_path')
        language = safe_get_string('language')
        transcription = safe_get_string('transcription_raw')
        
        reasons = []
        
        # 1. Basic validation
        if not utterance_id:
            reasons.append('missing_utterance_id')
        
        if not audio_path:
            reasons.append('missing_audio_path')
            
        if not language:
            reasons.append('missing_language')
            
        if not transcription or not transcription.strip():
            reasons.append('empty_transcription')
        
        # 2. Language validation
        if language and not LanguageUtils.is_supported_language(language):
            reasons.append('unsupported_language')
        
        # 3. Audio validation
        audio_properties = {}
        if audio_path and not reasons:  # Only validate if basic info is present
            try:
                is_audio_valid, audio_details = self.audio_validator.validate_audio_file(audio_path)
                audio_properties = audio_details.get('properties', {})
                
                if not is_audio_valid:
                    audio_issues = audio_details.get('issues', [])
                    reasons.extend([f'audio_{issue}' for issue in audio_issues])
                    
            except Exception as e:
                logger.error(f"Audio validation failed for {utterance_id}: {str(e)}")
                reasons.append('audio_validation_error')
        
        # 4. Duration validation (from CSV if available)
        duration = sample.get('duration_sec', 0)
        if duration:
            try:
                duration = float(duration)
                min_dur = self.config['audio_validation']['min_duration']
                max_dur = self.config['audio_validation']['max_duration']
                
                if duration < min_dur:
                    reasons.append('duration_too_short')
                elif duration > max_dur:
                    reasons.append('duration_too_long')
            except (ValueError, TypeError):
                reasons.append('invalid_duration_format')
        
        # 5. Language path mismatch check
        if (audio_path and language and 
            self.config['quality_filtering']['check_language_mismatch']):
            if DataValidationUtils.detect_language_path_mismatch(audio_path, language):
                reasons.append('language_path_mismatch')
        
        # 6. Text normalization and quality assessment
        normalized_text = ''
        text_metrics = {}
        
        if transcription and transcription.strip():
            try:
                # Normalize text
                normalized_text, norm_stats = self.text_normalizer.normalize_text(
                    transcription, language
                )
                
                # Calculate text quality metrics
                text_metrics = DataValidationUtils.calculate_text_quality_score(normalized_text)
                
                # Quality filtering
                quality_config = self.config['quality_filtering']
                
                if text_metrics['quality_score'] < quality_config['min_text_quality_score']:
                    reasons.append('low_text_quality')
                
                if text_metrics['word_count'] < quality_config['min_word_count']:
                    reasons.append('too_few_words')
                
                if text_metrics['repeated_word_ratio'] > quality_config['max_repeated_word_ratio']:
                    reasons.append('too_many_repeated_words')
                
                # Language script consistency (if text normalizer supports it)
                try:
                    is_script_valid, script_confidence, detected_script = \
                        self.text_normalizer.validate_language_script(normalized_text, language)
                    
                    if not is_script_valid and script_confidence < 0.5:
                        reasons.append(f'script_mismatch_{detected_script}')
                        
                except Exception as e:
                    logger.debug(f"Script validation failed for {utterance_id}: {str(e)}")
                
            except Exception as e:
                logger.error(f"Text normalization failed for {utterance_id}: {str(e)}")
                reasons.append('text_normalization_error')
        
        # 7. Additional quality checks
        quality_flag = sample.get('quality_flag', 0)
        try:
            quality_flag = int(quality_flag)
            if quality_flag < 0:  # Negative quality flag indicates known issues
                reasons.append('negative_quality_flag')
        except (ValueError, TypeError):
            pass
        
        # Determine final validity
        is_valid = len(reasons) == 0
        
        # Update statistics
        self.stats['total_processed'] += 1
        if is_valid:
            self.stats['valid_samples'] += 1
        else:
            self.stats['rejected_samples'] += 1
            
            # Track rejection reasons
            for reason in reasons:
                self.stats['rejection_reasons'][reason] = \
                    self.stats['rejection_reasons'].get(reason, 0) + 1
        
        processing_time = time.time() - start_time
        
        return ProcessingResult(
            utterance_id=utterance_id,
            is_valid=is_valid,
            reasons=reasons,
            normalized_text=normalized_text,
            original_text=transcription,
            audio_properties=audio_properties,
            text_metrics=text_metrics,
            processing_time=processing_time
        )
    
    def _separate_results(self, results: List[ProcessingResult], original_df: pd.DataFrame):
        """Separate results into valid and rejected samples."""
        self.valid_samples = []
        self.rejected_samples = []
        
        for i, result in enumerate(results):
            original_row = original_df.iloc[i].to_dict()
            
            if result.is_valid:
                # Add to valid samples with normalized text
                valid_sample = original_row.copy()
                valid_sample['transcription_normalized'] = result.normalized_text
                valid_sample['text_quality_score'] = result.text_metrics.get('quality_score', 0)
                self.valid_samples.append(valid_sample)
            else:
                # Add to rejected samples with reasons
                rejected_sample = original_row.copy()
                rejected_sample['reason'] = '; '.join(result.reasons)
                rejected_sample['original_transcription'] = result.original_text
                rejected_sample['processing_time'] = result.processing_time
                self.rejected_samples.append(rejected_sample)
    
    def _save_results(self, output_dir: str) -> Dict[str, str]:
        """Save processing results to CSV files."""
        FileUtils.ensure_directory(output_dir)
        
        output_files = {}
        
        # Save valid samples (train_ready.csv)
        train_ready_path = os.path.join(
            output_dir, 
            self.config['output']['train_ready_filename']
        )
        
        if self.valid_samples:
            valid_df = pd.DataFrame(self.valid_samples)
            valid_df.to_csv(train_ready_path, index=False)
            logger.info(f"Saved {len(self.valid_samples)} valid samples to {train_ready_path}")
        else:
            # Create empty file with headers
            pd.DataFrame(columns=self.REQUIRED_COLUMNS).to_csv(train_ready_path, index=False)
            logger.warning("No valid samples found - created empty train_ready.csv")
        
        output_files['train_ready'] = train_ready_path
        
        # Save rejected samples (rejected.csv)
        rejected_path = os.path.join(
            output_dir,
            self.config['output']['rejected_filename']
        )
        
        if self.rejected_samples:
            rejected_df = pd.DataFrame(self.rejected_samples)
            rejected_df.to_csv(rejected_path, index=False)
            logger.info(f"Saved {len(self.rejected_samples)} rejected samples to {rejected_path}")
        else:
            # Create empty file with headers
            headers = self.REQUIRED_COLUMNS + ['reason', 'original_transcription', 'processing_time']
            pd.DataFrame(columns=headers).to_csv(rejected_path, index=False)
            logger.info("No rejected samples - created empty rejected.csv")
        
        output_files['rejected'] = rejected_path
        
        # Save processing statistics if configured
        if self.config['output']['include_stats']:
            stats_path = os.path.join(output_dir, 'processing_stats.json')
            try:
                import json
                with open(stats_path, 'w') as f:
                    json.dump(self._get_detailed_stats(), f, indent=2)
                output_files['stats'] = stats_path
            except Exception as e:
                logger.error(f"Error saving stats: {str(e)}")
        
        return output_files
    
    def _generate_summary(self, output_files: Dict[str, str], processing_time: float) -> Dict:
        """Generate processing summary."""
        summary = {
            'processing_summary': {
                'total_samples': self.stats['total_processed'],
                'valid_samples': self.stats['valid_samples'],
                'rejected_samples': self.stats['rejected_samples'],
                'valid_ratio': (self.stats['valid_samples'] / self.stats['total_processed'] 
                               if self.stats['total_processed'] > 0 else 0),
                'processing_time_seconds': processing_time,
                'processing_time_formatted': ReportUtils.format_duration(processing_time),
                'samples_per_second': (self.stats['total_processed'] / processing_time 
                                     if processing_time > 0 else 0)
            },
            'output_files': output_files,
            'rejection_reasons': self.stats['rejection_reasons'],
            'component_stats': self._get_component_stats()
        }
        
        return summary
    
    def _get_component_stats(self) -> Dict:
        """Get statistics from individual components."""
        return {
            'text_normalization': self.text_normalizer.get_normalization_stats(),
            'audio_validation': self.audio_validator.get_validation_stats()
        }
    
    def _get_detailed_stats(self) -> Dict:
        """Get detailed processing statistics."""
        detailed_stats = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'config': self.config,
            'processing_stats': self.stats,
            'component_stats': self._get_component_stats(),
            'rejection_reason_analysis': ReportUtils.create_rejection_reasons_summary(
                self.rejected_samples
            )
        }
        
        return detailed_stats
    
    def get_processing_stats(self) -> Dict:
        """Get current processing statistics."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset all processing statistics."""
        self.stats = {
            'total_processed': 0,
            'valid_samples': 0,
            'rejected_samples': 0,
            'processing_time': 0.0,
            'rejection_reasons': {},
            'text_normalization': {},
            'audio_validation': {}
        }
        
        self.valid_samples = []
        self.rejected_samples = []
        
        # Reset component stats
        self.text_normalizer.reset_stats()
        self.audio_validator.reset_stats() 