import pytest
from datetime import datetime
from talkbut.storage.cache import CacheManager
from talkbut.models.commit import Commit

@pytest.fixture
def sample_commits():
    return [
        Commit(
            hash="hash1", author="User1", email="u1@e.com", 
            date=datetime(2023, 1, 1), message="msg1",
            files_changed=["f1"], insertions=1, deletions=1
        ),
        Commit(
            hash="hash2", author="User2", email="u2@e.com", 
            date=datetime(2023, 1, 2), message="msg2",
            files_changed=["f2"], insertions=2, deletions=2
        )
    ]

def test_cache_manager(tmp_path, sample_commits):
    # Mock config to use tmp_path
    with pytest.MonkeyPatch.context() as m:
        m.setenv("TALKBUT_CONFIG_PATH", "non_existent")
        # We need to patch ConfigManager or pass path directly.
        # Since CacheManager uses ConfigManager singleton, it's tricky without DI.
        # But we can monkeypatch ConfigManager.get
        
        from talkbut.core.config import ConfigManager
        
        original_get = ConfigManager.get
        def mock_get(self, key, default=None):
            if key == "storage.cache_dir":
                return str(tmp_path / "cache")
            return original_get(self, key, default)
            
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr(ConfigManager, "get", mock_get)
            
            cache = CacheManager()
            cache.save_commits("repo1", "range1", sample_commits)
            
            loaded = cache.load_commits("repo1", "range1")
            assert len(loaded) == 2
            assert loaded[0].hash == "hash1"
