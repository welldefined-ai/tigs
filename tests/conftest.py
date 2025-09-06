"""Simple pytest configuration for TUI testing."""

import subprocess
import tempfile
from pathlib import Path
from typing import Generator, List, Optional

import pytest


def create_test_repo(repo_path: Path, commits: Optional[List[str]] = None) -> None:
    """Create a test Git repository with optional commits.
    
    Args:
        repo_path: Path where to create the repository
        commits: List of commit messages to create
    """
    repo_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize git repo
    subprocess.run(['git', 'init'], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.email', 'test@example.com'], 
                   cwd=repo_path, check=True)
    subprocess.run(['git', 'config', 'user.name', 'Test User'], 
                   cwd=repo_path, check=True)
    
    if commits:
        for i, commit_msg in enumerate(commits):
            # Create a test file for each commit
            test_file = repo_path / f'file_{i}.txt'
            test_file.write_text(f'Content for commit: {commit_msg}\n')
            
            subprocess.run(['git', 'add', test_file.name], cwd=repo_path, check=True)
            subprocess.run(['git', 'commit', '-m', commit_msg], cwd=repo_path, check=True)


@pytest.fixture
def test_repo() -> Generator[Path, None, None]:
    """Create a test repository with many commits for scrolling tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "test_repo"
        
        # Create repository with 50 commits to ensure scrolling
        commits = [f"Change {i+1}" for i in range(50)]
        create_test_repo(repo_path, commits)
        
        yield repo_path