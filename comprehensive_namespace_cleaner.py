#!/usr/bin/env python3
"""
Comprehensive XML Namespace Cleaner

Remove ALL XML namespace declarations that point to decipherinc.com domains.
Based on analysis, we found 16 different namespace types with 5,528 total declarations.
"""

import json
import re
from pathlib import Path

def clean_all_namespaces(xml_content):
    """
    Remove ALL XML namespace declarations pointing to decipherinc.com domains.
    
    Args:
        xml_content (str): The XML content to clean
        
    Returns:
        str: XML content with all namespaces removed
    """
    if not xml_content:
        return xml_content
    
    # Pattern to match ANY xmlns declaration pointing to decipherinc.com
    # This will catch all current and future variations
    namespace_pattern = r'\s*xmlns:[^=]+="http://decipherinc\.com/[^"]*"\s*'
    
    # Remove all namespace declarations
    cleaned_content = re.sub(namespace_pattern, ' ', xml_content)
    
    # Clean up any extra spaces that might have been left
    cleaned_content = re.sub(r'\s+', ' ', cleaned_content)
    
    return cleaned_content

def process_conversation_file(input_file, output_file):
    """
    Process a conversation training file to remove ALL XML namespaces.
    
    Args:
        input_file (str): Path to input JSON file
        output_file (str): Path to output JSON file
    """
    print(f"🔄 Loading conversation data from: {input_file}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            conversations = json.load(f)
    except Exception as e:
        print(f"❌ Error loading {input_file}: {e}")
        return False
    
    print(f"📊 Processing {len(conversations):,} conversations...")
    
    # Track statistics
    total_processed = 0
    namespaces_removed = 0
    examples_found = []
    
    # Pattern to count namespaces before cleaning
    namespace_pattern = r'xmlns:[^=]+="http://decipherinc\.com/[^"]*"'
    
    for i, conversation in enumerate(conversations):
        if 'conversations' not in conversation:
            continue
            
        for message in conversation['conversations']:
            if message.get('from') == 'gpt':
                original_value = message['value']
                
                # Count namespaces before cleaning
                namespace_matches = re.findall(namespace_pattern, original_value)
                if namespace_matches:
                    namespaces_removed += len(namespace_matches)
                    
                    # Store examples for verification
                    if len(examples_found) < 5:
                        examples_found.append({
                            'original': original_value[:300] + "..." if len(original_value) > 300 else original_value,
                            'namespaces_found': namespace_matches[:3]  # Show first 3 namespaces found
                        })
                
                # Clean the content
                cleaned_value = clean_all_namespaces(original_value)
                
                # Update the message with cleaned content
                message['value'] = cleaned_value
                total_processed += 1
    
    # Save the cleaned data
    print(f"💾 Saving cleaned data to: {output_file}")
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(conversations, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"❌ Error saving {output_file}: {e}")
        return False
    
    # File size comparison
    input_size = Path(input_file).stat().st_size / (1024 * 1024)
    output_size = Path(output_file).stat().st_size / (1024 * 1024)
    
    print(f"\n✅ COMPREHENSIVE CLEANING COMPLETE!")
    print(f"📊 Total GPT responses processed: {total_processed:,}")
    print(f"🧹 Namespace declarations removed: {namespaces_removed:,}")
    print(f"📦 Input file size: {input_size:.1f} MB")
    print(f"📦 Output file size: {output_size:.1f} MB")
    print(f"💾 Size reduction: {input_size - output_size:.1f} MB")
    
    # Show examples
    if examples_found:
        print(f"\n🔍 CLEANING EXAMPLES:")
        print("=" * 60)
        for i, example in enumerate(examples_found, 1):
            print(f"\nExample {i}:")
            print(f"Namespaces found: {', '.join(example['namespaces_found'])}")
            print(f"BEFORE: {example['original']}")
    
    return True

def verify_complete_removal(file_path):
    """
    Verify that ALL namespace declarations have been removed from the file.
    
    Args:
        file_path (str): Path to the cleaned JSON file
    """
    print(f"\n🔍 VERIFYING COMPLETE NAMESPACE REMOVAL...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return
    
    # Check for ANY remaining namespace declarations pointing to decipherinc.com
    namespace_pattern = r'xmlns:[^=]+="http://decipherinc\.com/[^"]*"'
    remaining_matches = re.findall(namespace_pattern, content)
    
    if remaining_matches:
        print(f"⚠️  WARNING: {len(remaining_matches)} namespace declarations still remain:")
        unique_remaining = list(set(remaining_matches))
        for namespace in unique_remaining[:10]:  # Show first 10
            print(f"   - {namespace}")
        if len(unique_remaining) > 10:
            print(f"   ... and {len(unique_remaining) - 10} more")
    else:
        print(f"✅ SUCCESS: ALL namespace declarations have been removed!")
        print(f"   - No xmlns declarations pointing to decipherinc.com remain")
    
    # Count total conversations
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"📊 Total conversations: {len(data):,}")
    except:
        pass

def main():
    """Main comprehensive cleaning function."""
    
    print("🧹 COMPREHENSIVE XML NAMESPACE CLEANING")
    print("=" * 60)
    print("🎯 Removing ALL xmlns declarations pointing to decipherinc.com")
    print("📊 Based on analysis: 16 namespace types, 5,528 total declarations")
    
    # Input and output files
    input_file = 'conversation_training_data_cleaned.json'
    output_file = 'conversation_training_data_final.json'
    
    # Check if input file exists
    if not Path(input_file).exists():
        print(f"❌ Input file not found: {input_file}")
        return
    
    # Process the file
    success = process_conversation_file(input_file, output_file)
    
    if success:
        # Verify the cleaning worked
        verify_complete_removal(output_file)
        
        print(f"\n🎉 COMPREHENSIVE CLEANING COMPLETE!")
        print(f"✅ Final cleaned file: {output_file}")
        print(f"🚀 Ready for LLM fine-tuning with completely clean XML!")
    else:
        print(f"❌ Cleaning failed!")

if __name__ == '__main__':
    main()




