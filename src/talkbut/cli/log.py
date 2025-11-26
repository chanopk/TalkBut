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
        # Determine repository path(s)
        repos_to_process = []
        if repo is None:
            config = ConfigManager()
            repos = config.git_repos
            if repos and len(repos) > 0:
                # Use all configured repositories
                repos_to_process = repos
                click.echo(f"📝 Using {len(repos)} repositories from config:")
                for r in repos:
                    click.echo(f"   • {r.get('name', 'Unnamed')}: {r.get('path', 'N/A')}")
            else:
                # Use current directory
                repos_to_process = [{'path': '.', 'name': 'Current Directory'}]
                click.echo("📝 No repository in config, using current directory")
        else:
            # Use specified repository
            repos_to_process = [{'path': repo, 'name': repo}]
        
        click.echo(f"\n🔍 Collecting commits:")
        click.echo(f"   Since: {since}")
        if until:
            click.echo(f"   Until: {until}")
        if author:
            click.echo(f"   Author: {author}")
        
        # Collect commits from all repositories
        all_commits = []
        parser = DataParser()
        
        for repo_info in repos_to_process:
            repo_path = repo_info.get('path', '.')
            repo_name = repo_info.get('name', repo_path)
            
            try:
                click.echo(f"\n   Processing: {repo_name}...")
                collector = GitCollector(repo_path)
                
                commits = collector.collect_commits(
                    since=since,
                    until=until,
                    author=author,
                    branch=branch,
                    include_diffs=include_diffs
                )
                
                if commits:
                    click.echo(f"   ✓ Found {len(commits)} commits")
                    all_commits.extend(commits)
                else:
                    click.echo(f"   ⚠ No commits found")
                    
            except Exception as e:
                click.echo(f"   ✗ Error: {e}")
                logger.warning(f"Failed to collect from {repo_name}: {e}")
        
        # Use collected commits
        commits = all_commits
        
        if not commits:
            click.echo("\n⚠️  No commits found in the specified range.")
            return
        
        # Sort commits by date (newest first)
        commits.sort(key=lambda c: c.date, reverse=True)
        
        # Enrich commits with parsed metadata
        for commit in commits:
            parser.enrich_commit(commit)
        
        click.echo(f"\n✅ Total: {len(commits)} commits from {len(repos_to_process)} repository(ies)")
        
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
            "tasks": report.tasks if hasattr(report, 'tasks') and report.tasks else []
        }
        
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
        if report.tasks:
            click.echo(f"\n📋 Tasks ({len(report.tasks)}):")
            for task in report.tasks[:5]:
                task_id = task.get('id', 'N/A')
                task_title = task.get('title', 'Untitled')
                task_category = task.get('category', 'Unknown')
                click.echo(f"   • [{task_id}] {task_title} ({task_category})")
        
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error(f"Log generation failed: {e}", exc_info=True)
        click.echo(f"❌ Failed to generate log: {e}", err=True)
        raise click.Abort()
