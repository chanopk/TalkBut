import google.generativeai as genai
import json
import os
from typing import List, Dict, Any, Optional
from datetime import date
from pathlib import Path

from talkbut.models.commit import Commit
from talkbut.models.report import DailyReport
from talkbut.core.config import ConfigManager
from talkbut.utils.logger import get_logger

logger = get_logger(__name__)

class AIAnalyzer:
    def __init__(self):
        self.config = ConfigManager()
        self._setup_api()
        self._load_prompt_template()

    def _setup_api(self):
        api_key = self.config.ai_api_key
        if not api_key:
            logger.warning("No API key found. AI features will be disabled.")
            self.model = None
            return

        genai.configure(api_key=api_key)
        model_name = self.config.get("ai.model", "gemini-1.5-flash")
        self.model = genai.GenerativeModel(model_name)

    def _load_prompt_template(self):
        prompt_path = Path("config/prompts/analysis_prompt.txt")
        if prompt_path.exists():
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.prompt_template = f.read()
        else:
            # Fallback template
            self.prompt_template = """
            Analyze these commits for {date}:
            {commits_text}
            
            Return JSON with summary, categories, highlights, and timeline.
            """

    def analyze_commits(self, commits: List[Commit], report_date: date) -> DailyReport:
        """Analyze commits and generate a daily report."""
        
        # Basic stats calculation
        total_commits = len(commits)
        files_changed_set = set()
        insertions = 0
        deletions = 0
        
        commits_text = ""
        for c in commits:
            files_changed_set.update(c.files_changed)
            insertions += c.insertions
            deletions += c.deletions
            commits_text += f"- [{c.date.strftime('%H:%M')}] {c.message} (Hash: {c.short_hash})\n"

        # Prepare default/fallback report data
        report_data = {
            "date": report_date,
            "total_commits": total_commits,
            "files_changed": len(files_changed_set),
            "insertions": insertions,
            "deletions": deletions,
            "commits": commits,
            "ai_summary": "Auto-generated summary pending AI analysis.",
            "categories": {},
            "highlights": [],
            "timeline": []
        }

        if not self.model or not commits:
            return DailyReport(**report_data)

        # Call AI API
        try:
            prompt = self.prompt_template.format(
                date=report_date.isoformat(),
                total_commits=total_commits,
                files_changed_count=len(files_changed_set),
                commits_text=commits_text
            )
            
            response = self.model.generate_content(prompt)
            
            ai_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if ai_text.startswith("```"):
                lines = ai_text.split("\n")
                ai_text = "\n".join(lines[1:-1]) if len(lines) > 2 else ai_text
                ai_text = ai_text.replace("```json", "").replace("```", "").strip()
            
            ai_data = json.loads(ai_text)
            self._merge_ai_data(report_data, ai_data)
            
        except Exception as e:
            logger.error(f"AI Analysis failed: {e}")
            report_data["ai_summary"] = f"AI Analysis failed: {str(e)}"

        return DailyReport(**report_data)

    def _merge_ai_data(self, report_data: Dict, ai_data: Dict):
        """Merge AI response into report data."""
        if "summary" in ai_data:
            report_data["ai_summary"] = ai_data["summary"]
        if "categories" in ai_data:
            report_data["categories"] = ai_data["categories"]
        if "highlights" in ai_data:
            report_data["highlights"] = ai_data["highlights"]
        if "timeline" in ai_data:
            report_data["timeline"] = ai_data["timeline"]
