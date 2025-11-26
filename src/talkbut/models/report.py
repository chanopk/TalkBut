from dataclasses import dataclass, field
from datetime import date
from typing import List, Dict, Any
import json
from .commit import Commit

@dataclass
class DailyReport:
    date: date
    total_commits: int
    files_changed: int
    insertions: int
    deletions: int
    commits: List[Commit]  # Should be sorted chronologically
    ai_summary: str
    categories: Dict[str, int] = field(default_factory=dict)
    highlights: List[str] = field(default_factory=list)
    timeline: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "date": self.date.isoformat(),
            "total_commits": self.total_commits,
            "files_changed": self.files_changed,
            "insertions": self.insertions,
            "deletions": self.deletions,
            "commits": [c.to_dict() for c in self.commits],
            "ai_summary": self.ai_summary,
            "categories": self.categories,
            "highlights": self.highlights,
            "timeline": self.timeline,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
