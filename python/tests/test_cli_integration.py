"""Integration tests for CLI workflows."""

import subprocess

from tigs.cli import main


class TestIntegration:
    """Test complete workflows and integration scenarios."""

    def test_roundtrip_workflow(self, runner, git_repo):
        """Test a complete add-chat/show-chat/list-chats/remove-chat workflow."""
        content = "Integration test content"

        # Add chat
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", content])
        assert result.exit_code == 0
        commit_sha = result.output.split(":")[-1].strip()

        # List should contain it
        result = runner.invoke(main, ["--repo", str(git_repo), "list-chats"])
        assert commit_sha in result.output

        # Show should return exact content
        result = runner.invoke(main, ["--repo", str(git_repo), "show-chat"])
        assert result.output == content

        # Remove
        result = runner.invoke(main, ["--repo", str(git_repo), "remove-chat"])
        assert result.exit_code == 0

        # List should not contain it
        result = runner.invoke(main, ["--repo", str(git_repo), "list-chats"])
        assert commit_sha not in result.output or result.output.strip() == ""

    def test_git_notes_created(self, runner, git_repo):
        """Test that Git notes are created in the correct location."""
        # Add chat
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", "content"])
        assert result.exit_code == 0
        commit_sha = result.output.split(":")[-1].strip()

        # Verify note exists using git command
        result = subprocess.run(
            ["git", "notes", "--ref=refs/notes/chats", "show", commit_sha],
            cwd=git_repo,
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "content" in result.stdout

    def test_multiple_repos(self, runner, tmp_path):
        """Test working with multiple repositories."""
        # Create two repos
        repo1 = tmp_path / "repo1"
        repo2 = tmp_path / "repo2"

        for repo in [repo1, repo2]:
            repo.mkdir()
            subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            
            # Create initial commit (with unique content)
            (repo / "README.md").write_text(f"Test repository {repo.name}")
            subprocess.run(["git", "add", "README.md"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-m", f"Initial commit for {repo.name}"], cwd=repo, check=True, capture_output=True)

        # Add chat in repo1
        result = runner.invoke(main, ["--repo", str(repo1), "add-chat", "-m", "Repo 1 content"])
        assert result.exit_code == 0
        commit_sha1 = result.output.split(":")[-1].strip()

        # Add chat in repo2
        result = runner.invoke(main, ["--repo", str(repo2), "add-chat", "-m", "Repo 2 content"])
        assert result.exit_code == 0
        commit_sha2 = result.output.split(":")[-1].strip()

        # Verify isolation
        result = runner.invoke(main, ["--repo", str(repo1), "list-chats"])
        assert commit_sha1 in result.output
        assert commit_sha2 not in result.output

        result = runner.invoke(main, ["--repo", str(repo2), "list-chats"])
        assert commit_sha1 not in result.output
        assert commit_sha2 in result.output

    def test_git_ref_shortcuts(self, runner, git_repo):
        """Test that Git ref shortcuts work (HEAD~1, branch names, etc.)."""
        # Create a second commit
        (git_repo / "file2.txt").write_text("Second file")
        subprocess.run(["git", "add", "file2.txt"], cwd=git_repo, check=True)
        subprocess.run(["git", "commit", "-m", "Second commit"], cwd=git_repo, check=True, capture_output=True)

        # Add chat to HEAD~1 (first commit)
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "HEAD~1", "-m", "Chat for first commit"])
        assert result.exit_code == 0

        # Verify we can show it
        result = runner.invoke(main, ["--repo", str(git_repo), "show-chat", "HEAD~1"])
        assert result.exit_code == 0
        assert result.output == "Chat for first commit"