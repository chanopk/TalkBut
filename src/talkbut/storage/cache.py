import json
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from talkbut.models.commit import Commit
from talkbut.core.config import ConfigManager

class CacheManager:
    def __init__(self):
        config = ConfigManager()
        self.cache_dir = Path(config.get("storage.cache_dir", "./data/cache"))
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, repo_name: str, date_range: str) -> Path:
        safe_name = "".join(c for c in repo_name if c.isalnum() or c in ('-', '_'))
        return self.cache_dir / f"{safe_name}_{date_range}.json"

    def save_commits(self, repo_name: str, date_range: str, commits: List[Commit]) -> None:
        """Save commits to JSON cache."""
        path = self._get_cache_path(repo_name, date_range)
        data = [c.to_dict() for c in commits]
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_commits(self, repo_name: str, date_range: str) -> Optional[List[Commit]]:
        """Load commits from JSON cache."""
        path = self._get_cache_path(repo_name, date_range)
        if not path.exists():
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                commits = []
                for item in data:
                    # Convert date string back to datetime object if needed
                    # But Commit model expects datetime, so we might need parsing
                    # For simplicity in MVP, let's assume we handle it or re-fetch if complex
                    # Actually, let's implement basic reconstruction
                    from datetime import datetime
                    item['date'] = datetime.fromisoformat(item['date'])
                    commits.append(Commit(**item))
                return commits
        except Exception:
            return None

    def save_ai_response(self, key: str, response: str) -> None:
        """Cache AI response."""
        path = self.cache_dir / f"ai_{key}.json"
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({"response": response}, f, ensure_ascii=False)

    def get_ai_response(self, key: str) -> Optional[str]:
        """Get cached AI response."""
        path = self.cache_dir / f"ai_{key}.json"
        if not path.exists():
            return None
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)["response"]
        except Exception:
            return None
