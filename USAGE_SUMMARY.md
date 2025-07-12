# India Speaks Cleaner - Usage Summary

## ✅ Installation Complete

The preprocessing pipeline has been successfully installed and is ready to use!

## 🚀 Quick Start

### Basic Usage
```bash
# Simple preprocessing
python clean_data.py utterances_metadata.csv

# With custom output directory
python clean_data.py utterances_metadata.csv -o ./my_output

# With verbose logging
python clean_data.py utterances_metadata.csv --verbose
```

### Advanced Usage
```bash
# Custom duration filters
python clean_data.py data.csv --min-duration 2.0 --max-duration 8.0

# Skip certain validations for faster processing
python clean_data.py data.csv --skip-audio-validation --skip-language-mismatch-check

# Only text normalization (no filtering)
python clean_data.py data.csv --normalize-only

# Custom quality thresholds
python clean_data.py data.csv --min-quality-score 0.5

# Quiet mode (minimal output)
python clean_data.py data.csv --quiet
```

### Alternative Methods
```bash
# Using the original preprocessing script
python run_preprocessing.py

# Using direct Python import (if CLI entry point doesn't work)
python -c "from india_speaks_cleaner.cli import main; import sys; sys.argv = ['clean_data', 'data.csv']; main()"
```

## 📊 Your Results

**Latest Processing Results:**
- **Total samples:** 2,000
- **Valid samples:** 83 (4.2%)
- **Rejected samples:** 1,917 (95.8%)
- **Processing speed:** ~2,300 samples/second

**Top rejection reasons:**
- Language path mismatch: 1,807 samples
- Negative quality flag: 695 samples  
- Duration too short: 689 samples
- Empty transcription: 114 samples

## 📁 Output Files

Each run generates:
- `train_ready.csv` - Clean samples ready for training
- `rejected.csv` - Rejected samples with reasons
- `processing_stats.json` - Detailed processing statistics

## 🛠️ Configuration

The pipeline uses intelligent defaults but can be customized:
- **Audio validation:** Duration, sample rate, corruption detection
- **Text normalization:** Diacritics, numbers, punctuation, Unicode
- **Quality filtering:** Text quality, language consistency, word count
- **Output:** Custom filenames, statistics inclusion

## 📖 Full Documentation

See `README.md` for complete documentation and API reference.

## 🎯 Next Steps

1. **Run on your data:** `python clean_data.py your_data.csv`
2. **Adjust parameters:** Use `--help` to see all options
3. **Integrate with training:** Use `train_ready.csv` with your ASR/TTS pipeline
4. **Analyze rejections:** Review `rejected.csv` to improve data quality

The pipeline is production-ready and optimized for India Speaks' multilingual ASR/TTS training workflow! 