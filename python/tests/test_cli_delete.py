"""Test cases for rm-chat CLI command."""

from tigs.cli import main


class TestRmChat:
    """Test the 'tigs rm-chat' command."""

    def test_rm_chat_existing(self, runner, git_repo):
        """Test removing an existing chat."""
        # Store a chat
        result = runner.invoke(main, ["--repo", str(git_repo), "hash-chat", "To be deleted"])
        object_id = result.output.strip()

        # Remove it
        result = runner.invoke(main, ["--repo", str(git_repo), "rm-chat", object_id])
        assert result.exit_code == 0
        assert f"Deleted: {object_id}" in result.output

        # Verify it's gone
        result = runner.invoke(main, ["--repo", str(git_repo), "cat-chat", object_id])
        assert result.exit_code == 1
        assert "Chat not found" in result.output

    def test_rm_chat_nonexistent(self, runner, git_repo):
        """Test removing a nonexistent chat."""
        result = runner.invoke(main, ["--repo", str(git_repo), "rm-chat", "nonexistent"])
        assert result.exit_code == 1
        assert "Chat not found" in result.output

    def test_rm_chat_from_list(self, runner, git_repo):
        """Test that removed chats disappear from list."""
        # Store multiple chats
        ids = []
        for i in range(3):
            result = runner.invoke(main, ["--repo", str(git_repo), "hash-chat", f"Content {i}"])
            ids.append(result.output.strip())

        # Remove the middle one
        runner.invoke(main, ["--repo", str(git_repo), "rm-chat", ids[1]])

        # Verify list only contains the other two
        result = runner.invoke(main, ["--repo", str(git_repo), "ls-chats"])
        listed_ids = result.output.strip().split("\n")

        assert ids[0] in listed_ids
        assert ids[1] not in listed_ids
        assert ids[2] in listed_ids

