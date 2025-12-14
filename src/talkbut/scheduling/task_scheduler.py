"""TaskScheduler implementation for Windows systems."""

import subprocess
import re
from datetime import datetime, timedelta
from typing import Optional


class TaskScheduler:
    """Scheduler implementation using Windows Task Scheduler."""
    
    TASK_NAME = "TalkButDailyLog"
    
    def __init__(self):
        """Initialize TaskScheduler."""
        pass
    
    def create_task(self, time: str, command: str) -> bool:
        """
        Create a scheduled task for the specified time and command.
        
        Args:
            time: Time in HH:MM format (24-hour)
            command: Command to execute
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse and validate time
            hour, minute = time.split(":")
            hour = int(hour)
            minute = int(minute)
            
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                return False
            
            # Remove existing task if present
            self.remove_task()
            
            # Create new task using schtasks
            # /SC DAILY = daily schedule
            # /TN = task name
            # /TR = task to run
            # /ST = start time
            schtasks_command = [
                "schtasks",
                "/Create",
                "/SC", "DAILY",
                "/TN", self.TASK_NAME,
                "/TR", command,
                "/ST", time,
                "/F"  # Force create (overwrite if exists)
            ]
            
            result = subprocess.run(
                schtasks_command,
                capture_output=True,
                text=True,
                check=False
            )
            
            return result.returncode == 0
            
        except (ValueError, subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def remove_task(self) -> bool:
        """
        Remove the TalkBut scheduled task.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            result = subprocess.run(
                ["schtasks", "/Delete", "/TN", self.TASK_NAME, "/F"],
                capture_output=True,
                text=True,
                check=False
            )
            
            # Success if task was deleted or didn't exist
            return result.returncode == 0 or "cannot find" in result.stderr.lower()
            
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def task_exists(self) -> bool:
        """
        Check if the TalkBut scheduled task exists.
        
        Returns:
            True if task exists, False otherwise
        """
        try:
            result = subprocess.run(
                ["schtasks", "/Query", "/TN", self.TASK_NAME],
                capture_output=True,
                text=True,
                check=False
            )
            
            return result.returncode == 0
            
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def get_next_run(self) -> Optional[datetime]:
        """
        Get the next run time from the scheduled task.
        
        Returns:
            Next run datetime, or None if no task exists
        """
        try:
            # Query task with verbose output to get next run time
            result = subprocess.run(
                ["schtasks", "/Query", "/TN", self.TASK_NAME, "/V", "/FO", "LIST"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                return None
            
            # Parse output to find "Next Run Time"
            for line in result.stdout.split("\n"):
                if "Next Run Time:" in line:
                    # Extract datetime string
                    time_str = line.split(":", 1)[1].strip()
                    
                    # Handle various datetime formats
                    # Common format: "12/4/2025 6:00:00 PM"
                    try:
                        # Try parsing with different formats
                        for fmt in [
                            "%m/%d/%Y %I:%M:%S %p",  # 12/4/2025 6:00:00 PM
                            "%d/%m/%Y %H:%M:%S",      # 04/12/2025 18:00:00
                            "%Y-%m-%d %H:%M:%S",      # 2025-12-04 18:00:00
                        ]:
                            try:
                                return datetime.strptime(time_str, fmt)
                            except ValueError:
                                continue
                    except Exception:
                        pass
            
            # Fallback: calculate next run from task schedule
            # Look for "Start Time:" in the output
            for line in result.stdout.split("\n"):
                if "Start Time:" in line:
                    time_str = line.split(":", 1)[1].strip()
                    # Parse time (format: HH:MM:SS or HH:MM)
                    match = re.match(r"(\d{1,2}):(\d{2})", time_str)
                    if match:
                        hour = int(match.group(1))
                        minute = int(match.group(2))
                        
                        now = datetime.now()
                        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                        
                        # If time has passed today, schedule for tomorrow
                        if next_run <= now:
                            next_run += timedelta(days=1)
                        
                        return next_run
            
            return None
            
        except (subprocess.SubprocessError, FileNotFoundError):
            return None
