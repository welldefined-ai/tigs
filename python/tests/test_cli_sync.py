"""Test cases for push-chats and fetch-chats CLI commands."""

from tigs.cli import main


class TestPushFetchChats:
    """Test the 'tigs push-chats' and 'tigs fetch-chats' commands."""

    def test_push_chats_with_invalid_remote(self, runner, git_repo):
        """Test push-chats with a non-existent remote."""
        # This should fail because 'nonexistent' doesn't exist in our test repo
        result = runner.invoke(main, ["--repo", str(git_repo), "push-chats", "nonexistent"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_fetch_chats_with_invalid_remote(self, runner, git_repo):
        """Test fetch-chats with a non-existent remote."""
        # This should fail because 'nonexistent' doesn't exist in our test repo
        result = runner.invoke(main, ["--repo", str(git_repo), "fetch-chats", "nonexistent"])
        assert result.exit_code == 1
        assert "Error:" in result.output

    def test_push_chats_no_notes(self, runner, git_repo):
        """Test pushing when there are no chat notes."""
        # Add a remote (even though it doesn't exist, the push will fail gracefully)
        import subprocess
        try:
            subprocess.run(["git", "remote", "add", "test-remote", "/tmp/nonexistent"], 
                         cwd=git_repo, check=True, capture_output=True)
        except:
            pass  # Remote might already exist or command might fail
        
        result = runner.invoke(main, ["--repo", str(git_repo), "push-chats", "test-remote"])
        # Should exit with error (can't push to nonexistent remote)
        assert result.exit_code == 1

    def test_fetch_chats_no_notes(self, runner, git_repo):
        """Test fetching when there are no chat notes."""
        # Similar to push test
        import subprocess
        try:
            subprocess.run(["git", "remote", "add", "test-remote", "/tmp/nonexistent"], 
                         cwd=git_repo, check=True, capture_output=True)
        except:
            pass
        
        result = runner.invoke(main, ["--repo", str(git_repo), "fetch-chats", "test-remote"])
        # Should exit with error (can't fetch from nonexistent remote)
        assert result.exit_code == 1