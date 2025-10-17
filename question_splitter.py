#!/usr/bin/env python3
"""
Question-Level Training Data Generator

Splits survey questionnaires and XML into individual question pairs
for more granular LLM training data.
"""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from fuzzywuzzy import fuzz
from lxml import etree


class WordQuestionExtractor:
    """Extracts individual questions from Word document text."""
    
    def __init__(self, content_limit_chars: int = 2000):
        self.content_limit_chars = content_limit_chars
        
        # Flexible question number patterns
        self.question_patterns = [
            r'^\s*[qsQS]\d+[.\)]*\s*(.+)',           # q1. s2) Q3 
            r'^\s*\[?[qsQS]\d+\]?\s*(.+)',           # [q1] [s2] 
            r'^\s*\(?[qsQS]\d+\)?\s*(.+)',           # (q1) (s2)
            r'^\s*\d+[.\)]\s*(.+)',                  # 1. 2)
            r'^\s*[A-Z]\d+[.\)]*\s*(.+)',            # A1. B2)
            r'^\s*Question\s+\d+[:\.]?\s*(.+)',      # Question 1: Question 2.
            r'^\s*[A-Z]+\d*[.\)]\s*(.+)',            # A. B1. C2)
            r'^\s*\d+\.\d+\s*(.+)',                  # 1.1 2.3
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.question_patterns]
    
    def is_question_start(self, paragraph: str) -> bool:
        """Check if paragraph starts a new question."""
        paragraph = paragraph.strip()
        if not paragraph:
            return False
        
        for pattern in self.compiled_patterns:
            if pattern.match(paragraph):
                return True
        return False
    
    def extract_question_number(self, paragraph: str) -> str:
        """Extract the question number/identifier from paragraph."""
        paragraph = paragraph.strip()
        
        for pattern in self.compiled_patterns:
            match = pattern.match(paragraph)
            if match:
                # Extract the part before the actual question text
                full_match = match.group(0)
                question_text = match.group(1)
                question_number = full_match.replace(question_text, '').strip()
                return question_number
        
        return ""
    
    def extract_question_text(self, paragraph: str) -> str:
        """Extract clean question text without number/formatting."""
        paragraph = paragraph.strip()
        
        for pattern in self.compiled_patterns:
            match = pattern.match(paragraph)
            if match:
                return match.group(1).strip()
        
        return paragraph
    
    def extract_questions(self, docx_text: str) -> List[Dict]:
        """Extract all questions from Word document text."""
        print("📄 Extracting questions from Word document...")
        
        paragraphs = [p.strip() for p in docx_text.split('\n') if p.strip()]
        print(f"  📊 Processing {len(paragraphs)} paragraphs")
        
        questions = []
        current_question = None
        current_content = []
        current_number = ""
        
        # Debug: Show first few paragraphs to understand structure
        print("  🔍 First 5 paragraphs:")
        for i, para in enumerate(paragraphs[:5]):
            print(f"    {i+1}: {para[:100]}...")
        
        for i, para in enumerate(paragraphs):
            is_question = self.is_question_start(para)
            
            if is_question:
                # Save previous question if exists
                if current_question:
                    content = '\n'.join(current_content)
                    questions.append({
                        'number': current_number,
                        'text': current_question,
                        'full_content': content,
                        'word_index': len(questions)
                    })
                
                # Start new question
                current_number = self.extract_question_number(para)
                current_question = self.extract_question_text(para)
                current_content = [para]  # Include the question line itself
                
                print(f"  📝 Found question: {current_number} - {current_question[:60]}...")
                
            elif current_question and para:
                # Add content to current question
                current_content.append(para)
                
                # Check content limit
                total_chars = sum(len(line) for line in current_content)
                if total_chars > self.content_limit_chars:
                    print(f"    ⚠️  Content limit reached for question {current_number}")
                    break
            else:
                # Debug: Show paragraphs that don't match any pattern
                if i < 20:  # Only show first 20 to avoid spam
                    print(f"    ❓ Para {i+1} not recognized as question: {para[:80]}...")
        
        # Don't forget the last question
        if current_question:
            content = '\n'.join(current_content)
            questions.append({
                'number': current_number,
                'text': current_question,
                'full_content': content,
                'word_index': len(questions)
            })
        
        print(f"✅ Extracted {len(questions)} questions from Word document")
        return questions


class XMLQuestionExtractor:
    """Extracts individual questions from survey XML."""
    
    def __init__(self):
        pass
    
    def extract_questions(self, xml_content: str) -> List[Dict]:
        """Extract all questions from XML content."""
        print("🔧 Extracting questions from XML...")
        
        try:
            # Parse XML
            root = etree.fromstring(xml_content.encode('utf-8'))
            questions = []
            seen_question_ids = set()
            
            # Find all title elements with IDs directly (simpler approach)
            title_elements = root.xpath('//title[@id]')
            
            print(f"  📊 Found {len(title_elements)} title elements with IDs")
            
            for title in title_elements:
                question_id = title.get('id')
                question_text = title.text or ""
                
                # Skip duplicates and empty questions
                if question_id in seen_question_ids or not question_text.strip():
                    continue
                
                seen_question_ids.add(question_id)
                
                # Find the parent element that contains this question
                parent = title.getparent()
                while parent is not None and parent.tag not in ['suspend', 'page', 'question', 'exec']:
                    parent = parent.getparent()
                
                if parent is not None:
                    full_section = etree.tostring(parent, encoding='unicode', pretty_print=True)
                else:
                    # Fallback to a reasonable context around the title
                    context_parent = title.getparent()
                    if context_parent is not None:
                        full_section = etree.tostring(context_parent, encoding='unicode', pretty_print=True)
                    else:
                        full_section = etree.tostring(title, encoding='unicode', pretty_print=True)
                
                questions.append({
                    'id': question_id,
                    'text': question_text.strip(),
                    'full_section': full_section,
                    'xml_index': len(questions)
                })
                
                print(f"  🔧 Found XML question: {question_id} - {question_text.strip()[:60]}...")
            
            print(f"✅ Extracted {len(questions)} unique questions from XML")
            return questions
            
        except Exception as e:
            print(f"❌ Error parsing XML: {e}")
            return []
    
    def extract_section_content(self, suspend_element) -> etree._Element:
        """Extract content section associated with a suspend element."""
        # This is a simplified approach - in practice, you might need
        # more sophisticated logic to determine section boundaries
        
        # For now, return the parent element containing the suspend
        parent = suspend_element.getparent()
        if parent is not None:
            return parent
        else:
            return suspend_element


class QuestionMatcher:
    """Matches Word questions with XML questions using fuzzy matching."""
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for better matching."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove common survey artifacts
        artifacts = [
            r'\(please select one\)',
            r'\(select all that apply\)',
            r'\(check all that apply\)',
            r'\(single response\)',
            r'\(multiple response\)',
        ]
        
        for artifact in artifacts:
            text = re.sub(artifact, '', text, flags=re.IGNORECASE)
        
        # Remove excessive punctuation
        text = re.sub(r'[^\w\s\?]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text.lower()
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts."""
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)
        
        # Use multiple similarity metrics
        ratio = fuzz.ratio(norm1, norm2) / 100.0
        partial_ratio = fuzz.partial_ratio(norm1, norm2) / 100.0
        token_sort_ratio = fuzz.token_sort_ratio(norm1, norm2) / 100.0
        
        # Weighted average (favor token sort for word order independence)
        similarity = (ratio * 0.3 + partial_ratio * 0.3 + token_sort_ratio * 0.4)
        
        return similarity
    
    def find_best_match(self, word_question: Dict, xml_questions: List[Dict]) -> Optional[Tuple[Dict, float]]:
        """Find the best XML match for a Word question."""
        best_match = None
        best_score = 0.0
        
        word_text = word_question['text']
        
        for xml_question in xml_questions:
            xml_text = xml_question['text']
            score = self.calculate_similarity(word_text, xml_text)
            
            if score > best_score:
                best_score = score
                best_match = xml_question
        
        if best_score >= self.similarity_threshold:
            return best_match, best_score
        else:
            return None
    
    def match_questions(self, word_questions: List[Dict], xml_questions: List[Dict]) -> Dict:
        """Match Word questions with XML questions."""
        print(f"🔗 Matching {len(word_questions)} Word questions with {len(xml_questions)} XML questions...")
        
        matches = []
        unmatched_word = []
        unmatched_xml = xml_questions.copy()
        
        for word_q in word_questions:
            print(f"  🔍 Matching: {word_q['number']} - {word_q['text'][:50]}...")
            
            result = self.find_best_match(word_q, unmatched_xml)
            
            if result:
                xml_q, score = result
                matches.append({
                    'word_question': word_q,
                    'xml_question': xml_q,
                    'similarity_score': score
                })
                unmatched_xml.remove(xml_q)
                print(f"    ✅ Matched with XML {xml_q['id']} (similarity: {score:.2f})")
            else:
                unmatched_word.append(word_q)
                print(f"    ❌ No match found")
        
        print(f"✅ Matching complete: {len(matches)} matches, {len(unmatched_word)} unmatched Word, {len(unmatched_xml)} unmatched XML")
        
        return {
            'matches': matches,
            'unmatched_word': unmatched_word,
            'unmatched_xml': unmatched_xml
        }


class QuestionSplitter:
    """Main class for splitting surveys into question-level training data."""
    
    def __init__(self, similarity_threshold: float = 0.8, content_limit: int = 2000):
        self.word_extractor = WordQuestionExtractor(content_limit)
        self.xml_extractor = XMLQuestionExtractor()
        self.matcher = QuestionMatcher(similarity_threshold)
    
    def process_survey_pair(self, survey_title: str, word_text: str, xml_content: str) -> Dict:
        """Process a single survey pair into question-level data."""
        print(f"\n{'='*60}")
        print(f"PROCESSING: {survey_title}")
        print(f"{'='*60}")
        
        # Extract questions from both sources
        word_questions = self.word_extractor.extract_questions(word_text)
        xml_questions = self.xml_extractor.extract_questions(xml_content)
        
        if not word_questions:
            print("❌ No questions found in Word document")
            return {'survey_title': survey_title, 'matches': [], 'unmatched_word': [], 'unmatched_xml': xml_questions}
        
        if not xml_questions:
            print("❌ No questions found in XML")
            return {'survey_title': survey_title, 'matches': [], 'unmatched_word': word_questions, 'unmatched_xml': []}
        
        # Match questions
        results = self.matcher.match_questions(word_questions, xml_questions)
        results['survey_title'] = survey_title
        
        return results
    
    def create_training_pairs(self, survey_title: str, matches: List[Dict]) -> List[Dict]:
        """Convert matches into training pairs."""
        training_pairs = []
        
        for match in matches:
            word_q = match['word_question']
            xml_q = match['xml_question']
            
            training_pair = {
                'survey_title': survey_title,
                'question_number': word_q['number'],
                'natural_language': word_q['full_content'],
                'xml_code': xml_q['full_section'],
                'similarity_score': match['similarity_score'],
                'metadata': {
                    'word_index': word_q['word_index'],
                    'xml_index': xml_q['xml_index'],
                    'xml_id': xml_q['id']
                }
            }
            
            training_pairs.append(training_pair)
        
        return training_pairs


def main():
    """Test the question splitter with existing training data."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Split survey training data into question-level pairs")
    parser.add_argument('--input', default='./training_data.json', help='Input training data file')
    parser.add_argument('--output', default='./question_training_data.json', help='Output question-level training data')
    parser.add_argument('--debug-output', default='./question_debug.json', help='Debug output with unmatched questions')
    parser.add_argument('--threshold', type=float, default=0.8, help='Similarity threshold for matching')
    
    args = parser.parse_args()
    
    # Load existing training data
    try:
        with open(args.input, 'r', encoding='utf-8') as f:
            training_data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading training data: {e}")
        return
    
    splitter = QuestionSplitter(similarity_threshold=args.threshold)
    
    all_training_pairs = []
    debug_data = []
    
    # Process each survey
    for survey_data in training_data:
        survey_title = survey_data['survey_title']
        word_text = survey_data['natural_language']
        xml_content = survey_data['xml_code']
        
        # Process the survey
        results = splitter.process_survey_pair(survey_title, word_text, xml_content)
        
        # Create training pairs from matches
        if results['matches']:
            pairs = splitter.create_training_pairs(survey_title, results['matches'])
            all_training_pairs.extend(pairs)
        
        # Save debug information
        debug_data.append(results)
    
    # Save results
    print(f"\n{'='*60}")
    print(f"FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Total question pairs created: {len(all_training_pairs)}")
    
    if all_training_pairs:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(all_training_pairs, f, indent=2, ensure_ascii=False)
        print(f"✅ Saved training pairs to: {args.output}")
    
    # Save debug data
    with open(args.debug_output, 'w', encoding='utf-8') as f:
        json.dump(debug_data, f, indent=2, ensure_ascii=False)
    print(f"🔍 Saved debug data to: {args.debug_output}")
    
    # Print summary stats
    total_matches = sum(len(survey['matches']) for survey in debug_data)
    total_unmatched_word = sum(len(survey['unmatched_word']) for survey in debug_data)
    total_unmatched_xml = sum(len(survey['unmatched_xml']) for survey in debug_data)
    
    print(f"📊 Summary:")
    print(f"   Matched questions: {total_matches}")
    print(f"   Unmatched Word questions: {total_unmatched_word}")
    print(f"   Unmatched XML questions: {total_unmatched_xml}")


if __name__ == '__main__':
    main()
