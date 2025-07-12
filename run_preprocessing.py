#!/usr/bin/env python3
"""
Script to run the India Speaks preprocessing pipeline on sample data.
"""

import sys
import os
import logging

# Add current directory to Python path
sys.path.insert(0, '.')

try:
    from india_speaks_cleaner import AudioTextPreprocessor
    from india_speaks_cleaner.utils import ConfigUtils
    print("✓ Package imported successfully")
except ImportError as e:
    print(f"✗ Failed to import package: {e}")
    sys.exit(1)

def main():
    """Run preprocessing on sample data."""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    # Input and output paths
    input_csv = 'utterances_metadata.csv'
    output_dir = './output'
    
    # Check if input file exists
    if not os.path.exists(input_csv):
        logger.error(f"Input file not found: {input_csv}")
        return False
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        # Initialize preprocessor with default configuration
        logger.info("Initializing preprocessor...")
        preprocessor = AudioTextPreprocessor()
        
        # Process the dataset
        logger.info(f"Processing dataset: {input_csv}")
        summary = preprocessor.process_dataset(
            input_csv=input_csv,
            output_dir=output_dir
        )
        
        # Print summary
        print("\n" + "="*60)
        print("PROCESSING SUMMARY")
        print("="*60)
        
        proc_summary = summary['processing_summary']
        print(f"Total samples processed: {proc_summary['total_samples']:,}")
        print(f"Valid samples: {proc_summary['valid_samples']:,}")
        print(f"Rejected samples: {proc_summary['rejected_samples']:,}")
        print(f"Valid ratio: {proc_summary['valid_ratio']:.1%}")
        print(f"Processing time: {proc_summary['processing_time_formatted']}")
        
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
            for reason, count in sorted_reasons[:10]:
                print(f"  {reason}: {count}")
        
        print("="*60)
        print("✓ Processing completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 