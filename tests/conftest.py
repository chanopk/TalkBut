"""Shared fixtures for tests."""
import pytest
import os
from datetime import datetime
from talkbut.models.commit import Commit


@pytest.fixture
def sample_commit():
    """Create a sample commit for testing."""
    return Commit(
        hash="abc1234567890abcdef1234567890abcdef12",
        author="Test User",
        email="test@example.com",
        date=datetime(2023, 1, 1, 10, 0, 0),
        message="feat: add new feature\n\n- implemented feature x\n- fixed bug y",
        files_changed=["src/main.py", "tests/test_main.py"],
        insertions=10,
        deletions=5,
        branch="main"
    )


@pytest.fixture
def sample_commits():
    """Create multiple sample commits for testing."""
    return [
        Commit(
            hash="hash1abc",
            author="User1",
            email="user1@example.com",
            date=datetime(2023, 1, 1, 9, 0, 0),
            message="feat: add login feature",
            files_changed=["src/auth.py"],
            insertions=50,
            deletions=10,
            branch="main"
        ),
        Commit(
            hash="hash2def",
            author="User1",
            email="user1@example.com",
            date=datetime(2023, 1, 1, 14, 0, 0),
            message="fix: resolve auth bug\n\nFixed token validation issue",
            files_changed=["src/auth.py", "tests/test_auth.py"],
            insertions=20,
            deletions=5,
            branch="main"
        ),
    ]


@pytest.fixture
def mock_repo_path(tmp_path):
    """Create a mock git repository directory."""
    repo_dir = tmp_path / "mock_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()
    return str(repo_dir)


@pytest.fixture
def temp_config_dir(tmp_path, monkeypatch):
    """Create a temporary config directory."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    monkeypatch.setenv("TALKBUT_CONFIG_PATH", str(config_dir / "config.yaml"))
    return config_dir
