#!/usr/bin/env python3
"""
Test direct download using the async-get endpoint
"""

import random
import requests
from browser_auth_tester import BrowserAuthTester

def test_direct_download():
    """Test direct download without waiting for polling completion"""
    print("🧪 Testing Direct Async Download")
    print("=" * 40)
    
    # Setup authenticated session
    tester = BrowserAuthTester()
    
    if not tester.setup_browser():
        return False
    
    if not tester.interactive_login():
        return False
    
    if not tester.extract_cookies():
        return False
    
    # Test with the Clearwater Analytics project
    project_id = "250741"
    base_url = "https://sw2.decipherinc.com"
    
    # Step 1: Initiate document generation
    doc_url = (f"{base_url}/rep/selfserve/31c4/{project_id}:odt_docFormat?"
               f"quota=false&labels=true&sequential=false&logic=true&notes=true&"
               f"transient=false&quotas=true&selectedLanguages=&comparisonLanguages=&type=doc")
    
    print(f"📄 Initiating document generation...")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': f'{base_url}/rep/selfserve/31c4/{project_id}',
    }
    
    response = tester.session.get(doc_url, headers=headers, allow_redirects=True)
    print(f"📊 Initial response: {response.status_code}")
    
    # Extract identifier
    if 'async' in response.url:
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(response.url)
        query_params = parse_qs(parsed_url.query)
        if 'ident' in query_params:
            identifier = query_params['ident'][0]
            print(f"🆔 Extracted identifier: {identifier}")
        else:
            print("❌ No identifier found in URL")
            return False
    else:
        print("❌ No async redirect detected")
        return False
    
    # Step 2: Try direct download at different intervals
    for wait_time in [5, 10, 15, 30, 45, 60]:
        print(f"\n⏰ Waiting {wait_time} seconds before trying download...")
        import time
        time.sleep(wait_time - (0 if wait_time == 5 else 5))  # Adjust for previous waits
        
        # Try the async-get endpoint
        cache_buster = random.random()
        download_url = f"{base_url}/admin/async-get?ident={identifier}&_flurrfu={cache_buster}"
        
        print(f"🔗 Trying download: {download_url}")
        
        download_headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Referer': f'{base_url}/admin/async?ident={identifier}',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
        }
        
        try:
            dl_response = tester.session.get(download_url, headers=download_headers, timeout=10)
            
            print(f"   📊 Status: {dl_response.status_code}")
            print(f"   📊 Content-Type: {dl_response.headers.get('content-type', 'unknown')}")
            print(f"   📊 Content-Length: {dl_response.headers.get('content-length', 'unknown')}")
            print(f"   📊 Content-Disposition: {dl_response.headers.get('content-disposition', 'none')}")
            
            content_type = dl_response.headers.get('content-type', '').lower()
            
            if 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' in content_type:
                print(f"   🎉 SUCCESS! Got Word document!")
                
                # Save it
                output_path = f"direct_download_test_{wait_time}s.docx"
                with open(output_path, 'wb') as f:
                    f.write(dl_response.content)
                
                file_size = len(dl_response.content)
                print(f"   ✅ Saved document: {output_path} ({file_size:,} bytes)")
                tester.cleanup()
                return True
                
            elif 'html' in content_type:
                print(f"   ⏳ Still generating (got HTML)")
                # Show first bit of content to see if it's different
                content_preview = dl_response.text[:100].replace('\n', ' ')
                print(f"   🔍 Content: {content_preview}...")
            else:
                print(f"   ❓ Unknown content type: {content_type}")
                
        except Exception as e:
            print(f"   ❌ Download attempt failed: {e}")
    
    print(f"\n❌ All download attempts failed")
    tester.cleanup()
    return False

if __name__ == '__main__':
    test_direct_download()

