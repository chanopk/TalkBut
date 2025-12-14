"""
Batch processing utilities for date range expansion and log detection.

Requirements: 3.1, 3.2
"""
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Optional, Union
import re
from talkbut.utils.logger import get_logger

logger = get_logger(__name__)


def expand_date_range(since: str, until: Optional[str] = None) -> List[date]:
    """
    Parse since/until parameters and generate list of all dates in range.
    
    Supports:
    - Relative dates: "7 days ago", "1 week ago", "yesterday"
    - Absolute dates: "2025-12-01", "2025-11-20"
    
    Args:
        since: Start date (relative or absolute)
        until: End date (default: today)
        
    Returns:
        List of dates in chronological order with no duplicates
        
    Requirements: 3.1
    """
    # Parse since date
    since_date = _parse_date(since)
    
    # Parse until date (default to today)
    if until is None:
        until_date = date.today()
    else:
        until_date = _parse_date(until)
    
    # Ensure since is before or equal to until
    if since_date > until_date:
        since_date, until_date = until_date, since_date
    
    # Generate all dates in range (inclusive)
    dates = []
    current = since_date
    while current <= until_date:
        dates.append(current)
        current += timedelta(days=1)
    
    return dates


def _parse_date(date_str: str) -> date:
    """
    Parse a date string into a date object.
    
    Supports:
    - Relative: "N days ago", "N weeks ago", "yesterday", "today"
    - Absolute: "YYYY-MM-DD"
    
    Args:
        date_str: Date string to parse
        
    Returns:
        Parsed date object
        
    Raises:
        ValueError: If date string format is invalid
    """
    date_str = date_str.strip().lower()
    today = date.today()
    
    # Handle "today"
    if date_str == "today":
        return today
    
    # Handle "yesterday"
    if date_str == "yesterday":
        return today - timedelta(days=1)
    
    # Handle "N days ago"
    days_ago_match = re.match(r'^(\d+)\s+days?\s+ago$', date_str)
    if days_ago_match:
        days = int(days_ago_match.group(1))
        return today - timedelta(days=days)
    
    # Handle "N weeks ago"
    weeks_ago_match = re.match(r'^(\d+)\s+weeks?\s+ago$', date_str)
    if weeks_ago_match:
        weeks = int(weeks_ago_match.group(1))
        return today - timedelta(weeks=weeks)
    
    # Handle absolute date "YYYY-MM-DD"
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
        return parsed
    except ValueError:
        pass
    
    # If nothing matched, raise error
    raise ValueError(
        f"Invalid date format: '{date_str}'. "
        f"Supported formats: 'YYYY-MM-DD', 'N days ago', 'N weeks ago', 'yesterday', 'today'"
    )


def log_exists(log_date: date, log_dir: Union[str, Path]) -> bool:
    """
    Check if log file exists for a given date.
    
    Uses standard naming convention: daily_log_YYYY-MM-DD.json
    
    Args:
        log_date: Date to check
        log_dir: Directory containing log files
        
    Returns:
        True if log file exists, False otherwise
        
    Requirements: 3.2
    """
    log_dir_path = Path(log_dir)
    filename = f"daily_log_{log_date.isoformat()}.json"
    log_path = log_dir_path / filename
    return log_path.exists()
