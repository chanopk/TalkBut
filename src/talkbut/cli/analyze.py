"""
Analyze command - วิเคราะห์ข้อมูลด้วย AI
"""
import click
from datetime import datetime, date, timedelta
from talkbut.processors.ai_analyzer import AIAnalyzer
from talkbut.utils.logger import get_logger

logger = get_logger(__name__)

@click.command()
@click.option(
    '--date', '-d',
    default='today',
    help='Date to analyze (e.g., "today", "yesterday", "2023-01-01")'
)
@click.option(
    '--since', '-s',
    default=None,
    help='Start date for range analysis'
)
@click.option(
    '--until', '-u',
    default=None,
    help='End date for range analysis'
)
@click.option(
    '--output', '-o',
    type=click.Path(),
    default=None,
    help='Save analysis to file'
)
def analyze(date, since, until, output):
    """
    วิเคราะห์ commits ด้วย AI และสร้างรายงาน
    
    Examples:
        talkbut analyze
        talkbut analyze --date today
        talkbut analyze --date yesterday
        talkbut analyze --date 2023-01-15
        talkbut analyze --since 2023-01-01 --until 2023-01-31
    """
    try:
        # Parse date
        if since and until:
            start_date = _parse_date(since)
            end_date = _parse_date(until)
            click.echo(f"🔍 Analyzing commits from {start_date} to {end_date}")
        else:
            target_date = _parse_date(date)
            start_date = datetime.combine(target_date, datetime.min.time())
            end_date = datetime.combine(target_date, datetime.max.time())
            click.echo(f"🔍 Analyzing commits for {target_date}")
        
        # Note: Cache functionality removed
        click.echo("⚠️  This command is deprecated.")
        click.echo("💡 Use 'talkbut log' instead - it collects and analyzes in one step.")
        return
        
        click.echo(f"📊 Found {len(commits)} commits to analyze")
        
        # Analyze with AI
        click.echo("🤖 Analyzing with AI...")
        analyzer = AIAnalyzer()
        report = analyzer.analyze_commits(commits, target_date if not since else start_date.date())
        
        # Display summary
        click.echo("\n" + "="*60)
        click.echo(f"📝 AI Summary:")
        click.echo("="*60)
        click.echo(report.ai_summary)
        click.echo("")
        
        if report.highlights:
            click.echo("✨ Highlights:")
            for highlight in report.highlights:
                click.echo(f"   • {highlight}")
            click.echo("")
        
        if report.categories:
            click.echo("🏷️  Work Breakdown:")
            for category, count in report.categories.items():
                click.echo(f"   • {category}: {count}")
            click.echo("")
        
        click.echo("📊 Statistics:")
        click.echo(f"   • Total Commits: {report.total_commits}")
        click.echo(f"   • Files Changed: {report.files_changed}")
        click.echo(f"   • Changes: +{report.insertions} / -{report.deletions}")
        
        # Save to file if requested
        if output:
            from talkbut.processors.formatter import ReportFormatter
            formatter = ReportFormatter()
            
            # Determine format from extension
            if output.endswith('.json'):
                content = formatter.format_json(report)
            elif output.endswith('.txt'):
                content = formatter.format_text(report)
            else:
                content = formatter.format_markdown(report)
            
            with open(output, 'w', encoding='utf-8') as f:
                f.write(content)
            
            click.echo(f"\n💾 Report saved to: {output}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        click.echo(f"❌ Analysis failed: {e}", err=True)
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
