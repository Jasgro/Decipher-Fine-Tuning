#!/usr/bin/env python3
"""
Browser Authentication Tester

Lightweight tool to test browser-based authentication for Decipher platform.
Opens browser, lets user log in, extracts cookies, and tests authentication.
"""

import requests
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BrowserAuthTester:
    """Lightweight browser authentication tester."""
    
    def __init__(self):
        self.driver = None
        self.session = requests.Session()
        self.base_url = "https://sw2.decipherinc.com"
        
    def setup_browser(self):
        """Setup Chrome browser with appropriate options."""
        print("🌐 Setting up browser...")
        
        # Chrome options
        options = Options()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        try:
            # Try to use Chrome with automatic driver management
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            
        except ImportError:
            print("📦 webdriver_manager not found, trying system Chrome...")
            try:
                # Fallback to system Chrome
                self.driver = webdriver.Chrome(options=options)
            except Exception as e:
                print(f"❌ Chrome setup failed: {e}")
                print("💡 Please ensure Chrome and chromedriver are installed")
                return False
        
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False
        
        print("✅ Browser ready")
        return True
    
    def interactive_login(self):
        """Open browser for interactive login."""
        if not self.driver:
            print("❌ Browser not initialized")
            return False
        
        print("🔐 Opening login page...")
        
        # Navigate to the main login page
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
        
        # Give a moment for any final redirects
        time.sleep(2)
        
        print("✅ Login completed, extracting cookies...")
        return True
    
    def extract_cookies(self):
        """Extract cookies from browser session."""
        if not self.driver:
            print("❌ Browser not available")
            return False
        
        cookies = self.driver.get_cookies()
        cookie_count = 0
        
        print(f"🍪 Found {len(cookies)} cookies:")
        
        for cookie in cookies:
            # Add cookie to requests session
            self.session.cookies.set(
                cookie['name'], 
                cookie['value'], 
                domain=cookie.get('domain', ''),
                path=cookie.get('path', '/')
            )
            cookie_count += 1
            print(f"   📋 {cookie['name']}: {cookie['value'][:20]}{'...' if len(cookie['value']) > 20 else ''}")
        
        print(f"✅ Loaded {cookie_count} cookies into session")
        return cookie_count > 0
    
    def test_authentication(self, project_id: str = "250741"):
        """Test authentication with extracted cookies."""
        print(f"\n🧪 Testing authentication with project {project_id}...")
        
        # Test 1: API endpoint
        api_url = f"{self.base_url}/api/v1/rh/companies/all/surveys?query=test"
        print(f"🔍 Testing API: {api_url}")
        
        try:
            api_response = self.session.get(api_url, timeout=10)
            print(f"   📊 API Status: {api_response.status_code}")
        except Exception as e:
            print(f"   ❌ API Test Failed: {e}")
        
        # Test 2: Reporting interface
        rep_url = f"{self.base_url}/rep/"
        print(f"🔍 Testing Reporting: {rep_url}")
        
        try:
            rep_response = self.session.get(rep_url, timeout=10, allow_redirects=False)
            print(f"   📊 Reporting Status: {rep_response.status_code}")
        except Exception as e:
            print(f"   ❌ Reporting Test Failed: {e}")
        
        # Test 3: Project page
        project_url = f"{self.base_url}/rep/selfserve/31c4/{project_id}"
        print(f"🔍 Testing Project Page: {project_url}")
        
        try:
            project_response = self.session.get(project_url, timeout=10)
            print(f"   📊 Project Status: {project_response.status_code}")
            
            # Check if we got HTML with login form
            if 'login' in project_response.text.lower():
                print("   ⚠️  Response contains login form - authentication may have failed")
            else:
                print("   ✅ Project page accessible")
                
        except Exception as e:
            print(f"   ❌ Project Test Failed: {e}")
        
        # Test 4: Word document download
        doc_url = (f"{self.base_url}/rep/selfserve/31c4/{project_id}:odt_docFormat?"
                   f"quota=false&labels=true&sequential=false&logic=true&notes=true&"
                   f"transient=false&quotas=true&selectedLanguages=&comparisonLanguages=&type=doc")
        
        print(f"🔍 Testing Word Download: {doc_url}")
        
        try:
            # Add browser-like headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            doc_response = self.session.get(doc_url, timeout=10, headers=headers)
            print(f"   📊 Download Status: {doc_response.status_code}")
            print(f"   📊 Content-Type: {doc_response.headers.get('content-type', 'unknown')}")
            print(f"   📊 Content-Length: {doc_response.headers.get('content-length', 'unknown')}")
            
            content_type = doc_response.headers.get('content-type', '').lower()
            
            if 'html' in content_type:
                print("   ❌ Received HTML (likely login redirect)")
                # Check first 200 chars for login indicators
                content_start = doc_response.text[:200].lower()
                if 'login' in content_start or 'sign in' in content_start:
                    print("   🔍 Confirmed: Response is a login page")
                else:
                    print("   🔍 HTML response but might not be login page")
            else:
                print("   ✅ Received document content!")
                print(f"   📊 First 50 bytes: {doc_response.content[:50]}")
                
        except Exception as e:
            print(f"   ❌ Download Test Failed: {e}")
    
    def cleanup(self):
        """Clean up browser resources."""
        if self.driver:
            print("🧹 Closing browser...")
            self.driver.quit()
    
    def run_test(self, project_id: str = "250741"):
        """Run complete authentication test."""
        print("🚀 Browser Authentication Tester")
        print("=" * 40)
        
        try:
            # Setup browser
            if not self.setup_browser():
                return False
            
            # Interactive login
            if not self.interactive_login():
                return False
            
            # Extract cookies
            if not self.extract_cookies():
                return False
            
            # Test authentication
            self.test_authentication(project_id)
            
            print("\n✅ Authentication test completed!")
            return True
            
        except KeyboardInterrupt:
            print("\n❌ Test interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
            return False
        finally:
            self.cleanup()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test browser authentication for Decipher")
    parser.add_argument('--project-id', default='250741', help='Project ID to test with')
    
    args = parser.parse_args()
    
    tester = BrowserAuthTester()
    success = tester.run_test(args.project_id)
    
    if success:
        print("\n🎉 If the Word download test worked, we can integrate this into the main script!")
    else:
        print("\n❌ Authentication test failed - manual cookie export might be needed")


if __name__ == '__main__':
    main()

