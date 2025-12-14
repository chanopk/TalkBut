"""SchedulerManager for managing automated daily logging across platforms."""

import sys
from pathlib import Path
from typing import Optional

from .platform_detector import detect_platform, SchedulerType
from .cron_scheduler import CronScheduler
from .task_scheduler import TaskScheduler
from .models import ScheduleStatus, ErrorRecord


class SchedulerManager:
    """
    Manager for automated logging schedules across different platforms.
    
    Provides a unified interface for scheduling operations that works
    across Unix-like systems (using cron) and Windows (using Task Scheduler).
    """
    
    def __init__(self, config=None, status_manager=None):
        """
        Initialize SchedulerManager.
        
        Args:
            config: Optional ConfigManager instance
            status_manager: Optional StatusManager instance for tracking runs
        """
        self.config = config
        self.status_manager = status_manager
        self.platform_type = detect_platform()
        
        # Initialize platform-specific scheduler
        if self.platform_type == SchedulerType.CRON:
            self.scheduler = CronScheduler()
        elif self.platform_type == SchedulerType.TASK_SCHEDULER:
            self.scheduler = TaskScheduler()
        else:
            self.scheduler = None
    
    def enable(self, time: str, config_path: Optional[str] = None) -> bool:
        """
        Enable automated logging at the specified time.
        
        Args:
            time: Time in HH:MM format (24-hour)
            config_path: Optional path to config file
            
        Returns:
            True if successful, False otherwise
        """
        if self.scheduler is None:
            return False
        
        # Validate time format
        if not self._validate_time_format(time):
            return False
        
        # Build command to execute (includes config_path in the command string)
        command = self._build_command(config_path)
        
        # Create scheduled job
        return self.scheduler.create_job(time, command)
    
    def disable(self) -> bool:
        """
        Disable automated logging.
        
        Returns:
            True if successful, False otherwise
        """
        if self.scheduler is None:
            return False
        
        return self.scheduler.remove_job() if hasattr(self.scheduler, 'remove_job') else self.scheduler.remove_task()
    
    def update(self, time: str, config_path: Optional[str] = None) -> bool:
        """
        Update the schedule time.
        
        Args:
            time: New time in HH:MM format (24-hour)
            config_path: Optional path to config file
            
        Returns:
            True if successful, False otherwise
        """
        if self.scheduler is None:
            return False
        
        # Validate time format
        if not self._validate_time_format(time):
            return False
        
        # Build command with config path (includes config_path in the command string)
        command = self._build_command(config_path)
        
        # Update is essentially remove + create
        return self.scheduler.create_job(time, command)
    
    def get_status(self) -> ScheduleStatus:
        """
        Get current schedule status.
        
        Returns:
            ScheduleStatus object with current state
        """
        # Determine platform string
        platform_str = "unsupported"
        if self.platform_type == SchedulerType.CRON:
            platform_str = "cron"
        elif self.platform_type == SchedulerType.TASK_SCHEDULER:
            platform_str = "task_scheduler"
        
        # Check if enabled
        enabled = self.is_enabled()
        
        # Get schedule time and next run
        schedule_time = None
        next_run = None
        if enabled and self.scheduler:
            next_run = self.scheduler.get_next_run()
            if next_run:
                schedule_time = f"{next_run.hour:02d}:{next_run.minute:02d}"
        
        # Get last run and errors from status manager (if available)
        last_run = None
        recent_errors = []
        
        if self.status_manager:
            last_run = self.status_manager.get_last_run()
            recent_errors = self.status_manager.get_recent_errors()
        
        return ScheduleStatus(
            enabled=enabled,
            schedule_time=schedule_time,
            last_run=last_run,
            next_run=next_run,
            recent_errors=recent_errors,
            platform=platform_str
        )
    
    def is_enabled(self) -> bool:
        """
        Check if automated logging is enabled.
        
        Returns:
            True if enabled, False otherwise
        """
        if self.scheduler is None:
            return False
        
        if hasattr(self.scheduler, 'job_exists'):
            return self.scheduler.job_exists()
        elif hasattr(self.scheduler, 'task_exists'):
            return self.scheduler.task_exists()
        
        return False
    
    def _validate_time_format(self, time: str) -> bool:
        """
        Validate time format (HH:MM).
        
        Args:
            time: Time string to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            parts = time.split(":")
            if len(parts) != 2:
                return False
            
            hour = int(parts[0])
            minute = int(parts[1])
            
            return 0 <= hour <= 23 and 0 <= minute <= 59
        except (ValueError, AttributeError):
            return False
    
    def _build_command(self, config_path: Optional[str] = None) -> str:
        """
        Build the command to execute for automated logging.
        
        Uses the automated_runner script which handles:
        - Configuration loading
        - Error handling and logging
        - Status tracking
        - Retry logic with exponential backoff
        
        Args:
            config_path: Optional path to config file
            
        Returns:
            Command string
            
        Requirements: 1.2, 1.3, 1.4, 1.5
        """
        # Get Python executable path
        python_exe = sys.executable
        
        # Build command to run automated_runner
        # Use -m to run as module
        command_parts = [python_exe, "-m", "talkbut.scheduling.automated_runner"]
        
        # Add config path if provided
        if config_path:
            command_parts.append(config_path)
        
        return " ".join(command_parts)
