"""
Report command - สร้างรายงานสรุปผลงาน
"""
import click
from datetime import datetime, date, timedelta
from pathlib import Path
from talkbut.storage.cache import CacheManager
from talkbut.processors.ai_analyzer import AIAnalyzer
from talkbut.processors.formatter import ReportFormatter
from talkbut.utils.logger import get_logger

logger = get_logger(__name__)

@click.command()
@click.option(
    '--date', '-d',
    default='today',
    help='Date for report (e.g., "today", "yesterday", "2023-01-01")'
)
@click.option(
    '--format', '-f',
    type=click.Choice(['markdown', 'json', 'text'], case_sensitive=False),
    default='markdown',
    help='Output format (default: markdown)'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    default=None,
    help='Save report to file (default: print to console)'
)
@click.option(
    '--no-ai',
    is_flag=True,
    help='Skip AI analysis (faster, basic stats only)'
)
def report(date, format, output, no_ai):
    """
    สร้างรายงานสรุปผลงานประจำวัน
    
    Examples:
        talkbut report
        talkbut report --date today --format markdown
        talkbut report --date yesterday --output report.md
        talkbut report --format json --output report.json
        talkbut report --no-ai  # Skip AI analysis
    """
    try:
        # Parse date
        target_date = _parse_date(date)
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        click.echo(f"📄 Generating report for {target_date}")
        
        # Load commits from cache
        cache = CacheManager()
        # Note: This is a simplified version - in production you'd need to
        # implement a way to query cache by date range or load specific cache files
        click.echo("⚠️  This command requires cache query implementation.")
        click.echo("💡 Please run 'talkbut collect' first to gather commit data.")
        return
        
        if not commits:
            click.echo("⚠️  No commits found for the specified date.")
            click.echo("💡 Try running 'talkbut collect' first to gather data.")
            return
        
        click.echo(f"📊 Processing {len(commits)} commits...")
        
        # Generate report
        if no_ai:
            # Basic report without AI
            from talkbut.models.report import DailyReport
            report_obj = DailyReport(
                date=target_date,
                total_commits=len(commits),
                files_changed=len(set(f for c in commits for f in c.files_changed)),
                insertions=sum(c.insertions for c in commits),
                deletions=sum(c.deletions for c in commits),
                commits=commits,
                ai_summary="Basic report (AI analysis skipped)",
                categories={},
                highlights=[],
                timeline=[]
            )
        else:
            # Full report with AI
            click.echo("🤖 Analyzing with AI...")
            analyzer = AIAnalyzer()
            report_obj = analyzer.analyze_commits(commits, target_date)
        
        # Format report
        formatter = ReportFormatter()
        
        if format == 'json':
            content = formatter.format_json(report_obj)
        elif format == 'text':
            content = formatter.format_text(report_obj)
        else:  # markdown
            content = formatter.format_markdown(report_obj)
        
        # Output
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            click.echo(f"✅ Report saved to: {output}")
        else:
            click.echo("\n" + "="*60)
            click.echo(content)
            click.echo("="*60)
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        click.echo(f"❌ Failed to generate report: {e}", err=True)
        raise click.Abort()

def _parse_date(date_str: str) -> date:
    """Parse date string to date object."""
    date_str = date_str.lower().strip()
    
    if date_str == 'today':
        return date.today()
    elif date_str == 'yesterday':
        return date.today() - timedelta(days=1)
    else:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD, 'today', or 'yesterday'")
