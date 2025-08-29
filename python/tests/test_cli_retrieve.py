"""Test cases for cat-chat and ls-chats CLI commands."""

from tigs.cli import main


class TestCatChat:
    """Test the 'tigs cat-chat' command."""

    def test_cat_chat_existing(self, runner, git_repo):
        """Test displaying an existing chat."""
        # First store something
        result = runner.invoke(main, ["--repo", str(git_repo), "hash-chat", "Test content"])
        object_id = result.output.strip()

        # Then display it
        result = runner.invoke(main, ["--repo", str(git_repo), "cat-chat", object_id])
        assert result.exit_code == 0
        assert result.output == "Test content"

    def test_cat_chat_nonexistent(self, runner, git_repo):
        """Test displaying a nonexistent chat."""
        result = runner.invoke(main, ["--repo", str(git_repo), "cat-chat", "nonexistent"])
        assert result.exit_code == 1
        assert "Chat not found" in result.output

    def test_cat_chat_preserves_content_exactly(self, runner, git_repo):
        """Test that content is preserved exactly as stored."""
        # Test with trailing newline
        content = "Content with trailing newline\n"
        result = runner.invoke(main, ["--repo", str(git_repo), "hash-chat", content])
        object_id = result.output.strip()

        result = runner.invoke(main, ["--repo", str(git_repo), "cat-chat", object_id])
        assert result.exit_code == 0
        assert result.output == content


class TestLsChats:
    """Test the 'tigs ls-chats' command."""

    def test_ls_chats_empty(self, runner, git_repo):
        """Test listing when no chats exist."""
        result = runner.invoke(main, ["--repo", str(git_repo), "ls-chats"])
        assert result.exit_code == 0
        assert result.output.strip() == ""

    def test_ls_chats_multiple(self, runner, git_repo):
        """Test listing multiple chats."""
        # Store several chats
        ids = []
        for i in range(3):
            result = runner.invoke(main, ["--repo", str(git_repo), "hash-chat", f"Content {i}"])
            ids.append(result.output.strip())

        # List them
        result = runner.invoke(main, ["--repo", str(git_repo), "ls-chats"])
        assert result.exit_code == 0

        listed_ids = result.output.strip().split("\n")
        assert len(listed_ids) == 3
        for obj_id in ids:
            assert obj_id in listed_ids

    def test_ls_chats_with_custom_ids(self, runner, git_repo):
        """Test listing chats with custom IDs."""
        # Store with custom IDs
        custom_ids = ["first", "second", "third"]
        for custom_id in custom_ids:
            runner.invoke(main, ["--repo", str(git_repo), "hash-chat", "content", "--id", custom_id])

        # List and verify
        result = runner.invoke(main, ["--repo", str(git_repo), "ls-chats"])
        assert result.exit_code == 0

        listed_ids = result.output.strip().split("\n")
        for custom_id in custom_ids:
            assert custom_id in listed_ids

