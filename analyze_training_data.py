#!/usr/bin/env python3
"""
Training Data Analysis Script

Analyzes the question-level training data and generates descriptive statistics
with an HTML report showing key findings.
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median, stdev
from typing import Dict, List, Any
import html


class TrainingDataAnalyzer:
    """Analyzes question-level training data and generates reports."""
    
    def __init__(self, training_data_file: str = "./question_training_data.json",
                 debug_data_file: str = "./question_debug.json"):
        self.training_data_file = Path(training_data_file)
        self.debug_data_file = Path(debug_data_file)
        self.training_data = []
        self.debug_data = []
        
    def load_data(self):
        """Load training and debug data."""
        print("📊 Loading training data...")
        
        # Load training data
        if self.training_data_file.exists():
            with open(self.training_data_file, 'r', encoding='utf-8') as f:
                self.training_data = json.load(f)
            print(f"✅ Loaded {len(self.training_data)} training pairs")
        else:
            print("❌ Training data file not found")
            
        # Load debug data
        if self.debug_data_file.exists():
            with open(self.debug_data_file, 'r', encoding='utf-8') as f:
                self.debug_data = json.load(f)
            print(f"✅ Loaded debug data for {len(self.debug_data)} surveys")
        else:
            print("⚠️ Debug data file not found")
    
    def analyze_basic_stats(self) -> Dict[str, Any]:
        """Analyze basic statistics about the training data."""
        print("📈 Analyzing basic statistics...")
        
        if not self.training_data:
            return {}
            
        # Survey-level stats
        surveys = defaultdict(list)
        for item in self.training_data:
            surveys[item['survey_title']].append(item)
        
        # Question lengths
        natural_lengths = [len(item['natural_language']) for item in self.training_data]
        xml_lengths = [len(item['xml_code']) for item in self.training_data]
        
        # Similarity scores
        similarity_scores = [item['similarity_score'] for item in self.training_data]
        
        # Question number patterns
        question_numbers = [item['question_number'] for item in self.training_data]
        
        stats = {
            'total_pairs': len(self.training_data),
            'total_surveys': len(surveys),
            'survey_breakdown': {survey: len(questions) for survey, questions in surveys.items()},
            'natural_language_stats': {
                'min_length': min(natural_lengths),
                'max_length': max(natural_lengths),
                'mean_length': mean(natural_lengths),
                'median_length': median(natural_lengths),
                'std_length': stdev(natural_lengths) if len(natural_lengths) > 1 else 0
            },
            'xml_code_stats': {
                'min_length': min(xml_lengths),
                'max_length': max(xml_lengths),
                'mean_length': mean(xml_lengths),
                'median_length': median(xml_lengths),
                'std_length': stdev(xml_lengths) if len(xml_lengths) > 1 else 0
            },
            'similarity_stats': {
                'min_score': min(similarity_scores),
                'max_score': max(similarity_scores),
                'mean_score': mean(similarity_scores),
                'median_score': median(similarity_scores),
                'std_score': stdev(similarity_scores) if len(similarity_scores) > 1 else 0
            },
            'question_number_patterns': self.analyze_question_patterns(question_numbers)
        }
        
        return stats
    
    def analyze_question_patterns(self, question_numbers: List[str]) -> Dict[str, Any]:
        """Analyze patterns in question numbering."""
        patterns = {
            'starts_with_q': 0,
            'starts_with_s': 0,
            'starts_with_number': 0,
            'has_brackets': 0,
            'has_parentheses': 0,
            'has_period': 0,
            'empty_or_dash': 0
        }
        
        for qnum in question_numbers:
            qnum_lower = qnum.lower().strip()
            
            if qnum_lower.startswith('q'):
                patterns['starts_with_q'] += 1
            elif qnum_lower.startswith('s'):
                patterns['starts_with_s'] += 1
            elif re.match(r'^\d', qnum_lower):
                patterns['starts_with_number'] += 1
                
            if '[' in qnum or ']' in qnum:
                patterns['has_brackets'] += 1
            if '(' in qnum or ')' in qnum:
                patterns['has_parentheses'] += 1
            if '.' in qnum:
                patterns['has_period'] += 1
            if qnum.strip() in ['', '-'] or qnum.strip().endswith('-'):
                patterns['empty_or_dash'] += 1
        
        return patterns
    
    def analyze_matching_performance(self) -> Dict[str, Any]:
        """Analyze matching performance from debug data."""
        print("🎯 Analyzing matching performance...")
        
        if not self.debug_data:
            return {}
        
        performance = {
            'total_surveys_processed': len(self.debug_data),
            'surveys': {}
        }
        
        total_word_questions = 0
        total_xml_questions = 0
        total_matches = 0
        total_unmatched_word = 0
        total_unmatched_xml = 0
        
        for survey in self.debug_data:
            survey_title = survey['survey_title']
            matches = len(survey['matches'])
            unmatched_word = len(survey['unmatched_word'])
            unmatched_xml = len(survey['unmatched_xml'])
            
            word_questions = matches + unmatched_word
            xml_questions = matches + unmatched_xml
            
            match_rate = (matches / word_questions * 100) if word_questions > 0 else 0
            
            performance['surveys'][survey_title] = {
                'word_questions_found': word_questions,
                'xml_questions_found': xml_questions,
                'matches': matches,
                'unmatched_word': unmatched_word,
                'unmatched_xml': unmatched_xml,
                'match_rate_percent': round(match_rate, 1)
            }
            
            total_word_questions += word_questions
            total_xml_questions += xml_questions
            total_matches += matches
            total_unmatched_word += unmatched_word
            total_unmatched_xml += unmatched_xml
        
        performance['totals'] = {
            'word_questions_found': total_word_questions,
            'xml_questions_found': total_xml_questions,
            'matches': total_matches,
            'unmatched_word': total_unmatched_word,
            'unmatched_xml': total_unmatched_xml,
            'overall_match_rate_percent': round((total_matches / total_word_questions * 100) if total_word_questions > 0 else 0, 1)
        }
        
        return performance
    
    def analyze_content_patterns(self) -> Dict[str, Any]:
        """Analyze content patterns in natural language and XML."""
        print("🔍 Analyzing content patterns...")
        
        if not self.training_data:
            return {}
        
        # Common words in natural language
        all_natural_text = ' '.join(item['natural_language'].lower() for item in self.training_data)
        natural_words = re.findall(r'\b\w+\b', all_natural_text)
        common_natural_words = Counter(natural_words).most_common(20)
        
        # Common XML elements
        all_xml_text = ' '.join(item['xml_code'] for item in self.training_data)
        xml_elements = re.findall(r'<(\w+)', all_xml_text)
        common_xml_elements = Counter(xml_elements).most_common(20)
        
        # Question types (based on question text)
        question_types = {
            'multiple_choice': 0,
            'rating_scale': 0,
            'open_text': 0,
            'yes_no': 0,
            'ranking': 0
        }
        
        for item in self.training_data:
            text = item['natural_language'].lower()
            
            if any(phrase in text for phrase in ['select all', 'check all', 'multiple', 'following']):
                question_types['multiple_choice'] += 1
            elif any(phrase in text for phrase in ['rate', 'scale', '1-10', '0-10', 'satisfaction']):
                question_types['rating_scale'] += 1
            elif any(phrase in text for phrase in ['yes', 'no']) and 'yes/no' in text:
                question_types['yes_no'] += 1
            elif any(phrase in text for phrase in ['rank', 'order', 'priority']):
                question_types['ranking'] += 1
            else:
                question_types['open_text'] += 1
        
        return {
            'common_natural_words': common_natural_words,
            'common_xml_elements': common_xml_elements,
            'question_types': question_types
        }
    
    def generate_html_report(self, stats: Dict[str, Any], performance: Dict[str, Any], 
                           content: Dict[str, Any], output_file: str = "./training_data_analysis.html"):
        """Generate comprehensive HTML report."""
        print(f"📝 Generating HTML report: {output_file}")
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Training Data Analysis Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            text-align: center;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            border-left: 4px solid #3498db;
            padding-left: 15px;
            margin-top: 30px;
        }}
        h3 {{
            color: #7f8c8d;
            margin-top: 25px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            display: block;
        }}
        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background-color: white;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #3498db;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .metric:last-child {{
            border-bottom: none;
        }}
        .metric-label {{
            font-weight: bold;
            color: #555;
        }}
        .metric-value {{
            color: #2c3e50;
        }}
        .highlight {{
            background-color: #fff3cd;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #ffc107;
            margin: 15px 0;
        }}
        .success {{
            background-color: #d4edda;
            border-left-color: #28a745;
        }}
        .warning {{
            background-color: #fff3cd;
            border-left-color: #ffc107;
        }}
        .chart-placeholder {{
            background-color: #f8f9fa;
            border: 2px dashed #dee2e6;
            border-radius: 5px;
            padding: 40px;
            text-align: center;
            color: #6c757d;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🎯 Training Data Analysis Report</h1>
        <p style="text-align: center; color: #7f8c8d; font-style: italic;">
            Generated from question-level survey training data
        </p>
        
        {self._generate_overview_section(stats)}
        {self._generate_performance_section(performance)}
        {self._generate_content_analysis_section(content)}
        {self._generate_detailed_stats_section(stats)}
        {self._generate_recommendations_section(stats, performance)}
        
        <div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; text-align: center; color: #7f8c8d;">
            <p>Report generated on {self._get_timestamp()}</p>
        </div>
    </div>
</body>
</html>
        """
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ HTML report saved to: {Path(output_file).absolute()}")
    
    def _generate_overview_section(self, stats: Dict[str, Any]) -> str:
        """Generate overview section of the report."""
        if not stats:
            return "<h2>📊 Overview</h2><p>No training data available for analysis.</p>"
        
        return f"""
        <h2>📊 Overview</h2>
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-value">{stats['total_pairs']}</span>
                <span class="stat-label">Total Question Pairs</span>
            </div>
            <div class="stat-card">
                <span class="stat-value">{stats['total_surveys']}</span>
                <span class="stat-label">Surveys Processed</span>
            </div>
            <div class="stat-card">
                <span class="stat-value">{stats['similarity_stats']['mean_score']:.2f}</span>
                <span class="stat-label">Average Similarity Score</span>
            </div>
            <div class="stat-card">
                <span class="stat-value">{int(stats['natural_language_stats']['mean_length'])}</span>
                <span class="stat-label">Avg. Question Length (chars)</span>
            </div>
        </div>
        
        <h3>Survey Breakdown</h3>
        <table>
            <tr><th>Survey</th><th>Questions Matched</th><th>Percentage</th></tr>
            {self._generate_survey_breakdown_rows(stats['survey_breakdown'], stats['total_pairs'])}
        </table>
        """
    
    def _generate_survey_breakdown_rows(self, breakdown: Dict[str, int], total: int) -> str:
        """Generate table rows for survey breakdown."""
        rows = []
        for survey, count in breakdown.items():
            percentage = (count / total * 100) if total > 0 else 0
            # Truncate long survey names for display
            display_name = survey if len(survey) <= 40 else survey[:37] + "..."
            rows.append(f"<tr><td>{html.escape(display_name)}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>")
        return '\n'.join(rows)
    
    def _generate_performance_section(self, performance: Dict[str, Any]) -> str:
        """Generate performance analysis section."""
        if not performance:
            return "<h2>🎯 Matching Performance</h2><p>No performance data available.</p>"
        
        totals = performance['totals']
        
        return f"""
        <h2>🎯 Matching Performance</h2>
        
        <div class="highlight success">
            <strong>Overall Match Rate: {totals['overall_match_rate_percent']}%</strong><br>
            Successfully matched {totals['matches']} out of {totals['word_questions_found']} questions found in Word documents.
        </div>
        
        <h3>Performance by Survey</h3>
        <table>
            <tr>
                <th>Survey</th>
                <th>Word Questions</th>
                <th>XML Questions</th>
                <th>Matches</th>
                <th>Match Rate</th>
            </tr>
            {self._generate_performance_rows(performance['surveys'])}
        </table>
        
        <h3>Summary Statistics</h3>
        <div class="metric">
            <span class="metric-label">Total Word Questions Found:</span>
            <span class="metric-value">{totals['word_questions_found']}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Total XML Questions Found:</span>
            <span class="metric-value">{totals['xml_questions_found']}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Successful Matches:</span>
            <span class="metric-value">{totals['matches']}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Unmatched Word Questions:</span>
            <span class="metric-value">{totals['unmatched_word']}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Unmatched XML Questions:</span>
            <span class="metric-value">{totals['unmatched_xml']}</span>
        </div>
        """
    
    def _generate_performance_rows(self, surveys: Dict[str, Dict]) -> str:
        """Generate performance table rows."""
        rows = []
        for survey, data in surveys.items():
            display_name = survey if len(survey) <= 30 else survey[:27] + "..."
            rows.append(f"""
            <tr>
                <td>{html.escape(display_name)}</td>
                <td>{data['word_questions_found']}</td>
                <td>{data['xml_questions_found']}</td>
                <td>{data['matches']}</td>
                <td>{data['match_rate_percent']}%</td>
            </tr>
            """)
        return '\n'.join(rows)
    
    def _generate_content_analysis_section(self, content: Dict[str, Any]) -> str:
        """Generate content analysis section."""
        if not content:
            return "<h2>🔍 Content Analysis</h2><p>No content data available.</p>"
        
        return f"""
        <h2>🔍 Content Analysis</h2>
        
        <h3>Question Types Distribution</h3>
        <table>
            <tr><th>Question Type</th><th>Count</th><th>Percentage</th></tr>
            {self._generate_question_type_rows(content['question_types'])}
        </table>
        
        <h3>Most Common Words in Questions</h3>
        <table>
            <tr><th>Word</th><th>Frequency</th></tr>
            {self._generate_word_frequency_rows(content['common_natural_words'][:10])}
        </table>
        
        <h3>Most Common XML Elements</h3>
        <table>
            <tr><th>XML Element</th><th>Frequency</th></tr>
            {self._generate_word_frequency_rows(content['common_xml_elements'][:10])}
        </table>
        """
    
    def _generate_question_type_rows(self, question_types: Dict[str, int]) -> str:
        """Generate question type distribution rows."""
        total = sum(question_types.values())
        rows = []
        for qtype, count in question_types.items():
            percentage = (count / total * 100) if total > 0 else 0
            display_type = qtype.replace('_', ' ').title()
            rows.append(f"<tr><td>{display_type}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>")
        return '\n'.join(rows)
    
    def _generate_word_frequency_rows(self, word_freq: List[tuple]) -> str:
        """Generate word frequency table rows."""
        rows = []
        for word, freq in word_freq:
            rows.append(f"<tr><td>{html.escape(word)}</td><td>{freq}</td></tr>")
        return '\n'.join(rows)
    
    def _generate_detailed_stats_section(self, stats: Dict[str, Any]) -> str:
        """Generate detailed statistics section."""
        if not stats:
            return ""
        
        nl_stats = stats['natural_language_stats']
        xml_stats = stats['xml_code_stats']
        sim_stats = stats['similarity_stats']
        patterns = stats['question_number_patterns']
        
        return f"""
        <h2>📈 Detailed Statistics</h2>
        
        <h3>Natural Language Text Statistics</h3>
        <div class="metric">
            <span class="metric-label">Average Length:</span>
            <span class="metric-value">{nl_stats['mean_length']:.0f} characters</span>
        </div>
        <div class="metric">
            <span class="metric-label">Median Length:</span>
            <span class="metric-value">{nl_stats['median_length']:.0f} characters</span>
        </div>
        <div class="metric">
            <span class="metric-label">Range:</span>
            <span class="metric-value">{nl_stats['min_length']} - {nl_stats['max_length']} characters</span>
        </div>
        <div class="metric">
            <span class="metric-label">Standard Deviation:</span>
            <span class="metric-value">{nl_stats['std_length']:.0f} characters</span>
        </div>
        
        <h3>XML Code Statistics</h3>
        <div class="metric">
            <span class="metric-label">Average Length:</span>
            <span class="metric-value">{xml_stats['mean_length']:.0f} characters</span>
        </div>
        <div class="metric">
            <span class="metric-label">Median Length:</span>
            <span class="metric-value">{xml_stats['median_length']:.0f} characters</span>
        </div>
        <div class="metric">
            <span class="metric-label">Range:</span>
            <span class="metric-value">{xml_stats['min_length']} - {xml_stats['max_length']} characters</span>
        </div>
        <div class="metric">
            <span class="metric-label">Standard Deviation:</span>
            <span class="metric-value">{xml_stats['std_length']:.0f} characters</span>
        </div>
        
        <h3>Similarity Score Distribution</h3>
        <div class="metric">
            <span class="metric-label">Average Score:</span>
            <span class="metric-value">{sim_stats['mean_score']:.3f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Median Score:</span>
            <span class="metric-value">{sim_stats['median_score']:.3f}</span>
        </div>
        <div class="metric">
            <span class="metric-label">Range:</span>
            <span class="metric-value">{sim_stats['min_score']:.3f} - {sim_stats['max_score']:.3f}</span>
        </div>
        
        <h3>Question Numbering Patterns</h3>
        <table>
            <tr><th>Pattern</th><th>Count</th></tr>
            <tr><td>Starts with 'Q'</td><td>{patterns['starts_with_q']}</td></tr>
            <tr><td>Starts with 'S'</td><td>{patterns['starts_with_s']}</td></tr>
            <tr><td>Starts with Number</td><td>{patterns['starts_with_number']}</td></tr>
            <tr><td>Has Brackets []</td><td>{patterns['has_brackets']}</td></tr>
            <tr><td>Has Parentheses ()</td><td>{patterns['has_parentheses']}</td></tr>
            <tr><td>Has Period</td><td>{patterns['has_period']}</td></tr>
            <tr><td>Empty or Dash Only</td><td>{patterns['empty_or_dash']}</td></tr>
        </table>
        """
    
    def _generate_recommendations_section(self, stats: Dict[str, Any], performance: Dict[str, Any]) -> str:
        """Generate recommendations section."""
        recommendations = []
        
        if performance and performance['totals']['overall_match_rate_percent'] < 85:
            recommendations.append("Consider improving question parsing patterns to increase match rates.")
        
        if stats and stats['similarity_stats']['mean_score'] < 0.9:
            recommendations.append("Review similarity threshold settings - some matches may be too loose.")
        
        if performance:
            low_performers = [survey for survey, data in performance['surveys'].items() 
                            if data['match_rate_percent'] < 50]
            if low_performers:
                recommendations.append(f"Focus on improving parsing for surveys with low match rates: {', '.join(low_performers[:2])}")
        
        if not recommendations:
            recommendations.append("Training data quality looks good! Consider expanding the dataset with more surveys.")
        
        rec_html = '\n'.join([f"<li>{rec}</li>" for rec in recommendations])
        
        return f"""
        <h2>💡 Recommendations</h2>
        <div class="highlight">
            <ul>
                {rec_html}
            </ul>
        </div>
        """
    
    def _get_timestamp(self) -> str:
        """Get current timestamp for report."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def run_analysis(self, output_file: str = "./training_data_analysis.html"):
        """Run complete analysis and generate report."""
        print("🚀 Starting training data analysis...")
        
        self.load_data()
        
        if not self.training_data:
            print("❌ No training data to analyze")
            return
        
        # Run all analyses
        basic_stats = self.analyze_basic_stats()
        performance_stats = self.analyze_matching_performance()
        content_stats = self.analyze_content_patterns()
        
        # Generate report
        self.generate_html_report(basic_stats, performance_stats, content_stats, output_file)
        
        print("✅ Analysis complete!")
        
        # Print summary to console
        print("\n" + "="*50)
        print("📊 ANALYSIS SUMMARY")
        print("="*50)
        print(f"Total question pairs: {basic_stats['total_pairs']}")
        print(f"Surveys processed: {basic_stats['total_surveys']}")
        print(f"Average similarity score: {basic_stats['similarity_stats']['mean_score']:.3f}")
        if performance_stats:
            print(f"Overall match rate: {performance_stats['totals']['overall_match_rate_percent']}%")
        print(f"Report saved to: {Path(output_file).absolute()}")


def main():
    """Main entry point."""
    analyzer = TrainingDataAnalyzer()
    analyzer.run_analysis()


if __name__ == '__main__':
    main()




