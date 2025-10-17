#!/usr/bin/env python3
"""
Batch Survey Processor

Processes hundreds of surveys efficiently with progress tracking,
error handling, and resumption capabilities.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

from enhanced_survey_downloader import EnhancedSurveyProcessor


class BatchSurveyProcessor:
    """Processes multiple surveys in batches with comprehensive tracking."""
    
    def __init__(self, surveys_dir: Path, batch_size: int = 10):
        self.surveys_dir = Path(surveys_dir)
        self.batch_size = batch_size
        self.progress_file = Path("batch_progress.json")
        self.log_file = Path("batch_processing.log")
        self.results_file = Path("batch_results.json")
        
        # Setup logging
        self.setup_logging()
        
        # Initialize progress tracking
        self.progress = self.load_progress()
        self.results = self.load_results()
        
        # Initialize the enhanced processor (will setup auth when needed)
        self.processor = None
        
    def setup_logging(self):
        """Setup comprehensive logging."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_progress(self) -> Dict:
        """Load processing progress from file."""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load progress file: {e}")
        
        return {
            'completed_folders': [],
            'failed_folders': [],
            'skipped_folders': [],
            'current_batch': 0,
            'total_folders': 0,
            'start_time': None,
            'last_update': None
        }
    
    def save_progress(self):
        """Save current progress to file."""
        self.progress['last_update'] = datetime.now().isoformat()
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Could not save progress: {e}")
    
    def load_results(self) -> Dict:
        """Load batch processing results."""
        if self.results_file.exists():
            try:
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load results file: {e}")
        
        return {
            'successful_downloads': {},
            'failed_downloads': {},
            'processing_stats': {
                'total_processed': 0,
                'word_downloads_attempted': 0,
                'word_downloads_successful': 0,
                'xml_downloads_attempted': 0,
                'xml_downloads_successful': 0,
                'folders_with_existing_content': 0,
                'empty_folders_processed': 0
            },
            'error_summary': {},
            'batch_timings': []
        }
    
    def save_results(self):
        """Save current results to file."""
        try:
            with open(self.results_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Could not save results: {e}")
    
    def get_all_folders(self) -> List[str]:
        """Get list of all survey folders."""
        try:
            folders = []
            for item in self.surveys_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    folders.append(item.name)
            
            # Sort for consistent processing order
            folders.sort()
            return folders
            
        except Exception as e:
            self.logger.error(f"Could not list survey folders: {e}")
            return []
    
    def get_pending_folders(self) -> List[str]:
        """Get list of folders that still need processing."""
        all_folders = self.get_all_folders()
        completed = set(self.progress['completed_folders'])
        failed = set(self.progress['failed_folders'])
        skipped = set(self.progress['skipped_folders'])
        
        processed = completed | failed | skipped
        pending = [f for f in all_folders if f not in processed]
        
        self.logger.info(f"Total folders: {len(all_folders)}")
        self.logger.info(f"Completed: {len(completed)}")
        self.logger.info(f"Failed: {len(failed)}")
        self.logger.info(f"Skipped: {len(skipped)}")
        self.logger.info(f"Pending: {len(pending)}")
        
        return pending
    
    def setup_authentication(self) -> bool:
        """Setup authentication for the processor."""
        if self.processor is None:
            self.processor = EnhancedSurveyProcessor(self.surveys_dir / "dummy")
        
        self.logger.info("Setting up authentication...")
        success = self.processor.setup_authentication()
        
        if not success:
            self.logger.error("Authentication setup failed!")
            return False
        
        self.logger.info("Authentication setup successful!")
        return True
    
    def process_folder(self, folder_name: str) -> Dict:
        """Process a single survey folder."""
        folder_path = self.surveys_dir / folder_name
        
        try:
            # Create processor for the surveys directory
            folder_processor = EnhancedSurveyProcessor(self.surveys_dir)
            
            # Copy authentication from main processor
            if self.processor and self.processor.auth_client:
                folder_processor.auth_client = self.processor.auth_client
            
            # Process the folder
            self.logger.info(f"Processing folder: {folder_name}")
            start_time = time.time()
            
            success = folder_processor.process_specific_folder(folder_name)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Get detailed results
            summary = getattr(folder_processor, 'stats', {
                'word_downloads_attempted': 0,
                'word_downloads_successful': 0,
                'xml_downloads_attempted': 0,
                'xml_downloads_successful': 0,
                'errors': []
            })
            
            result = {
                'folder': folder_name,
                'success': success,
                'processing_time': processing_time,
                'word_downloads_attempted': summary['word_downloads_attempted'],
                'word_downloads_successful': summary['word_downloads_successful'],
                'xml_downloads_attempted': summary['xml_downloads_attempted'],
                'xml_downloads_successful': summary['xml_downloads_successful'],
                'errors': summary['errors']
            }
            
            # Update results
            if success:
                self.results['successful_downloads'][folder_name] = result
            else:
                self.results['failed_downloads'][folder_name] = result
            
            # Update processing stats
            stats = self.results['processing_stats']
            stats['total_processed'] += 1
            stats['word_downloads_attempted'] += summary['word_downloads_attempted']
            stats['word_downloads_successful'] += summary['word_downloads_successful']
            stats['xml_downloads_attempted'] += summary['xml_downloads_attempted']
            stats['xml_downloads_successful'] += summary['xml_downloads_successful']
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing {folder_name}: {e}")
            
            error_result = {
                'folder': folder_name,
                'success': False,
                'processing_time': 0,
                'error': str(e),
                'word_downloads_attempted': 0,
                'word_downloads_successful': 0,
                'xml_downloads_attempted': 0,
                'xml_downloads_successful': 0,
                'errors': [str(e)]
            }
            
            self.results['failed_downloads'][folder_name] = error_result
            return error_result
    
    def process_batch(self, folders: List[str]) -> List[Dict]:
        """Process a batch of folders."""
        batch_results = []
        batch_start = time.time()
        
        self.logger.info(f"Processing batch of {len(folders)} folders...")
        
        for i, folder in enumerate(folders, 1):
            self.logger.info(f"Batch progress: {i}/{len(folders)} - {folder}")
            
            try:
                result = self.process_folder(folder)
                batch_results.append(result)
                
                # Update progress
                if result['success']:
                    self.progress['completed_folders'].append(folder)
                    self.logger.info(f"SUCCESS: {folder} completed successfully")
                else:
                    self.progress['failed_folders'].append(folder)
                    self.logger.warning(f"FAILED: {folder} failed: {result.get('errors', ['Unknown error'])}")
                
            except KeyboardInterrupt:
                self.logger.info("Batch processing interrupted by user")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error processing {folder}: {e}")
                self.progress['failed_folders'].append(folder)
                batch_results.append({
                    'folder': folder,
                    'success': False,
                    'error': str(e),
                    'processing_time': 0
                })
            
            # Save progress after each folder
            self.save_progress()
            self.save_results()
        
        batch_end = time.time()
        batch_time = batch_end - batch_start
        
        self.results['batch_timings'].append({
            'batch_folders': len(folders),
            'batch_time': batch_time,
            'avg_time_per_folder': batch_time / len(folders) if folders else 0
        })
        
        self.logger.info(f"Batch completed in {batch_time:.1f}s (avg: {batch_time/len(folders):.1f}s per folder)")
        
        return batch_results
    
    def print_progress_summary(self):
        """Print current progress summary."""
        completed = len(self.progress['completed_folders'])
        failed = len(self.progress['failed_folders'])
        skipped = len(self.progress['skipped_folders'])
        total = self.progress.get('total_folders', 0)
        
        if total > 0:
            progress_pct = ((completed + failed + skipped) / total) * 100
        else:
            progress_pct = 0
        
        print("\n" + "="*60)
        print("📊 BATCH PROCESSING PROGRESS")
        print("="*60)
        print(f"Total folders: {total}")
        print(f"Completed successfully: {completed}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")
        print(f"Overall progress: {progress_pct:.1f}%")
        
        stats = self.results['processing_stats']
        print(f"\nProcessing Statistics:")
        print(f"  Word downloads attempted: {stats['word_downloads_attempted']}")
        print(f"  Word downloads successful: {stats['word_downloads_successful']}")
        print(f"  XML downloads attempted: {stats['xml_downloads_attempted']}")
        print(f"  XML downloads successful: {stats['xml_downloads_successful']}")
        
        if self.results['batch_timings']:
            avg_time = sum(b['avg_time_per_folder'] for b in self.results['batch_timings']) / len(self.results['batch_timings'])
            remaining = total - (completed + failed + skipped)
            est_time_remaining = remaining * avg_time
            print(f"\nTime Estimates:")
            print(f"  Average time per folder: {avg_time:.1f}s")
            print(f"  Estimated time remaining: {est_time_remaining/60:.1f} minutes")
        
        print("="*60)
    
    def run_batch_processing(self, resume: bool = True, max_folders: int = None):
        """Run the complete batch processing."""
        self.logger.info("Starting batch survey processing...")
        
        # Setup authentication first
        if not self.setup_authentication():
            self.logger.error("Cannot proceed without authentication")
            return False
        
        # Get folders to process
        if resume:
            pending_folders = self.get_pending_folders()
        else:
            # Fresh start
            self.progress = {
                'completed_folders': [],
                'failed_folders': [],
                'skipped_folders': [],
                'current_batch': 0,
                'total_folders': 0,
                'start_time': datetime.now().isoformat(),
                'last_update': None
            }
            pending_folders = self.get_all_folders()
        
        # Apply folder limit if specified
        if max_folders:
            pending_folders = pending_folders[:max_folders]
            self.logger.info(f"Limited processing to first {max_folders} folders")
        
        self.progress['total_folders'] = len(self.get_all_folders())
        
        if not pending_folders:
            self.logger.info("No folders to process!")
            return True
        
        self.logger.info(f"Processing {len(pending_folders)} folders in batches of {self.batch_size}")
        
        # Process in batches
        try:
            for i in range(0, len(pending_folders), self.batch_size):
                batch_folders = pending_folders[i:i + self.batch_size]
                batch_num = (i // self.batch_size) + 1
                
                self.logger.info(f"Starting batch {batch_num} ({len(batch_folders)} folders)")
                self.progress['current_batch'] = batch_num
                
                # Process the batch
                batch_results = self.process_batch(batch_folders)
                
                # Print progress summary
                self.print_progress_summary()
                
                # Small delay between batches to avoid overwhelming the system
                if i + self.batch_size < len(pending_folders):
                    self.logger.info("Pausing 5 seconds between batches...")
                    time.sleep(5)
        
        except KeyboardInterrupt:
            self.logger.info("Batch processing interrupted by user")
            self.logger.info("Progress has been saved. Use --resume to continue later.")
        
        except Exception as e:
            self.logger.error(f"Batch processing failed: {e}")
            return False
        
        finally:
            # Final save and cleanup
            self.save_progress()
            self.save_results()
            
            if self.processor:
                self.processor.cleanup()
        
        self.logger.info("Batch processing completed!")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Batch process survey folders")
    parser.add_argument('--surveys-dir', default='Surveys', help='Directory containing survey folders')
    parser.add_argument('--batch-size', type=int, default=10, help='Number of folders to process per batch')
    parser.add_argument('--resume', action='store_true', help='Resume from previous progress')
    parser.add_argument('--fresh-start', action='store_true', help='Start fresh (ignore previous progress)')
    parser.add_argument('--max-folders', type=int, help='Limit processing to first N folders (for testing)')
    
    args = parser.parse_args()
    
    # Determine resume behavior
    resume = not args.fresh_start
    if args.resume:
        resume = True
    
    processor = BatchSurveyProcessor(
        surveys_dir=Path(args.surveys_dir),
        batch_size=args.batch_size
    )
    
    success = processor.run_batch_processing(
        resume=resume,
        max_folders=args.max_folders
    )
    
    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
