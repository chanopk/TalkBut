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
from talkbut.collectors.git_collector import GitCollector

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
    '--unsave',
    is_flag=True,
    default=False,
    help='Display output only, do not save to file'
)
@click.option(
    '--fast',
    type=str,
    default=None,
    help='Fast mode: ดึง commits โดยตรงและสรุปด้วย AI (e.g., "1 month", "3 months", "YTD")'
)
def report(days, start, end, format, unsave, fast):
    """สร้างรายงานสรุปจาก daily logs (ย้อนหลังได้สูงสุด 1 เดือน) หรือใช้ --fast สำหรับช่วงยาว"""
    try:
        # Fast mode: ดึง commits โดยตรงและสรุปด้วย AI
        if fast:
            # Check if YTD (Year-to-Date) - special handling
            if fast.upper() == "YTD":
                _handle_ytd_report(format, unsave)
            else:
                _handle_fast_report(fast, format, unsave)
            return
        
        # Normal mode: ใช้ daily logs
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
        if unsave:
            # Display only, do not save
            click.echo("\n" + "=" * 60)
            click.echo(content)
            click.echo("=" * 60)
        else:
            # Auto-generate filename: report_{start}_{end}.{ext}
            ext_map = {'markdown': 'md', 'json': 'json', 'text': 'txt'}
            ext = ext_map.get(format, 'md')
            filename = f"report_{start_date.isoformat()}_{end_date.isoformat()}.{ext}"
            output_path = Path("data/reports") / filename
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Remove old file if exists
            if output_path.exists():
                output_path.unlink()
                click.echo(f"🗑️  Removed old file: {output_path}")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            click.echo(f"✅ Report saved to: {output_path}")
        
    except ValueError as e:
        click.echo(f"❌ Error: {e}", err=True)
        raise click.Abort()
    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        click.echo(f"❌ Failed to generate report: {e}", err=True)
        raise click.Abort()


def _handle_ytd_report(format: str, unsave: bool):
    """Handle Year-to-Date report by analyzing month by month."""
    config = ConfigManager()
    
    # Calculate YTD range
    today = date.today()
    start_of_year = date(today.year, 1, 1)
    
    click.echo(f"⚡ YTD Mode: Generating report from {start_of_year} to {today}")
    click.echo("📝 Will analyze month by month to avoid timeout")
    
    # Get author from config
    author = config.get("git.author")
    if not author:
        click.echo("⚠️  No author configured. Set git.author in config for better results.")
    
    # Get repositories
    repos = config.git_repos
    if not repos:
        repos = [{'path': '.', 'name': 'Current Directory'}]
        click.echo("📁 Using current directory")
    else:
        click.echo(f"📁 Using {len(repos)} repositories from config")
    
    # Generate monthly reports
    monthly_reports = []
    current_month_start = start_of_year
    
    while current_month_start <= today:
        # Calculate month end
        if current_month_start.month == 12:
            month_end = date(current_month_start.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(current_month_start.year, current_month_start.month + 1, 1) - timedelta(days=1)
        
        # Don't go beyond today
        if month_end > today:
            month_end = today
        
        month_name = current_month_start.strftime("%B %Y")
        click.echo(f"\n📅 Processing: {month_name} ({current_month_start} to {month_end})")
        
        # Collect commits for this month
        all_commits = []
        for repo_info in repos:
            repo_path = repo_info.get('path', '.')
            repo_name = repo_info.get('name', repo_path)
            
            try:
                collector = GitCollector(repo_path)
                commits = collector.collect_commits(
                    since=current_month_start.isoformat(),
                    until=month_end.isoformat(),
                    author=author,
                    include_diffs=False
                )
                
                if commits:
                    for c in commits:
                        c.repo_name = repo_name
                    all_commits.extend(commits)
                    
            except Exception as e:
                logger.warning(f"Failed to collect from {repo_name}: {e}")
        
        if all_commits:
            all_commits.sort(key=lambda c: c.date)
            click.echo(f"   ✓ Found {len(all_commits)} commits")
            
            # Generate report for this month
            click.echo(f"   🤖 Analyzing with AI...")
            month_report = _generate_fast_report(all_commits, current_month_start, month_end, month_name)
            
            if month_report:
                monthly_reports.append({
                    'month': month_name,
                    'start': current_month_start,
                    'end': month_end,
                    'report': month_report
                })
                click.echo(f"   ✅ Completed")
            else:
                click.echo(f"   ⚠️  Failed to generate report")
        else:
            click.echo(f"   ⚠️  No commits found")
        
        # Move to next month
        if current_month_start.month == 12:
            current_month_start = date(current_month_start.year + 1, 1, 1)
        else:
            current_month_start = date(current_month_start.year, current_month_start.month + 1, 1)
    
    if not monthly_reports:
        click.echo("\n⚠️  No data to generate YTD report")
        return
    
    # Combine monthly reports into YTD report
    click.echo(f"\n📊 Combining {len(monthly_reports)} monthly reports into YTD summary...")
    ytd_report = _combine_monthly_reports(monthly_reports, start_of_year, today)
    
    # Format output
    if format == 'json':
        content = json.dumps(ytd_report, ensure_ascii=False, indent=2)
    elif format == 'text':
        content = _format_text(ytd_report)
    else:  # markdown
        content = _format_ytd_markdown(ytd_report, monthly_reports)
    
    # Output
    if unsave:
        click.echo("\n" + "=" * 60)
        click.echo(content)
        click.echo("=" * 60)
    else:
        ext_map = {'markdown': 'md', 'json': 'json', 'text': 'txt'}
        ext = ext_map.get(format, 'md')
        filename = f"report_fast_YTD_{today.isoformat()}.{ext}"
        output_path = Path("data/reports") / filename
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.exists():
            output_path.unlink()
            click.echo(f"🗑️  Removed old file: {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        click.echo(f"✅ YTD Report saved to: {output_path}")


def _handle_fast_report(since: str, format: str, unsave: bool):
    """Handle fast report generation by collecting commits directly."""
    config = ConfigManager()
    
    click.echo(f"⚡ Fast mode: Generating report for the last {since}")
    click.echo("📝 This will collect commits directly without using daily logs")
    
    # Get author from config
    author = config.get("git.author")
    if not author:
        click.echo("⚠️  No author configured. Set git.author in config for better results.")
    
    # Get repositories
    repos = config.git_repos
    if not repos:
        repos = [{'path': '.', 'name': 'Current Directory'}]
        click.echo("📁 Using current directory")
    else:
        click.echo(f"📁 Using {len(repos)} repositories from config")
    
    # Collect commits from all repositories
    click.echo(f"\n🔍 Collecting commits since {since}...")
    all_commits = []
    
    for repo_info in repos:
        repo_path = repo_info.get('path', '.')
        repo_name = repo_info.get('name', repo_path)
        
        try:
            click.echo(f"   Processing: {repo_name}...")
            collector = GitCollector(repo_path)
            
            commits = collector.collect_commits(
                since=since,
                author=author,
                include_diffs=False
            )
            
            if commits:
                click.echo(f"   ✓ Found {len(commits)} commits")
                for c in commits:
                    c.repo_name = repo_name
                all_commits.extend(commits)
            else:
                click.echo(f"   ⚠ No commits found")
                
        except Exception as e:
            click.echo(f"   ✗ Error: {e}")
            logger.warning(f"Failed to collect from {repo_name}: {e}")
    
    if not all_commits:
        click.echo("\n⚠️  No commits found in the specified range.")
        return
    
    # Sort commits by date
    all_commits.sort(key=lambda c: c.date)
    
    click.echo(f"\n✅ Total: {len(all_commits)} commits")
    
    # Calculate date range
    start_date = all_commits[0].date.date()
    end_date = all_commits[-1].date.date()
    date_range = (end_date - start_date).days + 1
    
    click.echo(f"📅 Date range: {start_date} to {end_date} ({date_range} days)")
    
    # Generate fast report with AI
    click.echo("\n🤖 Analyzing with AI (single pass)...")
    report_data = _generate_fast_report(all_commits, start_date, end_date, since)
    
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
    if unsave:
        click.echo("\n" + "=" * 60)
        click.echo(content)
        click.echo("=" * 60)
    else:
        ext_map = {'markdown': 'md', 'json': 'json', 'text': 'txt'}
        ext = ext_map.get(format, 'md')
        filename = f"report_fast_{since.replace(' ', '_')}_{end_date.isoformat()}.{ext}"
        output_path = Path("data/reports") / filename
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.exists():
            output_path.unlink()
            click.echo(f"🗑️  Removed old file: {output_path}")
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        click.echo(f"✅ Report saved to: {output_path}")


def _generate_fast_report(commits: List, start_date: date, end_date: date, period: str) -> Optional[Dict]:
    """Generate report from commits using AI (single pass)."""
    config = ConfigManager()
    api_key = config.ai_api_key
    
    if not api_key:
        logger.warning("No API key found. Cannot generate AI report.")
        return _generate_basic_fast_report(commits, start_date, end_date, period)
    
    # Calculate stats
    total_commits = len(commits)
    files_changed_set = set()
    total_insertions = 0
    total_deletions = 0
    
    for c in commits:
        files_changed_set.update(c.files_changed)
        total_insertions += c.insertions
        total_deletions += c.deletions
    
    # Build commits summary (all commits, grouped efficiently)
    from collections import defaultdict
    
    # Group commits by repo
    commits_by_repo = defaultdict(list)
    for c in commits:
        repo_key = c.repo_name if c.repo_name else 'Unknown'
        commits_by_repo[repo_key].append(c)
    
    # Build compact summary with all commit messages
    commits_text = ""
    for repo_key in sorted(commits_by_repo.keys()):
        repo_commits = commits_by_repo[repo_key]
        commits_text += f"\n[{repo_key}] ({len(repo_commits)} commits):\n"
        for c in repo_commits:
            commits_text += f"  - [{c.date.strftime('%Y-%m-%d')}] {c.message}\n"
    
    # Calculate token estimate (rough: 1 token ≈ 4 chars)
    prompt_size = len(commits_text) // 4
    click.echo(f"   📝 Prompt size: ~{prompt_size:,} tokens ({len(commits_text):,} chars)")
    
    # Build prompt for fast report
    prompt = f"""วิเคราะห์และสรุปผลงานการพัฒนาซอฟต์แวร์จาก Git commits ของนักพัฒนาในช่วง {period} ที่ผ่านมา

**หมายเหตุ:** ข้อมูลนี้เป็นผลงานของนักพัฒนาคนเดียว (ไม่ใช่ทีม) ที่ถูกกรองด้วย author

ข้อมูลภาพรวม:
- ช่วงเวลา: {start_date.isoformat()} ถึง {end_date.isoformat()} ({(end_date - start_date).days + 1} วัน)
- จำนวน commits: {total_commits}
- ไฟล์ที่เปลี่ยนแปลง: {len(files_changed_set)}
- บรรทัดที่เพิ่ม: +{total_insertions}
- บรรทัดที่ลบ: -{total_deletions}

Commits (ทั้งหมด {total_commits} commits จัดกลุ่มตาม repository):
{commits_text}

กรุณาวิเคราะห์และสรุปเป็น JSON ตามโครงสร้างนี้:
{{
  "title": "ชื่อรายงาน",
  "period": {{
    "start": "{start_date.isoformat()}",
    "end": "{end_date.isoformat()}",
    "days": {(end_date - start_date).days + 1},
    "description": "{period}"
  }},
  "executive_summary": "สรุปภาพรวมการทำงานของนักพัฒนาในช่วงนี้ (2-3 ประโยค) - ใช้คำว่า 'นักพัฒนา' ไม่ใช่ 'ทีม'",
  "highlights": [
    "ความสำเร็จหรือผลงานที่โดดเด่น",
    "..."
  ],
  "themes": [
    {{
      "name": "ชื่อโปรเจคหรือธีม",
      "description": "รายละเอียด",
      "task_count": 0
    }}
  ],
  "statistics": {{
    "total_commits": {total_commits},
    "total_files": {len(files_changed_set)},
    "total_insertions": {total_insertions},
    "total_deletions": {total_deletions},
    "categories": {{
      "Feature": 0,
      "Bug Fix": 0,
      "Refactor": 0,
      "Documentation": 0,
      "Other": 0
    }}
  }},
  "insights": "ข้อสังเกตและข้อเสนอแนะเกี่ยวกับผลงานของนักพัฒนา - ใช้คำว่า 'นักพัฒนา' ไม่ใช่ 'ทีม'"
}}

ตอบเป็น JSON เท่านั้น ไม่ต้องมีคำอธิบายเพิ่มเติม"""
    
    # Call AI
    try:
        genai.configure(api_key=api_key)
        model_name = config.get("ai.model", "gemini-2.5-flash")
        model = genai.GenerativeModel(model_name=model_name)
        
        generation_config = {
            "temperature": 0.3,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 16384,  # Increased for fast reports with long output
        }
        
        response = model.generate_content(prompt, generation_config=generation_config)
        
        # Debug: Check response structure
        if not response.candidates:
            logger.error("No candidates in AI response")
            raise ValueError("AI returned no candidates")
        
        # Handle complex response
        try:
            ai_text = response.text.strip()
        except Exception as ex:
            logger.warning(f"response.text failed: {ex}, trying parts...")
            # If response.text fails, try to get text from parts
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                logger.info(f"Candidate finish_reason: {candidate.finish_reason}")
                parts = candidate.content.parts
                ai_text = "".join(part.text for part in parts if hasattr(part, 'text')).strip()
            else:
                logger.error(f"Unable to extract text from AI response: {ex}")
                raise ValueError("Unable to extract text from AI response")
        
        if not ai_text:
            logger.error(f"AI returned empty response. Finish reason: {response.candidates[0].finish_reason if response.candidates else 'N/A'}")
            raise ValueError("AI returned empty response")
        
        # Remove markdown code blocks if present
        if ai_text.startswith("```"):
            lines = ai_text.split("\n")
            ai_text = "\n".join(lines[1:-1]) if len(lines) > 2 else ai_text
            ai_text = ai_text.replace("```json", "").replace("```", "").strip()
        
        # Try to parse JSON
        try:
            return json.loads(ai_text)
        except json.JSONDecodeError as json_err:
            logger.error(f"JSON parse error: {json_err}")
            logger.error(f"AI response (first 500 chars): {ai_text[:500]}")
            # Try to fix common JSON issues
            import re
            # Remove trailing commas before } or ]
            ai_text_fixed = re.sub(r',(\s*[}\]])', r'\1', ai_text)
            try:
                return json.loads(ai_text_fixed)
            except:
                raise ValueError(f"Unable to parse AI response as JSON: {json_err}")
        
    except Exception as e:
        logger.error(f"AI fast report generation failed: {e}")
        return _generate_basic_fast_report(commits, start_date, end_date, period)


def _generate_basic_fast_report(commits: List, start_date: date, end_date: date, period: str) -> Dict:
    """Generate basic fast report without AI."""
    total_commits = len(commits)
    files_changed_set = set()
    total_insertions = 0
    total_deletions = 0
    
    for c in commits:
        files_changed_set.update(c.files_changed)
        total_insertions += c.insertions
        total_deletions += c.deletions
    
    return {
        "title": f"Development Report: {period}",
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": (end_date - start_date).days + 1,
            "description": period
        },
        "executive_summary": f"Report covers {period} with {total_commits} commits.",
        "highlights": [],
        "themes": [],
        "statistics": {
            "total_commits": total_commits,
            "total_files": len(files_changed_set),
            "total_insertions": total_insertions,
            "total_deletions": total_deletions,
            "categories": {}
        },
        "insights": "Basic report generated without AI analysis."
    }


def _combine_monthly_reports(monthly_reports: List[Dict], start_date: date, end_date: date) -> Dict:
    """Combine monthly reports into a YTD summary."""
    # Aggregate statistics
    total_commits = 0
    total_files = 0
    total_insertions = 0
    total_deletions = 0
    all_categories = {}
    all_highlights = []
    all_themes = {}
    
    for month_data in monthly_reports:
        report = month_data['report']
        stats = report.get('statistics', {})
        
        total_commits += stats.get('total_commits', 0)
        total_files += stats.get('total_files', 0)
        total_insertions += stats.get('total_insertions', 0)
        total_deletions += stats.get('total_deletions', 0)
        
        # Aggregate categories
        for cat, count in stats.get('categories', {}).items():
            all_categories[cat] = all_categories.get(cat, 0) + count
        
        # Collect highlights
        highlights = report.get('highlights', [])
        if highlights:
            all_highlights.append({
                'month': month_data['month'],
                'highlights': highlights[:3]  # Top 3 per month
            })
        
        # Aggregate themes
        for theme in report.get('themes', []):
            theme_name = theme.get('name', 'Unknown')
            if theme_name in all_themes:
                all_themes[theme_name]['task_count'] += theme.get('task_count', 0)
                all_themes[theme_name]['months'].append(month_data['month'])
            else:
                all_themes[theme_name] = {
                    'name': theme_name,
                    'description': theme.get('description', ''),
                    'task_count': theme.get('task_count', 0),
                    'months': [month_data['month']]
                }
    
    return {
        'title': f"Year-to-Date Report {start_date.year}",
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat(),
            'months': len(monthly_reports),
            'description': f"YTD {start_date.year}"
        },
        'executive_summary': f"รายงานสรุปผลงานตั้งแต่ต้นปี {start_date.year} จนถึงปัจจุบัน ครอบคลุม {len(monthly_reports)} เดือน ด้วย {total_commits} commits ทั้งหมด",
        'statistics': {
            'total_commits': total_commits,
            'total_files': total_files,
            'total_insertions': total_insertions,
            'total_deletions': total_deletions,
            'categories': all_categories
        },
        'highlights_by_month': all_highlights,
        'themes': list(all_themes.values()),
        'monthly_breakdown': [
            {
                'month': m['month'],
                'commits': m['report'].get('statistics', {}).get('total_commits', 0),
                'summary': m['report'].get('executive_summary', '')[:150]
            }
            for m in monthly_reports
        ]
    }


def _format_ytd_markdown(ytd_report: Dict, monthly_reports: List[Dict]) -> str:
    """Format YTD report as Markdown with monthly breakdown."""
    md = []
    
    # Title
    title = ytd_report.get('title', 'Year-to-Date Report')
    md.append(f"# {title}")
    md.append("")
    
    # Period
    period = ytd_report.get('period', {})
    md.append(f"📅 **Period**: {period.get('start', 'N/A')} to {period.get('end', 'N/A')} ({period.get('months', 0)} months)")
    md.append("")
    
    # Executive Summary
    md.append("## 📝 Executive Summary")
    md.append(ytd_report.get('executive_summary', 'No summary available.'))
    md.append("")
    
    # Overall Statistics
    stats = ytd_report.get('statistics', {})
    md.append("## 📊 Overall Statistics")
    md.append(f"- **Total Commits**: {stats.get('total_commits', 0):,}")
    md.append(f"- **Files Changed**: {stats.get('total_files', 0):,}")
    md.append(f"- **Lines Added**: +{stats.get('total_insertions', 0):,}")
    md.append(f"- **Lines Removed**: -{stats.get('total_deletions', 0):,}")
    md.append("")
    
    # Categories
    categories = stats.get('categories', {})
    if categories:
        md.append("### Work Breakdown")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            md.append(f"- **{cat}**: {count}")
        md.append("")
    
    # Themes
    themes = ytd_report.get('themes', [])
    if themes:
        md.append("## 🎯 Key Themes & Projects")
        for theme in sorted(themes, key=lambda x: x.get('task_count', 0), reverse=True)[:10]:
            name = theme.get('name', 'Unknown')
            desc = theme.get('description', '')
            task_count = theme.get('task_count', 0)
            months = theme.get('months', [])
            
            # Format active period as range
            if months:
                if len(months) == 1:
                    active_period = months[0]
                else:
                    active_period = f"{months[0]} - {months[-1]}"
            else:
                active_period = "Unknown"
            
            md.append(f"### {name}")
            md.append(f"{desc}")
            md.append(f"- Tasks: {task_count}")
            md.append(f"- Active in: {active_period}")
            md.append("")
    
    # Monthly Highlights
    highlights_by_month = ytd_report.get('highlights_by_month', [])
    if highlights_by_month:
        md.append("## ✨ Monthly Highlights")
        for month_highlights in highlights_by_month:
            month = month_highlights.get('month', 'Unknown')
            highlights = month_highlights.get('highlights', [])
            if highlights:
                md.append(f"### {month}")
                for h in highlights:
                    md.append(f"- {h}")
                md.append("")
    
    # Monthly Breakdown
    monthly_breakdown = ytd_report.get('monthly_breakdown', [])
    if monthly_breakdown:
        md.append("## 📅 Monthly Breakdown")
        for month_data in monthly_breakdown:
            month = month_data.get('month', 'Unknown')
            commits = month_data.get('commits', 0)
            summary = month_data.get('summary', 'No summary')
            md.append(f"### {month}")
            md.append(f"**Commits**: {commits}")
            md.append(f"{summary}...")
            md.append("")
    
    # Detailed Monthly Reports
    md.append("---")
    md.append("")
    md.append("## 📋 Detailed Monthly Reports")
    md.append("")
    
    for month_data in monthly_reports:
        month = month_data['month']
        report = month_data['report']
        
        md.append(f"### {month}")
        md.append("")
        
        # Month summary
        md.append(f"**Summary**: {report.get('executive_summary', 'N/A')}")
        md.append("")
        
        # Month stats
        month_stats = report.get('statistics', {})
        md.append(f"- Commits: {month_stats.get('total_commits', 0)}")
        md.append(f"- Files: {month_stats.get('total_files', 0)}")
        md.append(f"- Lines: +{month_stats.get('total_insertions', 0)}/-{month_stats.get('total_deletions', 0)}")
        md.append("")
        
        # Month highlights
        highlights = report.get('highlights', [])
        if highlights:
            md.append("**Highlights**:")
            for h in highlights[:5]:
                md.append(f"- {h}")
            md.append("")
    
    return "\n".join(md)


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
