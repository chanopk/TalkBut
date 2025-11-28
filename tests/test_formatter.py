"""Tests for ReportFormatter."""
import pytest
import json
from datetime import date, datetime
from talkbut.processors.formatter import ReportFormatter
from talkbut.models.report import DailyReport
from talkbut.models.commit import Commit


class TestReportFormatter:
    """Tests for ReportFormatter."""

    @pytest.fixture
    def formatter(self):
        """Create a ReportFormatter instance."""
        return ReportFormatter()

    @pytest.fixture
    def sample_report(self, sample_commits):
        """Create a sample report for testing."""
        return DailyReport(
            date=date(2023, 1, 1),
            total_commits=2,
            files_changed=3,
            insertions=70,
            deletions=15,
            commits=sample_commits,
            ai_summary="This is a test summary of the day's work.",
            categories={"feature": 1, "bugfix": 1},
            tasks=[{"task": "Implement login", "status": "done"}]
        )

    def test_format_markdown_header(self, formatter, sample_report):
        """Test markdown output contains header."""
        md = formatter.format_markdown(sample_report)
        assert "# Daily Report: 2023-01-01" in md

    def test_format_markdown_summary(self, formatter, sample_report):
        """Test markdown output contains summary."""
        md = formatter.format_markdown(sample_report)
        assert "## 📝 Summary" in md
        assert "This is a test summary" in md

    def test_format_markdown_stats(self, formatter, sample_report):
        """Test markdown output contains statistics."""
        md = formatter.format_markdown(sample_report)
        assert "## 📊 Statistics" in md
        assert "Total Commits**: 2" in md
        assert "Files Changed**: 3" in md
        assert "+70" in md
        assert "-15" in md

    def test_format_markdown_categories(self, formatter, sample_report):
        """Test markdown output contains categories."""
        md = formatter.format_markdown(sample_report)
        assert "## 🏷️ Work Breakdown" in md
        assert "feature" in md
        assert "bugfix" in md

    def test_format_markdown_tasks(self, formatter, sample_report):
        """Test markdown output contains tasks."""
        md = formatter.format_markdown(sample_report)
        assert "## ✅ Tasks" in md
        assert "Implement login" in md

    def test_format_markdown_commits(self, formatter, sample_report):
        """Test markdown output contains commit details."""
        md = formatter.format_markdown(sample_report)
        assert "## 💻 Detailed Commits" in md
        assert "feat: add login feature" in md
        assert "fix: resolve auth bug" in md

    def test_format_json(self, formatter, sample_report):
        """Test JSON output is valid."""
        json_str = formatter.format_json(sample_report)
        
        # Should be valid JSON
        data = json.loads(json_str)
        assert data["total_commits"] == 2
        assert data["ai_summary"] == "This is a test summary of the day's work."
        assert len(data["commits"]) == 2

    def test_format_text(self, formatter, sample_report):
        """Test plain text output."""
        text = formatter.format_text(sample_report)
        
        assert "Daily Report: 2023-01-01" in text
        assert "Summary:" in text
        assert "This is a test summary" in text
        assert "Tasks:" in text
        assert "Implement login" in text

    def test_format_markdown_empty_commits(self, formatter):
        """Test formatting report with no commits."""
        report = DailyReport(
            date=date(2023, 1, 1),
            total_commits=0,
            files_changed=0,
            insertions=0,
            deletions=0,
            commits=[],
            ai_summary="No commits today."
        )
        md = formatter.format_markdown(report)
        
        assert "# Daily Report: 2023-01-01" in md
        assert "No commits today." in md
        assert "Total Commits**: 0" in md

    def test_format_markdown_no_tasks(self, formatter):
        """Test formatting report without tasks."""
        report = DailyReport(
            date=date(2023, 1, 1),
            total_commits=0,
            files_changed=0,
            insertions=0,
            deletions=0,
            commits=[],
            ai_summary="Summary"
        )
        md = formatter.format_markdown(report)
        
        # Should not have Tasks section
        assert "## ✅ Tasks" not in md

    def test_format_markdown_commit_with_body(self, formatter):
        """Test formatting commit with multi-line message."""
        commit = Commit(
            hash="abc123def",
            author="Test User",
            email="test@test.com",
            date=datetime(2023, 1, 1, 10, 0),
            message="feat: add feature\n\nThis is the body.\nMore details here.",
            files_changed=["file.py"],
            insertions=10,
            deletions=5
        )
        report = DailyReport(
            date=date(2023, 1, 1),
            total_commits=1,
            files_changed=1,
            insertions=10,
            deletions=5,
            commits=[commit],
            ai_summary="Summary"
        )
        md = formatter.format_markdown(report)
        
        assert "feat: add feature" in md
        assert "This is the body" in md

    def test_format_text_no_tasks(self, formatter):
        """Test plain text output without tasks."""
        report = DailyReport(
            date=date(2023, 1, 1),
            total_commits=1,
            files_changed=1,
            insertions=10,
            deletions=5,
            commits=[],
            ai_summary="Summary"
        )
        text = formatter.format_text(report)
        
        assert "Tasks:" not in text
