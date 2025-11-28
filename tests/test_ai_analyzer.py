"""Tests for AIAnalyzer."""
import pytest
from unittest.mock import MagicMock, patch
from datetime import date, datetime
from talkbut.processors.ai_analyzer import AIAnalyzer
from talkbut.models.commit import Commit
from talkbut.models.report import DailyReport


class TestAIAnalyzer:
    """Tests for AIAnalyzer."""

    @pytest.fixture
    def sample_commits(self):
        """Create sample commits for testing."""
        return [
            Commit(
                hash="abc123",
                author="Test User",
                email="test@example.com",
                date=datetime(2023, 1, 1, 10, 0),
                message="feat: add login feature",
                files_changed=["src/auth.py"],
                insertions=50,
                deletions=10
            ),
            Commit(
                hash="def456",
                author="Test User",
                email="test@example.com",
                date=datetime(2023, 1, 1, 14, 0),
                message="fix: resolve auth bug",
                files_changed=["src/auth.py"],
                insertions=5,
                deletions=2
            ),
        ]

    @patch('talkbut.processors.ai_analyzer.genai')
    @patch('talkbut.processors.ai_analyzer.ConfigManager')
    def test_analyzer_no_api_key(self, mock_config_cls, mock_genai):
        """Test analyzer without API key."""
        mock_config = MagicMock()
        mock_config.ai_api_key = None
        mock_config.get.return_value = None
        mock_config_cls.return_value = mock_config
        
        analyzer = AIAnalyzer()
        
        assert analyzer.model is None

    @patch('talkbut.processors.ai_analyzer.genai')
    @patch('talkbut.processors.ai_analyzer.ConfigManager')
    def test_analyzer_with_api_key(self, mock_config_cls, mock_genai):
        """Test analyzer initializes with API key."""
        mock_config = MagicMock()
        mock_config.ai_api_key = "test_api_key"
        mock_config.get.side_effect = lambda key, default=None: {
            "ai.model": "gemini-1.5-flash",
            "ai.temperature": 0.3,
            "ai.top_p": 0.95,
            "ai.top_k": 40,
            "ai.max_output_tokens": 8192,
        }.get(key, default)
        mock_config_cls.return_value = mock_config
        
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        
        analyzer = AIAnalyzer()
        
        mock_genai.configure.assert_called_once_with(api_key="test_api_key")
        assert analyzer.model is not None

    @patch('talkbut.processors.ai_analyzer.genai')
    @patch('talkbut.processors.ai_analyzer.ConfigManager')
    def test_analyze_commits_no_model(self, mock_config_cls, mock_genai, sample_commits):
        """Test analyzing commits without AI model returns basic report."""
        mock_config = MagicMock()
        mock_config.ai_api_key = None
        mock_config.get.return_value = None
        mock_config_cls.return_value = mock_config
        
        analyzer = AIAnalyzer()
        report = analyzer.analyze_commits(sample_commits, date(2023, 1, 1))
        
        assert isinstance(report, DailyReport)
        assert report.total_commits == 2
        assert report.insertions == 55
        assert report.deletions == 12
        assert "pending" in report.ai_summary.lower() or "auto-generated" in report.ai_summary.lower()

    @patch('talkbut.processors.ai_analyzer.genai')
    @patch('talkbut.processors.ai_analyzer.ConfigManager')
    def test_analyze_commits_empty(self, mock_config_cls, mock_genai):
        """Test analyzing empty commits list."""
        mock_config = MagicMock()
        mock_config.ai_api_key = None
        mock_config.get.return_value = None
        mock_config_cls.return_value = mock_config
        
        analyzer = AIAnalyzer()
        report = analyzer.analyze_commits([], date(2023, 1, 1))
        
        assert report.total_commits == 0
        assert report.insertions == 0
        assert report.deletions == 0

    @patch('talkbut.processors.ai_analyzer.genai')
    @patch('talkbut.processors.ai_analyzer.ConfigManager')
    def test_analyze_commits_with_ai(self, mock_config_cls, mock_genai, sample_commits):
        """Test analyzing commits with AI response."""
        mock_config = MagicMock()
        mock_config.ai_api_key = "test_key"
        mock_config.get.side_effect = lambda key, default=None: {
            "ai.model": "gemini-1.5-flash",
            "ai.temperature": 0.3,
            "ai.top_p": 0.95,
            "ai.top_k": 40,
            "ai.max_output_tokens": 8192,
        }.get(key, default)
        mock_config_cls.return_value = mock_config
        
        # Mock AI response
        mock_response = MagicMock()
        mock_response.text = '{"summary": "Worked on authentication features", "categories": {"feature": 1, "bugfix": 1}, "tasks": [{"task": "Login"}]}'
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        analyzer = AIAnalyzer()
        report = analyzer.analyze_commits(sample_commits, date(2023, 1, 1))
        
        assert report.ai_summary == "Worked on authentication features"
        assert report.categories == {"feature": 1, "bugfix": 1}
        assert report.tasks == [{"task": "Login"}]

    @patch('talkbut.processors.ai_analyzer.genai')
    @patch('talkbut.processors.ai_analyzer.ConfigManager')
    def test_analyze_commits_ai_error(self, mock_config_cls, mock_genai, sample_commits):
        """Test handling AI API errors gracefully."""
        mock_config = MagicMock()
        mock_config.ai_api_key = "test_key"
        mock_config.get.side_effect = lambda key, default=None: {
            "ai.model": "gemini-1.5-flash",
            "ai.temperature": 0.3,
            "ai.top_p": 0.95,
            "ai.top_k": 40,
            "ai.max_output_tokens": 8192,
        }.get(key, default)
        mock_config_cls.return_value = mock_config
        
        mock_model = MagicMock()
        mock_model.generate_content.side_effect = Exception("API Error")
        mock_genai.GenerativeModel.return_value = mock_model
        
        analyzer = AIAnalyzer()
        report = analyzer.analyze_commits(sample_commits, date(2023, 1, 1))
        
        # Should still return a report with error message
        assert isinstance(report, DailyReport)
        assert "failed" in report.ai_summary.lower()

    @patch('talkbut.processors.ai_analyzer.genai')
    @patch('talkbut.processors.ai_analyzer.ConfigManager')
    def test_analyze_commits_json_in_code_block(self, mock_config_cls, mock_genai, sample_commits):
        """Test parsing AI response wrapped in code blocks."""
        mock_config = MagicMock()
        mock_config.ai_api_key = "test_key"
        mock_config.get.side_effect = lambda key, default=None: {
            "ai.model": "gemini-1.5-flash",
            "ai.temperature": 0.3,
            "ai.top_p": 0.95,
            "ai.top_k": 40,
            "ai.max_output_tokens": 8192,
        }.get(key, default)
        mock_config_cls.return_value = mock_config
        
        # Mock AI response with code block
        mock_response = MagicMock()
        mock_response.text = '```json\n{"summary": "Test summary", "categories": {}, "tasks": []}\n```'
        
        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response
        mock_genai.GenerativeModel.return_value = mock_model
        
        analyzer = AIAnalyzer()
        report = analyzer.analyze_commits(sample_commits, date(2023, 1, 1))
        
        assert report.ai_summary == "Test summary"
