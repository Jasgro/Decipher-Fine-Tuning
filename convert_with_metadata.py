#!/usr/bin/env python3
"""
Convert Training Data to Conversation Format with Metadata

Creates both a clean version (for training) and a version with metadata (for tracking).
"""

import json
from pathlib import Path

def create_conversation_formats():
    """Create both clean and metadata versions."""
    
    print("🔄 Loading training data...")
    with open('question_training_data.json', 'r', encoding='utf-8') as f:
        training_data = json.load(f)
    
    clean_conversations = []
    metadata_conversations = []
    
    print(f"🔄 Processing {len(training_data):,} pairs...")
    
    for item in training_data:
        natural_language = item.get('natural_language', '').strip()
        xml_code = item.get('xml_code', '').strip()
        
        if not natural_language or not xml_code:
            continue
            
        # Clean version (for training)
        clean_conv = {
            'conversations': [
                {'from': 'human', 'value': natural_language},
                {'from': 'gpt', 'value': xml_code}
            ]
        }
        clean_conversations.append(clean_conv)
        
        # Metadata version (for tracking)
        metadata_conv = {
            'conversations': [
                {'from': 'human', 'value': natural_language},
                {'from': 'gpt', 'value': xml_code}
            ],
            'metadata': {
                'survey_title': item.get('survey_title', 'Unknown'),
                'question_number': item.get('question_number', 'Unknown'),
                'similarity_score': item.get('similarity_score', 0),
                'survey_id': item.get('survey_id', 'Unknown')
            }
        }
        metadata_conversations.append(metadata_conv)
    
    # Save both versions
    print("💾 Saving clean version (for training)...")
    with open('conversation_training_clean.json', 'w', encoding='utf-8') as f:
        json.dump(clean_conversations, f, ensure_ascii=False, indent=2)
    
    print("💾 Saving metadata version (for tracking)...")
    with open('conversation_training_with_metadata.json', 'w', encoding='utf-8') as f:
        json.dump(metadata_conversations, f, ensure_ascii=False, indent=2)
    
    # File sizes
    clean_size = Path('conversation_training_clean.json').stat().st_size / (1024 * 1024)
    metadata_size = Path('conversation_training_with_metadata.json').stat().st_size / (1024 * 1024)
    
    print(f"✅ Clean version: {len(clean_conversations):,} conversations ({clean_size:.1f} MB)")
    print(f"✅ Metadata version: {len(metadata_conversations):,} conversations ({metadata_size:.1f} MB)")

if __name__ == '__main__':
    create_conversation_formats()


