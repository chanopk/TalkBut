"""Validation utilities for scheduling."""

import re
from typing import Tuple


def validate_time_format(time_str: str) -> Tuple[bool, str]:
    """
    Validate time string in HH:MM format.
    
    Args:
        time_str: Time string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        - If valid: (True, "")
        - If invalid: (False, "error description")
        
    Requirements: 2.1
    """
    if not time_str:
        return False, "Time string cannot be empty"
    
    # Check format with regex
    pattern = r'^([0-9]{2}):([0-9]{2})$'
    match = re.match(pattern, time_str)
    
    if not match:
        return False, "Time must be in HH:MM format (e.g., 09:30, 18:00)"
    
    hours_str, minutes_str = match.groups()
    
    try:
        hours = int(hours_str)
        minutes = int(minutes_str)
    except ValueError:
        return False, "Hours and minutes must be numeric"
    
    # Validate hours (00-23)
    if hours < 0 or hours > 23:
        return False, f"Hours must be between 00 and 23, got {hours_str}"
    
    # Validate minutes (00-59)
    if minutes < 0 or minutes > 59:
        return False, f"Minutes must be between 00 and 59, got {minutes_str}"
    
    return True, ""
