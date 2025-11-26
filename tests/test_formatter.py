import pytest
from datetime import date, datetime
from talkbut.processors.formatter import ReportFormatter
from talkbut.models.report import DailyReport
from talkbut.models.commit import Commit

@pytest.fixture
def sample_report():
    return DailyReport(
        date=date(2023, 1, 1),
        total_commits=2,
        files_changed=2,
        insertions=10,
        deletions=5,
        commits=[
            Commit("h1", "u1", "e1", datetime(2023, 1, 1, 10, 0), "feat: A", [], 5, 2),
            Commit("h2", "u1", "e1", datetime(2023, 1, 1, 14, 0), "fix: B\n\ndetails", [], 5, 3)
        ],
        ai_summary="This is a summary.",
        categories={"Feature": 1, "Bugfix": 1},
        highlights=["Highlight 1"],
        timeline=[{"time": "10:00", "activity": "Feature A"}]
    )

def test_format_markdown(sample_report):
    formatter = ReportFormatter()
    md = formatter.format_markdown(sample_report)
    
    assert "# Daily Report: 2023-01-01" in md
    assert "## 📝 Summary" in md
    assert "This is a summary." in md
    assert "## ✨ Highlights" in md
    assert "- Highlight 1" in md
    assert "## ⏱️ Timeline" in md
    assert "**10:00**: Feature A" in md
    assert "## 💻 Detailed Commits" in md
    assert "feat: A" in md
    assert "fix: B" in md
    assert "> details" in md

def test_format_json(sample_report):
    formatter = ReportFormatter()
    json_out = formatter.format_json(sample_report)
    assert '"total_commits": 2' in json_out
    assert '"ai_summary": "This is a summary."' in json_out

def test_format_text(sample_report):
    formatter = ReportFormatter()
    text = formatter.format_text(sample_report)
    assert "Daily Report: 2023-01-01" in text
    assert "Summary: This is a summary." in text
    assert "Stats: 2 commits" in text
