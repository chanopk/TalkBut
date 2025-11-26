import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import date, datetime
from talkbut.processors.ai_analyzer import AIAnalyzer
from talkbut.models.commit import Commit
from talkbut.models.report import DailyReport

@pytest.fixture
def sample_commits():
    return [
        Commit(
            hash="123", author="User", email="u@e.com", 
            date=datetime(2023, 1, 1, 10, 0), message="feat: test",
            files_changed=["f1"], insertions=1, deletions=1
        )
    ]

@patch('talkbut.processors.ai_analyzer.genai')
@patch('talkbut.processors.ai_analyzer.CacheManager')
@patch('talkbut.processors.ai_analyzer.ConfigManager')
def test_analyze_commits_api_call(mock_config, mock_cache_cls, mock_genai, sample_commits):
    # Setup mocks
    mock_config_instance = MagicMock()
    mock_config_instance.ai_api_key = "fake_key"
    mock_config.return_value = mock_config_instance
    
    mock_cache = MagicMock()
    mock_cache.get_ai_response.return_value = None
    mock_cache_cls.return_value = mock_cache
    
    mock_model = MagicMock()
    
    class MockResponse:
        def __init__(self, text):
            self.text = text
            
    mock_response = MockResponse('{"summary": "Test Summary", "categories": {"Feature": 1}, "highlights": ["H1"], "timeline": [{"time": "10:00", "activity": "Coding"}]}')
    mock_model.generate_content.return_value = mock_response
    mock_genai.GenerativeModel.return_value = mock_model

    # Test
    analyzer = AIAnalyzer()
    report = analyzer.analyze_commits(sample_commits, date(2023, 1, 1))

    # Verify
    assert isinstance(report, DailyReport)
    assert report.ai_summary == "Test Summary"
    assert report.categories == {"Feature": 1}
    assert report.highlights == ["H1"]
    assert report.timeline == [{"time": "10:00", "activity": "Coding"}]
    
    # Verify API called
    mock_model.generate_content.assert_called_once()
    # Verify cache saved
    mock_cache.save_ai_response.assert_called_once()

@patch('talkbut.processors.ai_analyzer.genai')
@patch('talkbut.processors.ai_analyzer.CacheManager')
@patch('talkbut.processors.ai_analyzer.ConfigManager')
def test_analyze_commits_cached(mock_config, mock_cache_cls, mock_genai, sample_commits):
    # Setup mocks
    mock_config_instance = MagicMock()
    mock_config_instance.ai_api_key = "fake_key"
    mock_config.return_value = mock_config_instance
    
    mock_cache = MagicMock()
    mock_cache.get_ai_response.return_value = '{"summary": "Cached Summary"}'
    mock_cache_cls.return_value = mock_cache
    
    # Test
    analyzer = AIAnalyzer()
    report = analyzer.analyze_commits(sample_commits, date(2023, 1, 1))

    # Verify
    assert report.ai_summary == "Cached Summary"
    # Verify API NOT called
    mock_genai.GenerativeModel.return_value.generate_content.assert_not_called()

@patch('talkbut.processors.ai_analyzer.genai')
@patch('talkbut.processors.ai_analyzer.ConfigManager')
def test_no_api_key(mock_config, mock_genai):
    mock_config_instance = MagicMock()
    mock_config_instance.ai_api_key = None
    mock_config.return_value = mock_config_instance
    
    analyzer = AIAnalyzer()
    assert analyzer.model is None
