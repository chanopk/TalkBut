"""Property-based tests for batch processing summary accuracy.

**Feature: automated-daily-logging, Property 8: Batch processing summary is accurate**
**Validates: Requirements 3.4**
"""

import pytest
import json
import tempfile
from datetime import date, timedelta
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
import os
import yaml

from talkbut.processors.batch_processor import BatchProcessor, BatchResult
from talkbut.core.config import ConfigManager


# Strategy for generating valid dates
@st.composite
def valid_date_strategy(draw):
    """Generate valid date objects."""
    year = draw(st.integers(min_value=2020, max_value=2030))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # Safe for all months
    return date(year, month, day)


# Strategy for generating date ranges
@st.composite
def date_range_strategy(draw):
    """Generate a list of consecutive dates."""
    start_date = draw(valid_date_strategy())
    num_days = draw(st.integers(min_value=1, max_value=10))
    
    dates = []
    for i in range(num_days):
        dates.append(start_date + timedelta(days=i))
    
    return dates


class TestBatchSummaryAccuracyProperties:
    """Property-based tests for batch processing summary accuracy."""
    
    @given(dates=date_range_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_summary_counts_equal_total_dates(self, dates):
        """
        Property 8: Batch processing summary is accurate.
        
        For any batch processing run, the sum of processed, skipped, and failed
        dates should equal the total dates in the range.
        
        **Feature: automated-daily-logging, Property 8: Batch processing summary is accurate**
        **Validates: Requirements 3.4**
        """
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
                
                # Create existing logs for some dates (to create skipped entries)
                for i, log_date in enumerate(dates):
                    if i % 3 == 0:  # Create log for every third date
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
                
                # Process the date range
                since_str = dates[0].isoformat()
                until_str = dates[-1].isoformat()
                
                result = processor.process_date_range(
                    since=since_str,
                    until=until_str,
                    force=False,
                    author=None
                )
                
                # Property: Sum of all categories should equal total_dates
                total_accounted = len(result.processed) + len(result.skipped) + len(result.failed)
                
                assert total_accounted == result.total_dates, \
                    f"Sum of processed ({len(result.processed)}) + skipped ({len(result.skipped)}) + " \
                    f"failed ({len(result.failed)}) = {total_accounted} should equal " \
                    f"total_dates ({result.total_dates})"
                
                # Property: total_dates should match the number of dates in the range
                assert result.total_dates == len(dates), \
                    f"total_dates ({result.total_dates}) should equal the number of dates " \
                    f"in the range ({len(dates)})"
            
            finally:
                # Restore environment
                if original_env is not None:
                    os.environ['TALKBUT_CONFIG_PATH'] = original_env
                elif 'TALKBUT_CONFIG_PATH' in os.environ:
                    del os.environ['TALKBUT_CONFIG_PATH']
                ConfigManager._instance = None
    
    @given(dates=date_range_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_no_duplicate_dates_in_summary(self, dates):
        """
        Property 8: Batch processing summary is accurate.
        
        For any batch processing run, no date should appear in multiple
        categories (processed, skipped, failed).
        
        **Feature: automated-daily-logging, Property 8: Batch processing summary is accurate**
        **Validates: Requirements 3.4**
        """
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
                
                # Create existing logs for some dates
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
                
                # Process the date range
                since_str = dates[0].isoformat()
                until_str = dates[-1].isoformat()
                
                result = processor.process_date_range(
                    since=since_str,
                    until=until_str,
                    force=False,
                    author=None
                )
                
                # Property: No date should appear in multiple categories
                processed_set = set(result.processed)
                skipped_set = set(result.skipped)
                failed_set = set([d for d, _ in result.failed])
                
                # Check for overlaps
                processed_and_skipped = processed_set & skipped_set
                processed_and_failed = processed_set & failed_set
                skipped_and_failed = skipped_set & failed_set
                
                assert len(processed_and_skipped) == 0, \
                    f"Dates should not appear in both processed and skipped: {processed_and_skipped}"
                
                assert len(processed_and_failed) == 0, \
                    f"Dates should not appear in both processed and failed: {processed_and_failed}"
                
                assert len(skipped_and_failed) == 0, \
                    f"Dates should not appear in both skipped and failed: {skipped_and_failed}"
            
            finally:
                # Restore environment
                if original_env is not None:
                    os.environ['TALKBUT_CONFIG_PATH'] = original_env
                elif 'TALKBUT_CONFIG_PATH' in os.environ:
                    del os.environ['TALKBUT_CONFIG_PATH']
                ConfigManager._instance = None
    
    @given(dates=date_range_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_all_dates_accounted_for(self, dates):
        """
        Property 8: Batch processing summary is accurate.
        
        For any batch processing run, every date in the input range should
        appear exactly once in the summary (processed, skipped, or failed).
        
        **Feature: automated-daily-logging, Property 8: Batch processing summary is accurate**
        **Validates: Requirements 3.4**
        """
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
                
                # Create existing logs for some dates
                for i, log_date in enumerate(dates):
                    if i % 3 == 0:  # Create log for every third date
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
                
                # Process the date range
                since_str = dates[0].isoformat()
                until_str = dates[-1].isoformat()
                
                result = processor.process_date_range(
                    since=since_str,
                    until=until_str,
                    force=False,
                    author=None
                )
                
                # Collect all dates from the result
                all_result_dates = set()
                all_result_dates.update(result.processed)
                all_result_dates.update(result.skipped)
                all_result_dates.update([d for d, _ in result.failed])
                
                # Property: Every input date should appear in the result
                input_dates_set = set(dates)
                
                for input_date in input_dates_set:
                    assert input_date in all_result_dates, \
                        f"Date {input_date} from input range should appear in result summary"
                
                # Property: No extra dates should appear in the result
                for result_date in all_result_dates:
                    assert result_date in input_dates_set, \
                        f"Date {result_date} in result should be from the input range"
            
            finally:
                # Restore environment
                if original_env is not None:
                    os.environ['TALKBUT_CONFIG_PATH'] = original_env
                elif 'TALKBUT_CONFIG_PATH' in os.environ:
                    del os.environ['TALKBUT_CONFIG_PATH']
                ConfigManager._instance = None
    
    @given(dates=date_range_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_skipped_dates_have_existing_logs(self, dates):
        """
        Property 8: Batch processing summary is accurate.
        
        For any batch processing run without force flag, all dates in the
        skipped list should have existing log files.
        
        **Feature: automated-daily-logging, Property 8: Batch processing summary is accurate**
        **Validates: Requirements 3.4**
        """
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
                
                # Create existing logs for some dates
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
                
                # Process the date range without force
                since_str = dates[0].isoformat()
                until_str = dates[-1].isoformat()
                
                result = processor.process_date_range(
                    since=since_str,
                    until=until_str,
                    force=False,
                    author=None
                )
                
                # Property: All skipped dates should have existing log files
                for skipped_date in result.skipped:
                    filename = f"daily_log_{skipped_date.isoformat()}.json"
                    log_path = log_dir / filename
                    
                    assert log_path.exists(), \
                        f"Skipped date {skipped_date} should have an existing log file at {log_path}"
                    
                    assert skipped_date in existing_dates, \
                        f"Skipped date {skipped_date} should be in the set of dates with existing logs"
            
            finally:
                # Restore environment
                if original_env is not None:
                    os.environ['TALKBUT_CONFIG_PATH'] = original_env
                elif 'TALKBUT_CONFIG_PATH' in os.environ:
                    del os.environ['TALKBUT_CONFIG_PATH']
                ConfigManager._instance = None
    
    @given(dates=date_range_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_processed_dates_create_log_files(self, dates):
        """
        Property 8: Batch processing summary is accurate.
        
        For any batch processing run, all dates in the processed list should
        have log files created (or updated if force=True).
        
        **Feature: automated-daily-logging, Property 8: Batch processing summary is accurate**
        **Validates: Requirements 3.4**
        """
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
                
                # Don't create any existing logs - all dates should be processed
                
                # Process the date range
                since_str = dates[0].isoformat()
                until_str = dates[-1].isoformat()
                
                result = processor.process_date_range(
                    since=since_str,
                    until=until_str,
                    force=False,
                    author=None
                )
                
                # Property: All processed dates should have log files
                for processed_date in result.processed:
                    filename = f"daily_log_{processed_date.isoformat()}.json"
                    log_path = log_dir / filename
                    
                    assert log_path.exists(), \
                        f"Processed date {processed_date} should have a log file at {log_path}"
                    
                    # Verify the log file is valid JSON
                    with open(log_path, 'r') as f:
                        log_data = json.load(f)
                        assert log_data["date"] == processed_date.isoformat(), \
                            f"Log file for {processed_date} should have correct date field"
            
            finally:
                # Restore environment
                if original_env is not None:
                    os.environ['TALKBUT_CONFIG_PATH'] = original_env
                elif 'TALKBUT_CONFIG_PATH' in os.environ:
                    del os.environ['TALKBUT_CONFIG_PATH']
                ConfigManager._instance = None
    
    @given(dates=date_range_strategy())
    @settings(max_examples=50, deadline=None)
    def test_property_force_flag_processes_all_dates(self, dates):
        """
        Property 8: Batch processing summary is accurate.
        
        For any batch processing run with force=True, no dates should be
        skipped (all should be either processed or failed).
        
        **Feature: automated-daily-logging, Property 8: Batch processing summary is accurate**
        **Validates: Requirements 3.4**
        """
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
                
                # Create existing logs for ALL dates
                for log_date in dates:
                    filename = f"daily_log_{log_date.isoformat()}.json"
                    log_path = log_dir / filename
                    log_data = {
                        "date": log_date.isoformat(),
                        "summary": "Old log",
                        "stats": {"commits": 1, "files": 1, "insertions": 10, "deletions": 5},
                        "categories": [],
                        "tasks": []
                    }
                    with open(log_path, 'w') as f:
                        json.dump(log_data, f)
                
                # Process the date range WITH force=True
                since_str = dates[0].isoformat()
                until_str = dates[-1].isoformat()
                
                result = processor.process_date_range(
                    since=since_str,
                    until=until_str,
                    force=True,
                    author=None
                )
                
                # Property: With force=True, no dates should be skipped
                assert len(result.skipped) == 0, \
                    f"With force=True, no dates should be skipped, but found {len(result.skipped)} skipped dates"
                
                # Property: All dates should be either processed or failed
                total_handled = len(result.processed) + len(result.failed)
                assert total_handled == len(dates), \
                    f"With force=True, all {len(dates)} dates should be processed or failed, " \
                    f"but only {total_handled} were handled"
            
            finally:
                # Restore environment
                if original_env is not None:
                    os.environ['TALKBUT_CONFIG_PATH'] = original_env
                elif 'TALKBUT_CONFIG_PATH' in os.environ:
                    del os.environ['TALKBUT_CONFIG_PATH']
                ConfigManager._instance = None
