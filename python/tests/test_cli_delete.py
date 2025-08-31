"""Test cases for remove-chat CLI command."""

from tigs.cli import main


class TestRemoveChat:
    """Test the 'tigs remove-chat' command."""

    def test_remove_chat_existing(self, runner, git_repo):
        """Test removing an existing chat."""
        # Add a chat
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", "To be deleted"])
        assert result.exit_code == 0
        commit_sha = result.output.split(":")[-1].strip()

        # Remove it
        result = runner.invoke(main, ["--repo", str(git_repo), "remove-chat"])
        assert result.exit_code == 0
        assert f"Removed chat from commit: HEAD" in result.output

        # Verify it's gone
        result = runner.invoke(main, ["--repo", str(git_repo), "show-chat"])
        assert result.exit_code == 1
        assert "No chat found" in result.output

    def test_remove_chat_specific_commit(self, runner, git_repo):
        """Test removing chat from specific commit."""
        # Add a chat
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", "To be deleted"])
        assert result.exit_code == 0
        commit_sha = result.output.split(":")[-1].strip()

        # Remove it by specific commit SHA
        result = runner.invoke(main, ["--repo", str(git_repo), "remove-chat", commit_sha])
        assert result.exit_code == 0
        assert f"Removed chat from commit: {commit_sha}" in result.output

    def test_remove_chat_nonexistent(self, runner, git_repo):
        """Test removing a nonexistent chat."""
        result = runner.invoke(main, ["--repo", str(git_repo), "remove-chat"])
        assert result.exit_code == 1
        assert "No chat found" in result.output

    def test_remove_chat_invalid_commit(self, runner, git_repo):
        """Test removing chat from invalid commit."""
        result = runner.invoke(main, ["--repo", str(git_repo), "remove-chat", "invalid-commit"])
        assert result.exit_code == 1
        assert "Invalid commit" in result.output

    def test_remove_chat_from_list(self, runner, git_repo):
        """Test that removed chats disappear from list."""
        import subprocess
        
        # Add first chat
        result1 = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", "First chat"])
        assert result1.exit_code == 0
        commit_sha1 = result1.output.split(":")[-1].strip()

        # Create another commit
        (git_repo / "file2.txt").write_text("Second file")
        subprocess.run(["git", "add", "file2.txt"], cwd=git_repo, check=True)
        subprocess.run(["git", "commit", "-m", "Second commit"], cwd=git_repo, check=True, capture_output=True)

        # Add second chat
        result2 = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", "Second chat"])
        assert result2.exit_code == 0
        commit_sha2 = result2.output.split(":")[-1].strip()

        # Remove the second chat
        result = runner.invoke(main, ["--repo", str(git_repo), "remove-chat"])
        assert result.exit_code == 0

        # Verify list only contains the first chat
        result = runner.invoke(main, ["--repo", str(git_repo), "list-chats"])
        listed_shas = result.output.strip().split("\n") if result.output.strip() else []

        assert commit_sha1 in listed_shas
        assert commit_sha2 not in listed_shas
        assert len(listed_shas) == 1