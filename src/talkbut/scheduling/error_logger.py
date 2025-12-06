"""Error logging functionality for automated daily logging."""

from datetime import datetime
from pathlib import Path
from typing import Optional


def log_error(error_log_path: Path, error_message: str, date_attempted: Optional[str] = None) -> None:
    """
    Write error to log file.
    
    Appends error entry to the error log file with timestamp and message.
    Creates the log file and parent directories if they don't exist.
    
    Args:
        error_log_path: Path to error log file
        error_message: Error message to log
        date_attempted: Optional date that was being processed when error occurred
        
    Requirements: 1.5, 6.1, 6.2
    """
    # Ensure parent directory exists
    error_log_path = Path(error_log_path)
    error_log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Format log entry
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {error_message}"
    
    if date_attempted:
        log_entry += f" (date: {date_attempted})"
    
    log_entry += "\n"
    
    # Append to log file (don't overwrite)
    with open(error_log_path, 'a', encoding='utf-8') as f:
        f.write(log_entry)
