"""Integration tests for CLI workflows."""

import subprocess

from tigs.cli import main


class TestIntegration:
    """Test complete workflows and integration scenarios."""

    def test_roundtrip_workflow(self, runner, git_repo):
        """Test a complete hash-chat/ls-chats/cat-chat/rm-chat workflow."""
        content = "Integration test content"

        # Store
        result = runner.invoke(main, ["--repo", str(git_repo), "hash-chat", content, "--id", "test-1"])
        assert result.exit_code == 0

        # List should contain it
        result = runner.invoke(main, ["--repo", str(git_repo), "ls-chats"])
        assert "test-1" in result.output

        # Display should return exact content
        result = runner.invoke(main, ["--repo", str(git_repo), "cat-chat", "test-1"])
        assert result.output == content

        # Remove
        result = runner.invoke(main, ["--repo", str(git_repo), "rm-chat", "test-1"])
        assert result.exit_code == 0

        # List should not contain it
        result = runner.invoke(main, ["--repo", str(git_repo), "ls-chats"])
        assert "test-1" not in result.output

    def test_git_refs_created(self, runner, git_repo):
        """Test that Git refs are created in the correct location."""
        # Store with known ID
        runner.invoke(main, ["--repo", str(git_repo), "hash-chat", "content", "--id", "check-ref"])

        # Verify ref exists using git command
        result = subprocess.run(
            ["git", "show-ref", "refs/tigs/chats/check-ref"],
            cwd=git_repo,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "refs/tigs/chats/check-ref" in result.stdout

    def test_multiple_repos(self, runner, tmp_path):
        """Test working with multiple repositories."""
        # Create two repos
        repo1 = tmp_path / "repo1"
        repo2 = tmp_path / "repo2"

        for repo in [repo1, repo2]:
            repo.mkdir()
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)

        # Store in repo1
        result = runner.invoke(main, ["--repo", str(repo1), "hash-chat", "Repo 1 content", "--id", "obj1"])
        assert result.exit_code == 0

        # Store in repo2
        result = runner.invoke(main, ["--repo", str(repo2), "hash-chat", "Repo 2 content", "--id", "obj2"])
        assert result.exit_code == 0

        # Verify isolation
        result = runner.invoke(main, ["--repo", str(repo1), "ls-chats"])
        assert "obj1" in result.output
        assert "obj2" not in result.output

        result = runner.invoke(main, ["--repo", str(repo2), "ls-chats"])
        assert "obj1" not in result.output
        assert "obj2" in result.output

