#!/usr/bin/env python3
"""
Clean XML Namespaces from Training Data

Remove the three specific XML namespace declarations from all GPT responses:
- xmlns:builder="http://decipherinc.com/builder"
- xmlns:ss="http://decipherinc.com/ss" 
- xmlns:html="http://decipherinc.com/html"

While preserving all other XML content exactly as is.
"""

import json
import re
from pathlib import Path

def clean_xml_namespaces(xml_content):
    """
    Remove the three specific namespace declarations from XML content.
    
    Args:
        xml_content (str): The XML content to clean
        
    Returns:
        str: XML content with namespaces removed
    """
    if not xml_content:
        return xml_content
    
    # Define the three namespace patterns to remove
    namespace_patterns = [
        r'xmlns:builder="http://decipherinc\.com/builder"',
        r'xmlns:ss="http://decipherinc\.com/ss"',
        r'xmlns:html="http://decipherinc\.com/html"'
    ]
    
    # Remove each namespace pattern
    cleaned_content = xml_content
    for pattern in namespace_patterns:
        # Remove the namespace with any surrounding whitespace
        cleaned_content = re.sub(r'\s*' + pattern + r'\s*', ' ', cleaned_content)
    
    # Clean up any extra spaces that might have been left
    cleaned_content = re.sub(r'\s+', ' ', cleaned_content)
    
    return cleaned_content

def process_conversation_file(input_file, output_file):
    """
    Process a conversation training file to remove XML namespaces.
    
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
    
    for i, conversation in enumerate(conversations):
        if 'conversations' not in conversation:
            continue
            
        for message in conversation['conversations']:
            if message.get('from') == 'gpt':
                original_value = message['value']
                cleaned_value = clean_xml_namespaces(original_value)
                
                # Check if any namespaces were removed
                if original_value != cleaned_value:
                    namespaces_removed += 1
                    
                    # Store a few examples for verification
                    if len(examples_found) < 3:
                        examples_found.append({
                            'original': original_value[:200] + "..." if len(original_value) > 200 else original_value,
                            'cleaned': cleaned_value[:200] + "..." if len(cleaned_value) > 200 else cleaned_value
                        })
                
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
    
    print(f"\n✅ CLEANING COMPLETE!")
    print(f"📊 Total GPT responses processed: {total_processed:,}")
    print(f"🧹 Namespaces removed from: {namespaces_removed:,} responses")
    print(f"📦 Input file size: {input_size:.1f} MB")
    print(f"📦 Output file size: {output_size:.1f} MB")
    print(f"💾 Size reduction: {input_size - output_size:.1f} MB")
    
    # Show examples
    if examples_found:
        print(f"\n🔍 CLEANING EXAMPLES:")
        print("=" * 60)
        for i, example in enumerate(examples_found, 1):
            print(f"\nExample {i}:")
            print(f"BEFORE: {example['original']}")
            print(f"AFTER:  {example['cleaned']}")
    
    return True

def verify_namespace_removal(file_path):
    """
    Verify that the three specific namespaces have been removed from the file.
    
    Args:
        file_path (str): Path to the cleaned JSON file
    """
    print(f"\n🔍 VERIFYING NAMESPACE REMOVAL...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error reading {file_path}: {e}")
        return
    
    # Check for remaining namespace declarations
    namespace_patterns = [
        r'xmlns:builder="http://decipherinc\.com/builder"',
        r'xmlns:ss="http://decipherinc\.com/ss"',
        r'xmlns:html="http://decipherinc\.com/html"'
    ]
    
    remaining_namespaces = []
    for pattern in namespace_patterns:
        matches = re.findall(pattern, content)
        if matches:
            remaining_namespaces.append(f"{pattern}: {len(matches)} occurrences")
    
    if remaining_namespaces:
        print(f"⚠️  WARNING: Some namespaces still remain:")
        for namespace in remaining_namespaces:
            print(f"   - {namespace}")
    else:
        print(f"✅ SUCCESS: All three namespace declarations have been removed!")
        print(f"   - xmlns:builder=\"http://decipherinc.com/builder\"")
        print(f"   - xmlns:ss=\"http://decipherinc.com/ss\"")
        print(f"   - xmlns:html=\"http://decipherinc.com/html\"")

def main():
    """Main cleaning function."""
    
    print("🧹 CLEANING XML NAMESPACES FROM TRAINING DATA")
    print("=" * 60)
    
    # Input and output files
    input_file = 'conversation_training_data.json'
    output_file = 'conversation_training_data_cleaned.json'
    
    # Check if input file exists
    if not Path(input_file).exists():
        print(f"❌ Input file not found: {input_file}")
        return
    
    # Process the file
    success = process_conversation_file(input_file, output_file)
    
    if success:
        # Verify the cleaning worked
        verify_namespace_removal(output_file)
        
        print(f"\n🎉 CLEANING COMPLETE!")
        print(f"✅ Cleaned file saved as: {output_file}")
        print(f"🚀 Ready for LLM fine-tuning with clean XML!")
    else:
        print(f"❌ Cleaning failed!")

if __name__ == '__main__':
    main()

