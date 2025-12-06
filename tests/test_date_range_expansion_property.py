"""Property-based tests for date range expansion.

**Feature: automated-daily-logging, Property 6: Date range expansion is complete and ordered**
**Validates: Requirements 3.1**
"""

import pytest
from datetime import date, timedelta
from hypothesis import given, strategies as st, settings, assume

from talkbut.processors.batch_utils import expand_date_range


# Strategy for generating valid date strings
@st.composite
def valid_date_string(draw):
    """Generate valid date strings in various supported formats."""
    choice = draw(st.integers(min_value=0, max_value=4))
    
    if choice == 0:
        # Absolute date: YYYY-MM-DD
        year = draw(st.integers(min_value=2020, max_value=2030))
        month = draw(st.integers(min_value=1, max_value=12))
        day = draw(st.integers(min_value=1, max_value=28))  # Safe for all months
        return f"{year:04d}-{month:02d}-{day:02d}"
    elif choice == 1:
        # N days ago
        days = draw(st.integers(min_value=0, max_value=365))
        return f"{days} days ago"
    elif choice == 2:
        # N weeks ago
        weeks = draw(st.integers(min_value=0, max_value=52))
        return f"{weeks} weeks ago"
    elif choice == 3:
        # "yesterday"
        return "yesterday"
    else:
        # "today"
        return "today"


class TestDateRangeExpansionProperties:
    """Property-based tests for date range expansion."""
    
    @given(since_str=valid_date_string(), until_str=valid_date_string())
    @settings(max_examples=100, deadline=None)
    def test_property_all_dates_included(self, since_str, until_str):
        """
        Property 6: Date range expansion is complete and ordered.
        
        For any valid date range (since, until), the expanded list should include
        all dates between since and until (inclusive).
        
        **Feature: automated-daily-logging, Property 6: Date range expansion is complete and ordered**
        **Validates: Requirements 3.1**
        """
        dates = expand_date_range(since_str, until_str)
        
        # Property: List should not be empty
        assert len(dates) > 0, \
            f"Date range from '{since_str}' to '{until_str}' should produce at least one date"
        
        # Property: All dates should be date objects
        assert all(isinstance(d, date) for d in dates), \
            f"All elements should be date objects"
        
        # Get the actual start and end dates
        start_date = min(dates)
        end_date = max(dates)
        
        # Property: All dates between start and end should be included
        expected_count = (end_date - start_date).days + 1
        assert len(dates) == expected_count, \
            f"Expected {expected_count} dates from {start_date} to {end_date}, got {len(dates)}"
        
        # Property: Check that each date is present
        current = start_date
        for i, d in enumerate(dates):
            assert d == current, \
                f"Date at position {i} should be {current}, got {d}"
            current += timedelta(days=1)
    
    @given(since_str=valid_date_string(), until_str=valid_date_string())
    @settings(max_examples=100, deadline=None)
    def test_property_no_duplicates(self, since_str, until_str):
        """
        Property 6: Date range expansion is complete and ordered.
        
        For any valid date range, the expanded list should contain no duplicates.
        
        **Feature: automated-daily-logging, Property 6: Date range expansion is complete and ordered**
        **Validates: Requirements 3.1**
        """
        dates = expand_date_range(since_str, until_str)
        
        # Property: No duplicates
        assert len(dates) == len(set(dates)), \
            f"Date range should have no duplicates. Got {len(dates)} dates but {len(set(dates))} unique"
    
    @given(since_str=valid_date_string(), until_str=valid_date_string())
    @settings(max_examples=100, deadline=None)
    def test_property_chronological_order(self, since_str, until_str):
        """
        Property 6: Date range expansion is complete and ordered.
        
        For any valid date range, the expanded list should be in chronological order.
        
        **Feature: automated-daily-logging, Property 6: Date range expansion is complete and ordered**
        **Validates: Requirements 3.1**
        """
        dates = expand_date_range(since_str, until_str)
        
        # Property: Dates should be in chronological order
        for i in range(len(dates) - 1):
            assert dates[i] < dates[i + 1], \
                f"Dates should be in chronological order. Date at {i} ({dates[i]}) >= date at {i+1} ({dates[i+1]})"
    
    @given(since_str=valid_date_string(), until_str=valid_date_string())
    @settings(max_examples=100, deadline=None)
    def test_property_consecutive_dates(self, since_str, until_str):
        """
        Property 6: Date range expansion is complete and ordered.
        
        For any valid date range, each date should be exactly one day after the previous.
        
        **Feature: automated-daily-logging, Property 6: Date range expansion is complete and ordered**
        **Validates: Requirements 3.1**
        """
        dates = expand_date_range(since_str, until_str)
        
        # Property: Each date should be consecutive (1 day apart)
        for i in range(len(dates) - 1):
            diff = (dates[i + 1] - dates[i]).days
            assert diff == 1, \
                f"Dates should be consecutive. Gap between {dates[i]} and {dates[i+1]} is {diff} days"
    
    @given(date_str=valid_date_string())
    @settings(max_examples=100, deadline=None)
    def test_property_single_date_range(self, date_str):
        """
        Property 6: Date range expansion is complete and ordered.
        
        For any date used as both since and until (implicitly), the result should
        contain exactly one date.
        
        **Feature: automated-daily-logging, Property 6: Date range expansion is complete and ordered**
        **Validates: Requirements 3.1**
        """
        # When until is None, it defaults to today
        # So we test with same date for both since and until
        dates = expand_date_range(date_str, date_str)
        
        # Property: Same start and end should give exactly one date
        assert len(dates) == 1, \
            f"Date range with same start and end should have exactly 1 date, got {len(dates)}"
    
    @given(days_back=st.integers(min_value=1, max_value=100))
    @settings(max_examples=100, deadline=None)
    def test_property_range_from_days_ago_to_today(self, days_back):
        """
        Property 6: Date range expansion is complete and ordered.
        
        For any N days ago to today, the result should contain exactly N+1 dates.
        
        **Feature: automated-daily-logging, Property 6: Date range expansion is complete and ordered**
        **Validates: Requirements 3.1**
        """
        since_str = f"{days_back} days ago"
        until_str = "today"
        
        dates = expand_date_range(since_str, until_str)
        
        # Property: N days ago to today should give N+1 dates (inclusive)
        expected_count = days_back + 1
        assert len(dates) == expected_count, \
            f"Range from {days_back} days ago to today should have {expected_count} dates, got {len(dates)}"
        
        # Property: Last date should be today
        assert dates[-1] == date.today(), \
            f"Last date should be today ({date.today()}), got {dates[-1]}"
        
        # Property: First date should be N days ago
        expected_start = date.today() - timedelta(days=days_back)
        assert dates[0] == expected_start, \
            f"First date should be {expected_start}, got {dates[0]}"
    
    @given(since_str=valid_date_string(), until_str=valid_date_string())
    @settings(max_examples=100, deadline=None)
    def test_property_reversed_range_is_corrected(self, since_str, until_str):
        """
        Property 6: Date range expansion is complete and ordered.
        
        For any date range where since > until, the function should swap them
        and still produce a valid chronological list.
        
        **Feature: automated-daily-logging, Property 6: Date range expansion is complete and ordered**
        **Validates: Requirements 3.1**
        """
        dates = expand_date_range(since_str, until_str)
        
        # Property: Result should always be in chronological order regardless of input order
        for i in range(len(dates) - 1):
            assert dates[i] < dates[i + 1], \
                f"Dates should be in chronological order even if inputs are reversed"
        
        # Property: Swapping since and until should give the same result
        dates_reversed = expand_date_range(until_str, since_str)
        assert dates == dates_reversed, \
            f"Swapping since and until should produce the same date list"
    
    @given(since_str=valid_date_string())
    @settings(max_examples=100, deadline=None)
    def test_property_default_until_is_today(self, since_str):
        """
        Property 6: Date range expansion is complete and ordered.
        
        For any since date with until=None, the range should include today
        (either as start or end, depending on whether since is past or future).
        
        **Feature: automated-daily-logging, Property 6: Date range expansion is complete and ordered**
        **Validates: Requirements 3.1**
        """
        dates = expand_date_range(since_str, until=None)
        
        # Property: When until is None, today should be in the range
        # (the function swaps dates if since > until, so today is always included)
        assert date.today() in dates, \
            f"When until is None, today should be in the date range, got range from {dates[0]} to {dates[-1]}"
    
    @given(year=st.integers(min_value=2020, max_value=2030),
           month=st.integers(min_value=1, max_value=12),
           day=st.integers(min_value=1, max_value=28))
    @settings(max_examples=100, deadline=None)
    def test_property_absolute_date_parsing(self, year, month, day):
        """
        Property 6: Date range expansion is complete and ordered.
        
        For any valid absolute date in YYYY-MM-DD format, the function should
        correctly parse it.
        
        **Feature: automated-daily-logging, Property 6: Date range expansion is complete and ordered**
        **Validates: Requirements 3.1**
        """
        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        expected_date = date(year, month, day)
        
        # Use same date for both since and until to test parsing
        dates = expand_date_range(date_str, date_str)
        
        # Property: Should parse to the correct date
        assert len(dates) == 1, \
            f"Single date range should have exactly 1 date"
        assert dates[0] == expected_date, \
            f"Date string '{date_str}' should parse to {expected_date}, got {dates[0]}"
