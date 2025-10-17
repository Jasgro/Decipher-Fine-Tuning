#!/usr/bin/env python3
"""
Verify XML Namespace Cleaning

Check that all three namespace declarations have been removed.
"""

import re

def verify_cleaning():
    """Verify that all namespaces have been removed."""
    
    print("🔍 VERIFYING XML NAMESPACE CLEANING...")
    print("=" * 50)
    
    try:
        with open('conversation_training_data_cleaned.json', 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    # Check for the three specific namespaces
    namespace_patterns = [
        'xmlns:builder="http://decipherinc.com/builder"',
        'xmlns:ss="http://decipherinc.com/ss"',
        'xmlns:html="http://decipherinc.com/html"'
    ]
    
    remaining_namespaces = []
    for pattern in namespace_patterns:
        matches = re.findall(re.escape(pattern), content)
        if matches:
            remaining_namespaces.append(f"{pattern}: {len(matches)} occurrences")
    
    if remaining_namespaces:
        print("⚠️  WARNING: Some namespaces still remain:")
        for namespace in remaining_namespaces:
            print(f"   - {namespace}")
    else:
        print("✅ SUCCESS: All three namespace declarations have been removed!")
        print("   - xmlns:builder=\"http://decipherinc.com/builder\"")
        print("   - xmlns:ss=\"http://decipherinc.com/ss\"")
        print("   - xmlns:html=\"http://decipherinc.com/html\"")
    
    # File size info
    import os
    file_size = os.path.getsize('conversation_training_data_cleaned.json') / (1024 * 1024)
    print(f"\n📦 Cleaned file size: {file_size:.1f} MB")
    
    # Count total conversations
    import json
    with open('conversation_training_data_cleaned.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    print(f"📊 Total conversations: {len(data):,}")

if __name__ == '__main__':
    verify_cleaning()




