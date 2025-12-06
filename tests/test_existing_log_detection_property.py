"""Property-based tests for existing log detection.

**Feature: automated-daily-logging, Property 7: Existing log detection prevents redundant processing**
**Validates: Requirements 3.2, 3.3**
"""

import pytest
import json
import tempfile
from datetime import date, timedelta
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume

from talkbut.processors.batch_utils import log_exists
from talkbut.processors.batch_processor import BatchProcessor
from talkbut.core.config import ConfigManager


# Strategy for generating valid dates
@st.composite
def valid_date_strategy(draw):
    """Generate valid date objects."""
    year = draw(st.integers(min_value=2020, max_value=2030))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # Safe for all months
    return date(year, month, day)


class TestExistingLogDetectionProperties:
    """Property-based tests for existing log detection."""
    
    @given(log_date=valid_date_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_log_exists_detects_existing_files(self, log_date):
        """
        Property 7: Existing log detection prevents redundant processing.
        
        For any date with an existing log file, log_exists should return True.
        
        **Feature: automated-daily-logging, Property 7: Existing log detection prevents redundant processing**
        **Validates: Requirements 3.2, 3.3**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            
            # Create a log file for the date
            filename = f"daily_log_{log_date.isoformat()}.json"
            log_path = log_dir / filename
            
            # Write a minimal valid log file
            log_data = {
                "date": log_date.isoformat(),
                "summary": "Test log",
                "stats": {"commits": 0, "files": 0, "insertions": 0, "deletions": 0},
                "categories": [],
                "tasks": []
            }
            with open(log_path, 'w') as f:
                json.dump(log_data, f)
            
            # Property: log_exists should return True for existing file
            assert log_exists(log_date, log_dir), \
                f"log_exists should return True for date {log_date} when file exists at {log_path}"
    
    @given(log_date=valid_date_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_log_exists_returns_false_for_missing_files(self, log_date):
        """
        Property 7: Existing log detection prevents redundant processing.
        
        For any date without an existing log file, log_exists should return False.
        
        **Feature: automated-daily-logging, Property 7: Existing log detection prevents redundant processing**
        **Validates: Requirements 3.2, 3.3**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            
            # Don't create any log file
            
            # Property: log_exists should return False for non-existent file
            assert not log_exists(log_date, log_dir), \
                f"log_exists should return False for date {log_date} when file does not exist"
    
    @given(log_date=valid_date_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_batch_processor_skips_existing_logs(self, log_date):
        """
        Property 7: Existing log detection prevents redundant processing.
        
        For any date with an existing log file, batch processing should skip
        that date unless force flag is True.
        
        **Feature: automated-daily-logging, Property 7: Existing log detection prevents redundant processing**
        **Validates: Requirements 3.2, 3.3**
        """
        import os
        import yaml
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            
            # Create a minimal config
            config_data = {
                "storage": {
                    "log_dir": str(log_dir)
                },
                "git": {
                    "author": "Test Author",
                    "repositories": []
                }
            }
            
            # Create config file
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Set environment variable and clear singleton
            original_env = os.environ.get('TALKBUT_CONFIG_PATH')
            try:
                os.environ['TALKBUT_CONFIG_PATH'] = str(config_path)
                ConfigManager._instance = None
                
                config = ConfigManager()
                processor = BatchProcessor(config)
                
                # Create an existing log file
                filename = f"daily_log_{log_date.isoformat()}.json"
                log_path = log_dir / filename
                log_data = {
                    "date": log_date.isoformat(),
                    "summary": "Existing log",
                    "stats": {"commits": 5, "files": 10, "insertions": 100, "deletions": 50},
                    "categories": [],
                    "tasks": []
                }
                with open(log_path, 'w') as f:
                    json.dump(log_data, f)
                
                # Process the single date without force flag
                result = processor._process_single_date(log_date, author=None, force=False)
                
                # Property: Result should indicate the date was skipped
                assert result.skipped, \
                    f"Processing date {log_date} without force should skip when log exists"
                assert not result.success, \
                    f"Skipped processing should not be marked as success"
                assert result.error is None, \
                    f"Skipped processing should not have an error"
            
            finally:
                # Restore environment
                if original_env is not None:
                    os.environ['TALKBUT_CONFIG_PATH'] = original_env
                elif 'TALKBUT_CONFIG_PATH' in os.environ:
                    del os.environ['TALKBUT_CONFIG_PATH']
                ConfigManager._instance = None
    
    @given(log_date=valid_date_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_force_flag_overrides_skip(self, log_date):
        """
        Property 7: Existing log detection prevents redundant processing.
        
        For any date with an existing log file, batch processing with force=True
        should process the date (not skip it).
        
        **Feature: automated-daily-logging, Property 7: Existing log detection prevents redundant processing**
        **Validates: Requirements 3.2, 3.3**
        """
        import os
        import yaml
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            
            # Create a minimal config with a test git repo
            config_data = {
                "storage": {
                    "log_dir": str(log_dir)
                },
                "git": {
                    "author": "Test Author",
                    "repositories": []
                }
            }
            
            # Create config file
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Set environment variable and clear singleton
            original_env = os.environ.get('TALKBUT_CONFIG_PATH')
            try:
                os.environ['TALKBUT_CONFIG_PATH'] = str(config_path)
                ConfigManager._instance = None
                
                config = ConfigManager()
                processor = BatchProcessor(config)
                
                # Create an existing log file
                filename = f"daily_log_{log_date.isoformat()}.json"
                log_path = log_dir / filename
                log_data = {
                    "date": log_date.isoformat(),
                    "summary": "Old log to be replaced",
                    "stats": {"commits": 5, "files": 10, "insertions": 100, "deletions": 50},
                    "categories": [],
                    "tasks": []
                }
                with open(log_path, 'w') as f:
                    json.dump(log_data, f)
                
                # Process the single date WITH force flag
                result = processor._process_single_date(log_date, author=None, force=True)
                
                # Property: Result should NOT be skipped when force=True
                assert not result.skipped, \
                    f"Processing date {log_date} with force=True should not skip even when log exists"
                
                # Property: The processing should attempt to run (success or failure, but not skipped)
                # Since we have no real git repo, it will succeed with empty commits
                assert result.success or result.error is not None, \
                    f"Processing with force=True should either succeed or fail, not skip"
            
            finally:
                # Restore environment
                if original_env is not None:
                    os.environ['TALKBUT_CONFIG_PATH'] = original_env
                elif 'TALKBUT_CONFIG_PATH' in os.environ:
                    del os.environ['TALKBUT_CONFIG_PATH']
                ConfigManager._instance = None
    
    @given(dates=st.lists(valid_date_strategy(), min_size=2, max_size=10, unique=True))
    @settings(max_examples=50, deadline=None)
    def test_property_batch_skips_only_existing_logs(self, dates):
        """
        Property 7: Existing log detection prevents redundant processing.
        
        For any set of dates where some have existing logs and some don't,
        batch processing should skip only the dates with existing logs.
        
        **Feature: automated-daily-logging, Property 7: Existing log detection prevents redundant processing**
        **Validates: Requirements 3.2, 3.3**
        """
        import os
        import yaml
        
        # Sort dates to ensure chronological order
        dates = sorted(dates)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            
            # Create a minimal config
            config_data = {
                "storage": {
                    "log_dir": str(log_dir)
                },
                "git": {
                    "author": "Test Author",
                    "repositories": []
                }
            }
            
            # Create config file
            config_path = Path(tmpdir) / "config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(config_data, f)
            
            # Set environment variable and clear singleton
            original_env = os.environ.get('TALKBUT_CONFIG_PATH')
            try:
                os.environ['TALKBUT_CONFIG_PATH'] = str(config_path)
                ConfigManager._instance = None
                
                config = ConfigManager()
                processor = BatchProcessor(config)
                
                # Create log files for half of the dates (alternating)
                existing_dates = set()
                for i, log_date in enumerate(dates):
                    if i % 2 == 0:  # Create log for even indices
                        filename = f"daily_log_{log_date.isoformat()}.json"
                        log_path = log_dir / filename
                        log_data = {
                            "date": log_date.isoformat(),
                            "summary": "Existing log",
                            "stats": {"commits": 1, "files": 1, "insertions": 10, "deletions": 5},
                            "categories": [],
                            "tasks": []
                        }
                        with open(log_path, 'w') as f:
                            json.dump(log_data, f)
                        existing_dates.add(log_date)
                
                # Process all dates without force
                results = []
                for log_date in dates:
                    result = processor._process_single_date(log_date, author=None, force=False)
                    results.append((log_date, result))
                
                # Property: Dates with existing logs should be skipped
                for log_date, result in results:
                    if log_date in existing_dates:
                        assert result.skipped, \
                            f"Date {log_date} has existing log and should be skipped"
                    else:
                        # Dates without existing logs should be processed (success or failure)
                        assert not result.skipped, \
                            f"Date {log_date} has no existing log and should not be skipped"
            
            finally:
                # Restore environment
                if original_env is not None:
                    os.environ['TALKBUT_CONFIG_PATH'] = original_env
                elif 'TALKBUT_CONFIG_PATH' in os.environ:
                    del os.environ['TALKBUT_CONFIG_PATH']
                ConfigManager._instance = None
    
    @given(log_date=valid_date_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_log_exists_uses_correct_filename_format(self, log_date):
        """
        Property 7: Existing log detection prevents redundant processing.
        
        For any date, log_exists should use the standard naming convention
        daily_log_YYYY-MM-DD.json.
        
        **Feature: automated-daily-logging, Property 7: Existing log detection prevents redundant processing**
        **Validates: Requirements 3.2, 3.3**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            
            # Create a log file with the standard naming convention
            expected_filename = f"daily_log_{log_date.isoformat()}.json"
            log_path = log_dir / expected_filename
            
            log_data = {"date": log_date.isoformat(), "summary": "Test"}
            with open(log_path, 'w') as f:
                json.dump(log_data, f)
            
            # Property: log_exists should find the file with standard naming
            assert log_exists(log_date, log_dir), \
                f"log_exists should find file with standard naming: {expected_filename}"
            
            # Property: log_exists should not find files with different naming
            # Create a file with wrong naming
            wrong_filename = f"log_{log_date.isoformat()}.json"
            wrong_path = log_dir / wrong_filename
            with open(wrong_path, 'w') as f:
                json.dump(log_data, f)
            
            # Remove the correct file
            log_path.unlink()
            
            # Should not find the wrong-named file
            assert not log_exists(log_date, log_dir), \
                f"log_exists should not find file with non-standard naming: {wrong_filename}"
    
    @given(log_date=valid_date_strategy(), 
           days_offset=st.integers(min_value=1, max_value=30))
    @settings(max_examples=100, deadline=None)
    def test_property_log_exists_is_date_specific(self, log_date, days_offset):
        """
        Property 7: Existing log detection prevents redundant processing.
        
        For any date, log_exists should only return True for that specific date,
        not for other dates even if their logs exist.
        
        **Feature: automated-daily-logging, Property 7: Existing log detection prevents redundant processing**
        **Validates: Requirements 3.2, 3.3**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            
            # Create a log file for log_date
            filename = f"daily_log_{log_date.isoformat()}.json"
            log_path = log_dir / filename
            log_data = {"date": log_date.isoformat(), "summary": "Test"}
            with open(log_path, 'w') as f:
                json.dump(log_data, f)
            
            # Check a different date
            other_date = log_date + timedelta(days=days_offset)
            
            # Property: log_exists should return True for log_date
            assert log_exists(log_date, log_dir), \
                f"log_exists should return True for {log_date} when its log exists"
            
            # Property: log_exists should return False for other_date
            assert not log_exists(other_date, log_dir), \
                f"log_exists should return False for {other_date} when only {log_date} log exists"
