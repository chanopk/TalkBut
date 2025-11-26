import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Load configuration from file and environment variables."""
        # Default configuration
        self._config = {
            "git": {
                "repositories": [],
                "default_branch": "main",
                "author_filter": None,
            },
            "ai": {
                "provider": "gemini",
                "api_key_env": "GEMINI_API_KEY",
                "model": "gemini-2.0-flash",
                "temperature": 0.3,
                "max_tokens": 2000,
            },
            "report": {
                "default_format": "markdown",
                "include_stats": True,
                "include_file_list": False,
                "sort_order": "asc",  # asc = chronological
                "group_by": "category",
            },
            "storage": {
                "log_dir": "./data/logs",
                "retention_days": 90,
            }
        }

        # Load from file
        config_path = os.getenv("TALKBUT_CONFIG_PATH", "config/config.yaml")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        self._merge_config(self._config, file_config)
            except Exception as e:
                print(f"Warning: Failed to load config file: {e}")

    def _merge_config(self, base: Dict, update: Dict) -> None:
        """Recursively merge configuration dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'ai.model')."""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    @property
    def git_repos(self) -> list:
        return self.get("git.repositories", [])

    @property
    def ai_api_key(self) -> Optional[str]:
        """
        Get AI API key from environment variable or directly from config.
        
        Supports two modes:
        1. api_key_env as env var name: "GEMINI_API_KEY" -> reads from os.getenv()
        2. api_key_env as direct key: "AIzaSy..." -> uses value directly
        """
        api_key_value = self.get("ai.api_key_env", "GEMINI_API_KEY")
        
        # If it looks like an actual API key (starts with common prefixes), use it directly
        if api_key_value and (
            api_key_value.startswith("AIza") or  # Google API keys
            api_key_value.startswith("sk-") or   # OpenAI keys
            len(api_key_value) > 30  # Likely a key, not an env var name
        ):
            return api_key_value
        
        # Otherwise, treat it as an environment variable name
        return os.getenv(api_key_value)
