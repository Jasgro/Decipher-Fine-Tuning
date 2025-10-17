# Decipher Survey Processing Scripts

This repository contains Python scripts for downloading, processing, and analyzing survey data from the Decipher platform. These scripts were developed as part of research for HU 695.

## Overview

The scripts in this repository provide functionality for:
- Automated survey downloading from Decipher
- XML data processing and cleaning
- Training data generation for machine learning models
- Data analysis and verification

## Requirements

Install dependencies using:

```bash
pip install -r requirements.txt
```

## Configuration

The scripts require a Decipher API key. Set up your environment:

1. Create a `.env` file in the working directory
2. Add your API key: `Decipher_API_Key=your_api_key_here`

## Main Scripts

### Survey Downloading

- **`decipher_downloader.py`** - Main script for downloading surveys from Decipher
- **`enhanced_survey_downloader.py`** - Enhanced version with additional features
- **`batch_survey_processor.py`** - Process multiple surveys in batch mode
- **`async_download_handler.py`** - Asynchronous download handler for improved performance

### Data Processing

- **`question_splitter.py`** - Split complex survey questions into components
- **`clean_xml_namespaces.py`** - Clean XML namespace issues in survey data
- **`comprehensive_namespace_cleaner.py`** - More thorough XML namespace cleaning
- **`analyze_xml_namespaces.py`** - Analyze XML namespace patterns

### Training Data Generation

- **`training_data_generator.py`** - Generate training data for ML models
- **`convert_to_conversation_format.py`** - Convert data to conversation format
- **`convert_with_metadata.py`** - Convert data with metadata preservation

### Analysis and Verification

- **`analyze_training_data.py`** - Analyze generated training data
- **`complete_dataset_summary.py`** - Generate summary statistics for datasets
- **`final_dataset_stats.py`** - Calculate final dataset statistics
- **`final_verification.py`** - Verify data integrity
- **`verify_cleaning.py`** - Verify data cleaning operations
- **`monitor_question_splitting.py`** - Monitor question splitting process

### Testing and Debugging

- **`test_direct_download.py`** - Test direct download functionality
- **`debug_download.py`** - Debug download issues
- **`browser_auth_tester.py`** - Test browser-based authentication
- **`manual_cookie_setup.py`** - Manual cookie configuration for authentication

## Usage Examples

### Download Surveys

```python
python decipher_downloader.py
```

### Process Survey Data

```python
python batch_survey_processor.py
```

### Generate Training Data

```python
python training_data_generator.py
```




