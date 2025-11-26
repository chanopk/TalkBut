"""
Collect command - เก็บข้อมูลจาก Git repository
"""
import click
from datetime import datetime, timedelta
from pathlib import Path
from talkbut.collectors.git_collector import GitCollector
from talkbut.collectors.parser import DataParser
from talkbut.utils.logger import get_logger

logger = get_logger(__name__)

@click.command()
@click.option(
    '--repo', '-r',
    type=click.Path(exists=True),
    default='.',
    help='Path to git repository (default: current directory)'
)
@click.option(
    '--since', '-s',
    default='1 day ago',
    help='Start date/time (e.g., "1 day ago", "2023-01-01", "yesterday")'
)
@click.option(
    '--until', '-u',
    default=None,
    help='End date/time (default: now)'
)
@click.option(
    '--author', '-a',
    default=None,
    help='Filter by author email or name'
)
@click.option(
    '--branch', '-b',
    default=None,
    help='Filter by branch (default: current branch)'
)
@click.option(
    '--save/--no-save',
    default=True,
    help='Save to cache (default: yes)'
)
@click.option(
    '--include-diffs/--no-diffs',
    default=False,
    help='Include file diffs in collected data (default: no)'
)
def collect(repo, since, until, author, branch, save, include_diffs):
    """
    เก็บข้อมูล commits จาก Git repository
    
    Examples:
        talkbut collect
        talkbut collect --repo /path/to/project
        talkbut collect --since "2023-01-01" --until "2023-01-31"
        talkbut collect --author "john@example.com"
    """
    try:
        click.echo(f"🔍 Collecting commits from: {repo}")
        click.echo(f"   Since: {since}")
        if until:
            click.echo(f"   Until: {until}")
        if author:
            click.echo(f"   Author: {author}")
        
        # Initialize collector
        collector = GitCollector(repo)
        parser = DataParser()
        
        # Collect commits
        commits = collector.collect_commits(
            since=since,
            until=until,
            author=author,
            branch=branch,
            include_diffs=include_diffs
        )
        
        if not commits:
            click.echo("⚠️  No commits found in the specified range.")
            return
        
        # Enrich commits with parsed metadata
        for commit in commits:
            parser.enrich_commit(commit)
        
        click.echo(f"✅ Found {len(commits)} commits")
        
        # Display summary
        total_insertions = sum(c.insertions for c in commits)
        total_deletions = sum(c.deletions for c in commits)
        files_changed = set()
        for c in commits:
            files_changed.update(c.files_changed)
        
        click.echo(f"   Files changed: {len(files_changed)}")
        click.echo(f"   Changes: +{total_insertions} / -{total_deletions}")
        
        # Note: Cache functionality removed - use 'talkbut log' for complete workflow
        if save:
            click.echo("\n💡 Tip: Use 'talkbut log' to collect and analyze in one step")
        
        # Show sample commits
        click.echo("\n📋 Recent commits:")
        for commit in commits[:5]:
            time_str = commit.date.strftime('%Y-%m-%d %H:%M')
            msg_preview = commit.message.split('\n')[0][:60]
            click.echo(f"   [{time_str}] {commit.short_hash} - {msg_preview}")
        
        if len(commits) > 5:
            click.echo(f"   ... and {len(commits) - 5} more")
            
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error(f"Collection failed: {e}", exc_info=True)
        click.echo(f"❌ Failed to collect commits: {e}", err=True)
        raise click.Abort()
