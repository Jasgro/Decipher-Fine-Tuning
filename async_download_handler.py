#!/usr/bin/env python3
"""
Async Download Handler

Handles the asynchronous document generation process for Decipher platform.
Implements polling mechanism to wait for document completion and download.
"""

import re
import time
import requests
from urllib.parse import urlparse, parse_qs
from pathlib import Path


class AsyncDownloadHandler:
    """Handles asynchronous document downloads from Decipher platform."""
    
    def __init__(self, session: requests.Session, base_url: str = "https://sw2.decipherinc.com"):
        self.session = session
        self.base_url = base_url
        
    def extract_async_identifier(self, response: requests.Response) -> str:
        """Extract async identifier from response."""
        # Method 1: Check if URL contains async identifier
        if 'async' in response.url:
            parsed_url = urlparse(response.url)
            query_params = parse_qs(parsed_url.query)
            if 'ident' in query_params:
                return query_params['ident'][0]
        
        # Method 2: Look for identifier in JavaScript setTimeout call
        content = response.text
        # Look for pattern: setTimeout('simpleAjax("asyncBody", "IDENTIFIER")', 500);
        match = re.search(r'setTimeout\([\'"]simpleAjax\([\'"]asyncBody[\'"],\s*[\'"]([^\'\"]+)[\'\"]\)', content)
        if match:
            return match.group(1)
        
        # Method 3: Look for any identifier pattern in the URL
        match = re.search(r'ident=([a-zA-Z0-9]+)', response.url)
        if match:
            return match.group(1)
        
        return None
    
    def wait_for_document_generation(self, identifier: str, wait_time: int = 15) -> dict:
        """Wait for document generation to complete using time-based approach."""
        print(f"⏳ Waiting {wait_time} seconds for document generation (ID: {identifier})...")
        
        import time
        time.sleep(wait_time)
        
        print(f"✅ Wait completed, document should be ready")
        return {
            'ready': True,
            'identifier': identifier,
            'wait_time': wait_time
        }
    
    def is_document_ready(self, content: str, response: requests.Response) -> bool:
        """Check if document is ready for download."""
        # Method 1: Check Content-Type - if it's not HTML, it's probably the document
        content_type = response.headers.get('content-type', '').lower()
        if content_type and 'html' not in content_type:
            return True
        
        # Method 2: Check for binary content (document files)
        if len(content) > 1000 and not content.startswith('<'):
            return True
        
        # Method 3: Look for download-related indicators in content-type or headers
        content_disposition = response.headers.get('content-disposition', '').lower()
        if any(indicator in content_type for indicator in [
            'application/vnd.', 'application/msword', 'application/octet-stream'
        ]) or 'attachment' in content_disposition:
            return True
        
        # Method 4: Check for specific document completion patterns in content
        if content and not content.startswith('<'):
            # If content doesn't start with HTML tags and is substantial, it's likely a document
            if len(content) > 500:
                return True
        
        # Method 5: Look for specific completion URLs or redirects
        if hasattr(response, 'url') and response.url:
            if 'download' in response.url.lower() or 'attachment' in response.url.lower():
                return True
        
        # If it's HTML, it's still processing
        if content.strip().startswith('<'):
            return False
        
        return False
    
    def is_error_response(self, content: str) -> bool:
        """Check if response indicates an error."""
        error_indicators = [
            'error', 'failed', 'exception', 'not found',
            'access denied', 'permission', 'invalid'
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in error_indicators)
    
    def download_completed_document(self, poll_result: dict, output_path: Path, identifier: str) -> bool:
        """Download the completed document using the async-get endpoint."""
        if not poll_result.get('ready'):
            print(f"❌ Document not ready: {poll_result.get('error', 'Unknown error')}")
            return False
        
        print(f"📄 Downloading completed document...")
        
        try:
            # Generate cache-busting parameter (random float like the browser)
            import random
            cache_buster = random.random()
            
            # Construct the download URL using the async-get endpoint
            download_url = f"{self.base_url}/admin/async-get?ident={identifier}&_flurrfu={cache_buster}"
            
            print(f"🔗 Download URL: {download_url}")
            
            # Make the download request
            headers = {
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br, zstd',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Referer': f'{self.base_url}/admin/async?ident={identifier}',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'same-origin',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
            }
            
            response = self.session.get(download_url, headers=headers, stream=True, timeout=30)
            
            print(f"📊 Download response: {response.status_code}")
            print(f"📊 Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"📊 Content-Length: {response.headers.get('content-length', 'unknown')}")
            print(f"📊 Content-Disposition: {response.headers.get('content-disposition', 'none')}")
            
            if response.status_code != 200:
                print(f"❌ Download request failed: HTTP {response.status_code}")
                return False
            
            # Check if we got the right content type
            content_type = response.headers.get('content-type', '').lower()
            if 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' not in content_type:
                print(f"⚠️  Unexpected content type: {content_type}")
                # But continue anyway, might still be the document
            
            # Save the document
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verify the download
            if output_path.exists() and output_path.stat().st_size > 0:
                file_size = output_path.stat().st_size
                print(f"✅ Document saved: {output_path.name} ({file_size:,} bytes)")
                
                # Quick verification - Word docs should be substantial
                if file_size > 1000:
                    return True
                else:
                    print(f"⚠️  File seems small ({file_size} bytes), checking content...")
                    # Check if it's HTML by looking at first few bytes
                    with open(output_path, 'rb') as f:
                        first_bytes = f.read(100)
                    
                    if b'<html' in first_bytes.lower() or b'<!doctype' in first_bytes.lower():
                        print(f"❌ File contains HTML, not a document")
                        return False
                    else:
                        print(f"✅ File appears to be binary document")
                        return True
            else:
                print(f"❌ Downloaded file is empty or missing")
                return False
                
        except Exception as e:
            print(f"❌ Download failed: {e}")
            import traceback
            traceback.print_exc()
            return False


def test_async_download():
    """Test the async download functionality."""
    from browser_auth_tester import BrowserAuthTester
    
    print("🚀 Testing Async Document Download")
    print("=" * 40)
    
    # Setup authenticated session
    tester = BrowserAuthTester()
    
    if not tester.setup_browser():
        return False
    
    if not tester.interactive_login():
        return False
    
    if not tester.extract_cookies():
        return False
    
    # Initialize async handler
    handler = AsyncDownloadHandler(tester.session)
    
    # Test with the Clearwater Analytics project
    project_id = "250741"
    doc_url = (f"https://sw2.decipherinc.com/rep/selfserve/31c4/{project_id}:odt_docFormat?"
               f"quota=false&labels=true&sequential=false&logic=true&notes=true&"
               f"transient=false&quotas=true&selectedLanguages=&comparisonLanguages=&type=doc")
    
    print(f"📄 Initiating document generation for project {project_id}...")
    
    try:
        # Submit the download request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': f'https://sw2.decipherinc.com/rep/selfserve/31c4/{project_id}',
        }
        
        response = tester.session.get(doc_url, headers=headers, allow_redirects=True)
        print(f"📊 Initial response: {response.status_code}")
        
        # Extract async identifier
        identifier = handler.extract_async_identifier(response)
        if not identifier:
            print("❌ Could not extract async identifier")
            return False
        
        print(f"🆔 Async identifier: {identifier}")
        
        # Wait for document generation
        wait_result = handler.wait_for_document_generation(identifier, wait_time=15)
        
        if wait_result['ready']:
            # Download the completed document
            output_path = Path(f"test_download_{project_id}.docx")
            success = handler.download_completed_document(wait_result, output_path, identifier)
            
            if success:
                print("🎉 Async document download completed successfully!")
                return True
            else:
                print("❌ Document download failed")
                return False
        else:
            print(f"❌ Document generation failed: {poll_result.get('error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        tester.cleanup()


if __name__ == '__main__':
    test_async_download()
