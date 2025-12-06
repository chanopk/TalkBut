"""
Automated runner for scheduled daily logging.

This script is designed to be called by cron/Task Scheduler.
It handles configuration loading, error logging, status tracking,
and retry logic with exponential backoff.

Requirements: 1.2, 1.3, 1.4, 1.5
"""

import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from talkbut.core.config import ConfigManager
from talkbut.scheduling.status_manager import StatusManager
from talkbut.scheduling.error_logger import log_error
from talkbut.collectors.git_collector import GitCollector
from talkbut.collectors.parser import DataParser
from talkbut.processors.ai_analyzer import AIAnalyzer


class APIError(Exception):
    """Exception for API-related failures that should trigger retry."""
    pass


class AutomatedRunner:
    """
    Runner for automated daily logging execution.
    
    Handles the complete workflow of:
    1. Loading configuration
    2. Collecting commits
    3. Analyzing with AI
    4. Saving daily log
    5. Error handling and logging
    6. Status tracking
    
    Requirements: 1.2, 1.3, 1.4, 1.5
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize automated runner.
        
        Args:
            config_path: Optional path to config file
        """
        self.config_path = config_path
        self.config = None
        self.status_manager = None
    
    def _load_configuration(self) -> bool:
        """
        Load configuration from standard location.
        
        Returns:
            True if successful, False otherwise
            
        Requirements: 1.3
        """
        try:
            # Set config path if provided
            if self.config_path:
                import os
                os.environ["TALKBUT_CONFIG_PATH"] = self.config_path
            
            # Load config
            self.config = ConfigManager()
            
            # Initialize status manager
            schedule_config = self.config.get_schedule_config()
            status_file = Path(schedule_config.get("status_file", "./data/schedule_status.json"))
            self.status_manager = StatusManager(status_file)
            
            return True
        except Exception as e:
            print(f"Failed to load configuration: {e}", file=sys.stderr)
            return False
    
    def _collect_commits(self, date_str: str) -> Tuple[bool, Optional[list], Optional[str]]:
        """
        Collect commits for the specified date.
        
        Args:
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            Tuple of (success, commits, error_message)
            
        Requirements: 1.2
        """
        try:
            # Get repositories from config
            repos = self.config.git_repos
            if not repos:
                return False, None, "No repositories configured"
            
            # Get author filter from config
            author = self.config.get("git.author")
            
            # Collect commits from all repositories
            all_commits = []
            parser = DataParser()
            
            for repo_info in repos:
                repo_path = repo_info.get('path', '.')
                repo_name = repo_info.get('name', repo_path)
                
                try:
                    collector = GitCollector(repo_path)
                    
                    # Collect commits for the specific date
                    commits = collector.collect_commits(
                        since=f"{date_str} 00:00:00",
                        until=f"{date_str} 23:59:59",
                        author=author,
                        branch=None,
                        include_diffs=False
                    )
                    
                    if commits:
                        # Add repo_name to each commit
                        for c in commits:
                            c.repo_name = repo_name
                        all_commits.extend(commits)
                        
                except Exception as e:
                    # Log warning but continue with other repos
                    print(f"Warning: Failed to collect from {repo_name}: {e}", file=sys.stderr)
            
            # Enrich commits with parsed metadata
            for commit in all_commits:
                parser.enrich_commit(commit)
            
            return True, all_commits, None
            
        except Exception as e:
            return False, None, f"Failed to collect commits: {e}"
    
    def _analyze_and_save(self, commits: list, date_str: str) -> Tuple[bool, Optional[str]]:
        """
        Analyze commits with AI and save daily log.
        
        Args:
            commits: List of commits to analyze
            date_str: Date string in YYYY-MM-DD format
            
        Returns:
            Tuple of (success, error_message)
            
        Requirements: 1.2, 1.4
        """
        try:
            import json
            from datetime import date
            
            # Parse date
            report_date = date.fromisoformat(date_str)
            
            # Analyze commits
            analyzer = AIAnalyzer()
            report = analyzer.analyze_commits(commits, report_date)
            
            # Build daily log
            daily_log = {
                "date": date_str,
                "summary": report.ai_summary,
                "stats": {
                    "commits": report.total_commits,
                    "files": report.files_changed,
                    "insertions": report.insertions,
                    "deletions": report.deletions
                },
                "categories": report.categories,
                "tasks": report.tasks if hasattr(report, 'tasks') and report.tasks else []
            }
            
            # Save to file
            log_dir = Path(self.config.get("storage.log_dir", "./data/logs"))
            log_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"daily_log_{date_str}.json"
            output_path = log_dir / filename
            
            # Write JSON file
            json_output = json.dumps(daily_log, ensure_ascii=False, separators=(',', ':'))
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_output)
            
            return True, None
            
        except Exception as e:
            # Check if this is an API error (should trigger retry)
            error_str = str(e).lower()
            if any(keyword in error_str for keyword in ['api', 'rate limit', 'quota', 'network', 'timeout', 'connection']):
                raise APIError(f"API failure: {e}")
            
            return False, f"Failed to analyze and save: {e}"
    
    def run_with_retry(self, max_retries: int = 3) -> int:
        """
        Run automated logging with retry logic and exponential backoff.
        
        Args:
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            Exit code (0 for success, 1 for failure)
            
        Requirements: 1.5
        """
        # Load configuration
        if not self._load_configuration():
            return 1
        
        # Get today's date
        today = datetime.now().date().isoformat()
        
        # Attempt execution with retries
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # Collect commits
                success, commits, error = self._collect_commits(today)
                if not success:
                    last_error = error
                    break
                
                # Skip if no commits
                if not commits:
                    print(f"No commits found for {today}")
                    self.status_manager.record_run(success=True)
                    return 0
                
                # Analyze and save
                success, error = self._analyze_and_save(commits, today)
                if success:
                    # Success - record and exit
                    self.status_manager.record_run(success=True)
                    print(f"Successfully created daily log for {today}")
                    return 0
                else:
                    last_error = error
                    break
                    
            except APIError as e:
                # API error - retry with exponential backoff
                last_error = str(e)
                
                if attempt < max_retries - 1:
                    # Calculate backoff time (2^attempt seconds)
                    backoff_time = 2 ** attempt
                    print(f"API error on attempt {attempt + 1}/{max_retries}: {e}", file=sys.stderr)
                    print(f"Retrying in {backoff_time} seconds...", file=sys.stderr)
                    time.sleep(backoff_time)
                else:
                    # Final attempt failed
                    print(f"API error on final attempt: {e}", file=sys.stderr)
                    
            except Exception as e:
                # Non-API error - don't retry
                last_error = f"Unexpected error: {e}\n{traceback.format_exc()}"
                print(last_error, file=sys.stderr)
                break
        
        # All retries exhausted or non-retryable error occurred
        # Log error and record failure
        if last_error:
            # Log to error file
            schedule_config = self.config.get_schedule_config()
            error_log_path = Path(schedule_config.get("error_log", "./data/schedule_errors.log"))
            log_error(error_log_path, last_error, today)
            
            # Record failure in status
            self.status_manager.record_run(success=False, error=last_error, date_attempted=today)
        
        return 1


def main():
    """
    Main entry point for automated runner.
    
    Can be called directly by cron/Task Scheduler.
    """
    # Parse command line arguments
    config_path = None
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    # Create and run
    runner = AutomatedRunner(config_path)
    exit_code = runner.run_with_retry()
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
