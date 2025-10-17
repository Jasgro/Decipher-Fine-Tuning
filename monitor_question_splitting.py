#!/usr/bin/env python3
"""
Question Splitting Progress Monitor

Monitor the progress of question-level training data generation.
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path


def get_file_size(file_path):
    """Get file size in MB."""
    try:
        size = os.path.getsize(file_path)
        return size / (1024 * 1024)  # Convert to MB
    except:
        return 0


def count_json_entries(file_path):
    """Count entries in JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return len(data) if isinstance(data, list) else 0
    except:
        return 0


def monitor_progress():
    """Monitor question splitting progress."""
    question_data_file = Path("question_training_data.json")
    debug_file = Path("question_debug.json")
    
    print("\n" + "="*70)
    print("📊 QUESTION SPLITTING PROGRESS MONITOR")
    print("="*70)
    
    if question_data_file.exists():
        file_size = get_file_size(question_data_file)
        entry_count = count_json_entries(question_data_file)
        
        print(f"✅ Question Training Data:")
        print(f"   File size: {file_size:.1f} MB")
        print(f"   Question pairs: {entry_count:,}")
        
        # Estimate progress based on file size (rough heuristic)
        estimated_total_mb = 50  # Rough estimate for 427 surveys
        progress_pct = min((file_size / estimated_total_mb) * 100, 100)
        print(f"   Estimated progress: {progress_pct:.1f}%")
    else:
        print("⏳ Question training data file not yet created...")
    
    if debug_file.exists():
        debug_size = get_file_size(debug_file)
        print(f"✅ Debug file size: {debug_size:.1f} MB")
    else:
        print("⏳ Debug file not yet created...")
    
    # Check if process is still running by looking for recent file modifications
    if question_data_file.exists():
        mod_time = os.path.getmtime(question_data_file)
        last_modified = datetime.fromtimestamp(mod_time)
        time_since_mod = datetime.now() - last_modified
        
        print(f"\nFile last modified: {last_modified.strftime('%H:%M:%S')}")
        print(f"Time since last update: {time_since_mod.total_seconds():.0f} seconds")
        
        if time_since_mod.total_seconds() < 60:
            print("🔄 Process appears to be actively running")
        else:
            print("⏸️  Process may have completed or paused")
    
    print(f"\nLast checked: {datetime.now().strftime('%H:%M:%S')}")
    print("="*70)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor question splitting progress")
    parser.add_argument('--once', action='store_true', help='Check once and exit')
    parser.add_argument('--interval', type=int, default=30, help='Update interval in seconds')
    
    args = parser.parse_args()
    
    if args.once:
        monitor_progress()
    else:
        try:
            while True:
                monitor_progress()
                time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")









