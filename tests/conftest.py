import pytest
import os
from datetime import datetime
from talkbut.models.commit import Commit

@pytest.fixture
def sample_commit():
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
def mock_repo_path(tmp_path):
    repo_dir = tmp_path / "mock_repo"
    repo_dir.mkdir()
    (repo_dir / ".git").mkdir()
    return str(repo_dir)
