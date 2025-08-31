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
            ["list-chats"],
            ["add-chat", "-m", "content"],
            ["show-chat"],
            ["remove-chat"],
            ["push-chats"],
            ["fetch-chats"]
        ]

        for cmd in commands:
            result = runner.invoke(main, ["--repo", str(non_git)] + cmd)
            assert result.exit_code == 1
            assert "Not a Git repository" in result.output

    def test_invalid_repo_path(self, runner):
        """Test with a non-existent repository path."""
        result = runner.invoke(main, ["--repo", "/nonexistent/path", "list-chats"])
        assert result.exit_code == 2  # Click's exit code for invalid path

    def test_no_commits_in_repository(self, runner, tmp_path):
        """Test commands in a Git repo with no commits."""
        empty_repo = tmp_path / "empty_repo"
        empty_repo.mkdir()
        
        import subprocess
        subprocess.run(["git", "init"], cwd=empty_repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=empty_repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=empty_repo, check=True)

        # Try to add chat to HEAD (which doesn't exist)
        result = runner.invoke(main, ["--repo", str(empty_repo), "add-chat", "-m", "test"])
        assert result.exit_code == 1
        assert "No commits" in result.output or "Invalid commit" in result.output