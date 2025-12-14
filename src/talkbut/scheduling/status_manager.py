"""StatusManager for tracking automated logging status and errors."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from .models import ErrorRecord


class StatusManager:
    """
    Manager for tracking automated logging status and error history.
    
    Maintains a JSON file with run history and error records.
    Implements bounded error history to prevent unbounded growth.
    
    Requirements: 4.3, 6.4
    """
    
    def __init__(self, status_file: Path, max_errors: int = 50):
        """
        Initialize StatusManager.
        
        Args:
            status_file: Path to status JSON file
            max_errors: Maximum number of errors to keep in history (default: 50)
        """
        self.status_file = Path(status_file)
        self.max_errors = max_errors
        self._ensure_status_file()
    
    def _ensure_status_file(self) -> None:
        """Ensure status file exists with valid structure."""
        if not self.status_file.exists():
            # Create parent directory if needed
            self.status_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Initialize with empty structure
            initial_data = {
                "last_run": None,
                "errors": []
            }
            self._write_status(initial_data)
    
    def _read_status(self) -> Dict[str, Any]:
        """
        Read status from file.
        
        Returns:
            Status dictionary
        """
        try:
            with open(self.status_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure required keys exist
                if "last_run" not in data:
                    data["last_run"] = None
                if "errors" not in data:
                    data["errors"] = []
                return data
        except (json.JSONDecodeError, FileNotFoundError):
            # Return default structure if file is corrupted or missing
            return {
                "last_run": None,
                "errors": []
            }
    
    def _write_status(self, data: Dict[str, Any]) -> None:
        """
        Write status to file.
        
        Args:
            data: Status dictionary to write
        """
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
    
    def record_run(self, success: bool, error: Optional[str] = None, date_attempted: Optional[str] = None) -> None:
        """
        Record a run attempt.
        
        Args:
            success: Whether the run was successful
            error: Error message if run failed
            date_attempted: Date that was attempted (for batch processing)
            
        Requirements: 4.3, 6.4
        """
        data = self._read_status()
        
        if success:
            # Update last successful run timestamp
            data["last_run"] = datetime.now().isoformat()
        else:
            # Add error to history
            error_record = {
                "timestamp": datetime.now().isoformat(),
                "error_message": error or "Unknown error",
                "date_attempted": date_attempted
            }
            data["errors"].append(error_record)
            
            # Maintain bounded error history
            if len(data["errors"]) > self.max_errors:
                # Keep only the most recent errors
                data["errors"] = data["errors"][-self.max_errors:]
        
        self._write_status(data)
    
    def get_last_run(self) -> Optional[datetime]:
        """
        Get timestamp of last successful run.
        
        Returns:
            Datetime of last run, or None if never run
            
        Requirements: 4.3
        """
        data = self._read_status()
        last_run_str = data.get("last_run")
        
        if last_run_str:
            try:
                return datetime.fromisoformat(last_run_str)
            except (ValueError, TypeError):
                return None
        
        return None
    
    def get_recent_errors(self, limit: int = 5) -> List[ErrorRecord]:
        """
        Get recent error records.
        
        Args:
            limit: Maximum number of errors to return (default: 5)
            
        Returns:
            List of ErrorRecord objects (most recent first)
            
        Requirements: 6.4
        """
        data = self._read_status()
        errors = data.get("errors", [])
        
        # Get most recent errors (up to limit)
        recent = errors[-limit:] if len(errors) > limit else errors
        
        # Convert to ErrorRecord objects and reverse (most recent first)
        error_records = []
        for err in reversed(recent):
            try:
                error_records.append(ErrorRecord(
                    timestamp=datetime.fromisoformat(err["timestamp"]),
                    error_message=err["error_message"],
                    date_attempted=err.get("date_attempted")
                ))
            except (ValueError, KeyError, TypeError):
                # Skip malformed error records
                continue
        
        return error_records
    
    def clear_errors(self) -> None:
        """
        Clear error history.
        
        Requirements: 6.4
        """
        data = self._read_status()
        data["errors"] = []
        self._write_status(data)
