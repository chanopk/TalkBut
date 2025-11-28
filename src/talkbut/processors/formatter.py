from typing import Dict, Any
import json
from talkbut.models.report import DailyReport

class ReportFormatter:
    def __init__(self):
        pass

    def format_markdown(self, report: DailyReport) -> str:
        """Format report as Markdown."""
        md = []
        md.append(f"# Daily Report: {report.date.strftime('%Y-%m-%d')}")
        md.append("")
        
        # Summary
        md.append("## 📝 Summary")
        md.append(report.ai_summary)
        md.append("")
        
        # Stats
        md.append("## 📊 Statistics")
        md.append(f"- **Total Commits**: {report.total_commits}")
        md.append(f"- **Files Changed**: {report.files_changed}")
        md.append(f"- **Changes**: +{report.insertions} / -{report.deletions}")
        md.append("")
        
        # Categories
        if report.categories:
            md.append("## 🏷️ Work Breakdown")
            for cat, count in report.categories.items():
                md.append(f"- **{cat}**: {count}")
            md.append("")

        # Tasks
        if report.tasks:
            md.append("## ✅ Tasks")
            for task in report.tasks:
                task_name = task.get("task", "") if isinstance(task, dict) else str(task)
                md.append(f"- {task_name}")
            md.append("")
            
        # Detailed Commits
        md.append("## 💻 Detailed Commits")
        for commit in report.commits:
            md.append(f"### {commit.short_hash} - {commit.message.splitlines()[0]}")
            md.append(f"- **Time**: {commit.date.strftime('%H:%M')}")
            md.append(f"- **Author**: {commit.author}")
            if len(commit.message.splitlines()) > 1:
                md.append(f"- **Details**:")
                for line in commit.message.splitlines()[1:]:
                    if line.strip():
                        md.append(f"  > {line.strip()}")
            md.append("")
            
        return "\n".join(md)

    def format_json(self, report: DailyReport) -> str:
        """Format report as JSON."""
        return report.to_json()

    def format_text(self, report: DailyReport) -> str:
        """Format report as plain text summary."""
        lines = [
            f"Daily Report: {report.date}",
            "-" * 20,
            f"Summary: {report.ai_summary}",
            "",
            f"Stats: {report.total_commits} commits, +{report.insertions}/-{report.deletions}",
        ]
        
        if report.tasks:
            lines.append("")
            lines.append("Tasks:")
            for task in report.tasks:
                task_name = task.get("task", "") if isinstance(task, dict) else str(task)
                lines.append(f"- {task_name}")
            
        return "\n".join(lines)
