"""
Progress display utilities for batch processing.

Requirements: 7.1, 7.2, 7.3, 7.4, 7.5
"""
import click
from datetime import date
from typing import List, Tuple
from talkbut.processors.batch_processor import ProcessResult, BatchResult


def display_batch_start(total_dates: int, since: str, until: str = None):
    """
    Display batch processing start message.
    
    Args:
        total_dates: Total number of dates to process
        since: Start date string
        until: End date string (optional)
        
    Requirements: 7.1
    """
    click.echo(f"\n📦 Batch Processing")
    click.echo(f"   Total dates: {total_dates}")
    click.echo(f"   Range: {since}" + (f" to {until}" if until else " to today"))
    click.echo()


def display_progress(
    current_date: date,
    index: int,
    total: int,
    result: ProcessResult
):
    """
    Display progress for a single date.
    
    Args:
        current_date: Date being processed
        index: Current position (1-indexed)
        total: Total number of dates
        result: ProcessResult for this date
        
    Requirements: 7.2, 7.3, 7.4
    """
    # Progress indicator
    progress = f"[{index}/{total}]"
    date_str = current_date.isoformat()
    
    if result.skipped:
        # Display skip reason
        click.echo(f"{progress} {date_str} - ⏭️  Skipped (log already exists)")
    elif result.success:
        # Display success confirmation
        commits_info = f"{result.commits_count} commit(s)" if result.commits_count > 0 else "no commits"
        click.echo(f"{progress} {date_str} - ✅ Processed ({commits_info})")
    else:
        # Display error
        error_msg = result.error or "Unknown error"
        click.echo(f"{progress} {date_str} - ❌ Failed: {error_msg}")


def display_batch_summary(result: BatchResult):
    """
    Display final batch processing summary with statistics.
    
    Args:
        result: BatchResult with processing outcomes
        
    Requirements: 7.5
    """
    click.echo(f"\n{'='*60}")
    click.echo("📊 Batch Processing Summary")
    click.echo(f"{'='*60}")
    
    # Statistics
    click.echo(f"Total dates:     {result.total_dates}")
    click.echo(f"✅ Processed:    {len(result.processed)}")
    click.echo(f"⏭️  Skipped:      {len(result.skipped)}")
    click.echo(f"❌ Failed:       {len(result.failed)}")
    click.echo(f"⏱️  Duration:     {result.duration:.2f}s")
    
    # Show failed dates with errors if any
    if result.failed:
        click.echo(f"\n❌ Failed Dates:")
        for failed_date, error in result.failed:
            click.echo(f"   • {failed_date.isoformat()}: {error}")
    
    # Success message
    if len(result.processed) > 0:
        click.echo(f"\n✨ Successfully processed {len(result.processed)} date(s)")
    
    click.echo(f"{'='*60}\n")


def create_progress_callback():
    """
    Create a progress callback function for BatchProcessor.
    
    Returns:
        Callback function that displays progress
        
    Requirements: 7.2, 7.3, 7.4
    """
    def callback(current_date: date, index: int, total: int, result: ProcessResult):
        display_progress(current_date, index, total, result)
    
    return callback
