import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

class ConfigManager:
    _instance = None
    _config: Dict[str, Any] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_env_file()
            cls._instance._load_config()
        return cls._instance

    def _load_env_file(self) -> None:
        """Load environment variables from .env file."""
        env_path = Path(".env")
        if env_path.exists():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        # Skip comments and empty lines
                        if not line or line.startswith("#"):
                            continue
                        # Parse KEY=VALUE
                        if "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip()
                            # Remove quotes if present
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            # Set environment variable if not already set
                            if key and not os.getenv(key):
                                os.environ[key] = value
            except Exception as e:
                print(f"Warning: Failed to load .env file: {e}")

    def _load_config(self) -> None:
        """Load configuration from file and environment variables."""
        # Default configuration
        self._config = {
            "git": {
                "repositories": [],
                "scan_paths": [],  # Paths to scan for git repos
                "scan_depth": 2,   # Max depth for scanning
                "default_branch": "main",
                "author": "",  # Filter commits by author (email or name)
            },
            "ai": {
                "provider": "gemini",
                "api_key_env": "GEMINI_API_KEY",
                "model": "gemini-2.0-flash-exp",
                "temperature": 0.3,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
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
            },
            "schedule": {
                "enabled": False,
                "time": "18:00",  # HH:MM format (24-hour)
                "status_file": "./data/schedule_status.json",
                "error_log": "./data/schedule_errors.log",
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
    def git_repos(self) -> List[Dict[str, str]]:
        """
        Get all git repositories from both explicit list and scanned paths.
        
        Returns:
            Combined list of repositories (deduplicated by path)
        """
        # Get explicitly defined repositories
        explicit_repos = self.get("git.repositories", [])
        
        # Get scan paths configuration
        scan_paths = self.get("git.scan_paths", [])
        scan_depth = self.get("git.scan_depth", 2)
        
        if not scan_paths:
            return explicit_repos
        
        # Scan for repositories
        from talkbut.collectors.repo_scanner import RepoScanner
        scanner = RepoScanner(max_depth=scan_depth)
        scanned_repos = scanner.scan_multiple(scan_paths, scan_depth)
        
        # Merge and deduplicate (explicit repos take priority)
        seen_paths = set()
        merged_repos = []
        
        # Add explicit repos first (they have priority)
        for repo in explicit_repos:
            path = str(Path(repo.get('path', '')).expanduser().resolve())
            if path not in seen_paths:
                seen_paths.add(path)
                merged_repos.append(repo)
        
        # Add scanned repos that aren't already in the list
        for repo in scanned_repos:
            path = str(Path(repo.get('path', '')).expanduser().resolve())
            if path not in seen_paths:
                seen_paths.add(path)
                merged_repos.append(repo)
        
        return merged_repos

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

    def get_schedule_config(self) -> Dict[str, Any]:
        """
        Get schedule configuration.
        
        Returns:
            Dictionary with schedule settings (enabled, time, status_file, error_log)
            
        Requirements: 1.3, 2.1
        """
        return {
            "enabled": self.get("schedule.enabled", False),
            "time": self.get("schedule.time", "18:00"),
            "status_file": self.get("schedule.status_file", "./data/schedule_status.json"),
            "error_log": self.get("schedule.error_log", "./data/schedule_errors.log"),
        }

    def set_schedule_config(self, **kwargs) -> None:
        """
        Set schedule configuration values.
        
        Args:
            **kwargs: Schedule configuration keys to update
                     (enabled, time, status_file, error_log)
                     
        Requirements: 1.3, 2.1
        """
        if "schedule" not in self._config:
            self._config["schedule"] = {}
        
        for key, value in kwargs.items():
            if key in ["enabled", "time", "status_file", "error_log"]:
                self._config["schedule"][key] = value

    def save_schedule_config(self, config_path: Optional[str] = None) -> None:
        """
        Save current configuration to file.
        
        Args:
            config_path: Path to config file (default: config/config.yaml)
            
        Requirements: 1.3
        """
        if config_path is None:
            config_path = os.getenv("TALKBUT_CONFIG_PATH", "config/config.yaml")
        
        # Ensure directory exists
        config_dir = os.path.dirname(config_path)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)
        
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)
        except Exception as e:
            raise IOError(f"Failed to save config file: {e}")
