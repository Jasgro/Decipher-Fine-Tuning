#!/usr/bin/env python3
"""
Convert Training Data to Conversation Format

Converts our existing question-level training data to the conversation format
required for LLM fine-tuning.

Format:
{'conversations': [
    {'from': 'human', 'value': '[question text]'},
    {'from': 'gpt', 'value': '[question script]'}
]}
"""

import json
import sys
from pathlib import Path

def load_training_data(filename):
    """Load the existing training data."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return []

def convert_to_conversation_format(training_data, min_similarity=0.7):
    """Convert training data to conversation format."""
    
    conversations = []
    skipped_count = 0
    
    print(f"🔄 Converting {len(training_data):,} training pairs...")
    
    for i, item in enumerate(training_data):
        # Extract fields
        natural_language = item.get('natural_language', '').strip()
        xml_code = item.get('xml_code', '').strip()
        similarity_score = item.get('similarity_score', 0)
        survey_title = item.get('survey_title', 'Unknown')
        question_number = item.get('question_number', 'Unknown')
        
        # Skip low-quality matches if desired
        if similarity_score < min_similarity:
            skipped_count += 1
            continue
            
        # Skip empty content
        if not natural_language or not xml_code:
            skipped_count += 1
            continue
        
        # Create conversation format
        conversation = {
            'conversations': [
                {
                    'from': 'human',
                    'value': natural_language
                },
                {
                    'from': 'gpt', 
                    'value': xml_code
                }
            ]
        }
        
        # Optionally add metadata as comments (can be removed if not needed)
        # conversation['metadata'] = {
        #     'survey_title': survey_title,
        #     'question_number': question_number,
        #     'similarity_score': similarity_score
        # }
        
        conversations.append(conversation)
        
        # Progress indicator
        if (i + 1) % 1000 == 0:
            print(f"✅ Processed {i + 1:,} pairs...")
    
    print(f"✅ Conversion complete!")
    print(f"📊 Converted pairs: {len(conversations):,}")
    print(f"⏭️  Skipped pairs: {skipped_count:,}")
    
    return conversations

def save_conversation_data(conversations, filename):
    """Save conversations to JSON file."""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(conversations, f, ensure_ascii=False, indent=2)
        print(f"💾 Saved to: {filename}")
        
        # File size info
        file_size = Path(filename).stat().st_size / (1024 * 1024)
        print(f"📦 File size: {file_size:.1f} MB")
        
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")

def preview_conversations(conversations, num_examples=3):
    """Preview a few conversation examples."""
    print(f"\n📋 PREVIEW OF CONVERSATION FORMAT:")
    print("=" * 60)
    
    for i, conv in enumerate(conversations[:num_examples]):
        print(f"\n🔍 Example {i + 1}:")
        print("-" * 30)
        
        human_msg = conv['conversations'][0]['value']
        gpt_msg = conv['conversations'][1]['value']
        
        # Truncate long messages for preview
        human_preview = human_msg[:200] + "..." if len(human_msg) > 200 else human_msg
        gpt_preview = gpt_msg[:200] + "..." if len(gpt_msg) > 200 else gpt_msg
        
        print(f"Human: {human_preview}")
        print(f"GPT: {gpt_preview}")
        
        # Show metadata if present
        if 'metadata' in conv:
            metadata = conv['metadata']
            print(f"Metadata: Survey={metadata.get('survey_title', 'N/A')}, "
                  f"Q={metadata.get('question_number', 'N/A')}, "
                  f"Sim={metadata.get('similarity_score', 0):.3f}")

def main():
    """Main conversion function."""
    
    print("🎯 CONVERTING TRAINING DATA TO CONVERSATION FORMAT")
    print("=" * 60)
    
    # Load existing training data
    input_file = 'question_training_data.json'
    output_file = 'conversation_training_data.json'
    
    if not Path(input_file).exists():
        print(f"❌ Input file not found: {input_file}")
        return
    
    print(f"📂 Loading training data from: {input_file}")
    training_data = load_training_data(input_file)
    
    if not training_data:
        print("❌ No training data loaded!")
        return
    
    # Convert to conversation format
    print(f"🔄 Converting {len(training_data):,} training pairs...")
    
    # You can adjust the minimum similarity threshold here
    min_similarity = 0.7  # Only include pairs with 70%+ similarity
    conversations = convert_to_conversation_format(training_data, min_similarity)
    
    if not conversations:
        print("❌ No conversations created!")
        return
    
    # Save converted data
    save_conversation_data(conversations, output_file)
    
    # Preview examples
    preview_conversations(conversations)
    
    print(f"\n🎉 CONVERSION COMPLETE!")
    print(f"✅ Input: {len(training_data):,} question pairs")
    print(f"✅ Output: {len(conversations):,} conversation pairs")
    print(f"📁 Saved to: {output_file}")
    
    # Quality summary
    if training_data:
        similarities = [item.get('similarity_score', 0) for item in training_data]
        avg_similarity = sum(similarities) / len(similarities)
        high_quality = len([s for s in similarities if s >= 0.9])
        
        print(f"\n📊 QUALITY SUMMARY:")
        print(f"⭐ Average similarity: {avg_similarity:.3f}")
        print(f"🏆 High quality (≥90%): {high_quality:,} ({high_quality/len(training_data)*100:.1f}%)")
        print(f"✅ Minimum similarity used: {min_similarity}")
    
    print(f"\n🚀 Ready for LLM fine-tuning!")

if __name__ == '__main__':
    main()





