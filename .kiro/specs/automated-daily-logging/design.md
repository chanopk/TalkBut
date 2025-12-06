# Design Document: Automated Daily Logging

## Overview

ฟีเจอร์ Automated Daily Logging จะเพิ่มความสามารถให้ TalkBut สามารถสร้าง daily log อัตโนมัติและรองรับการประมวลผลแบบ batch สำหรับหลายวัน โดยมีเป้าหมายหลัก 3 ประการ:

1. **Automated Scheduling**: ให้ระบบรัน `talkbut log` อัตโนมัติทุกวันตามเวลาที่กำหนด
2. **Batch Processing**: รองรับการสร้าง log สำหรับหลายวันพร้อมกัน (เช่น รันสัปดาห์ละครั้ง)
3. **Smart Skipping**: ข้าม log ที่มีอยู่แล้วเพื่อประหยัดค่า API

ระบบจะรองรับทั้ง Unix-like systems (macOS, Linux) ที่ใช้ cron และ Windows ที่ใช้ Task Scheduler

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     TalkBut CLI                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   schedule   │  │     log      │  │    status    │      │
│  │   command    │  │   command    │  │   command    │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│         v                  v                  v               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Scheduler Manager                           │   │
│  │  - Platform detection                                 │   │
│  │  - Cron/Task Scheduler abstraction                   │   │
│  │  - Schedule CRUD operations                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Batch Processor                             │   │
│  │  - Date range expansion                               │   │
│  │  - Existing log detection                             │   │
│  │  - Progress tracking                                  │   │
│  │  - Error handling per date                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Status Manager                              │   │
│  │  - Schedule status tracking                           │   │
│  │  - Error log management                               │   │
│  │  - Run history tracking                               │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

**Automated Scheduling Flow:**
```
User → schedule enable → SchedulerManager → Platform Detector
                                          ↓
                                    CronScheduler (Unix)
                                          or
                                    TaskScheduler (Windows)
                                          ↓
                                    Create scheduled job
                                          ↓
                                    StatusManager.record()
```

**Batch Processing Flow:**
```
User → log --since "7 days ago" → BatchProcessor
                                        ↓
                                  Expand date range
                                        ↓
                                  For each date:
                                    - Check existing log
                                    - Skip if exists (unless --force)
                                    - Run GitCollector
                                    - Run AIAnalyzer
                                    - Save daily log
                                    - Update progress
                                        ↓
                                  Display summary
```

## Components and Interfaces

### 1. SchedulerManager

**Purpose**: จัดการการสร้าง/แก้ไข/ลบ scheduled tasks ในแต่ละ platform

**Interface:**
```python
class SchedulerManager:
    def __init__(self, config: ConfigManager):
        """Initialize with configuration"""
        
    def enable(self, time: str, config_path: str) -> bool:
        """
        Enable automated logging at specified time
        
        Args:
            time: Time in HH:MM format (24-hour)
            config_path: Path to config file for the scheduled command
            
        Returns:
            True if successful
        """
        
    def disable(self) -> bool:
        """
        Disable automated logging
        
        Returns:
            True if successful
        """
        
    def update(self, time: str) -> bool:
        """
        Update schedule time
        
        Args:
            time: New time in HH:MM format
            
        Returns:
            True if successful
        """
        
    def get_status(self) -> ScheduleStatus:
        """
        Get current schedule status
        
        Returns:
            ScheduleStatus object with current state
        """
        
    def is_enabled(self) -> bool:
        """Check if automated logging is enabled"""
```

### 2. Platform-Specific Schedulers

**CronScheduler (Unix/Linux/macOS):**
```python
class CronScheduler:
    def create_job(self, time: str, command: str) -> bool:
        """Create cron job using crontab"""
        
    def remove_job(self) -> bool:
        """Remove cron job"""
        
    def job_exists(self) -> bool:
        """Check if job exists"""
        
    def get_next_run(self) -> Optional[datetime]:
        """Calculate next run time from cron expression"""
```

**TaskScheduler (Windows):**
```python
class TaskScheduler:
    def create_task(self, time: str, command: str) -> bool:
        """Create scheduled task using schtasks"""
        
    def remove_task(self) -> bool:
        """Remove scheduled task"""
        
    def task_exists(self) -> bool:
        """Check if task exists"""
        
    def get_next_run(self) -> Optional[datetime]:
        """Get next run time from task"""
```

### 3. BatchProcessor

**Purpose**: จัดการการประมวลผล log สำหรับหลายวัน

**Interface:**
```python
class BatchProcessor:
    def __init__(self, config: ConfigManager):
        """Initialize with configuration"""
        
    def process_date_range(
        self,
        since: str,
        until: Optional[str] = None,
        force: bool = False,
        author: Optional[str] = None
    ) -> BatchResult:
        """
        Process logs for date range
        
        Args:
            since: Start date (relative or absolute)
            until: End date (default: today)
            force: Force regeneration of existing logs
            author: Filter by author
            
        Returns:
            BatchResult with summary of processed dates
        """
        
    def _expand_date_range(self, since: str, until: Optional[str]) -> List[date]:
        """Convert date range to list of dates"""
        
    def _log_exists(self, date: date) -> bool:
        """Check if log file exists for date"""
        
    def _process_single_date(
        self,
        date: date,
        author: Optional[str]
    ) -> ProcessResult:
        """Process log for single date"""
```

### 4. StatusManager

**Purpose**: จัดการสถานะและประวัติการทำงานของ automated logging

**Interface:**
```python
class StatusManager:
    def __init__(self, status_file: Path):
        """Initialize with status file path"""
        
    def record_run(self, success: bool, error: Optional[str] = None):
        """Record a run attempt"""
        
    def get_last_run(self) -> Optional[datetime]:
        """Get timestamp of last successful run"""
        
    def get_recent_errors(self, limit: int = 5) -> List[ErrorRecord]:
        """Get recent error records"""
        
    def clear_errors(self):
        """Clear error history"""
```

### 5. CLI Commands

**schedule command:**
```python
@click.group()
def schedule():
    """Manage automated daily logging"""
    pass

@schedule.command()
@click.option('--time', '-t', required=True, help='Time in HH:MM format')
def enable(time):
    """Enable automated logging"""
    
@schedule.command()
def disable():
    """Disable automated logging"""
    
@schedule.command()
def status():
    """Show schedule status"""
```

**Enhanced log command:**
```python
@click.command()
@click.option('--since', default='1 day ago')
@click.option('--until', default=None)
@click.option('--force', is_flag=True, help='Force regeneration of existing logs')
@click.option('--batch', is_flag=True, help='Enable batch mode with progress display')
def log(since, until, force, batch):
    """Create daily logs (supports batch processing)"""
```

## Data Models

### ScheduleStatus
```python
@dataclass
class ScheduleStatus:
    enabled: bool
    schedule_time: Optional[str]  # HH:MM format
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    recent_errors: List[ErrorRecord]
    platform: str  # 'cron', 'task_scheduler', or 'unsupported'
```

### BatchResult
```python
@dataclass
class BatchResult:
    total_dates: int
    processed: List[date]
    skipped: List[date]
    failed: List[Tuple[date, str]]  # (date, error_message)
    duration: float  # seconds
```

### ProcessResult
```python
@dataclass
class ProcessResult:
    date: date
    success: bool
    skipped: bool
    error: Optional[str]
    commits_count: int
```

### ErrorRecord
```python
@dataclass
class ErrorRecord:
    timestamp: datetime
    error_message: str
    date_attempted: Optional[date]
```

### Configuration Extension

เพิ่มส่วน `schedule` ใน `config.yaml`:
```yaml
schedule:
  enabled: false
  time: "18:00"  # HH:MM format (24-hour)
  status_file: "./data/schedule_status.json"
  error_log: "./data/schedule_errors.log"
```

## 

## Error Handling

### Error Categories

1. **Scheduling Errors**
   - Permission denied (cron/task scheduler access)
   - Invalid time format
   - Platform not supported
   - Command execution failure

2. **Batch Processing Errors**
   - Invalid date range
   - Git repository access failure
   - AI API failure
   - File system errors

3. **Runtime Errors (Automated Execution)**
   - Configuration file not found
   - Missing API key
   - Network connectivity issues
   - Disk space issues

### Error Handling Strategies

**Scheduling Errors:**
- Validate time format before attempting to create schedule
- Check platform support and provide clear error messages
- Verify write permissions before modifying cron/task scheduler
- Provide fallback suggestions (e.g., manual cron setup instructions)

**Batch Processing Errors:**
- Continue processing remaining dates if one date fails
- Log all errors with context (date, error type, message)
- Display summary of failures at the end
- Provide retry mechanism with `--force` flag

**Runtime Errors:**
- Write errors to dedicated log file with timestamp
- Include error context (date, repository, operation)
- Implement exponential backoff for API failures
- Send error summary to status file for user review

### Error Recovery

**Automated Logging Failures:**
```python
def automated_log_with_retry():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            run_daily_log()
            status_manager.record_run(success=True)
            break
        except APIError as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                status_manager.record_run(success=False, error=str(e))
        except Exception as e:
            status_manager.record_run(success=False, error=str(e))
            break
```

**Batch Processing Resilience:**
- Skip dates with existing logs (unless `--force`)
- Continue on single-date failures
- Collect all errors and display at end
- Provide detailed error messages for debugging

## Testing Strategy

### Unit Testing

ระบบจะใช้ **pytest** สำหรับ unit testing โดยครอบคลุม:

**SchedulerManager Tests:**
- Test platform detection (mock `platform.system()`)
- Test time format validation
- Test enable/disable operations
- Test status retrieval

**BatchProcessor Tests:**
- Test date range expansion with various inputs
- Test existing log detection
- Test single date processing
- Test error handling and continuation

**CronScheduler Tests:**
- Test cron expression generation from time
- Test crontab manipulation (mock subprocess)
- Test job existence checking
- Test next run calculation

**TaskScheduler Tests:**
- Test schtasks command generation
- Test task creation/removal (mock subprocess)
- Test task existence checking

**StatusManager Tests:**
- Test run recording
- Test error logging
- Test status file persistence
- Test error history management

### Property-Based Testing

ระบบจะใช้ **Hypothesis** (Python property-based testing library) สำหรับ property-based testing

**Property Testing Approach:**
- Generate random date ranges and verify all dates are processed
- Generate random time formats and verify validation
- Generate random error scenarios and verify resilience
- Test idempotency of schedule operations

**Key Properties to Test:**
1. Date range expansion always produces valid dates
2. Batch processing handles all dates (success, skip, or fail)
3. Schedule enable/disable is idempotent
4. Status file remains valid JSON after any operation
5. Error logs are always appendable

### Integration Testing

**End-to-End Scenarios:**
- Complete automated scheduling workflow
- Batch processing with mixed existing/new logs
- Error recovery in automated execution
- Cross-platform compatibility (CI/CD on multiple OS)

**Test Environment:**
- Mock git repositories with known commit history
- Mock AI API responses
- Temporary file system for logs and status
- Isolated cron/task scheduler (test mode)


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Schedule operations maintain system consistency

*For any* schedule operation (enable, update, disable), after the operation completes, the system state should be consistent: if enabled, a scheduled task exists with the correct time; if disabled, no scheduled task exists.

**Validates: Requirements 1.1, 2.2, 2.3**

**Rationale:** This property combines the core scheduling operations. Rather than testing each operation separately, we verify that the system maintains consistency between its internal state and the actual scheduled task in the OS. This is a stronger guarantee than testing operations individually.

### Property 2: Configuration parameters are preserved in automated execution

*For any* configuration (author, repositories, schedule time), when automated logging executes, the parameters used should match the configuration file values.

**Validates: Requirements 1.3**

**Rationale:** This ensures that the scheduled execution doesn't lose or corrupt configuration data. It's critical for automated systems to maintain fidelity to user settings.

### Property 3: Automated logging always produces output or error record

*For any* automated logging execution, the system should either create a daily log file at the expected location OR record an error in the error log file.

**Validates: Requirements 1.4, 1.5**

**Rationale:** This is an important invariant - automated execution should never silently fail. Every run must leave a trace, either success (log file) or failure (error record).

### Property 4: Time format validation is consistent

*For any* string input to schedule configuration, the system should accept it if and only if it matches HH:MM format where HH is 00-23 and MM is 00-59.

**Validates: Requirements 2.1**

**Rationale:** Input validation must be deterministic and consistent. This property ensures that time parsing doesn't have edge cases or inconsistencies.

### Property 5: Status display reflects actual system state

*For any* system state (enabled/disabled, scheduled time, last run), the status display should accurately reflect the current state by querying the actual scheduled task and status files.

**Validates: Requirements 2.4, 4.4**

**Rationale:** Status information must be trustworthy. This property ensures we're not displaying stale or cached data, but actually checking the system state.

### Property 6: Date range expansion is complete and ordered

*For any* valid date range (since, until), the expanded list of dates should include all dates between since and until (inclusive), with no duplicates, in chronological order.

**Validates: Requirements 3.1**

**Rationale:** Date range expansion is a pure function that must be correct. Missing dates or duplicates would cause incomplete or redundant processing.

### Property 7: Existing log detection prevents redundant processing

*For any* date with an existing log file, batch processing should skip that date unless the force flag is true.

**Validates: Requirements 3.2, 3.3**

**Rationale:** This is a key optimization property. It ensures we respect existing work and don't waste API calls, while still allowing forced regeneration when needed.

### Property 8: Batch processing summary is accurate

*For any* batch processing run, the summary should correctly count processed, skipped, and failed dates, and the sum should equal the total dates in the range.

**Validates: Requirements 3.4**

**Rationale:** This is an accounting invariant. The summary must accurately reflect what happened during batch processing.

### Property 9: Batch processing is resilient to single-date failures

*For any* batch processing run where one date fails, all other dates in the range should still be attempted.

**Validates: Requirements 3.5**

**Rationale:** This is a resilience property. One failure shouldn't cascade to prevent processing of other dates. This is critical for long-running batch jobs.

### Property 10: Platform detection selects appropriate scheduler

*For any* supported platform (Darwin/macOS, Linux, Windows), the system should select the corresponding scheduler (CronScheduler for Unix-like, TaskScheduler for Windows).

**Validates: Requirements 5.1, 5.2, 5.3**

**Rationale:** Platform detection must be reliable. Using the wrong scheduler would cause all scheduling operations to fail.

### Property 11: Platform-specific commands are syntactically correct

*For any* scheduling operation on a given platform, the generated command should use the correct syntax for that platform's scheduler (crontab for Unix, schtasks for Windows).

**Validates: Requirements 5.4, 5.5**

**Rationale:** Command generation must produce valid syntax. Invalid commands would fail silently or with cryptic errors.

### Property 12: Error logs contain required information

*For any* error that occurs during automated logging, the error log entry should contain both a timestamp and the error message.

**Validates: Requirements 6.1, 6.2**

**Rationale:** Error logs must be useful for debugging. Missing timestamps or messages would make troubleshooting difficult.

### Property 13: Error history is maintained with bounded size

*For any* sequence of errors, the system should maintain a history of recent errors (up to a configured limit) and provide access to them.

**Validates: Requirements 6.4**

**Rationale:** Error history helps identify patterns, but unbounded history could grow indefinitely. This property ensures we keep useful history without memory leaks.

### Property 14: Progress indicators are displayed for each date

*For any* batch processing run with multiple dates, a progress indicator should be displayed for each date showing current position and remaining count.

**Validates: Requirements 7.2**

**Rationale:** Progress feedback is essential for long-running operations. Users need to know the system is working and how much remains.

### Property 15: Skip reasons are always provided

*For any* date that is skipped during batch processing, the system should display a reason (e.g., "log exists", "no commits found").

**Validates: Requirements 7.3**

**Rationale:** Skipped dates without explanation would be confusing. Users need to understand why work was skipped.

### Property 16: Success confirmations are displayed

*For any* date that is successfully processed, the system should display a confirmation message.

**Validates: Requirements 7.4**

**Rationale:** Success feedback is important for user confidence. Silent success could be mistaken for failure or hanging.

