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

