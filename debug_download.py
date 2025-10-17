#!/usr/bin/env python3
"""
Quick debug script to check what HTML we're getting from the Word download URL
"""

import requests
from browser_auth_tester import BrowserAuthTester

def debug_download():
    """Debug the Word download response"""
    print("🔍 Debug Word Download Response")
    print("=" * 40)
    
    # Use the browser tester to get authenticated session
    tester = BrowserAuthTester()
    
    if not tester.setup_browser():
        return
    
    if not tester.interactive_login():
        return
    
    if not tester.extract_cookies():
        return
    
    # Now test the download with more detailed debugging
    project_id = "250741"
    doc_url = (f"https://sw2.decipherinc.com/rep/selfserve/31c4/{project_id}:odt_docFormat?"
               f"quota=false&labels=true&sequential=false&logic=true&notes=true&"
               f"transient=false&quotas=true&selectedLanguages=&comparisonLanguages=&type=doc")
    
    print(f"🔗 Testing URL: {doc_url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Referer': f'https://sw2.decipherinc.com/rep/selfserve/31c4/{project_id}',
    }
    
    response = tester.session.get(doc_url, headers=headers, allow_redirects=True)
    
    print(f"📊 Status: {response.status_code}")
    print(f"📊 Headers: {dict(response.headers)}")
    print(f"📊 URL after redirects: {response.url}")
    print(f"📊 Content length: {len(response.content)} bytes")
    print(f"📊 First 500 chars:")
    print("-" * 40)
    print(response.text[:500])
    print("-" * 40)
    
    # Save full response for inspection
    with open("debug_download_response.html", "w", encoding="utf-8") as f:
        f.write(response.text)
    
    print("💾 Full response saved to debug_download_response.html")
    
    tester.cleanup()

if __name__ == '__main__':
    debug_download()

