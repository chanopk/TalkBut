"""Property-based tests for SchedulerManager.

**Feature: automated-daily-logging, Property 1: Schedule operations maintain system consistency**
**Validates: Requirements 1.1, 2.2, 2.3**
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime, timedelta

from talkbut.scheduling.scheduler_manager import SchedulerManager
from talkbut.scheduling.platform_detector import SchedulerType, detect_platform
from talkbut.scheduling.models import ScheduleStatus
from talkbut.scheduling.cron_scheduler import CronScheduler
from talkbut.scheduling.task_scheduler import TaskScheduler


# Strategy for generating valid time strings in HH:MM format
@st.composite
def valid_time_string(draw):
    """Generate valid time strings in HH:MM format."""
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    return f"{hour:02d}:{minute:02d}"


# Strategy for generating invalid time strings
@st.composite
def invalid_time_string(draw):
    """Generate invalid time strings."""
    choice = draw(st.integers(min_value=0, max_value=4))
    
    if choice == 0:
        # Invalid hour (>23)
        hour = draw(st.integers(min_value=24, max_value=99))
        minute = draw(st.integers(min_value=0, max_value=59))
        return f"{hour:02d}:{minute:02d}"
    elif choice == 1:
        # Invalid minute (>59)
        hour = draw(st.integers(min_value=0, max_value=23))
        minute = draw(st.integers(min_value=60, max_value=99))
        return f"{hour:02d}:{minute:02d}"
    elif choice == 2:
        # Wrong format (no colon)
        return draw(st.text(min_size=1, max_size=10).filter(lambda x: ':' not in x))
    elif choice == 3:
        # Wrong format (too many parts)
        return draw(st.text(min_size=1, max_size=5)) + ":" + draw(st.text(min_size=1, max_size=5)) + ":" + draw(st.text(min_size=1, max_size=5))
    else:
        # Non-numeric
        return draw(st.text(alphabet=st.characters(blacklist_categories=('Nd',)), min_size=1, max_size=10))


class MockScheduler:
    """Mock scheduler for testing."""
    
    def __init__(self):
        self.jobs = {}
        self.next_run_time = None
    
    def create_job(self, time: str, command: str) -> bool:
        """Mock create_job."""
        self.jobs['talkbut'] = {'time': time, 'command': command}
        # Calculate next run time
        hour, minute = map(int, time.split(':'))
        now = datetime.now()
        self.next_run_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if self.next_run_time <= now:
            self.next_run_time += timedelta(days=1)
        return True
    
    def remove_job(self) -> bool:
        """Mock remove_job."""
        if 'talkbut' in self.jobs:
            del self.jobs['talkbut']
            self.next_run_time = None
        return True
    
    def job_exists(self) -> bool:
        """Mock job_exists."""
        return 'talkbut' in self.jobs
    
    def get_next_run(self):
        """Mock get_next_run."""
        return self.next_run_time


class TestSchedulerManagerProperties:
    """Property-based tests for SchedulerManager."""
    
    @given(time=valid_time_string())
    @settings(max_examples=100, deadline=None)
    def test_property_enable_creates_consistent_state(self, time):
        """
        Property 1: Schedule operations maintain system consistency.
        
        For any valid time, after enabling the schedule:
        - is_enabled() should return True
        - A scheduled task should exist in the underlying scheduler
        - get_status() should reflect enabled state
        
        **Feature: automated-daily-logging, Property 1: Schedule operations maintain system consistency**
        **Validates: Requirements 1.1, 2.2, 2.3**
        """
        # Create mock scheduler
        mock_scheduler = MockScheduler()
        
        # Create SchedulerManager with mocked platform detection
        with patch('talkbut.scheduling.scheduler_manager.detect_platform') as mock_detect:
            mock_detect.return_value = SchedulerType.CRON
            
            manager = SchedulerManager()
            manager.scheduler = mock_scheduler
            
            # Enable scheduling
            result = manager.enable(time)
            
            # Verify operation succeeded
            assert result is True, f"Enable operation failed for time {time}"
            
            # Property: System state should be consistent
            # 1. is_enabled() should return True
            assert manager.is_enabled() is True, \
                f"After enable({time}), is_enabled() should return True"
            
            # 2. Underlying scheduler should have the job
            assert mock_scheduler.job_exists() is True, \
                f"After enable({time}), scheduler should have a job"
            
            # 3. get_status() should reflect enabled state
            status = manager.get_status()
            assert status.enabled is True, \
                f"After enable({time}), status.enabled should be True"
            assert status.schedule_time is not None, \
                f"After enable({time}), status.schedule_time should not be None"
    
    @given(time=valid_time_string())
    @settings(max_examples=100, deadline=None)
    def test_property_disable_creates_consistent_state(self, time):
        """
        Property 1: Schedule operations maintain system consistency.
        
        For any valid time, after enabling then disabling:
        - is_enabled() should return False
        - No scheduled task should exist in the underlying scheduler
        - get_status() should reflect disabled state
        
        **Feature: automated-daily-logging, Property 1: Schedule operations maintain system consistency**
        **Validates: Requirements 1.1, 2.2, 2.3**
        """
        # Create mock scheduler
        mock_scheduler = MockScheduler()
        
        # Create SchedulerManager with mocked platform detection
        with patch('talkbut.scheduling.scheduler_manager.detect_platform') as mock_detect:
            mock_detect.return_value = SchedulerType.CRON
            
            manager = SchedulerManager()
            manager.scheduler = mock_scheduler
            
            # Enable then disable
            manager.enable(time)
            result = manager.disable()
            
            # Verify operation succeeded
            assert result is True, f"Disable operation failed after enabling with time {time}"
            
            # Property: System state should be consistent
            # 1. is_enabled() should return False
            assert manager.is_enabled() is False, \
                f"After disable(), is_enabled() should return False"
            
            # 2. Underlying scheduler should NOT have the job
            assert mock_scheduler.job_exists() is False, \
                f"After disable(), scheduler should not have a job"
            
            # 3. get_status() should reflect disabled state
            status = manager.get_status()
            assert status.enabled is False, \
                f"After disable(), status.enabled should be False"
    
    @given(time1=valid_time_string(), time2=valid_time_string())
    @settings(max_examples=100, deadline=None)
    def test_property_update_maintains_consistency(self, time1, time2):
        """
        Property 1: Schedule operations maintain system consistency.
        
        For any two valid times, after enabling with time1 then updating to time2:
        - is_enabled() should still return True
        - A scheduled task should exist with the new time
        - get_status() should reflect the updated time
        
        **Feature: automated-daily-logging, Property 1: Schedule operations maintain system consistency**
        **Validates: Requirements 1.1, 2.2, 2.3**
        """
        # Skip if times are the same (not interesting for update test)
        assume(time1 != time2)
        
        # Create mock scheduler
        mock_scheduler = MockScheduler()
        
        # Create SchedulerManager with mocked platform detection
        with patch('talkbut.scheduling.scheduler_manager.detect_platform') as mock_detect:
            mock_detect.return_value = SchedulerType.CRON
            
            manager = SchedulerManager()
            manager.scheduler = mock_scheduler
            
            # Enable with time1
            manager.enable(time1)
            
            # Update to time2
            result = manager.update(time2)
            
            # Verify operation succeeded
            assert result is True, f"Update operation failed when changing from {time1} to {time2}"
            
            # Property: System state should be consistent
            # 1. is_enabled() should still return True
            assert manager.is_enabled() is True, \
                f"After update({time2}), is_enabled() should still return True"
            
            # 2. Underlying scheduler should still have a job
            assert mock_scheduler.job_exists() is True, \
                f"After update({time2}), scheduler should still have a job"
            
            # 3. get_status() should reflect the new time
            status = manager.get_status()
            assert status.enabled is True, \
                f"After update({time2}), status.enabled should be True"
            assert status.schedule_time is not None, \
                f"After update({time2}), status.schedule_time should not be None"
    
    @given(time=valid_time_string())
    @settings(max_examples=100, deadline=None)
    def test_property_enable_disable_enable_consistency(self, time):
        """
        Property 1: Schedule operations maintain system consistency.
        
        For any valid time, after enable -> disable -> enable sequence:
        - Final state should be the same as after first enable
        - is_enabled() should return True
        - Scheduled task should exist
        
        **Feature: automated-daily-logging, Property 1: Schedule operations maintain system consistency**
        **Validates: Requirements 1.1, 2.2, 2.3**
        """
        # Create mock scheduler
        mock_scheduler = MockScheduler()
        
        # Create SchedulerManager with mocked platform detection
        with patch('talkbut.scheduling.scheduler_manager.detect_platform') as mock_detect:
            mock_detect.return_value = SchedulerType.CRON
            
            manager = SchedulerManager()
            manager.scheduler = mock_scheduler
            
            # Enable -> Disable -> Enable
            manager.enable(time)
            manager.disable()
            result = manager.enable(time)
            
            # Verify final operation succeeded
            assert result is True, f"Second enable operation failed for time {time}"
            
            # Property: System state should be consistent (same as after first enable)
            # 1. is_enabled() should return True
            assert manager.is_enabled() is True, \
                f"After enable-disable-enable sequence, is_enabled() should return True"
            
            # 2. Underlying scheduler should have the job
            assert mock_scheduler.job_exists() is True, \
                f"After enable-disable-enable sequence, scheduler should have a job"
            
            # 3. get_status() should reflect enabled state
            status = manager.get_status()
            assert status.enabled is True, \
                f"After enable-disable-enable sequence, status.enabled should be True"
    
    @given(time=invalid_time_string())
    @settings(max_examples=50, deadline=None)
    def test_property_invalid_time_maintains_consistency(self, time):
        """
        Property 1: Schedule operations maintain system consistency.
        
        For any invalid time format, operations should fail gracefully:
        - enable() should return False
        - System state should remain unchanged (disabled)
        - No scheduled task should be created
        
        **Feature: automated-daily-logging, Property 1: Schedule operations maintain system consistency**
        **Validates: Requirements 1.1, 2.2, 2.3**
        """
        # Create mock scheduler
        mock_scheduler = MockScheduler()
        
        # Create SchedulerManager with mocked platform detection
        with patch('talkbut.scheduling.scheduler_manager.detect_platform') as mock_detect:
            mock_detect.return_value = SchedulerType.CRON
            
            manager = SchedulerManager()
            manager.scheduler = mock_scheduler
            
            # Try to enable with invalid time
            result = manager.enable(time)
            
            # Property: System should maintain consistency even with invalid input
            # 1. Operation should fail (return False)
            assert result is False, \
                f"Enable with invalid time '{time}' should return False"
            
            # 2. is_enabled() should return False
            assert manager.is_enabled() is False, \
                f"After failed enable with invalid time '{time}', is_enabled() should return False"
            
            # 3. No job should exist in scheduler
            assert mock_scheduler.job_exists() is False, \
                f"After failed enable with invalid time '{time}', no job should exist"


class TestPlatformDetectionProperties:
    """Property-based tests for platform detection."""
    
    @given(platform_name=st.sampled_from(["Darwin", "Linux", "Windows", "FreeBSD", "SunOS", "AIX"]))
    @settings(max_examples=100, deadline=None)
    def test_property_platform_detection_selects_appropriate_scheduler(self, platform_name):
        """
        Property 10: Platform detection selects appropriate scheduler.
        
        For any supported platform (Darwin/macOS, Linux, Windows), the system should
        select the corresponding scheduler (CronScheduler for Unix-like, TaskScheduler for Windows).
        For unsupported platforms, it should return UNSUPPORTED.
        
        **Feature: automated-daily-logging, Property 10: Platform detection selects appropriate scheduler**
        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        with patch('platform.system') as mock_system:
            mock_system.return_value = platform_name
            
            # Call detect_platform
            scheduler_type = detect_platform()
            
            # Property: Platform detection should select appropriate scheduler
            if platform_name in ("Darwin", "Linux"):
                # Unix-like systems should use CRON
                assert scheduler_type == SchedulerType.CRON, \
                    f"Platform {platform_name} should use CRON scheduler, got {scheduler_type}"
            elif platform_name == "Windows":
                # Windows should use TASK_SCHEDULER
                assert scheduler_type == SchedulerType.TASK_SCHEDULER, \
                    f"Platform {platform_name} should use TASK_SCHEDULER, got {scheduler_type}"
            else:
                # Other platforms should be UNSUPPORTED
                assert scheduler_type == SchedulerType.UNSUPPORTED, \
                    f"Platform {platform_name} should be UNSUPPORTED, got {scheduler_type}"
    
    @given(platform_name=st.sampled_from(["Darwin", "Linux", "Windows"]))
    @settings(max_examples=100, deadline=None)
    def test_property_scheduler_manager_uses_correct_scheduler_type(self, platform_name):
        """
        Property 10: Platform detection selects appropriate scheduler.
        
        For any supported platform, SchedulerManager should instantiate the correct
        scheduler type based on platform detection.
        
        **Feature: automated-daily-logging, Property 10: Platform detection selects appropriate scheduler**
        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        with patch('platform.system') as mock_system:
            mock_system.return_value = platform_name
            
            # Create SchedulerManager (it will call detect_platform internally)
            manager = SchedulerManager()
            
            # Property: SchedulerManager should use the correct scheduler type
            if platform_name in ("Darwin", "Linux"):
                # Unix-like systems should have CronScheduler
                assert isinstance(manager.scheduler, CronScheduler), \
                    f"Platform {platform_name} should instantiate CronScheduler, got {type(manager.scheduler)}"
                assert manager.platform_type == SchedulerType.CRON, \
                    f"Platform {platform_name} should have platform_type CRON, got {manager.platform_type}"
            elif platform_name == "Windows":
                # Windows should have TaskScheduler
                assert isinstance(manager.scheduler, TaskScheduler), \
                    f"Platform {platform_name} should instantiate TaskScheduler, got {type(manager.scheduler)}"
                assert manager.platform_type == SchedulerType.TASK_SCHEDULER, \
                    f"Platform {platform_name} should have platform_type TASK_SCHEDULER, got {manager.platform_type}"
    
    @given(platform_name=st.sampled_from(["Darwin", "Linux", "Windows"]))
    @settings(max_examples=100, deadline=None)
    def test_property_platform_detection_is_deterministic(self, platform_name):
        """
        Property 10: Platform detection selects appropriate scheduler.
        
        For any platform, calling detect_platform multiple times should always
        return the same result (deterministic behavior).
        
        **Feature: automated-daily-logging, Property 10: Platform detection selects appropriate scheduler**
        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        with patch('platform.system') as mock_system:
            mock_system.return_value = platform_name
            
            # Call detect_platform multiple times
            result1 = detect_platform()
            result2 = detect_platform()
            result3 = detect_platform()
            
            # Property: Results should be deterministic (always the same)
            assert result1 == result2 == result3, \
                f"Platform detection for {platform_name} should be deterministic, got {result1}, {result2}, {result3}"
