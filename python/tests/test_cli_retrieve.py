"""Test cases for show-chat and list-chats CLI commands."""

from tigs.cli import main


class TestShowChat:
    """Test the 'tigs show-chat' command."""

    def test_show_chat_existing(self, runner, git_repo):
        """Test displaying an existing chat."""
        # First add a chat
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", "Test content"])
        assert result.exit_code == 0

        # Then show it
        result = runner.invoke(main, ["--repo", str(git_repo), "show-chat"])
        assert result.exit_code == 0
        assert result.output == "Test content"

    def test_show_chat_specific_commit(self, runner, git_repo):
        """Test displaying chat for specific commit."""
        # Add chat to HEAD
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", "HEAD chat"])
        assert result.exit_code == 0
        
        # Get commit SHA from output
        commit_sha = result.output.split(":")[-1].strip()
        
        # Show chat for specific commit
        result = runner.invoke(main, ["--repo", str(git_repo), "show-chat", commit_sha])
        assert result.exit_code == 0
        assert result.output == "HEAD chat"

    def test_show_chat_nonexistent(self, runner, git_repo):
        """Test displaying a nonexistent chat."""
        result = runner.invoke(main, ["--repo", str(git_repo), "show-chat"])
        assert result.exit_code == 1
        assert "No chat found" in result.output

    def test_show_chat_invalid_commit(self, runner, git_repo):
        """Test showing chat for invalid commit."""
        result = runner.invoke(main, ["--repo", str(git_repo), "show-chat", "invalid-commit"])
        assert result.exit_code == 1
        assert "Invalid commit" in result.output

    def test_show_chat_preserves_content_exactly(self, runner, git_repo):
        """Test that content is preserved (note: git notes add -m strips trailing newlines)."""
        # Test content without trailing newline (git notes will show what we expect)
        content = "Content without trailing newline"
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", content])
        assert result.exit_code == 0

        result = runner.invoke(main, ["--repo", str(git_repo), "show-chat"])
        assert result.exit_code == 0
        assert result.output == content


class TestListChats:
    """Test the 'tigs list-chats' command."""

    def test_list_chats_empty(self, runner, git_repo):
        """Test listing when no chats exist."""
        result = runner.invoke(main, ["--repo", str(git_repo), "list-chats"])
        assert result.exit_code == 0
        assert result.output.strip() == ""

    def test_list_chats_single(self, runner, git_repo):
        """Test listing single chat."""
        # Add a chat
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", "Single chat"])
        assert result.exit_code == 0
        commit_sha = result.output.split(":")[-1].strip()

        # List chats
        result = runner.invoke(main, ["--repo", str(git_repo), "list-chats"])
        assert result.exit_code == 0
        assert commit_sha in result.output

    def test_list_chats_multiple(self, runner, git_repo):
        """Test listing multiple chats."""
        # Add first chat
        result1 = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", "First chat"])
        assert result1.exit_code == 0
        commit_sha1 = result1.output.split(":")[-1].strip()

        # Create another commit
        import subprocess
        (git_repo / "file2.txt").write_text("Second file")
        subprocess.run(["git", "add", "file2.txt"], cwd=git_repo, check=True)
        subprocess.run(["git", "commit", "-m", "Second commit"], cwd=git_repo, check=True, capture_output=True)

        # Add second chat
        result2 = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", "Second chat"])
        assert result2.exit_code == 0
        commit_sha2 = result2.output.split(":")[-1].strip()

        # List chats - should show both
        result = runner.invoke(main, ["--repo", str(git_repo), "list-chats"])
        assert result.exit_code == 0
        
        listed_shas = result.output.strip().split("\n")
        assert commit_sha1 in listed_shas
        assert commit_sha2 in listed_shas
        assert len(listed_shas) == 2