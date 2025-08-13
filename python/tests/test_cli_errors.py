"""Test cases for error handling in CLI."""

from tigs.cli import main


class TestErrorHandling:
    """Test error handling across CLI commands."""

    def test_not_git_repository(self, runner, tmp_path):
        """Test running commands in a non-Git directory."""
        non_git = tmp_path / "not_git"
        non_git.mkdir()

        # Test various commands
        commands = [
            ["list"],
            ["store", "content"],
            ["show", "some-id"],
            ["delete", "some-id"],
            ["sync", "--push"]
        ]

        for cmd in commands:
            result = runner.invoke(main, ["--repo", str(non_git)] + cmd)
            assert result.exit_code == 1
            assert "Not a Git repository" in result.output

    def test_invalid_repo_path(self, runner):
        """Test with a non-existent repository path."""
        result = runner.invoke(main, ["--repo", "/nonexistent/path", "list"])
        assert result.exit_code == 2  # Click's exit code for invalid path

