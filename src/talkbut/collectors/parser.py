import re
from typing import List, Dict, Any
from talkbut.models.commit import Commit

class DataParser:
    def __init__(self):
        pass

    def parse_commit_message(self, message: str) -> Dict[str, Any]:
        """Extract metadata from commit message."""
        lines = message.split('\n')
        subject = lines[0]
        body = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""

        # Extract ticket refs (e.g., JIRA-123, #456)
        ticket_refs = re.findall(r'([A-Z]+-\d+|#\d+)', message)
        
        # Extract tags (e.g., [FEATURE], [BUGFIX])
        tags = re.findall(r'\[([A-Z_]+)\]', subject)

        return {
            "subject": subject,
            "body": body,
            "ticket_refs": list(set(ticket_refs)),
            "tags": list(set(tags))
        }

    def categorize_commit(self, commit: Commit) -> str:
        """Categorize commit based on conventional commits or keywords."""
        msg = commit.message.lower()
        
        if any(x in msg for x in ['feat:', 'feature:', 'add:', 'new:']):
            return 'feature'
        elif any(x in msg for x in ['fix:', 'bug:', 'patch:', 'resolve:']):
            return 'bugfix'
        elif any(x in msg for x in ['refactor:', 'clean:', 'improve:', 'optimize:']):
            return 'refactor'
        elif any(x in msg for x in ['docs:', 'doc:']):
            return 'documentation'
        elif any(x in msg for x in ['test:', 'tests:']):
            return 'testing'
        elif any(x in msg for x in ['chore:', 'config:', 'setup:', 'build:']):
            return 'chore'
        else:
            return 'other'

    def enrich_commit(self, commit: Commit) -> Commit:
        """Parse message and update commit object with extracted metadata."""
        parsed = self.parse_commit_message(commit.message)
        commit.ticket_refs = parsed['ticket_refs']
        commit.tags = parsed['tags']
        return commit
