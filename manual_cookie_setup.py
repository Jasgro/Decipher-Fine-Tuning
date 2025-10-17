#!/usr/bin/env python3
"""
Manual Cookie Setup Helper

Helps extract cookies manually when automatic extraction fails.
"""

def print_cookie_instructions():
    """Print instructions for manual cookie extraction."""
    print("""
🔐 MANUAL COOKIE EXTRACTION INSTRUCTIONS
=========================================

Since automatic cookie extraction didn't work, please follow these steps:

1. Open Chrome and go to: https://sw2.decipherinc.com/rep/

2. Press F12 to open Developer Tools

3. Go to the "Application" tab (or "Storage" in some versions)

4. In the left sidebar, expand "Cookies" and click on "https://sw2.decipherinc.com"

5. Look for these important cookies and copy their values:
   - sessionid (if present)
   - csrftoken (if present)
   - Any cookie with "auth" or "session" in the name

6. You can also try this JavaScript in the console to get all cookies:
   
   document.cookie.split(';').forEach(c => console.log(c.trim()));

7. Or export cookies using a browser extension like "Cookie Editor"

Once you have the cookies, we can add them manually to the script.

ALTERNATIVE: Try visiting this URL manually first:
https://sw2.decipherinc.com/rep/selfserve/31c4/250741:odt_docFormat?quota=false&labels=true&sequential=false&logic=true&notes=true&transient=false&quotas=true&selectedLanguages=&comparisonLanguages=&type=doc

If it downloads the Word document, then we know the URL works and it's just an authentication issue.
    """)

if __name__ == '__main__':
    print_cookie_instructions()

