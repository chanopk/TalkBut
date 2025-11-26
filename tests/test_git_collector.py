import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from talkbut.collectors.git_collector import GitCollector
from talkbut.models.commit import Commit

class MockCommit:
    def __init__(self, hexsha, author, date, message, stats):
        self.hexsha = hexsha
        self.author = MagicMock(name=author, email=f"{author}@example.com")
        self.author.name = author
        self.committed_datetime = date
        self.message = message
        self.stats = MagicMock()
        self.stats.total = stats
        self.stats.files = {f: 1 for f in ["file1.py", "file2.py"]}

@patch('git.Repo')
def test_collect_commits(mock_repo_cls):
    # Setup mock repo and commits
    mock_repo = MagicMock()
    mock_repo_cls.return_value = mock_repo
    
    mock_commits = [
        MockCommit(
            hexsha="1234567890abcdef",
            author="Test User",
            date=datetime(2023, 1, 1, 12, 0, 0),
            message="feat: test commit",
            stats={'insertions': 5, 'deletions': 2}
        )
    ]
    mock_repo.iter_commits.return_value = mock_commits
    mock_repo.active_branch.name = "main"

    # Test
    collector = GitCollector("/path/to/repo")
    commits = collector.collect_commits(since="1 day ago")

    # Verify
    assert len(commits) == 1
    assert isinstance(commits[0], Commit)
    assert commits[0].hash == "1234567890abcdef"
    assert commits[0].author == "Test User"
    assert commits[0].insertions == 5
    assert commits[0].deletions == 2
    assert commits[0].files_changed == ["file1.py", "file2.py"]

@patch('git.Repo')
def test_invalid_repo(mock_repo_cls):
    import git
    mock_repo_cls.side_effect = git.InvalidGitRepositoryError
    
    with pytest.raises(ValueError):
        GitCollector("/invalid/path")
