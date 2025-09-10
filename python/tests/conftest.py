"""Shared fixtures for pytest tests."""

import subprocess
from pathlib import Path
from typing import List, Dict, Any
import yaml
import os

import pytest
from click.testing import CliRunner

from tests.mock_sessions import create_mock_claude_home


@pytest.fixture
def claude_logs(tmp_path, monkeypatch):
    """Create mock Claude Code logs for testing.
    
    This fixture creates a temporary home directory with mock .claude/projects
    structure containing realistic JSONL session files that cligent can parse.
    """
    # Create mock home directory
    mock_home = tmp_path / "mock_home"
    mock_home.mkdir()
    
    # Set HOME environment variable to our mock directory
    monkeypatch.setenv("HOME", str(mock_home))
    
    # Create mock Claude sessions
    sessions = create_mock_claude_home(mock_home, num_sessions=3)
    
    # Convert to absolute paths for cligent
    absolute_sessions = []
    for relative_path, metadata in sessions:
        absolute_path = mock_home / relative_path
        absolute_sessions.append((str(absolute_path), metadata))
    
    return absolute_sessions


@pytest.fixture
def git_repo(tmp_path):
    """Create a temporary Git repository for testing."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Initialize Git repo
    subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)

    # Create initial commit to have a valid repo
    (repo_path / "README.md").write_text("Test repository")
    subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True, capture_output=True)

    return repo_path


@pytest.fixture
def runner():
    """Create a Click test runner."""
    return CliRunner()


@pytest.fixture
def git_notes_helper():
    """Helper functions for Git notes verification."""
    class GitNotesHelper:
        @staticmethod
        def verify_note_exists(repo_path: Path, commit_sha: str) -> bool:
            """Check if a Git note exists for a commit."""
            result = subprocess.run(
                ["git", "notes", "--ref=refs/notes/chats", "show", commit_sha],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        
        @staticmethod
        def get_note_content(repo_path: Path, commit_sha: str) -> str:
            """Get Git note content for a commit."""
            result = subprocess.run(
                ["git", "notes", "--ref=refs/notes/chats", "show", commit_sha],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        
        @staticmethod
        def list_notes(repo_path: Path) -> List[str]:
            """List all commit SHAs with notes."""
            result = subprocess.run(
                ["git", "notes", "--ref=refs/notes/chats", "list"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return []
            return [line.split()[-1] for line in result.stdout.strip().split('\n') if line.strip()]
        
        @staticmethod
        def validate_yaml_schema(content: str) -> bool:
            """Validate that content matches tigs.chat/v1 schema."""
            try:
                data = yaml.safe_load(content)
                return (
                    isinstance(data, dict) and
                    data.get('schema') == 'tigs.chat/v1' and
                    'messages' in data and
                    isinstance(data['messages'], list) and
                    all(
                        isinstance(msg, dict) and 
                        'role' in msg and 
                        'content' in msg 
                        for msg in data['messages']
                    )
                )
            except yaml.YAMLError:
                return False
    
    return GitNotesHelper()


@pytest.fixture
def sample_yaml_content():
    """Sample YAML content matching tigs.chat/v1 schema."""
    return """schema: tigs.chat/v1
messages:
- role: user
  content: |
    How do I create a Python function?
- role: assistant
  content: |
    Here's a simple Python function:
    
    ```python
    def greet(name):
        return f"Hello, {name}!"
    ```
"""


@pytest.fixture
def multi_commit_repo(git_repo):
    """Create a Git repo with multiple commits for testing."""
    # Create additional commits
    commits = []
    
    for i in range(1, 4):
        file_path = git_repo / f"file{i}.py"
        file_path.write_text(f"# File {i}\nprint('Hello from file {i}')")
        subprocess.run(["git", "add", f"file{i}.py"], cwd=git_repo, check=True)
        result = subprocess.run(
            ["git", "commit", "-m", f"Add file{i}.py"],
            cwd=git_repo,
            check=True,
            capture_output=True,
            text=True
        )
        
        # Get commit SHA
        sha_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=git_repo,
            capture_output=True,
            text=True,
            check=True
        )
        commits.append(sha_result.stdout.strip())
    
    return git_repo, commits

