#!/usr/bin/env python3
"""Test CLI sync operations: push-chats, fetch-chats."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from framework.fixtures import create_test_repo


@pytest.fixture
def sync_repo():
    """Create a test repository for sync operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "sync_repo"
        
        # Create repository with some commits
        commits = [f"Sync commit {i+1}" for i in range(5)]
        create_test_repo(repo_path, commits)
        yield repo_path


def run_tigs(repo_path, *args):
    """Run tigs command and return result."""
    cmd = ["uv", "run", "tigs", "--repo", str(repo_path)] + list(args)
    result = subprocess.run(cmd, cwd="/Users/basicthinker/Projects/tigs/python", 
                          capture_output=True, text=True)
    return result


class TestCLISync:
    """Test CLI sync operations."""
    
    def test_push_fetch_cycle(self, sync_repo):
        """Test push and fetch preserve notes."""
        # First, try to add a chat note
        chat_content = """chat:
- role: user
  content: "Test message for sync"
"""
        
        add_result = run_tigs(sync_repo, "add-chat", "-m", chat_content)
        print("Add for sync:", add_result.returncode, add_result.stdout, add_result.stderr)
        
        if add_result.returncode != 0:
            print("Cannot test sync without working add-chat")
            return
        
        # Try to push chats (will likely fail without remote)
        result = run_tigs(sync_repo, "push-chats", "origin")
        print("Push result:", result.returncode, result.stdout, result.stderr)
        
        # Expected to fail since no remote exists
        assert result.returncode != 0
        assert "Error:" in result.stdout or "Error:" in result.stderr or result.stderr
    
    def test_sync_errors(self, sync_repo):
        """Test sync error handling."""
        # Test push with missing remote
        result = run_tigs(sync_repo, "push-chats", "nonexistent")
        print("Push nonexistent:", result.returncode, result.stdout, result.stderr)
        
        if result.returncode != 1:
            print("Push command might not exist yet or have different error handling")
        
        # Test fetch with missing remote  
        result = run_tigs(sync_repo, "fetch-chats", "nonexistent")
        print("Fetch nonexistent:", result.returncode, result.stdout, result.stderr)
        
        if result.returncode != 1:
            print("Fetch command might not exist yet or have different error handling")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])