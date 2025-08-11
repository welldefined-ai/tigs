"""Test cases for sync-related CLI commands."""

from tig.cli import main


class TestSync:
    """Test the 'tig sync' command."""
    
    def test_sync_requires_flag(self, runner, git_repo):
        """Test that sync requires either --push or --pull flag."""
        result = runner.invoke(main, ["--repo", str(git_repo), "sync"])
        assert result.exit_code == 1
        assert "Specify --push or --pull" in result.output
    
    def test_sync_with_invalid_remote(self, runner, git_repo):
        """Test sync with a non-existent remote."""
        # This should fail because 'origin' doesn't exist in our test repo
        result = runner.invoke(main, ["--repo", str(git_repo), "sync", "--push", "nonexistent"])
        assert result.exit_code == 1
        assert "Error:" in result.output