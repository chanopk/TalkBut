"""Data models for scheduling."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List


@dataclass
class ErrorRecord:
    """Record of a scheduling error."""
    timestamp: datetime
    error_message: str
    date_attempted: Optional[str] = None


@dataclass
class ScheduleStatus:
    """Status of the automated logging schedule."""
    enabled: bool
    schedule_time: Optional[str]  # HH:MM format
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    recent_errors: List[ErrorRecord]
    platform: str  # 'cron', 'task_scheduler', or 'unsupported'
