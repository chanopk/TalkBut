"""Property-based tests for time validation.

**Feature: automated-daily-logging, Property 4: Time format validation is consistent**
**Validates: Requirements 2.1**
"""

import pytest
from hypothesis import given, strategies as st, settings, assume

from talkbut.scheduling.validators import validate_time_format


# Strategy for generating valid time strings in HH:MM format
@st.composite
def valid_time_string(draw):
    """Generate valid time strings in HH:MM format (00:00 to 23:59)."""
    hour = draw(st.integers(min_value=0, max_value=23))
    minute = draw(st.integers(min_value=0, max_value=59))
    return f"{hour:02d}:{minute:02d}"


# Strategy for generating invalid time strings
@st.composite
def invalid_time_string(draw):
    """Generate invalid time strings that should be rejected."""
    choice = draw(st.integers(min_value=0, max_value=5))
    
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
        return draw(st.text(min_size=1, max_size=10).filter(lambda x: ':' not in x and len(x) > 0))
    elif choice == 3:
        # Wrong format (too many parts)
        parts = draw(st.lists(st.text(min_size=1, max_size=5), min_size=3, max_size=5))
        return ":".join(parts)
    elif choice == 4:
        # Non-numeric characters in time position
        return draw(st.text(alphabet=st.characters(blacklist_categories=('Nd',)), min_size=1, max_size=10).filter(lambda x: len(x) > 0))
    else:
        # Empty string
        return ""


class TestTimeValidationProperties:
    """Property-based tests for time format validation."""
    
    @given(time_str=valid_time_string())
    @settings(max_examples=100, deadline=None)
    def test_property_valid_times_are_accepted(self, time_str):
        """
        Property 4: Time format validation is consistent.
        
        For any string in HH:MM format where HH is 00-23 and MM is 00-59,
        validate_time_format should accept it (return True with empty error message).
        
        **Feature: automated-daily-logging, Property 4: Time format validation is consistent**
        **Validates: Requirements 2.1**
        """
        is_valid, error_msg = validate_time_format(time_str)
        
        # Property: All valid time strings should be accepted
        assert is_valid is True, \
            f"Valid time string '{time_str}' should be accepted, but got error: {error_msg}"
        assert error_msg == "", \
            f"Valid time string '{time_str}' should have empty error message, got: {error_msg}"
    
    @given(time_str=invalid_time_string())
    @settings(max_examples=100, deadline=None)
    def test_property_invalid_times_are_rejected(self, time_str):
        """
        Property 4: Time format validation is consistent.
        
        For any string that doesn't match HH:MM format with valid ranges,
        validate_time_format should reject it (return False with error message).
        
        **Feature: automated-daily-logging, Property 4: Time format validation is consistent**
        **Validates: Requirements 2.1**
        """
        is_valid, error_msg = validate_time_format(time_str)
        
        # Property: All invalid time strings should be rejected
        assert is_valid is False, \
            f"Invalid time string '{time_str}' should be rejected"
        assert error_msg != "", \
            f"Invalid time string '{time_str}' should have non-empty error message"
        assert isinstance(error_msg, str), \
            f"Error message should be a string, got {type(error_msg)}"
    
    @given(time_str=valid_time_string())
    @settings(max_examples=100, deadline=None)
    def test_property_validation_is_deterministic(self, time_str):
        """
        Property 4: Time format validation is consistent.
        
        For any time string, calling validate_time_format multiple times
        should always return the same result (deterministic behavior).
        
        **Feature: automated-daily-logging, Property 4: Time format validation is consistent**
        **Validates: Requirements 2.1**
        """
        # Call validation multiple times
        result1 = validate_time_format(time_str)
        result2 = validate_time_format(time_str)
        result3 = validate_time_format(time_str)
        
        # Property: Results should be deterministic
        assert result1 == result2 == result3, \
            f"Validation of '{time_str}' should be deterministic, got {result1}, {result2}, {result3}"
    
    @given(hour=st.integers(min_value=0, max_value=23), 
           minute=st.integers(min_value=0, max_value=59))
    @settings(max_examples=100, deadline=None)
    def test_property_boundary_values_are_valid(self, hour, minute):
        """
        Property 4: Time format validation is consistent.
        
        For any hour in [0, 23] and minute in [0, 59], the formatted time
        string should be accepted as valid.
        
        **Feature: automated-daily-logging, Property 4: Time format validation is consistent**
        **Validates: Requirements 2.1**
        """
        time_str = f"{hour:02d}:{minute:02d}"
        is_valid, error_msg = validate_time_format(time_str)
        
        # Property: All times within valid ranges should be accepted
        assert is_valid is True, \
            f"Time {time_str} (hour={hour}, minute={minute}) should be valid, got error: {error_msg}"
    
    @given(hour=st.integers().filter(lambda x: x < 0 or x > 23),
           minute=st.integers(min_value=0, max_value=59))
    @settings(max_examples=100, deadline=None)
    def test_property_invalid_hours_are_rejected(self, hour, minute):
        """
        Property 4: Time format validation is consistent.
        
        For any hour outside [0, 23] range, the time string should be rejected.
        
        **Feature: automated-daily-logging, Property 4: Time format validation is consistent**
        **Validates: Requirements 2.1**
        """
        # Only test hours that can be formatted as 2 digits
        assume(-99 <= hour <= 99)
        
        time_str = f"{hour:02d}:{minute:02d}"
        is_valid, error_msg = validate_time_format(time_str)
        
        # Property: Hours outside valid range should be rejected
        assert is_valid is False, \
            f"Time {time_str} with invalid hour {hour} should be rejected"
        assert "hour" in error_msg.lower() or "must be in hh:mm format" in error_msg.lower(), \
            f"Error message should mention hour issue, got: {error_msg}"
    
    @given(hour=st.integers(min_value=0, max_value=23),
           minute=st.one_of(
               st.integers(min_value=-99, max_value=-1),
               st.integers(min_value=60, max_value=99)
           ))
    @settings(max_examples=100, deadline=None)
    def test_property_invalid_minutes_are_rejected(self, hour, minute):
        """
        Property 4: Time format validation is consistent.
        
        For any minute outside [0, 59] range, the time string should be rejected.
        
        **Feature: automated-daily-logging, Property 4: Time format validation is consistent**
        **Validates: Requirements 2.1**
        """
        time_str = f"{hour:02d}:{minute:02d}"
        is_valid, error_msg = validate_time_format(time_str)
        
        # Property: Minutes outside valid range should be rejected
        assert is_valid is False, \
            f"Time {time_str} with invalid minute {minute} should be rejected"
        assert "minute" in error_msg.lower() or "must be in hh:mm format" in error_msg.lower(), \
            f"Error message should mention minute issue, got: {error_msg}"
    
    @given(time_str=st.text(min_size=1, max_size=20).filter(lambda x: ':' not in x))
    @settings(max_examples=100, deadline=None)
    def test_property_strings_without_colon_are_rejected(self, time_str):
        """
        Property 4: Time format validation is consistent.
        
        For any string without a colon, validation should reject it.
        
        **Feature: automated-daily-logging, Property 4: Time format validation is consistent**
        **Validates: Requirements 2.1**
        """
        is_valid, error_msg = validate_time_format(time_str)
        
        # Property: Strings without colon should be rejected
        assert is_valid is False, \
            f"Time string '{time_str}' without colon should be rejected"
        assert error_msg != "", \
            f"Time string '{time_str}' should have error message"
