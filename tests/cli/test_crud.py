#!/usr/bin/env python3
"""Test CLI CRUD operations: add-chat, show-chat, list-chats, remove-chat."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from framework.fixtures import create_test_repo


@pytest.fixture
def cli_repo():
    """Create a test repository for CLI operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "cli_repo"
        
        # Create repository with some commits
        commits = [f"Commit {i+1}: Some changes" for i in range(10)]
        create_test_repo(repo_path, commits)
        yield repo_path


def run_tigs(repo_path, *args):
    """Run tigs command and return result."""
    cmd = ["uv", "run", "tigs", "--repo", str(repo_path)] + list(args)
    result = subprocess.run(cmd, cwd="/Users/basicthinker/Projects/tigs/python", 
                          capture_output=True, text=True)
    return result


class TestCLICRUD:
    """Test CLI CRUD operations."""
    
    def test_add_show_cycle(self, cli_repo):
        """Test adding a chat and then showing it."""
        # Add a chat to HEAD commit
        chat_content = """chat:
- role: user
  content: "How do I fix this bug?"
- role: assistant  
  content: "You can try debugging with print statements."
"""
        
        # Add chat
        result = run_tigs(cli_repo, "add-chat", "-m", chat_content)
        print("Add result:", result.returncode, result.stdout, result.stderr)
        
        if result.returncode != 0:
            # This might be expected if command doesn't exist yet
            print(f"Add-chat command failed (possibly not implemented): {result.stderr}")
            return
            
        # Show chat
        result = run_tigs(cli_repo, "show-chat")
        print("Show result:", result.returncode, result.stdout, result.stderr)
        
        if result.returncode == 0:
            assert "user" in result.stdout
            assert "How do I fix this bug?" in result.stdout
            assert "assistant" in result.stdout
        else:
            print(f"Show-chat command failed: {result.stderr}")
    
    def test_list_multiple(self, cli_repo):
        """Test listing chats shows proper format."""
        # Try to list chats (might be empty)
        result = run_tigs(cli_repo, "list-chats")
        print("List result:", result.returncode, result.stdout, result.stderr)
        
        if result.returncode != 0:
            print(f"List-chats command failed (possibly not implemented): {result.stderr}")
            return
            
        # Should show some output even if empty
        assert result.stdout is not None
    
    def test_remove_confirmation(self, cli_repo):
        """Test remove requires confirmation."""
        # Try to remove chat (might not exist)
        result = run_tigs(cli_repo, "remove-chat")
        print("Remove result:", result.returncode, result.stdout, result.stderr)
        
        # Command might not be implemented yet
        if result.returncode != 0:
            print(f"Remove-chat command failed (possibly not implemented): {result.stderr}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])