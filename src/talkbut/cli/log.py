"""
Log command - รวม collect และ analyze เป็นคำสั่งเดียว สร้าง daily log แบบ JSON
"""
import click
import json
from datetime import datetime
from pathlib import Path
from talkbut.collectors.git_collector import GitCollector
from talkbut.collectors.parser import DataParser
from talkbut.processors.ai_analyzer import AIAnalyzer
from talkbut.core.config import ConfigManager
from talkbut.utils.logger import get_logger

logger = get_logger(__name__)

@click.command()
@click.option(
    '--repo', '-r',
    type=click.Path(exists=True),
    default=None,
    help='Path to git repository (default: from config or current directory)'
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
    '--include-diffs/--no-diffs',
    default=False,
    help='Include file diffs in output (default: no)'
)
@click.option(
    '--unsave',
    is_flag=True,
    default=False,
    help='Display output only, do not save to file'
)
def log(repo, since, until, author, branch, include_diffs, unsave):
    """
    เก็บข้อมูล commits และวิเคราะห์ด้วย AI ในคำสั่งเดียว
    สร้าง daily log แบบ JSON ที่กระชับ และบันทึกเป็นไฟล์อัตโนมัติ
    
    Examples:
        talkbut log
        talkbut log --since "1 day ago"
        talkbut log --unsave
        talkbut log --author "john@example.com"
    """
    try:
        # Determine repository path
        if repo is None:
            config = ConfigManager()
            repos = config.git_repos
            if repos and len(repos) > 0:
                repo = repos[0].get('path', '.')
                click.echo(f"📝 Using repository from config: {repos[0].get('name', repo)}")
            else:
                repo = '.'
                click.echo("📝 No repository in config, using current directory")
        
        click.echo(f"🔍 Collecting commits from: {repo}")
        click.echo(f"   Since: {since}")
        if until:
            click.echo(f"   Until: {until}")
        if author:
            click.echo(f"   Author: {author}")
        
        # Initialize collector
        collector = GitCollector(repo)
        parser = DataParser()
        
        # Collect commits with optional diffs
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
        
        # Analyze with AI
        click.echo("🤖 Analyzing with AI...")
        analyzer = AIAnalyzer()
        
        # Use the first commit's date as report date
        report_date = commits[0].date.date()
        report = analyzer.analyze_commits(commits, report_date)
        
        # Build compact daily log
        daily_log = {
            "date": report_date.isoformat(),
            "summary": report.ai_summary,
            "stats": {
                "commits": report.total_commits,
                "files": report.files_changed,
                "insertions": report.insertions,
                "deletions": report.deletions
            },
            "categories": report.categories,
            "highlights": report.highlights,
            "commits": []
        }
        
        # Add commits with selective fields
        for commit in commits:
            commit_data = {
                "hash": commit.short_hash,
                "time": commit.date.strftime('%H:%M'),
                "message": commit.message.split('\n')[0],  # First line only
                "files": commit.files_changed,
                "changes": f"+{commit.insertions}/-{commit.deletions}"
            }
            
            # Add ticket refs if available
            if commit.ticket_refs:
                commit_data["tickets"] = commit.ticket_refs
            
            # Add diffs if requested
            if include_diffs and commit.file_diffs:
                commit_data["diffs"] = commit.file_diffs
            
            daily_log["commits"].append(commit_data)
        
        # Format JSON (always compact)
        json_output = json.dumps(daily_log, ensure_ascii=False, separators=(',', ':'))
        
        # Output
        if unsave:
            # Display only, do not save
            click.echo("\n📋 Daily Log:")
            click.echo(json_output)
        else:
            # Save to file automatically
            # Generate filename: daily_log_YYYY-MM-DD.json
            filename = f"daily_log_{report_date.isoformat()}.json"
            output_dir = Path("data/logs")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / filename
            
            # Remove old file if exists (no prompt)
            if output_path.exists():
                output_path.unlink()
                click.echo(f"🗑️  Removed old file: {output_path}")
            
            # Save new file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_output)
            click.echo(f"\n💾 Daily log saved to: {output_path}")
        
        # Show summary
        click.echo(f"\n✨ Summary:")
        click.echo(f"   {report.ai_summary[:100]}...")
        if report.highlights:
            click.echo(f"\n🎯 Highlights:")
            for highlight in report.highlights[:3]:
                click.echo(f"   • {highlight}")
        
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error(f"Log generation failed: {e}", exc_info=True)
        click.echo(f"❌ Failed to generate log: {e}", err=True)
        raise click.Abort()
