"""Property-based tests for error history management with bounded size.

**Feature: automated-daily-logging, Property 13: Error history is maintained with bounded size**
**Validates: Requirements 6.4**
"""

import pytest
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume

from src.talkbut.scheduling.status_manager import StatusManager


# Strategy for generating error messages
@st.composite
def error_messages(draw):
    """Generate realistic error messages."""
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
        "Unknown error"
    ]
    
    error_type = draw(st.sampled_from(error_types))
    
    # Sometimes add additional context
    add_context = draw(st.booleans())
    if add_context:
        context = draw(st.text(alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')), 
                              min_size=5, max_size=50))
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


class TestErrorHistoryBoundedSizeProperty:
    """Property-based tests for bounded error history."""
    
    @given(
        max_errors=st.integers(min_value=1, max_value=100),
        num_errors=st.integers(min_value=1, max_value=200),
        error_msg=error_messages(),
        date_attempted=st.one_of(st.none(), date_strings())
    )
    @settings(max_examples=100, deadline=None)
    def test_property_error_history_bounded_size(self, max_errors, num_errors, error_msg, date_attempted):
        """
        Property 13: Error history is maintained with bounded size.
        
        For any sequence of errors, the system should maintain a history of recent
        errors (up to a configured limit) and provide access to them. The history
        should never exceed the configured maximum size.
        
        This test verifies that:
        1. Error history never exceeds max_errors limit
        2. Most recent errors are kept when limit is exceeded
        3. Errors can be retrieved up to the limit
        
        **Feature: automated-daily-logging, Property 13: Error history is maintained with bounded size**
        **Validates: Requirements 6.4**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            manager = StatusManager(status_file, max_errors=max_errors)
            
            # Record num_errors errors
            for i in range(num_errors):
                error_message = f"{error_msg} #{i}"
                manager.record_run(success=False, error=error_message, date_attempted=date_attempted)
            
            # Property 1: Error history should never exceed max_errors
            # Read the status file directly to check the actual stored count
            import json
            with open(status_file, 'r') as f:
                data = json.load(f)
                stored_errors = data.get('errors', [])
            
            assert len(stored_errors) <= max_errors, \
                f"Error history size {len(stored_errors)} should not exceed max_errors {max_errors}"
            
            # Property 2: If we recorded more errors than the limit, 
            # the stored count should equal max_errors
            if num_errors > max_errors:
                assert len(stored_errors) == max_errors, \
                    f"When {num_errors} errors recorded with limit {max_errors}, " \
                    f"should store exactly {max_errors} errors, got {len(stored_errors)}"
            else:
                # If we recorded fewer errors than the limit, all should be stored
                assert len(stored_errors) == num_errors, \
                    f"When {num_errors} errors recorded with limit {max_errors}, " \
                    f"should store all {num_errors} errors, got {len(stored_errors)}"
            
            # Property 3: Most recent errors should be kept
            # The last error recorded should be in the history
            if num_errors > 0:
                last_error_msg = f"{error_msg} #{num_errors - 1}"
                recent_errors = manager.get_recent_errors(limit=max_errors)
                
                # The most recent error should be first in the list
                assert len(recent_errors) > 0, "Should have at least one error"
                assert last_error_msg in recent_errors[0].error_message, \
                    f"Most recent error should contain '{last_error_msg}', got '{recent_errors[0].error_message}'"
            
            # Property 4: Retrieved errors should not exceed requested limit
            retrieve_limit = min(5, max_errors)
            retrieved = manager.get_recent_errors(limit=retrieve_limit)
            assert len(retrieved) <= retrieve_limit, \
                f"Retrieved errors {len(retrieved)} should not exceed requested limit {retrieve_limit}"
    
    @given(
        max_errors=st.integers(min_value=5, max_value=50),
        batch_size=st.integers(min_value=1, max_value=20),
        num_batches=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_error_history_maintains_most_recent(self, max_errors, batch_size, num_batches):
        """
        Property 13: Error history is maintained with bounded size.
        
        For any sequence of error batches, when the total exceeds the limit,
        the system should maintain only the most recent errors and discard
        the oldest ones.
        
        This test verifies that:
        1. When errors exceed the limit, oldest errors are discarded
        2. Most recent errors are always accessible
        3. The order of errors is preserved (most recent first)
        
        **Feature: automated-daily-logging, Property 13: Error history is maintained with bounded size**
        **Validates: Requirements 6.4**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            manager = StatusManager(status_file, max_errors=max_errors)
            
            total_errors = batch_size * num_batches
            
            # Record errors in batches
            for batch in range(num_batches):
                for i in range(batch_size):
                    error_id = batch * batch_size + i
                    manager.record_run(
                        success=False, 
                        error=f"Error batch {batch} item {i} (ID: {error_id})"
                    )
            
            # Property: If total errors exceed max_errors, only the most recent max_errors should be kept
            if total_errors > max_errors:
                # The oldest error that should still be present
                oldest_kept_id = total_errors - max_errors
                
                # The newest error
                newest_id = total_errors - 1
                
                # Retrieve all errors
                all_errors = manager.get_recent_errors(limit=max_errors)
                
                # Should have exactly max_errors
                assert len(all_errors) == max_errors, \
                    f"Should have exactly {max_errors} errors, got {len(all_errors)}"
                
                # Most recent error should be first
                assert f"ID: {newest_id}" in all_errors[0].error_message, \
                    f"First error should be ID {newest_id}, got: {all_errors[0].error_message}"
                
                # Oldest kept error should be last
                assert f"ID: {oldest_kept_id}" in all_errors[-1].error_message, \
                    f"Last error should be ID {oldest_kept_id}, got: {all_errors[-1].error_message}"
                
                # Errors older than oldest_kept_id should not be present
                for error in all_errors:
                    # Extract ID from error message
                    if "ID:" in error.error_message:
                        id_str = error.error_message.split("ID: ")[1].rstrip(")")
                        error_id = int(id_str)
                        assert error_id >= oldest_kept_id, \
                            f"Error ID {error_id} should not be present (older than {oldest_kept_id})"
            else:
                # All errors should be present
                all_errors = manager.get_recent_errors(limit=max_errors)
                assert len(all_errors) == total_errors, \
                    f"Should have all {total_errors} errors, got {len(all_errors)}"
    
    @given(
        max_errors=st.integers(min_value=10, max_value=100),
        num_errors=st.integers(min_value=20, max_value=200),
        retrieve_limit=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_error_retrieval_respects_limit(self, max_errors, num_errors, retrieve_limit):
        """
        Property 13: Error history is maintained with bounded size.
        
        For any error history and retrieval limit, the number of errors
        returned should never exceed the requested limit, and should be
        the most recent errors available.
        
        **Feature: automated-daily-logging, Property 13: Error history is maintained with bounded size**
        **Validates: Requirements 6.4**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            manager = StatusManager(status_file, max_errors=max_errors)
            
            # Record errors
            for i in range(num_errors):
                manager.record_run(success=False, error=f"Error {i}")
            
            # Retrieve with limit
            retrieved = manager.get_recent_errors(limit=retrieve_limit)
            
            # Property 1: Retrieved count should not exceed limit
            assert len(retrieved) <= retrieve_limit, \
                f"Retrieved {len(retrieved)} errors should not exceed limit {retrieve_limit}"
            
            # Property 2: Retrieved count should not exceed stored count
            stored_count = min(num_errors, max_errors)
            assert len(retrieved) <= stored_count, \
                f"Retrieved {len(retrieved)} errors should not exceed stored count {stored_count}"
            
            # Property 3: Retrieved count should be min(retrieve_limit, stored_count)
            expected_count = min(retrieve_limit, stored_count)
            assert len(retrieved) == expected_count, \
                f"Should retrieve {expected_count} errors, got {len(retrieved)}"
            
            # Property 4: Retrieved errors should be the most recent ones
            if len(retrieved) > 0:
                # Most recent error should be first
                most_recent_id = num_errors - 1
                assert f"Error {most_recent_id}" == retrieved[0].error_message, \
                    f"First retrieved error should be 'Error {most_recent_id}', got '{retrieved[0].error_message}'"
    
    @given(
        max_errors=st.integers(min_value=5, max_value=50),
        num_errors_before_clear=st.integers(min_value=1, max_value=100),
        num_errors_after_clear=st.integers(min_value=0, max_value=100)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_clear_errors_resets_history(self, max_errors, num_errors_before_clear, num_errors_after_clear):
        """
        Property 13: Error history is maintained with bounded size.
        
        For any error history, after clearing errors, the history should be empty.
        New errors recorded after clearing should start fresh and respect the
        bounded size limit.
        
        **Feature: automated-daily-logging, Property 13: Error history is maintained with bounded size**
        **Validates: Requirements 6.4**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            manager = StatusManager(status_file, max_errors=max_errors)
            
            # Record some errors
            for i in range(num_errors_before_clear):
                manager.record_run(success=False, error=f"Before clear {i}")
            
            # Clear errors
            manager.clear_errors()
            
            # Property 1: After clearing, error history should be empty
            errors_after_clear = manager.get_recent_errors(limit=max_errors)
            assert len(errors_after_clear) == 0, \
                f"After clearing, should have 0 errors, got {len(errors_after_clear)}"
            
            # Record new errors after clearing
            for i in range(num_errors_after_clear):
                manager.record_run(success=False, error=f"After clear {i}")
            
            # Property 2: New errors should be stored correctly
            new_errors = manager.get_recent_errors(limit=max_errors)
            expected_count = min(num_errors_after_clear, max_errors)
            assert len(new_errors) == expected_count, \
                f"After recording {num_errors_after_clear} new errors, should have {expected_count}, got {len(new_errors)}"
            
            # Property 3: Only new errors should be present (no old errors)
            for error in new_errors:
                assert "After clear" in error.error_message, \
                    f"Error should be from after clear, got: {error.error_message}"
                assert "Before clear" not in error.error_message, \
                    f"Old error should not be present: {error.error_message}"
    
    @given(
        max_errors=st.integers(min_value=1, max_value=50),
        num_successes=st.integers(min_value=0, max_value=20),
        num_failures=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=100, deadline=None)
    def test_property_successful_runs_dont_affect_error_history(self, max_errors, num_successes, num_failures):
        """
        Property 13: Error history is maintained with bounded size.
        
        For any mix of successful and failed runs, successful runs should not
        affect the error history. Only failures should be recorded in the error
        history, and the bounded size should apply only to errors.
        
        **Feature: automated-daily-logging, Property 13: Error history is maintained with bounded size**
        **Validates: Requirements 6.4**
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            status_file = Path(tmpdir) / "status.json"
            manager = StatusManager(status_file, max_errors=max_errors)
            
            # Record failures
            for i in range(num_failures):
                manager.record_run(success=False, error=f"Failure {i}")
            
            # Record successes (should not affect error history)
            for i in range(num_successes):
                manager.record_run(success=True)
            
            # Property: Error history should only contain failures, bounded by max_errors
            errors = manager.get_recent_errors(limit=max_errors)
            expected_error_count = min(num_failures, max_errors)
            
            assert len(errors) == expected_error_count, \
                f"Should have {expected_error_count} errors, got {len(errors)}"
            
            # All errors should be failures (not successes)
            for error in errors:
                assert "Failure" in error.error_message, \
                    f"Error should be a failure, got: {error.error_message}"
            
            # Verify last_run was updated by successful runs
            if num_successes > 0:
                last_run = manager.get_last_run()
                assert last_run is not None, \
                    "Last run should be set after successful runs"
