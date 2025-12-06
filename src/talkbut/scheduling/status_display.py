"""Status display functionality for automated logging schedule."""

from typing import Optional
from pathlib import Path

from .scheduler_manager import SchedulerManager
from .status_manager import StatusManager
from .models import ScheduleStatus


def format_status_display(
    scheduler_manager: SchedulerManager,
    status_manager: Optional[StatusManager] = None
) -> str:
    """
    Format and display schedule status.
    
    Queries actual system state (not just cached data) to show:
    - Enabled/disabled status
    - Schedule time
    - Last successful run
    - Next scheduled run
    - Recent errors (if any)
    
    Args:
        scheduler_manager: SchedulerManager instance
        status_manager: Optional StatusManager instance for run history
        
    Returns:
        Formatted status string
        
    Requirements: 2.4, 4.1, 4.2, 4.3, 4.4, 4.5
    """
    # Get current status from scheduler (queries actual system state)
    status = scheduler_manager.get_status()
    
    # Get additional info from status manager if available
    if status_manager:
        last_run = status_manager.get_last_run()
        recent_errors = status_manager.get_recent_errors(limit=5)
        
        # Update status with data from status manager
        status.last_run = last_run
        status.recent_errors = recent_errors
    
    # Build status display
    lines = []
    lines.append("=== Automated Daily Logging Status ===")
    lines.append("")
    
    # Platform
    lines.append(f"Platform: {status.platform}")
    
    # Enabled/Disabled
    if status.enabled:
        lines.append("Status: ENABLED ✓")
    else:
        lines.append("Status: DISABLED")
    
    # Schedule time
    if status.schedule_time:
        lines.append(f"Schedule Time: {status.schedule_time}")
    else:
        lines.append("Schedule Time: Not configured")
    
    # Last run
    if status.last_run:
        lines.append(f"Last Run: {status.last_run.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        lines.append("Last Run: Never")
    
    # Next run
    if status.next_run:
        lines.append(f"Next Run: {status.next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        if status.enabled:
            lines.append("Next Run: Unable to determine")
        else:
            lines.append("Next Run: N/A (disabled)")
    
    # Recent errors
    if status.recent_errors:
        lines.append("")
        lines.append("Recent Errors:")
        for i, error in enumerate(status.recent_errors, 1):
            timestamp_str = error.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            lines.append(f"  {i}. [{timestamp_str}] {error.error_message}")
            if error.date_attempted:
                lines.append(f"     Date attempted: {error.date_attempted}")
    else:
        lines.append("")
        lines.append("Recent Errors: None")
    
    return "\n".join(lines)


def display_status(
    scheduler_manager: SchedulerManager,
    status_manager: Optional[StatusManager] = None
) -> None:
    """
    Display schedule status to console.
    
    Args:
        scheduler_manager: SchedulerManager instance
        status_manager: Optional StatusManager instance for run history
        
    Requirements: 2.4, 4.1, 4.2, 4.3, 4.4, 4.5
    """
    status_text = format_status_display(scheduler_manager, status_manager)
    print(status_text)
