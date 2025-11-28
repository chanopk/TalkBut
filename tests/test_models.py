"""Tests for data models."""
import pytest
from datetime import datetime, date
from talkbut.models.commit import Commit
from talkbut.models.report import DailyReport


class TestCommit:
    """Tests for Commit model."""

    def test_commit_creation(self, sample_commit):
        """Test basic commit creation."""
        assert sample_commit.hash == "abc1234567890abcdef1234567890abcdef12"
        assert sample_commit.author == "Test User"
        assert sample_commit.email == "test@example.com"
        assert sample_commit.insertions == 10
        assert sample_commit.deletions == 5

    def test_short_hash(self, sample_commit):
        """Test short_hash property."""
        assert sample_commit.short_hash == "abc1234"

    def test_commit_defaults(self):
        """Test commit with default values."""
        commit = Commit(
            hash="abc123",
            author="Test",
            email="test@test.com",
            date=datetime.now(),
            message="test message"
        )
        assert commit.files_changed == []
        assert commit.insertions == 0
        assert commit.deletions == 0
        assert commit.branch == ""
        assert commit.tags == []
        assert commit.ticket_refs == []
        assert commit.file_diffs == {}

    def test_to_dict(self, sample_commit):
        """Test commit serialization to dict."""
        data = sample_commit.to_dict()
        assert data["hash"] == sample_commit.hash
        assert data["author"] == sample_commit.author
        assert data["insertions"] == 10
        assert data["deletions"] == 5
        assert "file_diffs" not in data

    def test_to_dict_with_diffs(self):
        """Test commit serialization with diffs included."""
        commit = Commit(
            hash="abc123",
            author="Test",
            email="test@test.com",
            date=datetime.now(),
            message="test",
            file_diffs={"file.py": "+line1\n-line2"}
        )
        data = commit.to_dict(include_diffs=True)
        assert "file_diffs" in data
        assert data["file_diffs"]["file.py"] == "+line1\n-line2"


class TestDailyReport:
    """Tests for DailyReport model."""

    def test_report_creation(self, sample_commits):
        """Test basic report creation."""
        report = DailyReport(
            date=date(2023, 1, 1),
            total_commits=2,
            files_changed=3,
            insertions=70,
            deletions=15,
            commits=sample_commits,
            ai_summary="Test summary",
            categories={"feature": 1, "bugfix": 1},
            tasks=[{"task": "Implement login"}]
        )
        assert report.total_commits == 2
        assert report.ai_summary == "Test summary"
        assert len(report.commits) == 2

    def test_report_to_dict(self, sample_commits):
        """Test report serialization to dict."""
        report = DailyReport(
            date=date(2023, 1, 1),
            total_commits=2,
            files_changed=3,
            insertions=70,
            deletions=15,
            commits=sample_commits,
            ai_summary="Test summary"
        )
        data = report.to_dict()
        assert data["date"] == "2023-01-01"
        assert data["total_commits"] == 2
        assert len(data["commits"]) == 2

    def test_report_to_json(self, sample_commits):
        """Test report serialization to JSON."""
        report = DailyReport(
            date=date(2023, 1, 1),
            total_commits=1,
            files_changed=1,
            insertions=10,
            deletions=5,
            commits=[sample_commits[0]],
            ai_summary="Summary"
        )
        json_str = report.to_json()
        assert '"total_commits": 1' in json_str
        assert '"ai_summary": "Summary"' in json_str
