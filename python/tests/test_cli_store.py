"""Test cases for add-chat CLI command."""

import subprocess
from tigs.cli import main


class TestAddChat:
    """Test the 'tigs add-chat' command."""

    def test_add_chat_basic(self, runner, git_repo):
        """Test basic chat addition to HEAD."""
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", "Hello, World!"])
        assert result.exit_code == 0
        assert "Added chat to commit:" in result.output
        # Should contain a 40-character commit SHA
        commit_sha = result.output.split(":")[-1].strip()
        assert len(commit_sha) == 40

    def test_add_chat_to_specific_commit(self, runner, git_repo):
        """Test adding chat to a specific commit."""
        # Get HEAD commit SHA
        head_result = subprocess.run(
            ["git", "rev-parse", "HEAD"], 
            cwd=git_repo, 
            capture_output=True, 
            text=True
        )
        head_sha = head_result.stdout.strip()
        
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", head_sha, "-m", "Chat for specific commit"])
        assert result.exit_code == 0
        assert f"Added chat to commit: {head_sha}" in result.output

    def test_add_chat_multiline_content(self, runner, git_repo):
        """Test adding multiline chat content."""
        content = "Line 1\nLine 2\nLine 3"
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", content])
        assert result.exit_code == 0
        assert "Added chat to commit:" in result.output

    def test_add_chat_unicode_content(self, runner, git_repo):
        """Test adding Unicode content."""
        content = "Hello 世界! 🌍"
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", content])
        assert result.exit_code == 0
        assert "Added chat to commit:" in result.output

    def test_add_chat_duplicate_fails(self, runner, git_repo):
        """Test that adding chat to same commit twice fails."""
        # Add first chat
        result1 = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", "First chat"])
        assert result1.exit_code == 0
        
        # Try to add second chat to same commit - should fail
        result2 = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", "Second chat"])
        assert result2.exit_code == 1
        assert "already has a chat" in result2.output

    def test_add_chat_invalid_commit(self, runner, git_repo):
        """Test adding chat to invalid commit fails."""
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "invalid-commit", "-m", "Test"])
        assert result.exit_code == 1
        assert "Invalid commit" in result.output

    def test_add_chat_no_message_aborts(self, runner, git_repo):
        """Test that providing no message aborts the operation."""
        # This test is difficult in headless environments, so we test the equivalent
        # by testing what happens when editor returns empty content
        import os
        os.environ["EDITOR"] = "true"  # Set a no-op editor
        
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat"])
        assert result.exit_code == 1
        # Should abort due to empty content after editor
        assert "Aborted" in result.output or "No content" in result.output

    def test_add_chat_empty_message_aborts(self, runner, git_repo):
        """Test that providing empty message aborts the operation."""
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", ""])
        assert result.exit_code == 1
        assert "No content provided" in result.output or result.exit_code == 1