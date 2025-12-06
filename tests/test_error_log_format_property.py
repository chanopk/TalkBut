"""Property-based tests for error log format.

**Feature: automated-daily-logging, Property 12: Error logs contain required information**
**Validates: Requirements 6.1, 6.2**
"""

import pytest
import tempfile
import re
from pathlib import Path
from datetime import datetime
from hypothesis import given, strategies as st, settings

from src.talkbut.scheduling.error_logger import log_error


# Strategy for generating error messages
@st.composite
def error_messages(draw):
    """Generate realistic error messages with various characteristics."""
    error_types = [
        "API connection failed",
        "Git repository not found",
        "Configuration file missing",
        "Network timeout",
        "Authentication failed",
        "Rate limit exceeded",
        "Invalid date format",
        "Disk space insufficient",
        "Permission denied",
        "Unknown error",
        "Database connection lost",
        "File not found",
        "Invalid configuration",
        "Memory allocation failed",
        "Timeout exceeded"
    ]
    
    error_type = draw(st.sampled_from(error_types))
    
    # Sometimes add additional context
    add_context = draw(st.booleans())
    if add_context:
        context = draw(st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Pd')), 
            min_size=5, 
            max_size=100
        ))
        return f"{error_type}: {context}"
    
    return error_type


# Strategy for generating date strings
@st.composite
def date_strings(draw):
    """Generate valid date strings in YYYY-MM-DD format."""
    year = draw(st.integers(min_value=2020, max_value=2030))
    month = draw(st.integers(min_value=1, max_value=12))
    day = draw(st.integers(min_value=1, max_value=28))  # Use 28 to avoid invalid dates
    return f"{year:04d}-{month:02d}-{day:02d}"


class TestErrorLogFormatProperty:
    """Property-based tests for error log format."""
    
    @given(
        error_msg=error_messages(),
        date_attempted=st.one_of(st.none(), date_strings())
    )
    @settings(max_examples=100, deadline=None)
    def test_property_error_logs_contain_timestamp_and_message(self, error_msg, date_attempted):
        """
        Property 12: Error logs contain required information.
        
        For any error that occurs during automated logging, the error log entry
        should contain both a timestamp and the error message.
        
        This test verifies that:
        1. Every error log entry contains a timestamp in ISO format
        2. Every error log entry contains the error message
        3. The timestamp is valid and parseable
        4. The error message is preserved exactly as provided
        
        **Feature: automated-daily-logging, Property 12: Error logs contain required information**
        **Validates: Requirements 6.1, 6.2**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            error_log_path = Path(tmpdir) / "errors.log"
            
            # Log the error
            log_error(error_log_path, error_msg, date_attempted=date_attempted)
            
            # Read the log file
            with open(error_log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            # Property 1: Log entry should contain a timestamp in brackets
            # Format: [YYYY-MM-DDTHH:MM:SS.ffffff]
            timestamp_pattern = r'\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)\]'
            timestamp_match = re.search(timestamp_pattern, log_content)
            
            assert timestamp_match is not None, \
                f"Error log should contain a timestamp in ISO format, got: {log_content}"
            
            # Property 2: The timestamp should be valid and parseable
            timestamp_str = timestamp_match.group(1)
            try:
                parsed_timestamp = datetime.fromisoformat(timestamp_str)
                assert isinstance(parsed_timestamp, datetime), \
                    f"Timestamp should be a valid datetime, got: {timestamp_str}"
            except ValueError as e:
                pytest.fail(f"Timestamp should be parseable as ISO format: {e}")
            
            # Property 3: Log entry should contain the error message
            assert error_msg in log_content, \
                f"Error log should contain the error message '{error_msg}', got: {log_content}"
            
            # Property 4: If date_attempted is provided, it should be in the log
            if date_attempted:
                assert date_attempted in log_content, \
                    f"Error log should contain date_attempted '{date_attempted}', got: {log_content}"
                assert f"(date: {date_attempted})" in log_content, \
                    f"Date should be formatted as '(date: {date_attempted})', got: {log_content}"
    
    @given(
        error_messages_list=st.lists(error_messages(), min_size=1, max_size=20),
        dates_list=st.lists(st.one_of(st.none(), date_strings()), min_size=1, max_size=20)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_multiple_errors_all_contain_required_info(self, error_messages_list, dates_list):
        """
        Property 12: Error logs contain required information.
        
        For any sequence of errors logged to the same file, each entry should
        contain both timestamp and error message. Multiple entries should be
        properly separated and all should be parseable.
        
        This test verifies that:
        1. Multiple error entries can be written to the same file
        2. Each entry contains timestamp and message
        3. Entries are properly separated (newlines)
        4. All timestamps are valid
        
        **Feature: automated-daily-logging, Property 12: Error logs contain required information**
        **Validates: Requirements 6.1, 6.2**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            error_log_path = Path(tmpdir) / "errors.log"
            
            # Ensure both lists have the same length
            num_errors = min(len(error_messages_list), len(dates_list))
            
            # Log multiple errors
            for i in range(num_errors):
                log_error(error_log_path, error_messages_list[i], date_attempted=dates_list[i])
            
            # Read the log file
            with open(error_log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
            
            # Split into lines (each error should be on its own line)
            log_lines = [line for line in log_content.split('\n') if line.strip()]
            
            # Property 1: Number of log lines should match number of errors
            assert len(log_lines) == num_errors, \
                f"Should have {num_errors} log lines, got {len(log_lines)}"
            
            # Property 2: Each line should contain timestamp and message
            timestamp_pattern = r'\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)\]'
            
            for i, line in enumerate(log_lines):
                # Check timestamp
                timestamp_match = re.search(timestamp_pattern, line)
                assert timestamp_match is not None, \
                    f"Line {i} should contain timestamp, got: {line}"
                
                # Verify timestamp is parseable
                timestamp_str = timestamp_match.group(1)
                try:
                    datetime.fromisoformat(timestamp_str)
                except ValueError:
                    pytest.fail(f"Line {i} timestamp should be valid ISO format: {timestamp_str}")
                
                # Check error message
                assert error_messages_list[i] in line, \
                    f"Line {i} should contain error message '{error_messages_list[i]}', got: {line}"
                
                # Check date if provided
                if dates_list[i]:
                    assert dates_list[i] in line, \
                        f"Line {i} should contain date '{dates_list[i]}', got: {line}"
    
    @given(
        error_msg=error_messages()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_error_log_format_consistency(self, error_msg):
        """
        Property 12: Error logs contain required information.
        
        For any error message, the log format should be consistent:
        [timestamp] error_message [optional date info]
        
        This test verifies that:
        1. Format follows the pattern: [timestamp] message
        2. Timestamp is always at the beginning in brackets
        3. Message follows immediately after timestamp
        4. Format is consistent regardless of message content
        
        **Feature: automated-daily-logging, Property 12: Error logs contain required information**
        **Validates: Requirements 6.1, 6.2**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            error_log_path = Path(tmpdir) / "errors.log"
            
            # Log error without date
            log_error(error_log_path, error_msg, date_attempted=None)
            
            # Read the log file
            with open(error_log_path, 'r', encoding='utf-8') as f:
                log_content = f.read().strip()
            
            # Property 1: Format should match: [timestamp] message
            # The line should start with [
            assert log_content.startswith('['), \
                f"Log entry should start with '[', got: {log_content[:20]}"
            
            # Property 2: After the closing ], there should be a space and then the message
            closing_bracket_idx = log_content.find(']')
            assert closing_bracket_idx > 0, \
                f"Log entry should contain closing bracket ']', got: {log_content}"
            
            # After ] should be a space
            assert log_content[closing_bracket_idx + 1] == ' ', \
                f"After timestamp bracket should be a space, got: '{log_content[closing_bracket_idx:closing_bracket_idx+5]}'"
            
            # After the space should be the error message (strip both for comparison)
            message_start = closing_bracket_idx + 2
            remaining_content = log_content[message_start:]
            # Compare stripped versions to handle trailing whitespace
            assert remaining_content.strip().startswith(error_msg.strip()), \
                f"After timestamp should be the error message '{error_msg.strip()}', got: '{remaining_content.strip()[:50]}'"
    
    @given(
        error_msg=error_messages(),
        date_attempted=date_strings()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_error_log_with_date_format(self, error_msg, date_attempted):
        """
        Property 12: Error logs contain required information.
        
        For any error with a date_attempted, the log should include the date
        in a consistent format: (date: YYYY-MM-DD)
        
        This test verifies that:
        1. Date information is included when provided
        2. Date format is consistent: (date: YYYY-MM-DD)
        3. Date appears after the error message
        
        **Feature: automated-daily-logging, Property 12: Error logs contain required information**
        **Validates: Requirements 6.1, 6.2**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            error_log_path = Path(tmpdir) / "errors.log"
            
            # Log error with date
            log_error(error_log_path, error_msg, date_attempted=date_attempted)
            
            # Read the log file
            with open(error_log_path, 'r', encoding='utf-8') as f:
                log_content = f.read().strip()
            
            # Property 1: Date should be in format (date: YYYY-MM-DD)
            expected_date_format = f"(date: {date_attempted})"
            assert expected_date_format in log_content, \
                f"Log should contain date in format '{expected_date_format}', got: {log_content}"
            
            # Property 2: Date should appear after the error message
            error_msg_idx = log_content.find(error_msg)
            date_format_idx = log_content.find(expected_date_format)
            
            assert error_msg_idx < date_format_idx, \
                f"Date format should appear after error message, got: {log_content}"
    
    @given(
        error_msg=error_messages()
    )
    @settings(max_examples=100, deadline=None)
    def test_property_error_log_appends_correctly(self, error_msg):
        """
        Property 12: Error logs contain required information.
        
        For any sequence of errors, each should be appended to the log file
        (not overwrite), and each entry should maintain the required format.
        
        This test verifies that:
        1. New errors are appended, not overwriting existing ones
        2. Each appended entry has proper format
        3. File grows with each error
        
        **Feature: automated-daily-logging, Property 12: Error logs contain required information**
        **Validates: Requirements 6.1, 6.2**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            error_log_path = Path(tmpdir) / "errors.log"
            
            # Log first error
            first_error = f"First: {error_msg}"
            log_error(error_log_path, first_error)
            
            # Read file size and content
            first_size = error_log_path.stat().st_size
            with open(error_log_path, 'r', encoding='utf-8') as f:
                first_content = f.read()
            
            # Log second error
            second_error = f"Second: {error_msg}"
            log_error(error_log_path, second_error)
            
            # Read file size and content again
            second_size = error_log_path.stat().st_size
            with open(error_log_path, 'r', encoding='utf-8') as f:
                second_content = f.read()
            
            # Property 1: File should have grown
            assert second_size > first_size, \
                f"File should grow after appending, first: {first_size}, second: {second_size}"
            
            # Property 2: First error should still be present
            assert first_error in second_content, \
                f"First error should still be in file after appending second error"
            
            # Property 3: Second error should be present
            assert second_error in second_content, \
                f"Second error should be in file"
            
            # Property 4: Both errors should have timestamps
            timestamp_pattern = r'\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)\]'
            timestamps = re.findall(timestamp_pattern, second_content)
            assert len(timestamps) >= 2, \
                f"Should have at least 2 timestamps after logging 2 errors, got {len(timestamps)}"
