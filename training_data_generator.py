#!/usr/bin/env python3
"""
LLM Training Data Generator for Decipher Surveys

Pairs natural language questionnaires (.docx) with their XML implementations
to create training data for LLM fine-tuning.
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

from docx import Document
from dotenv import load_dotenv

from decipher_downloader import SurveyDownloader


class DocumentProcessor:
    """Handles .docx document text extraction."""
    
    @staticmethod
    def extract_text_from_docx(docx_path: Path) -> str:
        """Extract plain text from a .docx file."""
        try:
            doc = Document(docx_path)
            text_parts = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text.strip())
            
            return '\n'.join(text_parts)
        except Exception as e:
            raise Exception(f"Failed to extract text from {docx_path}: {e}")
    
    @staticmethod
    def combine_docx_files(docx_paths: List[Path]) -> str:
        """Combine text from multiple .docx files."""
        combined_text = []
        
        for docx_path in docx_paths:
            text = DocumentProcessor.extract_text_from_docx(docx_path)
            if text.strip():
                combined_text.append(f"=== {docx_path.name} ===")
                combined_text.append(text)
                combined_text.append("")  # Empty line between documents
        
        return '\n'.join(combined_text)


class TrainingDataGenerator:
    """Generates LLM training data from survey folders and XML files."""
    
    def __init__(self, surveys_dir: str = "./Surveys", exports_dir: str = "./exports", 
                 output_file: str = "./training_data.json"):
        self.surveys_dir = Path(surveys_dir)
        self.exports_dir = Path(exports_dir)
        self.output_file = Path(output_file)
        self.doc_processor = DocumentProcessor()
        
        # Statistics
        self.stats = {
            'folders_found': 0,
            'folders_with_docx': 0,
            'folders_skipped_empty': 0,
            'xmls_matched': 0,
            'xmls_missing': 0,
            'training_pairs_created': 0,
            'errors': 0
        }
    
    def find_survey_folders(self) -> List[Path]:
        """Find all survey folders with .docx files."""
        folders = []
        
        if not self.surveys_dir.exists():
            raise Exception(f"Surveys directory not found: {self.surveys_dir}")
        
        for folder in self.surveys_dir.iterdir():
            if folder.is_dir():
                self.stats['folders_found'] += 1
                
                # Check for .docx files
                docx_files = list(folder.glob("*.docx"))
                if docx_files:
                    folders.append(folder)
                    self.stats['folders_with_docx'] += 1
                else:
                    print(f"Skipping empty folder: {folder.name}")
                    self.stats['folders_skipped_empty'] += 1
        
        return folders
    
    def find_matching_xml(self, survey_title: str) -> Optional[Path]:
        """Find XML file that matches the survey title."""
        if not self.exports_dir.exists():
            return None
        
        # Convert survey title to expected XML filename pattern
        sanitized_title = self.sanitize_title(survey_title)
        expected_prefix = f"{sanitized_title}--"
        
        # Look for XML files that start with the sanitized title
        for xml_file in self.exports_dir.glob("*.survey.xml"):
            if xml_file.name.startswith(expected_prefix):
                return xml_file
        
        return None
    
    def sanitize_title(self, title: str) -> str:
        """Sanitize title to match the XML filename pattern."""
        import re
        # Same sanitization logic as in decipher_downloader.py
        unsafe_chars = r'[/\\:*?"<>|]'
        sanitized = re.sub(unsafe_chars, '-', title)
        sanitized = re.sub(r'[-\s]+', '-', sanitized).strip('-')
        return sanitized.lower()
    
    def create_training_pair(self, folder: Path) -> Optional[Dict]:
        """Create a training pair from a survey folder."""
        survey_title = folder.name
        print(f"Processing: {survey_title}")
        
        try:
            # Extract natural language from .docx files
            docx_files = list(folder.glob("*.docx"))
            if not docx_files:
                print(f"  ✗ No .docx files found")
                return None
            
            print(f"  Found {len(docx_files)} .docx file(s)")
            natural_language = self.doc_processor.combine_docx_files(docx_files)
            
            if not natural_language.strip():
                print(f"  ✗ No text extracted from .docx files")
                return None
            
            # Find matching XML file
            xml_file = self.find_matching_xml(survey_title)
            if not xml_file:
                print(f"  ✗ No matching XML file found")
                self.stats['xmls_missing'] += 1
                return None
            
            print(f"  ✓ Found matching XML: {xml_file.name}")
            self.stats['xmls_matched'] += 1
            
            # Read XML content
            xml_content = xml_file.read_text(encoding='utf-8')
            
            # Create training pair
            training_pair = {
                "survey_title": survey_title,
                "natural_language": natural_language,
                "xml_code": xml_content,
                "source_files": {
                    "docx_files": [f.name for f in docx_files],
                    "xml_file": xml_file.name
                }
            }
            
            print(f"  ✓ Training pair created")
            self.stats['training_pairs_created'] += 1
            return training_pair
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            self.stats['errors'] += 1
            return None
    
    def generate_training_data(self, download_missing: bool = False) -> None:
        """Generate complete training dataset."""
        print("=" * 60)
        print("LLM TRAINING DATA GENERATOR")
        print("=" * 60)
        print(f"Surveys directory: {self.surveys_dir.absolute()}")
        print(f"Exports directory: {self.exports_dir.absolute()}")
        print(f"Output file: {self.output_file.absolute()}")
        print("-" * 60)
        
        # Find survey folders
        folders = self.find_survey_folders()
        print(f"Found {len(folders)} folders with .docx files")
        print()
        
        # Optionally download missing XMLs
        if download_missing:
            print("Downloading missing XML files...")
            self.download_missing_xmls(folders)
            print()
        
        # Generate training pairs
        training_data = []
        
        for folder in folders:
            training_pair = self.create_training_pair(folder)
            if training_pair:
                training_data.append(training_pair)
            print()  # Empty line between folders
        
        # Save training data
        if training_data:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, indent=2, ensure_ascii=False)
            print(f"✓ Saved {len(training_data)} training pairs to {self.output_file}")
        else:
            print("✗ No training pairs created")
        
        # Print summary
        self.print_summary()
    
    def download_missing_xmls(self, folders: List[Path]) -> None:
        """Download XML files for surveys that don't have them yet."""
        load_dotenv()
        api_key = os.getenv('Decipher_API_Key')
        
        if not api_key:
            print("Warning: No API key found, skipping XML downloads")
            return
        
        downloader = SurveyDownloader(api_key, str(self.exports_dir))
        
        # Find surveys that need XML downloads
        titles_to_download = []
        for folder in folders:
            survey_title = folder.name
            if not self.find_matching_xml(survey_title):
                titles_to_download.append(survey_title)
        
        if titles_to_download:
            print(f"Downloading {len(titles_to_download)} missing XML files...")
            downloader.download_surveys(titles_to_download)
        else:
            print("All XML files already exist")
    
    def print_summary(self) -> None:
        """Print generation summary."""
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Folders found: {self.stats['folders_found']}")
        print(f"Folders with .docx: {self.stats['folders_with_docx']}")
        print(f"Folders skipped (empty): {self.stats['folders_skipped_empty']}")
        print(f"XMLs matched: {self.stats['xmls_matched']}")
        print(f"XMLs missing: {self.stats['xmls_missing']}")
        print(f"Training pairs created: {self.stats['training_pairs_created']}")
        print(f"Errors: {self.stats['errors']}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate LLM training data from survey questionnaires and XML files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python training_data_generator.py
  python training_data_generator.py --download-missing
  python training_data_generator.py --surveys-dir ./MySurveys --output training.json
        """
    )
    parser.add_argument(
        '--surveys-dir',
        default='./Surveys',
        help='Directory containing survey folders (default: ./Surveys)'
    )
    parser.add_argument(
        '--exports-dir',
        default='./exports',
        help='Directory containing XML files (default: ./exports)'
    )
    parser.add_argument(
        '--output',
        default='./training_data.json',
        help='Output JSON file (default: ./training_data.json)'
    )
    parser.add_argument(
        '--download-missing',
        action='store_true',
        help='Download missing XML files before generating training data'
    )
    
    args = parser.parse_args()
    
    # Generate training data
    generator = TrainingDataGenerator(
        surveys_dir=args.surveys_dir,
        exports_dir=args.exports_dir,
        output_file=args.output
    )
    generator.generate_training_data(download_missing=args.download_missing)


if __name__ == '__main__':
    main()

