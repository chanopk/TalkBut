"""
Batch processor for handling multiple dates in a single operation.

Requirements: 3.2, 3.3, 3.4, 3.5
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Optional, Tuple
from talkbut.core.config import ConfigManager
from talkbut.collectors.git_collector import GitCollector
from talkbut.collectors.parser import DataParser
from talkbut.processors.ai_analyzer import AIAnalyzer
from talkbut.processors.batch_utils import expand_date_range, log_exists
from talkbut.utils.logger import get_logger
import json

logger = get_logger(__name__)


@dataclass
class ProcessResult:
    """Result of processing a single date."""
    date: date
    success: bool
    skipped: bool
    error: Optional[str]
    commits_count: int


@dataclass
class BatchResult:
    """Result of batch processing multiple dates."""
    total_dates: int
    processed: List[date] = field(default_factory=list)
    skipped: List[date] = field(default_factory=list)
    failed: List[Tuple[date, str]] = field(default_factory=list)
    duration: float = 0.0  # seconds


class BatchProcessor:
    """
    Handles batch processing of daily logs for multiple dates.
    
    Requirements: 3.2, 3.3, 3.4, 3.5
    """
    
    def __init__(self, config: ConfigManager):
        """
        Initialize BatchProcessor with configuration.
        
        Args:
            config: ConfigManager instance
        """
        self.config = config
        self.log_dir = Path(config.get("storage.log_dir", "./data/logs"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
    
    def process_date_range(
        self,
        since: str,
        until: Optional[str] = None,
        force: bool = False,
        author: Optional[str] = None,
        progress_callback: Optional[callable] = None
    ) -> BatchResult:
        """
        Process logs for a date range.
        
        Args:
            since: Start date (relative or absolute)
            until: End date (default: today)
            force: Force regeneration of existing logs
            author: Filter by author
            progress_callback: Optional callback for progress updates
                              Called with (current_date, index, total, result)
            
        Returns:
            BatchResult with summary of processed dates
            
        Requirements: 3.2, 3.3, 3.4, 3.5
        """
        start_time = datetime.now()
        
        # Expand date range
        dates = expand_date_range(since, until)
        
        result = BatchResult(total_dates=len(dates))
        
        # Process each date
        for idx, process_date in enumerate(dates, 1):
            date_result = self._process_single_date(
                process_date,
                author=author,
                force=force
            )
            
            # Collect results
            if date_result.skipped:
                result.skipped.append(process_date)
            elif date_result.success:
                result.processed.append(process_date)
            else:
                result.failed.append((process_date, date_result.error or "Unknown error"))
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(process_date, idx, len(dates), date_result)
        
        # Calculate duration
        end_time = datetime.now()
        result.duration = (end_time - start_time).total_seconds()
        
        return result
    
    def _process_single_date(
        self,
        process_date: date,
        author: Optional[str] = None,
        force: bool = False
    ) -> ProcessResult:
        """
        Process log for a single date.
        
        Args:
            process_date: Date to process
            author: Filter by author
            force: Force regeneration if log exists
            
        Returns:
            ProcessResult with outcome
            
        Requirements: 3.2, 3.3, 3.5
        """
        # Check if log already exists
        if not force and log_exists(process_date, self.log_dir):
            return ProcessResult(
                date=process_date,
                success=False,
                skipped=True,
                error=None,
                commits_count=0
            )
        
        try:
            # Get repositories from config
            repos = self.config.git_repos
            if not repos:
                repos = [{'path': '.', 'name': 'Current Directory'}]
            
            # Use author from config if not specified
            if author is None:
                author = self.config.get("git.author")
            
            # Collect commits from all repositories for this date
            all_commits = []
            parser = DataParser()
            
            # Calculate since/until for this specific date
            since_str = process_date.isoformat()
            # Until is the end of the day (next day at 00:00)
            next_day = process_date + timedelta(days=1)
            until_str = next_day.isoformat()
            
            for repo_info in repos:
                repo_path = repo_info.get('path', '.')
                repo_name = repo_info.get('name', repo_path)
                
                try:
                    collector = GitCollector(repo_path)
                    commits = collector.collect_commits(
                        since=since_str,
                        until=until_str,
                        author=author,
                        branch=None,
                        include_diffs=False
                    )
                    
                    # Add repo_name to each commit
                    for c in commits:
                        c.repo_name = repo_name
                    
                    all_commits.extend(commits)
                    
                except Exception as e:
                    logger.warning(f"Failed to collect from {repo_name} for {process_date}: {e}")
            
            # If no commits found, still create an empty log
            if not all_commits:
                # Create empty log
                daily_log = {
                    "date": process_date.isoformat(),
                    "summary": "No commits found for this date.",
                    "stats": {
                        "commits": 0,
                        "files": 0,
                        "insertions": 0,
                        "deletions": 0
                    },
                    "categories": [],
                    "tasks": []
                }
                
                # Save to file
                filename = f"daily_log_{process_date.isoformat()}.json"
                output_path = self.log_dir / filename
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(daily_log, f, ensure_ascii=False, separators=(',', ':'))
                
                return ProcessResult(
                    date=process_date,
                    success=True,
                    skipped=False,
                    error=None,
                    commits_count=0
                )
            
            # Sort commits by date
            all_commits.sort(key=lambda c: c.date, reverse=True)
            
            # Enrich commits with parsed metadata
            for commit in all_commits:
                parser.enrich_commit(commit)
            
            # Analyze commits
            analyzer = AIAnalyzer()
            report = analyzer.analyze_commits(all_commits, process_date)
            
            # Build daily log
            daily_log = {
                "date": process_date.isoformat(),
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
            filename = f"daily_log_{process_date.isoformat()}.json"
            output_path = self.log_dir / filename
            
            # Remove old file if exists
            if output_path.exists():
                output_path.unlink()
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(daily_log, f, ensure_ascii=False, separators=(',', ':'))
            
            return ProcessResult(
                date=process_date,
                success=True,
                skipped=False,
                error=None,
                commits_count=len(all_commits)
            )
            
        except Exception as e:
            logger.error(f"Failed to process {process_date}: {e}", exc_info=True)
            return ProcessResult(
                date=process_date,
                success=False,
                skipped=False,
                error=str(e),
                commits_count=0
            )
