#!/usr/bin/env python3
"""
Enhanced Survey Downloader

Downloads both Word documents and XML files from Decipher platform.
Handles authentication via browser cookies and supports both existing
and new survey workflows.
"""

import json
import os
import re
import sys
import urllib.parse
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import browser_cookie3
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from decipher_downloader import SurveyDownloader
from async_download_handler import AsyncDownloadHandler


class DecipherAuthenticatedClient:
    """HTTP client for Decipher platform with browser-based authentication."""
    
    def __init__(self, base_url: str = "https://sw2.decipherinc.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 30
        self.authenticated = False
        self.driver = None
        self.async_handler = None
        
    def setup_browser_authentication(self) -> bool:
        """Setup authentication using browser automation."""
        print("🔐 Setting up browser authentication...")
        
        try:
            # Setup Chrome browser
            options = Options()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            try:
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            except ImportError:
                self.driver = webdriver.Chrome(options=options)
            
            print("✅ Browser ready")
            
            # Navigate to login page
            login_url = f"{self.base_url}/rep/"
            self.driver.get(login_url)
            
            print("\n" + "="*60)
            print("🎯 PLEASE LOG IN MANUALLY")
            print("="*60)
            print("1. Complete the login process in the browser window")
            print("2. Make sure you can see the main dashboard/interface")
            print("3. Come back here and press ENTER when you're logged in")
            print("="*60)
            
            # Wait for user confirmation
            input("\n⏳ Press ENTER when you've successfully logged in...")
            
            # Extract cookies from browser
            cookies = self.driver.get_cookies()
            cookie_count = 0
            
            for cookie in cookies:
                self.session.cookies.set(
                    cookie['name'], 
                    cookie['value'], 
                    domain=cookie.get('domain', ''),
                    path=cookie.get('path', '/')
                )
                cookie_count += 1
            
            print(f"✅ Loaded {cookie_count} cookies from browser session")
            
            # Initialize async handler
            self.async_handler = AsyncDownloadHandler(self.session, self.base_url)
            
            self.authenticated = True
            return True
            
        except Exception as e:
            print(f"❌ Browser authentication failed: {e}")
            return False
    
    def cleanup(self):
        """Clean up browser resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def download_word_document(self, project_id: str, output_path: Path) -> bool:
        """Download Word document for a given project ID using async method."""
        if not self.authenticated or not self.async_handler:
            print("❌ Not authenticated or async handler not initialized")
            return False
        
        print(f"📄 Downloading Word document for project {project_id}...")
        
        # Construct the download URL
        url = (f"{self.base_url}/rep/selfserve/31c4/{project_id}:odt_docFormat?"
               f"quota=false&labels=true&sequential=false&logic=true&notes=true&"
               f"transient=false&quotas=true&selectedLanguages=&comparisonLanguages=&type=doc")
        
        try:
            # Submit the document generation request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': f'{self.base_url}/rep/selfserve/31c4/{project_id}',
            }
            
            response = self.session.get(url, headers=headers, allow_redirects=True)
            
            if response.status_code != 200:
                print(f"❌ Document generation request failed: {response.status_code}")
                return False
            
            # Extract async identifier
            identifier = self.async_handler.extract_async_identifier(response)
            if not identifier:
                print("❌ Could not extract async identifier from response")
                return False
            
            print(f"🆔 Async identifier: {identifier}")
            
            # Wait for document generation (15 seconds)
            wait_result = self.async_handler.wait_for_document_generation(identifier, wait_time=15)
            
            if not wait_result['ready']:
                print(f"❌ Document generation failed: {wait_result.get('error', 'Unknown error')}")
                return False
            
            # Download the completed document
            success = self.async_handler.download_completed_document(wait_result, output_path, identifier)
            
            if success:
                print(f"✅ Word document downloaded successfully: {output_path.name}")
                return True
            else:
                print("❌ Failed to download completed document")
                return False
                
        except Exception as e:
            print(f"❌ Word document download failed: {e}")
            return False


class EnhancedSurveyProcessor:
    """Enhanced survey processor that handles both Word and XML downloads."""
    
    def __init__(self, surveys_dir: str = "./Surveys", exports_dir: str = "./exports"):
        self.surveys_dir = Path(surveys_dir)
        self.exports_dir = Path(exports_dir)
        self.auth_client = DecipherAuthenticatedClient()
        
        # Initialize standard XML downloader
        load_dotenv()
        api_key = os.getenv('Decipher_API_Key')
        if api_key:
            self.xml_downloader = SurveyDownloader(api_key, str(self.exports_dir))
        else:
            self.xml_downloader = None
            print("⚠️ No API key found - XML downloads will be skipped")
        
        # Statistics
        self.stats = {
            'folders_processed': 0,
            'word_downloads_attempted': 0,
            'word_downloads_successful': 0,
            'xml_downloads_attempted': 0,
            'xml_downloads_successful': 0,
            'errors': []
        }
    
    def setup_authentication(self) -> bool:
        """Setup authentication for Word document downloads."""
        return self.auth_client.setup_browser_authentication()
    
    def cleanup(self):
        """Clean up resources."""
        if self.auth_client:
            self.auth_client.cleanup()
    
    def extract_project_id_from_xml(self, survey_title: str) -> Optional[str]:
        """Extract project ID from existing XML file if available."""
        # Look for existing XML file
        sanitized_title = self.sanitize_title(survey_title)
        
        for xml_file in self.exports_dir.glob("*.survey.xml"):
            if xml_file.name.startswith(f"{sanitized_title}--"):
                # Extract project ID from filename pattern: title--ID.survey.xml
                match = re.search(r'--(\d+)\.survey\.xml$', xml_file.name)
                if match:
                    return match.group(1)
        
        return None
    
    def sanitize_title(self, title: str) -> str:
        """Sanitize title for filename use."""
        import re
        unsafe_chars = r'[/\\:*?"<>|]'
        sanitized = re.sub(unsafe_chars, '-', title)
        sanitized = re.sub(r'[-\s]+', '-', sanitized).strip('-')
        return sanitized.lower()
    
    def folder_has_docx(self, folder_path: Path) -> bool:
        """Check if folder contains any .docx files."""
        return len(list(folder_path.glob("*.docx"))) > 0
    
    def download_xml_for_survey(self, survey_title: str) -> Optional[str]:
        """Download XML for survey and return project ID if successful."""
        if not self.xml_downloader:
            return None
        
        print(f"📜 Downloading XML for: {survey_title}")
        
        try:
            # Use existing XML downloader
            self.xml_downloader.download_surveys([survey_title])
            
            # Extract project ID from downloaded file
            project_id = self.extract_project_id_from_xml(survey_title)
            if project_id:
                print(f"✅ XML downloaded, extracted project ID: {project_id}")
                self.stats['xml_downloads_successful'] += 1
            else:
                print("⚠️ XML downloaded but couldn't extract project ID")
            
            return project_id
            
        except Exception as e:
            error_msg = f"XML download failed for {survey_title}: {e}"
            print(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return None
    
    def download_word_for_project(self, project_id: str, survey_title: str, folder_path: Path) -> bool:
        """Download Word document for project."""
        if not self.auth_client.authenticated:
            error_msg = f"Cannot download Word doc for {survey_title} - not authenticated"
            print(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return False
        
        # Generate filename for Word document
        sanitized_title = self.sanitize_title(survey_title)
        word_filename = f"{sanitized_title}--{project_id}.docx"
        word_path = folder_path / word_filename
        
        # Skip if file already exists
        if word_path.exists():
            print(f"✅ Word document already exists: {word_filename}")
            return True
        
        self.stats['word_downloads_attempted'] += 1
        success = self.auth_client.download_word_document(project_id, word_path)
        
        if success:
            self.stats['word_downloads_successful'] += 1
        else:
            error_msg = f"Word download failed for project {project_id} ({survey_title})"
            self.stats['errors'].append(error_msg)
        
        return success
    
    def process_survey_folder(self, folder_path: Path) -> Dict[str, bool]:
        """Process a single survey folder."""
        survey_title = folder_path.name
        print(f"\n{'='*60}")
        print(f"PROCESSING FOLDER: {survey_title}")
        print(f"{'='*60}")
        
        results = {'word_success': False, 'xml_success': False}
        
        # Check if folder has existing Word documents
        has_existing_docx = self.folder_has_docx(folder_path)
        
        if has_existing_docx:
            print("📁 Folder contains existing .docx files")
            # For existing folders, just ensure we have XML
            project_id = self.extract_project_id_from_xml(survey_title)
            
            if not project_id:
                # Download XML to get project ID
                self.stats['xml_downloads_attempted'] += 1
                project_id = self.download_xml_for_survey(survey_title)
                results['xml_success'] = project_id is not None
            else:
                print(f"✅ Found existing XML with project ID: {project_id}")
                results['xml_success'] = True
            
            results['word_success'] = True  # Already have Word docs
            
        else:
            print("📁 Empty folder - downloading both Word and XML")
            
            # Step 1: Download XML to get project ID
            self.stats['xml_downloads_attempted'] += 1
            project_id = self.download_xml_for_survey(survey_title)
            results['xml_success'] = project_id is not None
            
            # Step 2: Download Word document if we got project ID
            if project_id:
                results['word_success'] = self.download_word_for_project(project_id, survey_title, folder_path)
            else:
                error_msg = f"Cannot download Word doc for {survey_title} - no project ID available"
                print(f"❌ {error_msg}")
                self.stats['errors'].append(error_msg)
        
        return results
    
    def process_specific_folder(self, folder_name: str) -> bool:
        """Process a specific folder by name."""
        folder_path = self.surveys_dir / folder_name
        
        if not folder_path.exists() or not folder_path.is_dir():
            print(f"❌ Folder not found: {folder_name}")
            return False
        
        self.stats['folders_processed'] += 1
        results = self.process_survey_folder(folder_path)
        
        return results['word_success'] and results['xml_success']
    
    def print_summary(self):
        """Print processing summary."""
        print(f"\n{'='*60}")
        print("PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"Folders processed: {self.stats['folders_processed']}")
        print(f"Word downloads attempted: {self.stats['word_downloads_attempted']}")
        print(f"Word downloads successful: {self.stats['word_downloads_successful']}")
        print(f"XML downloads attempted: {self.stats['xml_downloads_attempted']}")
        print(f"XML downloads successful: {self.stats['xml_downloads_successful']}")
        
        if self.stats['errors']:
            print(f"\nErrors encountered: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                print(f"  ❌ {error}")


def main():
    """Main entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced survey downloader with Word document support")
    parser.add_argument('--folder', required=True, help='Specific folder to process')
    parser.add_argument('--surveys-dir', default='./Surveys', help='Surveys directory path')
    parser.add_argument('--exports-dir', default='./exports', help='Exports directory path')
    
    args = parser.parse_args()
    
    print("🚀 Enhanced Survey Downloader")
    print("=" * 40)
    
    # Initialize processor
    processor = EnhancedSurveyProcessor(args.surveys_dir, args.exports_dir)
    
    # Setup authentication
    if not processor.setup_authentication():
        print("\n❌ Authentication setup failed!")
        print("💡 Please ensure you're logged into Decipher in Chrome or Firefox")
        sys.exit(1)
    
    try:
        # Process the specified folder
        success = processor.process_specific_folder(args.folder)
        
        # Print summary
        processor.print_summary()
        
        if success:
            print("\n✅ Processing completed successfully!")
        else:
            print("\n⚠️ Processing completed with issues - check summary above")
            
    finally:
        # Clean up resources
        processor.cleanup()


if __name__ == '__main__':
    main()
