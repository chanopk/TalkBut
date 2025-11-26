from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

@dataclass
class Commit:
    hash: str
    author: str
    email: str
    date: datetime
    message: str
    files_changed: List[str] = field(default_factory=list)
    insertions: int = 0
    deletions: int = 0
    branch: str = ""
    tags: List[str] = field(default_factory=list)
    ticket_refs: List[str] = field(default_factory=list)
    file_diffs: dict = field(default_factory=dict)  # {filename: diff_text}

    @property
    def short_hash(self) -> str:
        return self.hash[:7]

    def to_dict(self, include_diffs: bool = False) -> dict:
        data = {
            "hash": self.hash,
            "author": self.author,
            "email": self.email,
            "date": self.date.isoformat(),
            "message": self.message,
            "files_changed": self.files_changed,
            "insertions": self.insertions,
            "deletions": self.deletions,
            "branch": self.branch,
            "tags": self.tags,
            "ticket_refs": self.ticket_refs,
        }
        if include_diffs and self.file_diffs:
            data["file_diffs"] = self.file_diffs
        return data
