#!/usr/bin/env python3
"""
Decipher Survey XML Downloader

Downloads survey XML files from Decipher API by matching survey titles.
Usage: python decipher_downloader.py "Survey Title 1" "Survey Title 2" ...
"""

import argparse
import os
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv


class DecipherClient:
    """HTTP client for Decipher API with authentication and error handling."""
    
    def __init__(self, api_key: str, base_url: str = "https://sw2.decipherinc.com/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'x-apikey': api_key,
            'User-Agent': 'Decipher-Survey-Downloader/1.0'
        })
        self.session.timeout = 30
    
    def search_surveys(self, title: str) -> List[Dict]:
        """Search for surveys by title."""
        url = f"{self.base_url}/rh/companies/all/surveys"
        params = {'query': title}
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise Exception(f"Failed to search surveys: {e}")
    
    def download_survey_xml(self, survey_path: str) -> bytes:
        """Download survey XML file."""
        # URL encode the path
        encoded_path = urllib.parse.quote(survey_path, safe='')
        url = f"{self.base_url}/surveys/{encoded_path}/files/survey.xml"
        
        try:
            response = self.session.get(url)
            
            if response.status_code == 401:
                raise Exception("Invalid or expired API key")
            elif response.status_code == 403:
                raise Exception("No permission to access this survey")
            elif response.status_code == 404:
                raise Exception("Survey or XML file not found")
            elif response.status_code == 429:
                raise Exception("Rate limit exceeded")
            
            response.raise_for_status()
            return response.content
            
        except requests.RequestException as e:
            raise Exception(f"Failed to download XML: {e}")


class SurveyDownloader:
    """Main survey downloader class."""
    
    def __init__(self, api_key: str, output_dir: str = "./exports"):
        self.client = DecipherClient(api_key)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Statistics
        self.stats = {
            'requested': 0,
            'resolved': 0,
            'downloaded': 0,
            'not_found': 0,
            'ambiguous': 0,
            'errors': 0
        }
    
    def sanitize_filename(self, title: str) -> str:
        """Sanitize title for use in filename."""
        # Remove or replace filesystem-unsafe characters
        unsafe_chars = r'[/\\:*?"<>|]'
        sanitized = re.sub(unsafe_chars, '-', title)
        # Collapse multiple spaces/dashes and strip
        sanitized = re.sub(r'[-\s]+', '-', sanitized).strip('-')
        return sanitized.lower()
    
    def normalize_title(self, title: str) -> str:
        """Normalize title for exact matching."""
        return ' '.join(title.strip().split())
    
    def find_exact_match(self, surveys: List[Dict], target_title: str) -> Optional[str]:
        """Find exact case-insensitive match and return survey path."""
        normalized_target = target_title.lower()
        matches = []
        
        for survey in surveys:
            survey_title = survey.get('title', '').lower()
            if survey_title == normalized_target:
                matches.append(survey.get('path'))
        
        if len(matches) == 0:
            return None
        elif len(matches) > 1:
            raise Exception("Ambiguous: multiple surveys with same title")
        else:
            return matches[0]
    
    def extract_survey_id(self, path: str) -> str:
        """Extract the last path segment (survey ID)."""
        return path.rstrip('/').split('/')[-1]
    
    def process_survey(self, title: str) -> bool:
        """Process a single survey title. Returns True if successful."""
        print(f'Processing survey: "{title}"')
        normalized_title = self.normalize_title(title)
        
        try:
            # Step 1: Search for survey
            surveys = self.client.search_surveys(normalized_title)
            
            # Step 2: Find exact match
            survey_path = self.find_exact_match(surveys, normalized_title)
            
            if survey_path is None:
                print("✗ No exact match found")
                self.stats['not_found'] += 1
                return False
            
            print(f"✓ Found exact match, path: {survey_path}")
            self.stats['resolved'] += 1
            
            # Step 3: Download XML
            xml_content = self.client.download_survey_xml(survey_path)
            
            # Step 4: Save file
            survey_id = self.extract_survey_id(survey_path)
            sanitized_title = self.sanitize_filename(title)
            filename = f"{sanitized_title}--{survey_id}.survey.xml"
            filepath = self.output_dir / filename
            
            filepath.write_bytes(xml_content)
            print(f"✓ Downloaded XML, saved as: {filename}")
            self.stats['downloaded'] += 1
            return True
            
        except Exception as e:
            if "Ambiguous" in str(e):
                print(f"✗ {e}")
                self.stats['ambiguous'] += 1
            else:
                print(f"✗ Error: {e}")
                self.stats['errors'] += 1
            return False
    
    def download_surveys(self, titles: List[str]) -> None:
        """Download surveys for all provided titles."""
        self.stats['requested'] = len(titles)
        
        print(f"Starting download for {len(titles)} survey(s)...")
        print(f"Output directory: {self.output_dir.absolute()}")
        print("-" * 50)
        
        for title in titles:
            self.process_survey(title)
            print()  # Empty line between surveys
        
        # Print summary
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print download summary."""
        print("=" * 50)
        print("SUMMARY")
        print("=" * 50)
        print(f"Requested: {self.stats['requested']}")
        print(f"Resolved: {self.stats['resolved']}")
        print(f"Downloaded: {self.stats['downloaded']}")
        print(f"Not found: {self.stats['not_found']}")
        print(f"Ambiguous: {self.stats['ambiguous']}")
        print(f"Errors: {self.stats['errors']}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download survey XML files from Decipher API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python decipher_downloader.py "Survey Title 1"
  python decipher_downloader.py "Survey A" "Survey B" "Survey C"
        """
    )
    parser.add_argument(
        'titles',
        nargs='+',
        help='Survey titles to download'
    )
    parser.add_argument(
        '--output-dir',
        default='./exports',
        help='Output directory for downloaded files (default: ./exports)'
    )
    
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('Decipher_API_Key')
    
    if not api_key:
        print("Error: Decipher_API_Key not found in environment variables")
        print("Please ensure .env file contains: Decipher_API_Key=your_key_here")
        sys.exit(1)
    
    # Initialize downloader and process surveys
    downloader = SurveyDownloader(api_key, args.output_dir)
    downloader.download_surveys(args.titles)


if __name__ == '__main__':
    main()

