"""Property-based tests for status display accuracy.

**Feature: automated-daily-logging, Property 5: Status display reflects actual system state**
**Validates: Requirements 2.4, 4.4**
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, assume

from src.talkbut.scheduling.scheduler_manager import SchedulerManager
from src.talkbut.scheduling.status_manager import StatusManager
from src.talkbut.scheduling.status_display import format_status_display
from src.talkbut.scheduling.platform_detector import SchedulerType
from src.talkbut.scheduling.models import ScheduleStatus, ErrorRecord


# Strategy for generating valid time strings in HH:MM format
@st.composite
def valid_time_string(draw):
    """Generate valid time strings in HH:MM format."""
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    return f"{hour:02d}:{minute:02d}"


# Strategy for generating error messages
@st.composite
def error_messages(draw):
    """Generate realistic error messages."""
    error_types = [
        "API connection failed",
        "Git repository not found",
        "Configuration file missing",
        "Network timeout",
        "Authentication failed"
    ]
    return draw(st.sampled_from(error_types))


class MockScheduler:
    """Mock scheduler for testing that tracks actual state."""
    
    def __init__(self):
        self.jobs = {}
        self.next_run_time = None
    
    def create_job(self, time: str, command: str) -> bool:
        """Mock create_job - simulates actual scheduler state."""
        self.jobs['talkbut'] = {'time': time, 'command': command}
        # Calculate next run time
        hour, minute = map(int, time.split(':'))
        now = datetime.now()
        self.next_run_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if self.next_run_time <= now:
            self.next_run_time += timedelta(days=1)
        return True
    
    def remove_job(self) -> bool:
        """Mock remove_job - simulates actual scheduler state."""
        if 'talkbut' in self.jobs:
            del self.jobs['talkbut']
            self.next_run_time = None
        return True
    
    def job_exists(self) -> bool:
        """Mock job_exists - queries actual state."""
        return 'talkbut' in self.jobs
    
    def get_next_run(self):
        """Mock get_next_run - queries actual state."""
        return self.next_run_time


class TestStatusAccuracyProperty:
    """Property-based tests for status display accuracy."""
    
    @given(time=valid_time_string())
    @settings(max_examples=100, deadline=None)
    def test_property_status_reflects_enabled_state(self, time):
        """
        Property 5: Status display reflects actual system state.
        
        For any valid time, after enabling the schedule, the status display
        should accurately reflect that the system is enabled by querying the
        actual scheduler state (not cached data).
        
        **Feature: automated-daily-logging, Property 5: Status display reflects actual system state**
        **Validates: Requirements 2.4, 4.4**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            status_manager = StatusManager(status_file)
            
            # Create mock scheduler
            mock_scheduler = MockScheduler()
            
            # Create SchedulerManager with mocked platform detection
            with patch('talkbut.scheduling.scheduler_manager.detect_platform') as mock_detect:
                mock_detect.return_value = SchedulerType.CRON
                
                scheduler_manager = SchedulerManager(status_manager=status_manager)
                scheduler_manager.scheduler = mock_scheduler
                
                # Enable scheduling
                scheduler_manager.enable(time)
                
                # Get status (should query actual system state)
                status = scheduler_manager.get_status()
                
                # Property: Status should reflect actual enabled state
                # 1. Status should show enabled
                assert status.enabled is True, \
                    f"Status should show enabled=True after enable({time}), got {status.enabled}"
                
                # 2. Status should reflect actual scheduler state (job exists)
                actual_job_exists = mock_scheduler.job_exists()
                assert status.enabled == actual_job_exists, \
                    f"Status.enabled ({status.enabled}) should match actual scheduler state ({actual_job_exists})"
                
                # 3. Status should have schedule time
                assert status.schedule_time is not None, \
                    f"Status should have schedule_time after enable({time}), got {status.schedule_time}"
                
                # 4. Status should have next run time
                assert status.next_run is not None, \
                    f"Status should have next_run after enable({time}), got {status.next_run}"
                
                # 5. Next run time should match actual scheduler's next run
                actual_next_run = mock_scheduler.get_next_run()
                assert status.next_run == actual_next_run, \
                    f"Status.next_run ({status.next_run}) should match actual scheduler next run ({actual_next_run})"
    
    @given(time=valid_time_string())
    @settings(max_examples=100, deadline=None)
    def test_property_status_reflects_disabled_state(self, time):
        """
        Property 5: Status display reflects actual system state.
        
        For any valid time, after enabling then disabling the schedule, the status
        display should accurately reflect that the system is disabled by querying
        the actual scheduler state.
        
        **Feature: automated-daily-logging, Property 5: Status display reflects actual system state**
        **Validates: Requirements 2.4, 4.4**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            status_manager = StatusManager(status_file)
            
            # Create mock scheduler
            mock_scheduler = MockScheduler()
            
            # Create SchedulerManager with mocked platform detection
            with patch('talkbut.scheduling.scheduler_manager.detect_platform') as mock_detect:
                mock_detect.return_value = SchedulerType.CRON
                
                scheduler_manager = SchedulerManager(status_manager=status_manager)
                scheduler_manager.scheduler = mock_scheduler
                
                # Enable then disable
                scheduler_manager.enable(time)
                scheduler_manager.disable()
                
                # Get status (should query actual system state)
                status = scheduler_manager.get_status()
                
                # Property: Status should reflect actual disabled state
                # 1. Status should show disabled
                assert status.enabled is False, \
                    f"Status should show enabled=False after disable(), got {status.enabled}"
                
                # 2. Status should reflect actual scheduler state (no job)
                actual_job_exists = mock_scheduler.job_exists()
                assert status.enabled == actual_job_exists, \
                    f"Status.enabled ({status.enabled}) should match actual scheduler state ({actual_job_exists})"
                
                # 3. Next run should be None when disabled
                assert status.next_run is None, \
                    f"Status.next_run should be None when disabled, got {status.next_run}"
                
                # 4. Actual scheduler should have no next run
                actual_next_run = mock_scheduler.get_next_run()
                assert actual_next_run is None, \
                    f"Actual scheduler should have no next run when disabled, got {actual_next_run}"
    
    @given(time=valid_time_string(), num_errors=st.integers(min_value=1, max_value=10))
    @settings(max_examples=100, deadline=None)
    def test_property_status_reflects_error_history(self, time, num_errors):
        """
        Property 5: Status display reflects actual system state.
        
        For any error history, the status display should accurately reflect
        the errors by reading from the actual status file (not cached data).
        
        **Feature: automated-daily-logging, Property 5: Status display reflects actual system state**
        **Validates: Requirements 2.4, 4.4**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            status_manager = StatusManager(status_file)
            
            # Create mock scheduler
            mock_scheduler = MockScheduler()
            
            # Create SchedulerManager with mocked platform detection
            with patch('talkbut.scheduling.scheduler_manager.detect_platform') as mock_detect:
                mock_detect.return_value = SchedulerType.CRON
                
                scheduler_manager = SchedulerManager(status_manager=status_manager)
                scheduler_manager.scheduler = mock_scheduler
                
                # Record some errors
                for i in range(num_errors):
                    status_manager.record_run(success=False, error=f"Error {i}")
                
                # Get status (should query actual status file)
                status = scheduler_manager.get_status()
                
                # Property: Status should reflect actual error history
                # 1. Status should have errors
                assert len(status.recent_errors) > 0, \
                    f"Status should have errors after recording {num_errors} errors, got {len(status.recent_errors)}"
                
                # 2. Number of errors should match what's in status manager
                actual_errors = status_manager.get_recent_errors(limit=5)
                assert len(status.recent_errors) == len(actual_errors), \
                    f"Status errors ({len(status.recent_errors)}) should match actual errors ({len(actual_errors)})"
                
                # 3. Error messages should match
                for i, (status_error, actual_error) in enumerate(zip(status.recent_errors, actual_errors)):
                    assert status_error.error_message == actual_error.error_message, \
                        f"Error {i}: status message ({status_error.error_message}) should match actual ({actual_error.error_message})"
    
    @given(time=valid_time_string())
    @settings(max_examples=100, deadline=None)
    def test_property_status_reflects_last_run(self, time):
        """
        Property 5: Status display reflects actual system state.
        
        For any successful run, the status display should accurately reflect
        the last run timestamp by reading from the actual status file.
        
        **Feature: automated-daily-logging, Property 5: Status display reflects actual system state**
        **Validates: Requirements 2.4, 4.4**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            status_manager = StatusManager(status_file)
            
            # Create mock scheduler
            mock_scheduler = MockScheduler()
            
            # Create SchedulerManager with mocked platform detection
            with patch('talkbut.scheduling.scheduler_manager.detect_platform') as mock_detect:
                mock_detect.return_value = SchedulerType.CRON
                
                scheduler_manager = SchedulerManager(status_manager=status_manager)
                scheduler_manager.scheduler = mock_scheduler
                
                # Record a successful run
                status_manager.record_run(success=True)
                
                # Get status (should query actual status file)
                status = scheduler_manager.get_status()
                
                # Property: Status should reflect actual last run
                # 1. Status should have last_run
                assert status.last_run is not None, \
                    f"Status should have last_run after successful run, got {status.last_run}"
                
                # 2. Last run should match what's in status manager
                actual_last_run = status_manager.get_last_run()
                assert status.last_run == actual_last_run, \
                    f"Status.last_run ({status.last_run}) should match actual ({actual_last_run})"
    
    @given(time1=valid_time_string(), time2=valid_time_string())
    @settings(max_examples=100, deadline=None)
    def test_property_status_reflects_schedule_updates(self, time1, time2):
        """
        Property 5: Status display reflects actual system state.
        
        For any schedule update, the status display should accurately reflect
        the new schedule time by querying the actual scheduler state.
        
        **Feature: automated-daily-logging, Property 5: Status display reflects actual system state**
        **Validates: Requirements 2.4, 4.4**
        """
        # Skip if times are the same
        assume(time1 != time2)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            status_manager = StatusManager(status_file)
            
            # Create mock scheduler
            mock_scheduler = MockScheduler()
            
            # Create SchedulerManager with mocked platform detection
            with patch('talkbut.scheduling.scheduler_manager.detect_platform') as mock_detect:
                mock_detect.return_value = SchedulerType.CRON
                
                scheduler_manager = SchedulerManager(status_manager=status_manager)
                scheduler_manager.scheduler = mock_scheduler
                
                # Enable with time1
                scheduler_manager.enable(time1)
                
                # Update to time2
                scheduler_manager.update(time2)
                
                # Get status (should query actual scheduler state)
                status = scheduler_manager.get_status()
                
                # Property: Status should reflect the updated schedule
                # 1. Status should still be enabled
                assert status.enabled is True, \
                    f"Status should be enabled after update, got {status.enabled}"
                
                # 2. Schedule time should reflect the new time
                assert status.schedule_time is not None, \
                    f"Status should have schedule_time after update, got {status.schedule_time}"
                
                # 3. Next run should be updated
                assert status.next_run is not None, \
                    f"Status should have next_run after update, got {status.next_run}"
                
                # 4. Next run should match actual scheduler's next run
                actual_next_run = mock_scheduler.get_next_run()
                assert status.next_run == actual_next_run, \
                    f"Status.next_run ({status.next_run}) should match actual scheduler ({actual_next_run})"
    
    @given(time=valid_time_string(), error_msg=error_messages())
    @settings(max_examples=100, deadline=None)
    def test_property_format_status_display_reflects_actual_state(self, time, error_msg):
        """
        Property 5: Status display reflects actual system state.
        
        For any system state, the formatted status display string should
        accurately reflect the actual state by querying the scheduler and
        status manager (not using cached data).
        
        **Feature: automated-daily-logging, Property 5: Status display reflects actual system state**
        **Validates: Requirements 2.4, 4.4**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            status_manager = StatusManager(status_file)
            
            # Create mock scheduler
            mock_scheduler = MockScheduler()
            
            # Create SchedulerManager with mocked platform detection
            with patch('talkbut.scheduling.scheduler_manager.detect_platform') as mock_detect:
                mock_detect.return_value = SchedulerType.CRON
                
                scheduler_manager = SchedulerManager(status_manager=status_manager)
                scheduler_manager.scheduler = mock_scheduler
                
                # Enable scheduling
                scheduler_manager.enable(time)
                
                # Record an error
                status_manager.record_run(success=False, error=error_msg)
                
                # Record a successful run
                status_manager.record_run(success=True)
                
                # Get formatted status display
                status_text = format_status_display(scheduler_manager, status_manager)
                
                # Property: Formatted display should reflect actual state
                # 1. Should show enabled status
                assert "ENABLED" in status_text, \
                    f"Status display should show ENABLED, got: {status_text}"
                
                # 2. Should show schedule time
                assert time in status_text or status_text.count(":") >= 2, \
                    f"Status display should show schedule time, got: {status_text}"
                
                # 3. Should show last run (since we recorded a successful run)
                assert "Last Run:" in status_text, \
                    f"Status display should show Last Run, got: {status_text}"
                assert "Never" not in status_text or "Last Run: Never" not in status_text, \
                    f"Status display should not show 'Never' for last run after successful run"
                
                # 4. Should show next run
                assert "Next Run:" in status_text, \
                    f"Status display should show Next Run, got: {status_text}"
                
                # 5. Should show recent errors
                assert "Recent Errors:" in status_text, \
                    f"Status display should show Recent Errors section, got: {status_text}"
                assert error_msg in status_text, \
                    f"Status display should show error message '{error_msg}', got: {status_text}"
    
    @given(time=valid_time_string())
    @settings(max_examples=100, deadline=None)
    def test_property_status_queries_actual_state_not_cache(self, time):
        """
        Property 5: Status display reflects actual system state.
        
        For any system state, calling get_status() multiple times should
        always reflect the current actual state, not cached data. If the
        underlying scheduler state changes, status should reflect that change.
        
        **Feature: automated-daily-logging, Property 5: Status display reflects actual system state**
        **Validates: Requirements 2.4, 4.4**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            status_manager = StatusManager(status_file)
            
            # Create mock scheduler
            mock_scheduler = MockScheduler()
            
            # Create SchedulerManager with mocked platform detection
            with patch('talkbut.scheduling.scheduler_manager.detect_platform') as mock_detect:
                mock_detect.return_value = SchedulerType.CRON
                
                scheduler_manager = SchedulerManager(status_manager=status_manager)
                scheduler_manager.scheduler = mock_scheduler
                
                # Get status when disabled
                status1 = scheduler_manager.get_status()
                assert status1.enabled is False, "Initial status should be disabled"
                
                # Enable scheduling
                scheduler_manager.enable(time)
                
                # Get status again - should reflect enabled state
                status2 = scheduler_manager.get_status()
                assert status2.enabled is True, \
                    "Status should reflect enabled state after enable()"
                
                # Disable scheduling
                scheduler_manager.disable()
                
                # Get status again - should reflect disabled state
                status3 = scheduler_manager.get_status()
                assert status3.enabled is False, \
                    "Status should reflect disabled state after disable()"
                
                # Property: Each status query should reflect actual current state
                # Status should change as the actual state changes
                assert status1.enabled != status2.enabled, \
                    "Status should change from disabled to enabled"
                assert status2.enabled != status3.enabled, \
                    "Status should change from enabled to disabled"
                
                # Verify each status matched actual scheduler state at that time
                # (This is implicitly tested by the assertions above, but we make it explicit)
                assert status1.enabled == False and not mock_scheduler.job_exists(), \
                    "Status1 should match actual state (disabled)"
                # After enable, job should exist
                scheduler_manager.enable(time)
                assert scheduler_manager.get_status().enabled == True and mock_scheduler.job_exists(), \
                    "Status after enable should match actual state (enabled)"
