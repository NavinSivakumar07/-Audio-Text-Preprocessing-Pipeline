"""
Command-line interface for India Speaks audio-text preprocessing pipeline.

Provides CLI entry point for processing datasets with various configuration options.
"""

import argparse
import logging
import sys
import os
import json
from typing import Optional

from . import __version__
from .core import AudioTextPreprocessor
from .utils import ConfigUtils, ReportUtils

def setup_logging(verbose: bool = False, log_file: Optional[str] = None):
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            print(f"Warning: Could not setup file logging: {e}")

def create_parser() -> argparse.ArgumentParser:
    """Create argument parser for CLI."""
    parser = argparse.ArgumentParser(
        prog='india_speaks_cleaner',
        description='Preprocessing pipeline for Indic language audio-text data',
        epilog='For more information, see the README.md file.'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'%(prog)s {__version__}'
    )
    
    # Input/Output arguments
    parser.add_argument(
        'input_csv',
        help='Path to input CSV file containing audio-text metadata'
    )
    
    parser.add_argument(
        '-o', '--output-dir',
        default='./output',
        help='Output directory for processed files (default: ./output)'
    )
    
    # Configuration arguments
    parser.add_argument(
        '-c', '--config',
        help='Path to JSON configuration file (optional)'
    )
    
    parser.add_argument(
        '--min-duration',
        type=float,
        help='Minimum audio duration in seconds (overrides config)'
    )
    
    parser.add_argument(
        '--max-duration',
        type=float,
        help='Maximum audio duration in seconds (overrides config)'
    )
    
    parser.add_argument(
        '--min-quality-score',
        type=float,
        help='Minimum text quality score (0-1, overrides config)'
    )
    
    # Processing options
    parser.add_argument(
        '--skip-audio-validation',
        action='store_true',
        help='Skip audio file validation (faster but less thorough)'
    )
    
    parser.add_argument(
        '--skip-language-mismatch-check',
        action='store_true',
        help='Skip language path mismatch detection'
    )
    
    parser.add_argument(
        '--normalize-only',
        action='store_true',
        help='Only perform text normalization without quality filtering'
    )
    
    # Output options
    parser.add_argument(
        '--train-filename',
        default='train_ready.csv',
        help='Filename for valid samples output (default: train_ready.csv)'
    )
    
    parser.add_argument(
        '--rejected-filename',
        default='rejected.csv',
        help='Filename for rejected samples output (default: rejected.csv)'
    )
    
    parser.add_argument(
        '--no-stats',
        action='store_true',
        help='Do not generate processing statistics file'
    )
    
    # Logging options
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--log-file',
        help='Path to log file (optional)'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress all output except errors'
    )
    
    return parser

def load_and_merge_config(args: argparse.Namespace) -> dict:
    """Load configuration and merge with command line arguments."""
    # Load base config
    config = ConfigUtils.load_config(args.config)
    
    # Override with command line arguments
    if args.min_duration is not None:
        config['audio_validation']['min_duration'] = args.min_duration
    
    if args.max_duration is not None:
        config['audio_validation']['max_duration'] = args.max_duration
    
    if args.min_quality_score is not None:
        config['quality_filtering']['min_text_quality_score'] = args.min_quality_score
    
    if args.skip_language_mismatch_check:
        config['quality_filtering']['check_language_mismatch'] = False
    
    if args.normalize_only:
        # Set very permissive quality filtering for normalize-only mode
        config['quality_filtering']['min_text_quality_score'] = 0.0
        config['quality_filtering']['min_word_count'] = 0
        config['quality_filtering']['max_repeated_word_ratio'] = 1.0
    
    # Output configuration
    config['output']['train_ready_filename'] = args.train_filename
    config['output']['rejected_filename'] = args.rejected_filename
    config['output']['include_stats'] = not args.no_stats
    
    return config

def validate_arguments(args: argparse.Namespace) -> None:
    """Validate command line arguments."""
    # Check input file
    if not os.path.exists(args.input_csv):
        raise FileNotFoundError(f"Input CSV file not found: {args.input_csv}")
    
    # Check config file if specified
    if args.config and not os.path.exists(args.config):
        raise FileNotFoundError(f"Configuration file not found: {args.config}")
    
    # Validate numeric arguments
    if args.min_duration is not None and args.min_duration <= 0:
        raise ValueError("Minimum duration must be positive")
    
    if args.max_duration is not None and args.max_duration <= 0:
        raise ValueError("Maximum duration must be positive")
    
    if (args.min_duration is not None and args.max_duration is not None and 
        args.min_duration >= args.max_duration):
        raise ValueError("Minimum duration must be less than maximum duration")
    
    if args.min_quality_score is not None:
        if not 0 <= args.min_quality_score <= 1:
            raise ValueError("Quality score must be between 0 and 1")

def print_summary(summary: dict, quiet: bool = False):
    """Print processing summary to console."""
    if quiet:
        return
    
    print("\n" + "="*60)
    print("PROCESSING SUMMARY")
    print("="*60)
    
    proc_summary = summary['processing_summary']
    print(f"Total samples processed: {proc_summary['total_samples']:,}")
    print(f"Valid samples: {proc_summary['valid_samples']:,}")
    print(f"Rejected samples: {proc_summary['rejected_samples']:,}")
    print(f"Valid ratio: {proc_summary['valid_ratio']:.1%}")
    print(f"Processing time: {proc_summary['processing_time_formatted']}")
    print(f"Processing speed: {proc_summary['samples_per_second']:.1f} samples/sec")
    
    print(f"\nOutput files:")
    for file_type, filepath in summary['output_files'].items():
        print(f"  {file_type}: {filepath}")
    
    # Show top rejection reasons
    if summary['rejection_reasons']:
        print(f"\nTop rejection reasons:")
        sorted_reasons = sorted(
            summary['rejection_reasons'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        for reason, count in sorted_reasons[:5]:
            print(f"  {reason}: {count}")
    
    print("="*60)

def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    try:
        # Validate arguments
        validate_arguments(args)
        
        # Setup logging
        setup_logging(
            verbose=args.verbose and not args.quiet,
            log_file=args.log_file
        )
        
        logger = logging.getLogger(__name__)
        
        if not args.quiet:
            print(f"India Speaks Cleaner v{__version__}")
            print("Starting audio-text preprocessing pipeline...")
        
        # Load configuration
        config = load_and_merge_config(args)
        
        if args.verbose and not args.quiet:
            print(f"\nConfiguration:")
            print(json.dumps(config, indent=2))
        
        # Initialize preprocessor
        preprocessor = AudioTextPreprocessor(config)
        
        # Process dataset
        logger.info(f"Processing dataset: {args.input_csv}")
        summary = preprocessor.process_dataset(
            input_csv=args.input_csv,
            output_dir=args.output_dir
        )
        
        # Print summary
        print_summary(summary, quiet=args.quiet)
        
        # Exit with appropriate code
        if summary['processing_summary']['valid_samples'] == 0:
            if not args.quiet:
                print("WARNING: No valid samples produced!")
            sys.exit(1)
        else:
            if not args.quiet:
                print("Processing completed successfully!")
            sys.exit(0)
    
    except KeyboardInterrupt:
        print("\nProcessing interrupted by user.")
        sys.exit(130)
    
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Processing failed: {str(e)}")
        
        if args.verbose:
            import traceback
            traceback.print_exc()
        else:
            print(f"Error: {str(e)}")
            print("Use --verbose for detailed error information.")
        
        sys.exit(1)

# Additional CLI utilities
def create_sample_config():
    """Create a sample configuration file."""
    sample_config = ConfigUtils.DEFAULT_CONFIG.copy()
    
    # Add comments to the config
    sample_config['_comments'] = {
        'audio_validation': 'Audio quality thresholds',
        'text_normalization': 'Text processing options',
        'quality_filtering': 'Quality filtering criteria',
        'output': 'Output file configuration'
    }
    
    return sample_config

def generate_config_file(output_path: str):
    """Generate a sample configuration file."""
    config = create_sample_config()
    
    try:
        with open(output_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Sample configuration file created: {output_path}")
    except Exception as e:
        print(f"Error creating configuration file: {e}")
        sys.exit(1)

# Entry point for package installation
if __name__ == '__main__':
    main() 