import os
from talkbut.core.config import ConfigManager

def test_config_defaults():
    config = ConfigManager()
    assert config.get("git.default_branch") == "main"
    assert config.get("ai.provider") == "gemini"
    assert config.get("report.sort_order") == "asc"

def test_config_env_override(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test_key")
    config = ConfigManager()
    assert config.ai_api_key == "test_key"
