"""Tests for DataParser."""
import pytest
from datetime import datetime
from talkbut.collectors.parser import DataParser
from talkbut.models.commit import Commit


class TestDataParser:
    """Tests for DataParser."""

    @pytest.fixture
    def parser(self):
        """Create a DataParser instance."""
        return DataParser()

    def test_parse_commit_message_basic(self, parser):
        """Test parsing a basic commit message."""
        message = "feat: add login feature"
        parsed = parser.parse_commit_message(message)
        
        assert parsed["subject"] == "feat: add login feature"
        assert parsed["body"] == ""
        assert parsed["ticket_refs"] == []
        assert parsed["tags"] == []

    def test_parse_commit_message_with_body(self, parser):
        """Test parsing commit message with body."""
        message = "feat: add login feature\n\nImplemented OAuth2 login flow.\nAdded tests."
        parsed = parser.parse_commit_message(message)
        
        assert parsed["subject"] == "feat: add login feature"
        assert "Implemented OAuth2" in parsed["body"]
        assert "Added tests" in parsed["body"]

    def test_parse_commit_message_with_ticket_refs(self, parser):
        """Test extracting ticket references."""
        message = "feat: add login [FEATURE]\n\nRelates to JIRA-123 and #456"
        parsed = parser.parse_commit_message(message)
        
        assert "JIRA-123" in parsed["ticket_refs"]
        assert "#456" in parsed["ticket_refs"]

    def test_parse_commit_message_with_tags(self, parser):
        """Test extracting tags from subject."""
        message = "feat: add feature [FEATURE] [BETA]"
        parsed = parser.parse_commit_message(message)
        
        assert "FEATURE" in parsed["tags"]
        assert "BETA" in parsed["tags"]

    def test_categorize_commit_feature(self, parser):
        """Test categorizing feature commits."""
        commit = Commit("h", "a", "e", datetime.now(), "feat: new feature")
        assert parser.categorize_commit(commit) == "feature"
        
        commit2 = Commit("h", "a", "e", datetime.now(), "add: new module")
        assert parser.categorize_commit(commit2) == "feature"

    def test_categorize_commit_bugfix(self, parser):
        """Test categorizing bugfix commits."""
        commit = Commit("h", "a", "e", datetime.now(), "fix: resolve issue")
        assert parser.categorize_commit(commit) == "bugfix"
        
        commit2 = Commit("h", "a", "e", datetime.now(), "bug: fix crash")
        assert parser.categorize_commit(commit2) == "bugfix"

    def test_categorize_commit_refactor(self, parser):
        """Test categorizing refactor commits."""
        commit = Commit("h", "a", "e", datetime.now(), "refactor: clean up code")
        assert parser.categorize_commit(commit) == "refactor"

    def test_categorize_commit_docs(self, parser):
        """Test categorizing documentation commits."""
        commit = Commit("h", "a", "e", datetime.now(), "docs: update README")
        assert parser.categorize_commit(commit) == "documentation"

    def test_categorize_commit_test(self, parser):
        """Test categorizing test commits."""
        commit = Commit("h", "a", "e", datetime.now(), "test: add unit tests")
        assert parser.categorize_commit(commit) == "testing"

    def test_categorize_commit_chore(self, parser):
        """Test categorizing chore commits."""
        commit = Commit("h", "a", "e", datetime.now(), "chore: update deps")
        assert parser.categorize_commit(commit) == "chore"

    def test_categorize_commit_other(self, parser):
        """Test categorizing unknown commits."""
        commit = Commit("h", "a", "e", datetime.now(), "random message")
        assert parser.categorize_commit(commit) == "other"

    def test_enrich_commit(self, parser):
        """Test enriching commit with parsed metadata."""
        commit = Commit(
            hash="abc123",
            author="Test",
            email="test@test.com",
            date=datetime.now(),
            message="feat: add feature [BETA]\n\nRef JIRA-999 and #123"
        )
        
        enriched = parser.enrich_commit(commit)
        
        assert "JIRA-999" in enriched.ticket_refs
        assert "#123" in enriched.ticket_refs
        assert "BETA" in enriched.tags
