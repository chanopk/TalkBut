# Implementation Plan

- [x] 1. Create core scheduling infrastructure
  - [x] 1.1 Implement platform detection utility
    - Create function to detect OS (Darwin/Linux/Windows)
    - Return appropriate scheduler type
    - _Requirements: 5.3_

  - [x] 1.2 Implement CronScheduler for Unix-like systems
    - Create CronScheduler class with create_job, remove_job, job_exists methods
    - Generate cron expression from HH:MM time format
    - Use subprocess to interact with crontab
    - Calculate next run time from cron expression
    - _Requirements: 5.1, 5.4, 5.5_

  - [x] 1.3 Write property test for CronScheduler
    - **Property 11: Platform-specific commands are syntactically correct**
    - **Validates: Requirements 5.4, 5.5**

  - [x] 1.4 Implement TaskScheduler for Windows
    - Create TaskScheduler class with create_task, remove_task, task_exists methods
    - Generate schtasks command from HH:MM time format
    - Use subprocess to interact with schtasks
    - Parse task information to get next run time
    - _Requirements: 5.2, 5.4, 5.5_

  - [x] 1.5 Write property test for TaskScheduler
    - **Property 11: Platform-specific commands are syntactically correct**
    - **Validates: Requirements 5.4, 5.5**

  - [x] 1.6 Implement SchedulerManager with platform abstraction
    - Create SchedulerManager class that wraps platform-specific schedulers
    - Implement enable, disable, update, get_status, is_enabled methods
    - Use platform detection to select appropriate scheduler
    - _Requirements: 1.1, 2.2, 2.3, 5.3_

  - [x] 1.7 Write property test for SchedulerManager
    - **Property 1: Schedule operations maintain system consistency**
    - **Validates: Requirements 1.1, 2.2, 2.3**

  - [x] 1.8 Write property test for platform detection
    - **Property 10: Platform detection selects appropriate scheduler**
    - **Validates: Requirements 5.1, 5.2, 5.3**

- [x] 2. Implement time validation and configuration
  - [x] 2.1 Create time format validator
    - Implement function to validate HH:MM format
    - Check HH is 00-23 and MM is 00-59
    - Return validation result with error message
    - _Requirements: 2.1_

  - [x] 2.2 Write property test for time validation
    - **Property 4: Time format validation is consistent**
    - **Validates: Requirements 2.1**

  - [x] 2.3 Extend ConfigManager for schedule settings
    - Add schedule section to config schema
    - Add methods to get/set schedule configuration
    - Include enabled, time, status_file, error_log fields
    - _Requirements: 1.3, 2.1_

  - [x] 2.4 Write property test for configuration preservation
    - **Property 2: Configuration parameters are preserved in automated execution**
    - **Validates: Requirements 1.3**

- [x] 3. Implement status tracking and error logging
  - [x] 3.1 Create StatusManager class
    - Implement record_run, get_last_run, get_recent_errors, clear_errors methods
    - Use JSON file for status persistence
    - Maintain bounded error history (default: 50 entries)
    - _Requirements: 4.3, 6.4_

  - [x] 3.2 Write property test for error history management
    - **Property 13: Error history is maintained with bounded size**
    - **Validates: Requirements 6.4**

  - [x] 3.3 Implement error logging functionality
    - Create function to write errors to log file
    - Include timestamp and error message in each entry
    - Append to error log file (don't overwrite)
    - _Requirements: 1.5, 6.1, 6.2_

  - [x] 3.4 Write property test for error log format
    - **Property 12: Error logs contain required information**
    - **Validates: Requirements 6.1, 6.2**

  - [x] 3.5 Implement status display functionality
    - Create function to format and display schedule status
    - Show enabled/disabled, schedule time, last run, next run, recent errors
    - Query actual system state (not just cached data)
    - _Requirements: 2.4, 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 3.6 Write property test for status accuracy
    - **Property 5: Status display reflects actual system state**
    - **Validates: Requirements 2.4, 4.4**

- [x] 4. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 5. Implement batch processing functionality
  - [x] 5.1 Create date range expansion utility
    - Implement function to parse since/until parameters
    - Support relative dates ("7 days ago") and absolute dates ("2025-12-01")
    - Generate list of all dates in range (inclusive)
    - Return dates in chronological order with no duplicates
    - _Requirements: 3.1_

  - [x] 5.2 Write property test for date range expansion
    - **Property 6: Date range expansion is complete and ordered**
    - **Validates: Requirements 3.1**

  - [x] 5.3 Implement existing log detection
    - Create function to check if log file exists for a given date
    - Use standard log file naming convention (daily_log_YYYY-MM-DD.json)
    - Check in configured log directory
    - _Requirements: 3.2_

  - [x] 5.4 Create BatchProcessor class
    - Implement process_date_range method
    - Implement _process_single_date method for individual date processing
    - Handle force flag to override existing log detection
    - Collect results (processed, skipped, failed) for summary
    - _Requirements: 3.2, 3.3, 3.4, 3.5_

  - [x] 5.5 Write property test for existing log detection
    - **Property 7: Existing log detection prevents redundant processing**
    - **Validates: Requirements 3.2, 3.3**

  - [ ] 5.6 Write property test for batch summary accuracy
    - **Property 8: Batch processing summary is accurate**
    - **Validates: Requirements 3.4**

  - [ ]* 5.7 Write property test for batch resilience
    - **Property 9: Batch processing is resilient to single-date failures**
    - **Validates: Requirements 3.5**

  - [x] 5.8 Implement progress display for batch processing
    - Display total dates at start
    - Show progress indicator for each date (current/total)
    - Display skip reasons when dates are skipped
    - Display success confirmation for each processed date
    - Display final summary with statistics
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 5.9 Write property test for progress indicators
    - **Property 14: Progress indicators are displayed for each date**
    - **Validates: Requirements 7.2**

  - [ ]* 5.10 Write property test for skip reasons
    - **Property 15: Skip reasons are always provided**
    - **Validates: Requirements 7.3**

  - [ ]* 5.11 Write property test for success confirmations
    - **Property 16: Success confirmations are displayed**
    - **Validates: Requirements 7.4**

- [x] 6. Enhance log command for batch processing
  - [x] 6.1 Update log command to use BatchProcessor
    - Modify log command to detect date ranges (multiple days)
    - Use BatchProcessor when range spans multiple days
    - Add --force flag to override existing log detection
    - Add --batch flag to explicitly enable batch mode with progress
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

  - [x] 6.2 Integrate progress display into log command
    - Show progress when processing multiple dates
    - Display summary at the end
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

  - [ ]* 6.3 Write property test for output guarantee
    - **Property 3: Automated logging always produces output or error record**
    - **Validates: Requirements 1.4, 1.5**

- [x] 7. Create schedule CLI commands
  - [x] 7.1 Create schedule command group
    - Add schedule command group to CLI
    - _Requirements: 1.1, 2.2, 2.3, 2.4_

  - [x] 7.2 Implement schedule enable command
    - Add --time option for HH:MM format
    - Validate time format before enabling
    - Use SchedulerManager to create scheduled task
    - Display success message with next run time
    - _Requirements: 1.1, 2.1_

  - [x] 7.3 Implement schedule disable command
    - Use SchedulerManager to remove scheduled task
    - Display confirmation message
    - _Requirements: 2.3_

  - [x] 7.4 Implement schedule status command
    - Use SchedulerManager to get current status
    - Display enabled/disabled, schedule time, last run, next run
    - Display recent errors if any
    - _Requirements: 2.4, 4.1, 4.2, 4.3, 4.4, 4.5_

  - [x] 7.5 Implement schedule update command
    - Add --time option for new time
    - Validate time format
    - Use SchedulerManager to update schedule
    - Display confirmation with new next run time
    - _Requirements: 2.2_

- [x] 8. Create automated execution wrapper
  - [x] 8.1 Create standalone script for scheduled execution
    - Create script that can be called by cron/Task Scheduler
    - Load configuration from standard location
    - Execute log command with configured parameters
    - Handle errors and log to error file
    - Record run status using StatusManager
    - _Requirements: 1.2, 1.3, 1.4, 1.5_

  - [x] 8.2 Implement retry logic with exponential backoff
    - Retry on API failures (up to 3 attempts)
    - Use exponential backoff between retries
    - Log final failure if all retries exhausted
    - _Requirements: 1.5_

- [x] 9. Update configuration and documentation
  - [x] 9.1 Add schedule section to config.yaml.example
    - Add schedule configuration with defaults
    - Document all schedule options
    - _Requirements: 2.1_

  - [x] 9.2 Update README with automated logging instructions
    - Add section on automated scheduling
    - Add examples for schedule commands
    - Add examples for batch processing
    - Document platform-specific considerations

- [x] 10. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
