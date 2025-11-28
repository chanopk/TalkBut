"""
Report command - สร้างรายงานสรุปจาก daily logs หลายวัน
"""
import click
import json
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

import google.generativeai as genai

from talkbut.core.config import ConfigManager
from talkbut.utils.logger import get_logger

logger = get_logger(__name__)

MAX_DAYS = 30  # Maximum days allowed for report


@click.command()
@click.option(
    '--days', '-d',
    type=int,
    default=7,
    help=f'Number of days to include (max: {MAX_DAYS}, default: 7)'
)
@click.option(
    '--start', '-s',
    type=str,
    default=None,
    help='Start date (YYYY-MM-DD). If not specified, uses --days from today'
)
@click.option(
    '--end', '-e',
    type=str,
    default=None,
    help='End date (YYYY-MM-DD, default: today)'
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
def report(days, start, end, format, output):
    """สร้างรายงานสรุปจาก daily logs (ย้อนหลังได้สูงสุด 1 เดือน)"""
    try:
        # Parse dates
        end_date = _parse_date(end) if end else date.today()
        
        if start:
            start_date = _parse_date(start)
        else:
            start_date = end_date - timedelta(days=days - 1)
        
        # Validate date range
        date_range = (end_date - start_date).days + 1
        if date_range > MAX_DAYS:
            click.echo(f"❌ Date range exceeds maximum of {MAX_DAYS} days ({date_range} days requested)")
            click.echo(f"💡 Try a shorter range or use --days {MAX_DAYS}")
            raise click.Abort()
        
        if date_range < 1:
            click.echo("❌ Invalid date range: start date must be before end date")
            raise click.Abort()
        
        click.echo(f"📊 Generating report: {start_date} to {end_date} ({date_range} days)")
        
        # Load daily logs
        daily_logs = _load_daily_logs(start_date, end_date)
        
        if not daily_logs:
            click.echo("⚠️  No daily logs found in the specified range.")
            click.echo("💡 Run 'talkbut log' first to generate daily logs.")
            return
        
        click.echo(f"📁 Found {len(daily_logs)} daily log(s)")
        
        # Generate report with AI
        click.echo("🤖 Analyzing with AI...")
        report_data = _generate_report(daily_logs, start_date, end_date)
        
        if not report_data:
            click.echo("❌ Failed to generate report")
            raise click.Abort()
        
        # Format output
        if format == 'json':
            content = json.dumps(report_data, ensure_ascii=False, indent=2)
        elif format == 'text':
            content = _format_text(report_data)
        else:  # markdown
            content = _format_markdown(report_data)
        
        # Output
        if output:
            output_path = Path(output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            click.echo(f"✅ Report saved to: {output}")
        else:
            click.echo("\n" + "=" * 60)
            click.echo(content)
            click.echo("=" * 60)
        
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
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
            raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD")


def _load_daily_logs(start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """Load daily logs from files within date range."""
    logs_dir = Path("data/logs")
    daily_logs = []
    
    if not logs_dir.exists():
        return []
    
    current_date = start_date
    while current_date <= end_date:
        filename = f"daily_log_{current_date.isoformat()}.json"
        filepath = logs_dir / filename
        
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
                    daily_logs.append(log_data)
            except Exception as e:
                logger.warning(f"Failed to load {filename}: {e}")
        
        current_date += timedelta(days=1)
    
    return daily_logs


def _generate_report(daily_logs: List[Dict], start_date: date, end_date: date) -> Optional[Dict]:
    """Generate report using AI."""
    config = ConfigManager()
    api_key = config.ai_api_key
    
    if not api_key:
        logger.warning("No API key found. Cannot generate AI report.")
        return _generate_basic_report(daily_logs, start_date, end_date)
    
    # Calculate totals
    total_commits = sum(log.get('stats', {}).get('commits', 0) for log in daily_logs)
    total_files = sum(log.get('stats', {}).get('files', 0) for log in daily_logs)
    total_insertions = sum(log.get('stats', {}).get('insertions', 0) for log in daily_logs)
    total_deletions = sum(log.get('stats', {}).get('deletions', 0) for log in daily_logs)
    
    # Build logs text
    daily_logs_text = ""
    for log in daily_logs:
        log_date = log.get('date', 'Unknown')
        summary = log.get('summary', 'No summary')
        tasks = log.get('tasks', [])
        categories = log.get('categories', {})
        
        daily_logs_text += f"\n--- {log_date} ---\n"
        daily_logs_text += f"Summary: {summary}\n"
        daily_logs_text += f"Categories: {json.dumps(categories)}\n"
        daily_logs_text += f"Tasks ({len(tasks)}):\n"
        for task in tasks:
            task_id = task.get('id', 'N/A')
            title = task.get('title', 'Untitled')
            category = task.get('category', 'Other')
            daily_logs_text += f"  - [{task_id}] {title} ({category})\n"
    
    # Load prompt template
    prompt_path = Path("config/prompts/report_prompt.txt")
    if prompt_path.exists():
        with open(prompt_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
    else:
        logger.error("Report prompt template not found")
        return _generate_basic_report(daily_logs, start_date, end_date)
    
    # Build prompt
    prompt = prompt_template.format(
        start_date=start_date.isoformat(),
        end_date=end_date.isoformat(),
        total_days=len(daily_logs),
        total_commits=total_commits,
        total_files=total_files,
        total_insertions=total_insertions,
        total_deletions=total_deletions,
        daily_logs_text=daily_logs_text
    )
    
    # Call AI
    try:
        genai.configure(api_key=api_key)
        model_name = config.get("ai.model", "gemini-2.0-flash-exp")
        model = genai.GenerativeModel(model_name=model_name)
        
        generation_config = {
            "temperature": config.get("ai.temperature", 0.3),
            "top_p": config.get("ai.top_p", 0.95),
            "top_k": config.get("ai.top_k", 40),
            "max_output_tokens": config.get("ai.max_output_tokens", 8192),
        }
        
        response = model.generate_content(prompt, generation_config=generation_config)
        ai_text = response.text.strip()
        
        # Remove markdown code blocks if present
        if ai_text.startswith("```"):
            lines = ai_text.split("\n")
            ai_text = "\n".join(lines[1:-1]) if len(lines) > 2 else ai_text
            ai_text = ai_text.replace("```json", "").replace("```", "").strip()
        
        return json.loads(ai_text)
        
    except Exception as e:
        logger.error(f"AI report generation failed: {e}")
        return _generate_basic_report(daily_logs, start_date, end_date)


def _generate_basic_report(daily_logs: List[Dict], start_date: date, end_date: date) -> Dict:
    """Generate basic report without AI."""
    total_commits = sum(log.get('stats', {}).get('commits', 0) for log in daily_logs)
    total_files = sum(log.get('stats', {}).get('files', 0) for log in daily_logs)
    total_insertions = sum(log.get('stats', {}).get('insertions', 0) for log in daily_logs)
    total_deletions = sum(log.get('stats', {}).get('deletions', 0) for log in daily_logs)
    
    # Aggregate categories
    all_categories: Dict[str, int] = {}
    for log in daily_logs:
        for cat, count in log.get('categories', {}).items():
            all_categories[cat] = all_categories.get(cat, 0) + count
    
    # Build daily breakdown
    daily_breakdown = []
    for log in daily_logs:
        daily_breakdown.append({
            "date": log.get('date', 'Unknown'),
            "summary": log.get('summary', 'No summary')[:100],
            "task_count": len(log.get('tasks', []))
        })
    
    return {
        "title": f"Development Report: {start_date} to {end_date}",
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": len(daily_logs)
        },
        "executive_summary": f"Report covers {len(daily_logs)} days with {total_commits} commits.",
        "highlights": [],
        "themes": [],
        "statistics": {
            "total_commits": total_commits,
            "total_files": total_files,
            "total_insertions": total_insertions,
            "total_deletions": total_deletions,
            "categories": all_categories
        },
        "daily_breakdown": daily_breakdown,
        "insights": "Basic report generated without AI analysis."
    }


def _format_markdown(report: Dict) -> str:
    """Format report as Markdown."""
    md = []
    
    # Title
    title = report.get('title', 'Development Report')
    md.append(f"# {title}")
    md.append("")
    
    # Period
    period = report.get('period', {})
    md.append(f"📅 **Period**: {period.get('start', 'N/A')} to {period.get('end', 'N/A')} ({period.get('days', 0)} days)")
    md.append("")
    
    # Executive Summary
    md.append("## 📝 Executive Summary")
    md.append(report.get('executive_summary', 'No summary available.'))
    md.append("")
    
    # Highlights
    highlights = report.get('highlights', [])
    if highlights:
        md.append("## ✨ Highlights")
        for h in highlights:
            md.append(f"- {h}")
        md.append("")
    
    # Statistics
    stats = report.get('statistics', {})
    md.append("## 📊 Statistics")
    md.append(f"- **Total Commits**: {stats.get('total_commits', 0)}")
    md.append(f"- **Files Changed**: {stats.get('total_files', 0)}")
    md.append(f"- **Lines Added**: +{stats.get('total_insertions', 0)}")
    md.append(f"- **Lines Removed**: -{stats.get('total_deletions', 0)}")
    md.append("")
    
    # Categories
    categories = stats.get('categories', {})
    if categories:
        md.append("### Work Breakdown")
        for cat, count in categories.items():
            md.append(f"- **{cat}**: {count}")
        md.append("")
    
    # Themes
    themes = report.get('themes', [])
    if themes:
        md.append("## 🎯 Themes & Projects")
        for theme in themes:
            name = theme.get('name', 'Unknown')
            desc = theme.get('description', '')
            task_count = theme.get('task_count', 0)
            md.append(f"### {name}")
            md.append(f"{desc}")
            md.append(f"- Tasks: {task_count}")
            md.append("")
    
    # Daily Breakdown
    daily = report.get('daily_breakdown', [])
    if daily:
        md.append("## 📅 Daily Breakdown")
        for day in daily:
            day_date = day.get('date', 'Unknown')
            summary = day.get('summary', 'No summary')
            task_count = day.get('task_count', 0)
            md.append(f"### {day_date}")
            md.append(f"{summary}")
            md.append(f"- Tasks completed: {task_count}")
            md.append("")
    
    # Insights
    insights = report.get('insights', '')
    if insights:
        md.append("## 💡 Insights")
        md.append(insights)
        md.append("")
    
    return "\n".join(md)


def _format_text(report: Dict) -> str:
    """Format report as plain text."""
    lines = []
    
    title = report.get('title', 'Development Report')
    lines.append(title)
    lines.append("=" * len(title))
    lines.append("")
    
    period = report.get('period', {})
    lines.append(f"Period: {period.get('start', 'N/A')} to {period.get('end', 'N/A')}")
    lines.append("")
    
    lines.append("Summary:")
    lines.append(report.get('executive_summary', 'No summary available.'))
    lines.append("")
    
    stats = report.get('statistics', {})
    lines.append(f"Stats: {stats.get('total_commits', 0)} commits, +{stats.get('total_insertions', 0)}/-{stats.get('total_deletions', 0)}")
    
    return "\n".join(lines)
