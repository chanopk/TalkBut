import git
from datetime import datetime
from typing import List, Optional, Union
from pathlib import Path
from talkbut.models.commit import Commit
from talkbut.utils.logger import get_logger

logger = get_logger(__name__)

class GitCollector:
    def __init__(self, repo_path: Union[str, Path]):
        self.repo_path = Path(repo_path)
        try:
            self.repo = git.Repo(self.repo_path)
        except git.InvalidGitRepositoryError:
            raise ValueError(f"Invalid git repository: {self.repo_path}")

    def collect_commits(
        self,
        since: Union[str, datetime],
        until: Union[str, datetime, None] = None,
        author: Optional[str] = None,
        branch: Optional[str] = None,
        include_diffs: bool = False
    ) -> List[Commit]:
        """
        Collect commits using git log command.
        
        Args:
            since: Start date/time (e.g. "1 day ago", "2023-01-01")
            until: End date/time
            author: Filter by author email or name
            branch: Filter by branch (default: current branch)
        """
        commits = []
        
        # Build git log arguments
        kwargs = {
            'no_merges': True,
            'date': 'iso',
            'stat': True,  # Include diffstat
            'numstat': True, # Machine readable stats
            'format': '%H%n%an%n%ae%n%ad%n%s%n%b%n===END_COMMIT===' # Custom format
        }

        if since:
            kwargs['since'] = since
        if until:
            kwargs['until'] = until
        if author:
            kwargs['author'] = author
        
        # Select revision range
        rev = branch if branch else 'HEAD'

        try:
            # Execute git log
            # We use the git command directly for better control over output format
            log_output = self.repo.git.log(rev, **kwargs)
            
            if not log_output:
                return []

            # Parse the output
            # Note: This is a simplified parsing logic. 
            # In a real implementation, we might need a more robust parser 
            # or use GitPython's commit objects directly if performance allows.
            # However, for 'stat' and 'numstat', parsing raw output is often necessary 
            # to get the exact details we want efficiently.
            
            # For MVP, let's use GitPython's iteration which is safer but might be slower for huge repos.
            # But since we want specific 'git log' behavior as requested, let's stick to parsing or 
            # using GitPython's iter_commits but ensuring we get the stats.
            
            # Re-thinking: The requirement emphasized "using git log". 
            # GitPython's iter_commits actually calls git rev-list/log internally.
            # Let's use iter_commits but ensure we populate our Commit model correctly.
            
            commits_iter = self.repo.iter_commits(
                rev=rev,
                since=since,
                until=until,
                author=author,
                no_merges=True
            )

            for c in commits_iter:
                # Get stats
                stats = c.stats.total
                files_changed = list(c.stats.files.keys())
                
                # Get file diffs if requested
                file_diffs = {}
                if include_diffs:
                    try:
                        # Get diff for each file
                        if c.parents:
                            parent = c.parents[0]
                            diffs = parent.diff(c, create_patch=True)
                            for diff_item in diffs:
                                file_path = diff_item.b_path or diff_item.a_path
                                if file_path:
                                    file_diffs[file_path] = diff_item.diff.decode('utf-8', errors='ignore') if diff_item.diff else ""
                    except Exception as e:
                        logger.warning(f"Failed to get diff for commit {c.hexsha[:7]}: {e}")
                
                commit = Commit(
                    hash=c.hexsha,
                    author=c.author.name,
                    email=c.author.email,
                    date=c.committed_datetime,
                    message=c.message.strip(),
                    files_changed=files_changed,
                    insertions=stats.get('insertions', 0),
                    deletions=stats.get('deletions', 0),
                    branch=branch or self.repo.active_branch.name,
                    file_diffs=file_diffs
                )
                commits.append(commit)

        except git.GitCommandError as e:
            logger.error(f"Git command failed: {e}")
            raise

        return commits

    def get_current_branch(self) -> str:
        return self.repo.active_branch.name
