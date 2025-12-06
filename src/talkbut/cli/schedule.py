"""
TalkBut CLI - Schedule commands for automated daily logging
"""
import click
from pathlib import Path

from talkbut.core.config import ConfigManager
from talkbut.scheduling.scheduler_manager import SchedulerManager
from talkbut.scheduling.status_manager import StatusManager
from talkbut.scheduling.status_display import display_status
from talkbut.scheduling.validators import validate_time_format
from talkbut.utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
def schedule():
    """
    Manage automated daily logging schedule.
    
    \b
    Examples:
        talkbut schedule enable --time 18:00
        talkbut schedule status
        talkbut schedule update --time 09:00
        talkbut schedule disable
    """
    pass


@schedule.command()
@click.option(
    '--time', '-t',
    required=True,
    help='Time in HH:MM format (24-hour), e.g., 09:00 or 18:30'
)
def enable(time):
    """
    Enable automated daily logging at specified time.
    
    Creates a scheduled task that runs 'talkbut log' daily at the specified time.
    Uses cron on Unix-like systems (macOS, Linux) and Task Scheduler on Windows.
    
    Requirements: 1.1, 2.1
    """
    # Validate time format
    is_valid, error_msg = validate_time_format(time)
    if not is_valid:
        click.echo(f"❌ Invalid time format: {error_msg}", err=True)
        raise click.Abort()
    
    # Load configuration
    config = ConfigManager()
    schedule_config = config.get_schedule_config()
    
    # Initialize status manager
    status_file = Path(schedule_config['status_file'])
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_manager = StatusManager(status_file)
    
    # Initialize scheduler manager
    scheduler_manager = SchedulerManager(config=config, status_manager=status_manager)
    
    # Check if already enabled
    if scheduler_manager.is_enabled():
        click.echo("⚠️  Automated logging is already enabled.")
        click.echo("Use 'talkbut schedule update --time HH:MM' to change the time.")
        return
    
    # Enable scheduling
    click.echo(f"Enabling automated daily logging at {time}...")
    
    success = scheduler_manager.enable(time)
    
    if success:
        # Update config
        config.set_schedule_config(enabled=True, time=time)
        
        # Get next run time
        status = scheduler_manager.get_status()
        
        click.echo(f"✓ Automated logging enabled successfully!")
        click.echo(f"  Schedule: Daily at {time}")
        
        if status.next_run:
            click.echo(f"  Next run: {status.next_run.strftime('%Y-%m-%d %H:%M:%S')}")
        
        click.echo(f"\nUse 'talkbut schedule status' to check the schedule.")
    else:
        click.echo("❌ Failed to enable automated logging.", err=True)
        click.echo("Please check that you have permission to create scheduled tasks.", err=True)
        raise click.Abort()


@schedule.command()
def disable():
    """
    Disable automated daily logging.
    
    Removes the scheduled task from the system.
    
    Requirements: 2.3
    """
    # Load configuration
    config = ConfigManager()
    schedule_config = config.get_schedule_config()
    
    # Initialize status manager
    status_file = Path(schedule_config['status_file'])
    status_manager = StatusManager(status_file) if status_file.exists() else None
    
    # Initialize scheduler manager
    scheduler_manager = SchedulerManager(config=config, status_manager=status_manager)
    
    # Check if already disabled
    if not scheduler_manager.is_enabled():
        click.echo("ℹ️  Automated logging is already disabled.")
        return
    
    # Disable scheduling
    click.echo("Disabling automated daily logging...")
    
    success = scheduler_manager.disable()
    
    if success:
        # Update config
        config.set_schedule_config(enabled=False)
        
        click.echo("✓ Automated logging disabled successfully!")
    else:
        click.echo("❌ Failed to disable automated logging.", err=True)
        click.echo("Please check that you have permission to remove scheduled tasks.", err=True)
        raise click.Abort()


@schedule.command()
def status():
    """
    Show current schedule status.
    
    Displays:
    - Enabled/disabled status
    - Configured schedule time
    - Last successful run
    - Next scheduled run
    - Recent errors (if any)
    
    Requirements: 2.4, 4.1, 4.2, 4.3, 4.4, 4.5
    """
    # Load configuration
    config = ConfigManager()
    schedule_config = config.get_schedule_config()
    
    # Initialize status manager
    status_file = Path(schedule_config['status_file'])
    status_manager = StatusManager(status_file) if status_file.exists() else None
    
    # Initialize scheduler manager
    scheduler_manager = SchedulerManager(config=config, status_manager=status_manager)
    
    # Display status
    display_status(scheduler_manager, status_manager)


@schedule.command()
@click.option(
    '--time', '-t',
    required=True,
    help='New time in HH:MM format (24-hour), e.g., 09:00 or 18:30'
)
def update(time):
    """
    Update the schedule time.
    
    Changes the time when automated daily logging runs.
    
    Requirements: 2.2
    """
    # Validate time format
    is_valid, error_msg = validate_time_format(time)
    if not is_valid:
        click.echo(f"❌ Invalid time format: {error_msg}", err=True)
        raise click.Abort()
    
    # Load configuration
    config = ConfigManager()
    schedule_config = config.get_schedule_config()
    
    # Initialize status manager
    status_file = Path(schedule_config['status_file'])
    status_file.parent.mkdir(parents=True, exist_ok=True)
    status_manager = StatusManager(status_file)
    
    # Initialize scheduler manager
    scheduler_manager = SchedulerManager(config=config, status_manager=status_manager)
    
    # Check if enabled
    if not scheduler_manager.is_enabled():
        click.echo("⚠️  Automated logging is not enabled.")
        click.echo("Use 'talkbut schedule enable --time HH:MM' to enable it first.")
        return
    
    # Update schedule
    click.echo(f"Updating schedule to {time}...")
    
    success = scheduler_manager.update(time)
    
    if success:
        # Update config
        config.set_schedule_config(time=time)
        
        # Get next run time
        status = scheduler_manager.get_status()
        
        click.echo(f"✓ Schedule updated successfully!")
        click.echo(f"  New schedule: Daily at {time}")
        
        if status.next_run:
            click.echo(f"  Next run: {status.next_run.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        click.echo("❌ Failed to update schedule.", err=True)
        click.echo("Please check that you have permission to modify scheduled tasks.", err=True)
        raise click.Abort()
