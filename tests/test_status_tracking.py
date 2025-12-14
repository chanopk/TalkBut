"""Tests for status tracking and error logging functionality."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from src.talkbut.scheduling.status_manager import StatusManager
from src.talkbut.scheduling.error_logger import log_error
from src.talkbut.scheduling.status_display import format_status_display
from src.talkbut.scheduling.scheduler_manager import SchedulerManager


class TestStatusManager:
    """Tests for StatusManager class."""
    
    def test_status_manager_initialization(self):
        """Test StatusManager creates status file on initialization."""
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            manager = StatusManager(status_file)
            
            assert status_file.exists()
            
            # Check file structure
            with open(status_file, 'r') as f:
                data = json.load(f)
                assert "last_run" in data
                assert "errors" in data
                assert data["last_run"] is None
                assert data["errors"] == []
    
    def test_record_successful_run(self):
        """Test recording a successful run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            manager = StatusManager(status_file)
            
            manager.record_run(success=True)
            
            last_run = manager.get_last_run()
            assert last_run is not None
            assert isinstance(last_run, datetime)
    
    def test_record_failed_run(self):
        """Test recording a failed run."""
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            manager = StatusManager(status_file)
            
            manager.record_run(success=False, error="Test error", date_attempted="2025-12-01")
            
            errors = manager.get_recent_errors(limit=1)
            assert len(errors) == 1
            assert errors[0].error_message == "Test error"
            assert errors[0].date_attempted == "2025-12-01"
    
    def test_bounded_error_history(self):
        """Test that error history is bounded."""
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            manager = StatusManager(status_file, max_errors=5)
            
            # Record 10 errors
            for i in range(10):
                manager.record_run(success=False, error=f"Error {i}")
            
            # Should only keep the last 5
            errors = manager.get_recent_errors(limit=10)
            assert len(errors) == 5
            assert errors[0].error_message == "Error 9"  # Most recent first
            assert errors[4].error_message == "Error 5"  # Oldest kept
    
    def test_clear_errors(self):
        """Test clearing error history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            manager = StatusManager(status_file)
            
            # Record some errors
            manager.record_run(success=False, error="Error 1")
            manager.record_run(success=False, error="Error 2")
            
            # Clear errors
            manager.clear_errors()
            
            errors = manager.get_recent_errors()
            assert len(errors) == 0


class TestErrorLogger:
    """Tests for error logging functionality."""
    
    def test_log_error_creates_file(self):
        """Test that log_error creates the log file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            error_log = Path(tmpdir) / "errors.log"
            
            log_error(error_log, "Test error")
            
            assert error_log.exists()
    
    def test_log_error_format(self):
        """Test that error log entries have correct format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            error_log = Path(tmpdir) / "errors.log"
            
            log_error(error_log, "Test error message")
            
            with open(error_log, 'r') as f:
                content = f.read()
                assert "Test error message" in content
                assert "[" in content  # Timestamp bracket
                assert "]" in content
    
    def test_log_error_with_date(self):
        """Test error logging with date_attempted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            error_log = Path(tmpdir) / "errors.log"
            
            log_error(error_log, "Test error", date_attempted="2025-12-01")
            
            with open(error_log, 'r') as f:
                content = f.read()
                assert "Test error" in content
                assert "2025-12-01" in content
    
    def test_log_error_appends(self):
        """Test that log_error appends to existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            error_log = Path(tmpdir) / "errors.log"
            
            log_error(error_log, "Error 1")
            log_error(error_log, "Error 2")
            
            with open(error_log, 'r') as f:
                content = f.read()
                assert "Error 1" in content
                assert "Error 2" in content


class TestStatusDisplay:
    """Tests for status display functionality."""
    
    def test_format_status_display_basic(self):
        """Test basic status display formatting."""
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            status_manager = StatusManager(status_file)
            scheduler_manager = SchedulerManager()
            
            status_text = format_status_display(scheduler_manager, status_manager)
            
            assert "Automated Daily Logging Status" in status_text
            assert "Platform:" in status_text
            assert "Status:" in status_text
    
    def test_format_status_display_with_errors(self):
        """Test status display with error history."""
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            status_manager = StatusManager(status_file)
            
            # Record an error
            status_manager.record_run(success=False, error="Test error")
            
            scheduler_manager = SchedulerManager()
            status_text = format_status_display(scheduler_manager, status_manager)
            
            assert "Recent Errors:" in status_text
            assert "Test error" in status_text
    
    def test_format_status_display_no_errors(self):
        """Test status display with no errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            status_manager = StatusManager(status_file)
            scheduler_manager = SchedulerManager()
            
            status_text = format_status_display(scheduler_manager, status_manager)
            
            assert "Recent Errors: None" in status_text
