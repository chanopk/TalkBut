"""Platform detection utility for selecting appropriate scheduler."""

import platform
from enum import Enum


class SchedulerType(Enum):
    """Types of schedulers supported by the system."""
    CRON = "cron"
    TASK_SCHEDULER = "task_scheduler"
    UNSUPPORTED = "unsupported"


def detect_platform() -> SchedulerType:
    """
    Detect the operating system and return appropriate scheduler type.
    
    Returns:
        SchedulerType: CRON for Unix-like systems (Darwin/Linux),
                      TASK_SCHEDULER for Windows,
                      UNSUPPORTED for other platforms
    """
    system = platform.system()
    
    if system in ("Darwin", "Linux"):
        return SchedulerType.CRON
    elif system == "Windows":
        return SchedulerType.TASK_SCHEDULER
    else:
        return SchedulerType.UNSUPPORTED
