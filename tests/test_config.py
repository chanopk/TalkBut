"""Tests for ConfigManager."""
import pytest
import os
from talkbut.core.config import ConfigManager


@pytest.fixture(autouse=True)
def reset_config_singleton():
    """Reset ConfigManager singleton before each test."""
    ConfigManager._instance = None
    ConfigManager._config = {}
    yield
    ConfigManager._instance = None
    ConfigManager._config = {}


class TestConfigManager:
    """Tests for ConfigManager."""

    def test_config_defaults(self, monkeypatch):
        """Test default configuration values."""
        monkeypatch.setenv("TALKBUT_CONFIG_PATH", "nonexistent.yaml")
        config = ConfigManager()
        
        assert config.get("git.default_branch") == "main"
        assert config.get("ai.provider") == "gemini"
        assert config.get("report.sort_order") == "asc"
        assert config.get("report.default_format") == "markdown"

    def test_config_get_nested(self, monkeypatch):
        """Test getting nested config values."""
        monkeypatch.setenv("TALKBUT_CONFIG_PATH", "nonexistent.yaml")
        config = ConfigManager()
        
        assert config.get("ai.model") == "gemini-2.0-flash-exp"
        assert config.get("ai.temperature") == 0.3
        assert config.get("storage.log_dir") == "./data/logs"

    def test_config_get_default(self, monkeypatch):
        """Test getting non-existent key returns default."""
        monkeypatch.setenv("TALKBUT_CONFIG_PATH", "nonexistent.yaml")
        config = ConfigManager()
        
        assert config.get("nonexistent.key") is None
        assert config.get("nonexistent.key", "default") == "default"

    def test_config_env_override_api_key(self, monkeypatch):
        """Test API key from environment variable."""
        monkeypatch.setenv("TALKBUT_CONFIG_PATH", "nonexistent.yaml")
        monkeypatch.setenv("GEMINI_API_KEY", "test_api_key_123")
        
        config = ConfigManager()
        assert config.ai_api_key == "test_api_key_123"

    def test_config_direct_api_key(self, monkeypatch, tmp_path):
        """Test direct API key in config (not env var name)."""
        monkeypatch.setenv("TALKBUT_CONFIG_PATH", "nonexistent.yaml")
        
        config = ConfigManager()
        # Simulate direct key in config
        config._config["ai"]["api_key_env"] = "AIzaSyTestDirectKey123456789"
        
        assert config.ai_api_key == "AIzaSyTestDirectKey123456789"

    def test_config_no_api_key(self, monkeypatch):
        """Test when no API key is available (using non-existent env var)."""
        monkeypatch.setenv("TALKBUT_CONFIG_PATH", "nonexistent.yaml")
        monkeypatch.delenv("NONEXISTENT_API_KEY", raising=False)
        
        config = ConfigManager()
        # Set to use a non-existent env var name
        config._config["ai"]["api_key_env"] = "NONEXISTENT_API_KEY"
        
        assert config.ai_api_key is None

    def test_config_singleton(self, monkeypatch):
        """Test ConfigManager is a singleton."""
        monkeypatch.setenv("TALKBUT_CONFIG_PATH", "nonexistent.yaml")
        
        config1 = ConfigManager()
        config2 = ConfigManager()
        assert config1 is config2

    def test_git_repos_property(self, monkeypatch):
        """Test git_repos property."""
        monkeypatch.setenv("TALKBUT_CONFIG_PATH", "nonexistent.yaml")
        config = ConfigManager()
        
        assert config.git_repos == []
