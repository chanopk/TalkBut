"""
Repository Scanner - Automatically discover git repositories under specified paths.
"""
import os
from pathlib import Path
from typing import List, Dict, Optional, Set
from talkbut.utils.logger import get_logger

logger = get_logger(__name__)


class RepoScanner:
    """Scan directories to find git repositories."""
    
    def __init__(self, max_depth: int = 3):
        """
        Initialize RepoScanner.
        
        Args:
            max_depth: Maximum directory depth to search (default: 3)
        """
        self.max_depth = max_depth
        self._exclude_dirs: Set[str] = {
            'node_modules', 'venv', '.venv', '__pycache__', 
            'dist', 'build', '.git', 'vendor', 'target'
        }
    
    def scan(self, base_path: str, max_depth: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Scan a directory for git repositories.
        
        Args:
            base_path: Base directory path to scan
            max_depth: Override default max depth for this scan
            
        Returns:
            List of dicts with 'path' and 'name' keys for each found repo
        """
        base = Path(base_path).expanduser().resolve()
        
        if not base.exists():
            logger.warning(f"Scan path does not exist: {base_path}")
            return []
        
        if not base.is_dir():
            logger.warning(f"Scan path is not a directory: {base_path}")
            return []
        
        depth = max_depth if max_depth is not None else self.max_depth
        repos = []
        
        self._scan_recursive(base, repos, current_depth=0, max_depth=depth)
        
        logger.info(f"Found {len(repos)} git repositories under {base_path}")
        return repos
    
    def _scan_recursive(
        self, 
        path: Path, 
        repos: List[Dict[str, str]], 
        current_depth: int,
        max_depth: int
    ) -> bool:
        """
        Recursively scan for git repositories.
        
        Args:
            path: Current directory path
            repos: List to append found repos
            current_depth: Current recursion depth
            max_depth: Maximum depth to search
            
        Returns:
            True if this path is a git repo (to stop deeper scanning)
        """
        if current_depth > max_depth:
            return False
        
        # Check if this directory is a git repository
        git_dir = path / '.git'
        if git_dir.exists() and git_dir.is_dir():
            repo_info = {
                'path': str(path),
                'name': path.name
            }
            repos.append(repo_info)
            logger.debug(f"Found git repository: {path.name}")
            # Don't scan inside git repos (nested repos are rare and usually submodules)
            return True
        
        # Scan subdirectories
        try:
            for entry in path.iterdir():
                if entry.is_dir() and entry.name not in self._exclude_dirs:
                    # Skip hidden directories except we already checked .git
                    if entry.name.startswith('.'):
                        continue
                    self._scan_recursive(entry, repos, current_depth + 1, max_depth)
        except PermissionError:
            logger.debug(f"Permission denied: {path}")
        except OSError as e:
            logger.debug(f"Error scanning {path}: {e}")
        
        return False
    
    def scan_multiple(self, paths: List[str], max_depth: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Scan multiple base paths for git repositories.
        
        Args:
            paths: List of base directory paths to scan
            max_depth: Override default max depth
            
        Returns:
            Combined list of found repos (deduplicated by path)
        """
        seen_paths: Set[str] = set()
        all_repos: List[Dict[str, str]] = []
        
        for base_path in paths:
            repos = self.scan(base_path, max_depth)
            for repo in repos:
                if repo['path'] not in seen_paths:
                    seen_paths.add(repo['path'])
                    all_repos.append(repo)
        
        return all_repos
