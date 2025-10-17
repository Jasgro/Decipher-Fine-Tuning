#!/usr/bin/env python3
"""
Analyze XML Namespaces in Training Data

Find all XML namespace declarations that start with xmlns: and point to decipherinc.com
to identify all the variations we need to remove.
"""

import json
import re
from collections import Counter

def find_all_namespaces():
    """Find all XML namespace declarations in the training data."""
    
    print("🔍 ANALYZING XML NAMESPACES IN TRAINING DATA")
    print("=" * 60)
    
    try:
        with open('conversation_training_data_cleaned.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading file: {e}")
        return
    
    print(f"📊 Analyzing {len(data):,} conversations...")
    
    # Pattern to find all xmlns declarations pointing to decipherinc.com
    namespace_pattern = r'xmlns:([^=]+)="http://decipherinc\.com/[^"]*"'
    
    all_namespaces = []
    conversations_with_namespaces = 0
    
    for i, conversation in enumerate(data):
        if 'conversations' not in conversation:
            continue
            
        for message in conversation['conversations']:
            if message.get('from') == 'gpt':
                xml_content = message['value']
                
                # Find all namespace declarations
                matches = re.findall(namespace_pattern, xml_content)
                if matches:
                    conversations_with_namespaces += 1
                    all_namespaces.extend(matches)
                    
                    # Show first few examples
                    if len(all_namespaces) <= 20:
                        print(f"\n🔍 Found in conversation {i+1}:")
                        for match in matches:
                            full_declaration = f'xmlns:{match}="http://decipherinc.com/{match}"'
                            print(f"   - {full_declaration}")
    
    # Count occurrences
    namespace_counts = Counter(all_namespaces)
    
    print(f"\n📊 NAMESPACE ANALYSIS RESULTS:")
    print("=" * 50)
    print(f"📁 Total conversations: {len(data):,}")
    print(f"🔍 Conversations with namespaces: {conversations_with_namespaces:,}")
    print(f"📝 Total namespace declarations found: {len(all_namespaces):,}")
    print(f"🎯 Unique namespace types: {len(namespace_counts):,}")
    
    print(f"\n📋 ALL NAMESPACE TYPES FOUND:")
    print("-" * 50)
    for namespace, count in namespace_counts.most_common():
        print(f"xmlns:{namespace} - {count:,} occurrences")
    
    # Show some examples of the actual XML with namespaces
    print(f"\n🔍 SAMPLE XML WITH NAMESPACES:")
    print("-" * 50)
    
    sample_count = 0
    for conversation in data:
        if sample_count >= 3:
            break
            
        if 'conversations' not in conversation:
            continue
            
        for message in conversation['conversations']:
            if message.get('from') == 'gpt':
                xml_content = message['value']
                if re.search(namespace_pattern, xml_content):
                    # Extract the first line with namespaces
                    lines = xml_content.split('\n')
                    for line in lines:
                        if re.search(namespace_pattern, line):
                            print(f"Example {sample_count + 1}:")
                            print(f"   {line[:200]}{'...' if len(line) > 200 else ''}")
                            sample_count += 1
                            break
                    if sample_count >= 3:
                        break
    
    # Generate the complete list of patterns to remove
    print(f"\n🎯 NAMESPACE PATTERNS TO REMOVE:")
    print("-" * 50)
    for namespace in sorted(namespace_counts.keys()):
        pattern = f'xmlns:{namespace}="http://decipherinc.com/{namespace}"'
        print(f"   - {pattern}")
    
    return namespace_counts

def main():
    """Main analysis function."""
    namespace_counts = find_all_namespaces()
    
    if namespace_counts:
        print(f"\n✅ ANALYSIS COMPLETE!")
        print(f"🎯 Found {len(namespace_counts)} different namespace types")
        print(f"📊 Total declarations to remove: {sum(namespace_counts.values()):,}")
        
        # Create a comprehensive cleaning script
        print(f"\n💡 NEXT STEPS:")
        print(f"1. Use the patterns above to create a comprehensive cleaning script")
        print(f"2. Remove ALL xmlns declarations pointing to decipherinc.com")
        print(f"3. Verify complete removal")

if __name__ == '__main__':
    main()




