"""Tests for GitCollector."""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime
import git

from talkbut.collectors.git_collector import GitCollector
from talkbut.models.commit import Commit


class MockGitCommit:
    """Mock git commit object."""
    
    def __init__(self, hexsha, author_name, author_email, date, message, stats_dict, files):
        self.hexsha = hexsha
        self.author = MagicMock()
        self.author.name = author_name
        self.author.email = author_email
        self.committed_datetime = date
        self.message = message
        self.stats = MagicMock()
        self.stats.total = stats_dict
        self.stats.files = {f: {"insertions": 1, "deletions": 1} for f in files}
        self.parents = []


class TestGitCollector:
    """Tests for GitCollector."""

    @patch('git.Repo')
    def test_init_valid_repo(self, mock_repo_cls):
        """Test initializing with a valid repository."""
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        
        collector = GitCollector("/path/to/repo")
        
        assert collector.repo == mock_repo
        mock_repo_cls.assert_called_once()

    @patch('git.Repo')
    def test_init_invalid_repo(self, mock_repo_cls):
        """Test initializing with an invalid repository."""
        mock_repo_cls.side_effect = git.InvalidGitRepositoryError("Not a git repo")
        
        with pytest.raises(ValueError, match="Invalid git repository"):
            GitCollector("/invalid/path")

    @patch('git.Repo')
    def test_collect_commits_basic(self, mock_repo_cls):
        """Test collecting commits."""
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        
        mock_commit = MockGitCommit(
            hexsha="1234567890abcdef",
            author_name="Test User",
            author_email="test@example.com",
            date=datetime(2023, 1, 1, 12, 0, 0),
            message="feat: test commit",
            stats_dict={"insertions": 5, "deletions": 2, "files": 1},
            files=["file1.py", "file2.py"]
        )
        mock_repo.iter_commits.return_value = [mock_commit]
        mock_repo.active_branch.name = "main"

        collector = GitCollector("/path/to/repo")
        commits = collector.collect_commits(since="1 day ago")

        assert len(commits) == 1
        assert isinstance(commits[0], Commit)
        assert commits[0].hash == "1234567890abcdef"
        assert commits[0].author == "Test User"
        assert commits[0].email == "test@example.com"
        assert commits[0].insertions == 5
        assert commits[0].deletions == 2
        assert set(commits[0].files_changed) == {"file1.py", "file2.py"}

    @patch('git.Repo')
    def test_collect_commits_empty(self, mock_repo_cls):
        """Test collecting commits when none exist."""
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.iter_commits.return_value = []
        mock_repo.active_branch.name = "main"

        collector = GitCollector("/path/to/repo")
        commits = collector.collect_commits(since="1 day ago")

        assert commits == []

    @patch('git.Repo')
    def test_collect_commits_with_branch(self, mock_repo_cls):
        """Test collecting commits from specific branch."""
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.iter_commits.return_value = []

        collector = GitCollector("/path/to/repo")
        collector.collect_commits(since="1 day ago", branch="feature-branch")

        # Verify iter_commits was called with the branch
        call_kwargs = mock_repo.iter_commits.call_args
        assert call_kwargs[1].get("rev") == "feature-branch" or call_kwargs[0][0] == "feature-branch"

    @patch('git.Repo')
    def test_collect_commits_with_author(self, mock_repo_cls):
        """Test collecting commits filtered by author."""
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.iter_commits.return_value = []
        mock_repo.active_branch.name = "main"

        collector = GitCollector("/path/to/repo")
        collector.collect_commits(since="1 day ago", author="test@example.com")

        call_kwargs = mock_repo.iter_commits.call_args[1]
        assert call_kwargs.get("author") == "test@example.com"

    @patch('git.Repo')
    def test_get_current_branch(self, mock_repo_cls):
        """Test getting current branch name."""
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        mock_repo.active_branch.name = "develop"

        collector = GitCollector("/path/to/repo")
        branch = collector.get_current_branch()

        assert branch == "develop"

    @patch('git.Repo')
    def test_collect_commits_multiple(self, mock_repo_cls):
        """Test collecting multiple commits."""
        mock_repo = MagicMock()
        mock_repo_cls.return_value = mock_repo
        
        mock_commits = [
            MockGitCommit(
                hexsha="commit1",
                author_name="User1",
                author_email="user1@test.com",
                date=datetime(2023, 1, 1, 10, 0),
                message="feat: first commit",
                stats_dict={"insertions": 10, "deletions": 5, "files": 2},
                files=["a.py"]
            ),
            MockGitCommit(
                hexsha="commit2",
                author_name="User2",
                author_email="user2@test.com",
                date=datetime(2023, 1, 1, 14, 0),
                message="fix: second commit",
                stats_dict={"insertions": 3, "deletions": 1, "files": 1},
                files=["b.py"]
            ),
        ]
        mock_repo.iter_commits.return_value = mock_commits
        mock_repo.active_branch.name = "main"

        collector = GitCollector("/path/to/repo")
        commits = collector.collect_commits(since="1 day ago")

        assert len(commits) == 2
        assert commits[0].hash == "commit1"
        assert commits[1].hash == "commit2"
