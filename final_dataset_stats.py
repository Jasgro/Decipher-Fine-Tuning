#!/usr/bin/env python3
"""
Final Dataset Statistics

Generate comprehensive statistics on the final training dataset.
"""

import json
import sys
from collections import defaultdict, Counter

def load_json_safely(filename):
    """Load JSON file safely with proper encoding."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filename}: {e}")
        return []

def analyze_dataset():
    """Analyze the complete training dataset."""
    
    print("🔄 Loading training data files...")
    
    # Load training data
    training_data = load_json_safely('question_training_data.json')
    debug_data = load_json_safely('question_debug.json')
    
    print(f"✅ Loaded {len(training_data):,} training pairs")
    print(f"✅ Loaded {len(debug_data):,} debug entries")
    
    print("\n" + "="*60)
    print("🎯 FINAL TRAINING DATASET STATISTICS")
    print("="*60)
    
    # Basic statistics
    total_pairs = len(training_data)
    unique_surveys = len(set([item.get('survey_title', 'Unknown') for item in training_data]))
    
    print(f"📊 Total Question Pairs: {total_pairs:,}")
    print(f"📁 Surveys Processed: {unique_surveys:,}")
    
    # Similarity score analysis
    similarity_scores = [item.get('similarity_score', 0) for item in training_data]
    avg_similarity = sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0
    
    print(f"⭐ Average Similarity Score: {avg_similarity:.3f}")
    
    # Quality breakdown
    print(f"\n📈 MATCH QUALITY BREAKDOWN:")
    high_quality = len([s for s in similarity_scores if s >= 0.9])
    good_quality = len([s for s in similarity_scores if 0.8 <= s < 0.9])
    fair_quality = len([s for s in similarity_scores if 0.7 <= s < 0.8])
    low_quality = len([s for s in similarity_scores if s < 0.7])
    
    print(f"🏆 High Quality (≥90%): {high_quality:,} ({high_quality/total_pairs*100:.1f}%)")
    print(f"👍 Good Quality (80-89%): {good_quality:,} ({good_quality/total_pairs*100:.1f}%)")
    print(f"👌 Fair Quality (70-79%): {fair_quality:,} ({fair_quality/total_pairs*100:.1f}%)")
    print(f"⚠️  Low Quality (<70%): {low_quality:,} ({low_quality/total_pairs*100:.1f}%)")
    
    # Survey distribution
    survey_counts = Counter([item.get('survey_title', 'Unknown') for item in training_data])
    print(f"\n📋 SURVEY DISTRIBUTION:")
    print(f"📊 Average questions per survey: {total_pairs/unique_surveys:.1f}")
    print(f"🔝 Most questions in one survey: {max(survey_counts.values())}")
    print(f"🔽 Fewest questions in one survey: {min(survey_counts.values())}")
    
    # Top surveys by question count
    print(f"\n🏆 TOP 10 SURVEYS BY QUESTION COUNT:")
    for i, (survey, count) in enumerate(survey_counts.most_common(10), 1):
        print(f"{i:2d}. {survey}: {count} questions")
    
    # Debug data analysis
    if debug_data:
        print(f"\n🔍 DEBUG DATA ANALYSIS:")
        print(f"📝 Debug entries: {len(debug_data):,}")
        
        # Count unmatched questions
        unmatched_word = 0
        unmatched_xml = 0
        
        for entry in debug_data:
            if 'unmatched_word_questions' in entry:
                unmatched_word += len(entry['unmatched_word_questions'])
            if 'unmatched_xml_questions' in entry:
                unmatched_xml += len(entry['unmatched_xml_questions'])
        
        print(f"❌ Unmatched Word questions: {unmatched_word:,}")
        print(f"❌ Unmatched XML questions: {unmatched_xml:,}")
        
        total_questions = total_pairs + unmatched_word + unmatched_xml
        match_rate = (total_pairs / total_questions * 100) if total_questions > 0 else 0
        print(f"📊 Overall match rate: {match_rate:.1f}%")
    
    print(f"\n💾 FILE SIZES:")
    import os
    training_size = os.path.getsize('question_training_data.json') / (1024*1024)
    debug_size = os.path.getsize('question_debug.json') / (1024*1024)
    
    print(f"📄 Training data: {training_size:.1f} MB")
    print(f"🐛 Debug data: {debug_size:.1f} MB")
    print(f"📦 Total dataset: {training_size + debug_size:.1f} MB")
    
    print("\n" + "="*60)
    print("✅ ANALYSIS COMPLETE!")
    print("="*60)

if __name__ == '__main__':
    analyze_dataset()








