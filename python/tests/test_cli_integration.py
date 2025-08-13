"""Integration tests for CLI workflows."""

import subprocess

from tigs.cli import main


class TestIntegration:
    """Test complete workflows and integration scenarios."""

    def test_roundtrip_workflow(self, runner, git_repo):
        """Test a complete store-list-show-delete workflow."""
        content = "Integration test content"

        # Store
        result = runner.invoke(main, ["--repo", str(git_repo), "store", content, "--id", "test-1"])
        assert result.exit_code == 0

        # List should contain it
        result = runner.invoke(main, ["--repo", str(git_repo), "list"])
        assert "test-1" in result.output

        # Show should return exact content
        result = runner.invoke(main, ["--repo", str(git_repo), "show", "test-1"])
        assert result.output == content

        # Delete
        result = runner.invoke(main, ["--repo", str(git_repo), "delete", "test-1"])
        assert result.exit_code == 0

        # List should not contain it
        result = runner.invoke(main, ["--repo", str(git_repo), "list"])
        assert "test-1" not in result.output

    def test_git_refs_created(self, runner, git_repo):
        """Test that Git refs are created in the correct location."""
        # Store with known ID
        runner.invoke(main, ["--repo", str(git_repo), "store", "content", "--id", "check-ref"])

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
        result = runner.invoke(main, ["--repo", str(repo1), "store", "Repo 1 content", "--id", "obj1"])
        assert result.exit_code == 0

        # Store in repo2
        result = runner.invoke(main, ["--repo", str(repo2), "store", "Repo 2 content", "--id", "obj2"])
        assert result.exit_code == 0

        # Verify isolation
        result = runner.invoke(main, ["--repo", str(repo1), "list"])
        assert "obj1" in result.output
        assert "obj2" not in result.output

        result = runner.invoke(main, ["--repo", str(repo2), "list"])
        assert "obj1" not in result.output
        assert "obj2" in result.output

