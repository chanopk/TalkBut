"""CronScheduler implementation for Unix-like systems (macOS, Linux)."""

import subprocess
from datetime import datetime, timedelta
from typing import Optional


class CronScheduler:
    """Scheduler implementation using cron for Unix-like systems."""
    
    TALKBUT_MARKER = "# TalkBut automated daily logging"
    
    def __init__(self):
        """Initialize CronScheduler."""
        pass
    
    def create_job(self, time: str, command: str) -> bool:
        """
        Create a cron job for the specified time and command.
        
        Args:
            time: Time in HH:MM format (24-hour)
            command: Command to execute (should include config path if needed)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Parse time
            hour, minute = time.split(":")
            hour = int(hour)
            minute = int(minute)
            
            # Validate time
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                return False
            
            # Generate cron expression: minute hour * * * command
            cron_line = f"{minute} {hour} * * * {command} {self.TALKBUT_MARKER}\n"
            
            # Get current crontab
            try:
                result = subprocess.run(
                    ["crontab", "-l"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                current_crontab = result.stdout if result.returncode == 0 else ""
            except FileNotFoundError:
                return False
            
            # Remove existing TalkBut job if present
            lines = current_crontab.split("\n")
            filtered_lines = [line for line in lines if self.TALKBUT_MARKER not in line]
            
            # Add new job
            new_crontab = "\n".join(filtered_lines).strip()
            if new_crontab:
                new_crontab += "\n"
            new_crontab += cron_line
            
            # Write new crontab
            process = subprocess.Popen(
                ["crontab", "-"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=new_crontab)
            
            return process.returncode == 0
            
        except (ValueError, subprocess.SubprocessError):
            return False
    
    def remove_job(self) -> bool:
        """
        Remove the TalkBut cron job.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get current crontab
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                # No crontab exists, nothing to remove
                return True
            
            current_crontab = result.stdout
            
            # Remove TalkBut job
            lines = current_crontab.split("\n")
            filtered_lines = [line for line in lines if self.TALKBUT_MARKER not in line]
            new_crontab = "\n".join(filtered_lines).strip()
            
            # Write new crontab (or remove if empty)
            if new_crontab:
                new_crontab += "\n"
                process = subprocess.Popen(
                    ["crontab", "-"],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                stdout, stderr = process.communicate(input=new_crontab)
                return process.returncode == 0
            else:
                # Remove crontab entirely if empty
                result = subprocess.run(
                    ["crontab", "-r"],
                    capture_output=True,
                    check=False
                )
                return True  # Success even if no crontab existed
                
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def job_exists(self) -> bool:
        """
        Check if a TalkBut cron job exists.
        
        Returns:
            True if job exists, False otherwise
        """
        try:
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                return False
            
            return self.TALKBUT_MARKER in result.stdout
            
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def get_next_run(self) -> Optional[datetime]:
        """
        Calculate the next run time from the cron expression.
        
        Returns:
            Next run datetime, or None if no job exists
        """
        try:
            # Get current crontab
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode != 0:
                return None
            
            # Find TalkBut job line
            for line in result.stdout.split("\n"):
                if self.TALKBUT_MARKER in line:
                    # Parse cron expression: minute hour * * * command
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            minute = int(parts[0])
                            hour = int(parts[1])
                            
                            # Calculate next run time
                            now = datetime.now()
                            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                            
                            # If the time has passed today, schedule for tomorrow
                            if next_run <= now:
                                next_run += timedelta(days=1)
                            
                            return next_run
                        except (ValueError, IndexError):
                            return None
            
            return None
            
        except (subprocess.SubprocessError, FileNotFoundError):
            return None
