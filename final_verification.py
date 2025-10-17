#!/usr/bin/env python3
"""
Final Verification of Complete Namespace Removal

Verify that ALL XML namespace declarations have been completely removed.
"""

import json
import re

def final_verification():
    """Perform final verification of complete namespace removal."""
    
    print("🔍 FINAL VERIFICATION: COMPLETE NAMESPACE REMOVAL")
    print("=" * 60)
    
    try:
        with open('conversation_training_data_final.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading final file: {e}")
        return
    
    print(f"📊 Verifying {len(data):,} conversations...")
    
    # Pattern to find ANY xmlns declaration pointing to decipherinc.com
    namespace_pattern = r'xmlns:[^=]+="http://decipherinc\.com/[^"]*"'
    
    total_namespaces_found = 0
    conversations_with_namespaces = 0
    sample_remaining = []
    
    for i, conversation in enumerate(data):
        if 'conversations' not in conversation:
            continue
            
        for message in conversation['conversations']:
            if message.get('from') == 'gpt':
                xml_content = message['value']
                
                # Check for any remaining namespaces
                matches = re.findall(namespace_pattern, xml_content)
                if matches:
                    total_namespaces_found += len(matches)
                    conversations_with_namespaces += 1
                    
                    # Store samples of remaining namespaces
                    if len(sample_remaining) < 5:
                        sample_remaining.append({
                            'conversation': i + 1,
                            'namespaces': matches,
                            'xml_sample': xml_content[:200] + "..." if len(xml_content) > 200 else xml_content
                        })
    
    # Results
    print(f"\n📊 VERIFICATION RESULTS:")
    print("=" * 40)
    print(f"📁 Total conversations checked: {len(data):,}")
    print(f"🔍 Conversations with namespaces: {conversations_with_namespaces:,}")
    print(f"📝 Total namespace declarations found: {total_namespaces_found:,}")
    
    if total_namespaces_found == 0:
        print(f"\n✅ PERFECT! ALL NAMESPACES REMOVED!")
        print(f"🎯 Zero xmlns declarations pointing to decipherinc.com remain")
        print(f"🚀 Training data is completely clean and ready!")
    else:
        print(f"\n⚠️  WARNING: {total_namespaces_found} namespace declarations still remain!")
        print(f"🔍 Sample remaining namespaces:")
        for sample in sample_remaining:
            print(f"   Conversation {sample['conversation']}: {', '.join(sample['namespaces'])}")
    
    # File size info
    import os
    file_size = os.path.getsize('conversation_training_data_final.json') / (1024 * 1024)
    print(f"\n📦 Final file size: {file_size:.1f} MB")
    
    # Show a sample of clean XML
    if data:
        print(f"\n🔍 SAMPLE OF CLEAN XML:")
        print("-" * 40)
        sample_conv = data[0]['conversations'][1]['value']
        print(f"{sample_conv[:300]}{'...' if len(sample_conv) > 300 else ''}")

if __name__ == '__main__':
    final_verification()




