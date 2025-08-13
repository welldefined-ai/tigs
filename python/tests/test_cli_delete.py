"""Test cases for delete-related CLI commands."""

from tigs.cli import main


class TestDelete:
    """Test the 'tig delete' command."""

    def test_delete_existing_object(self, runner, git_repo):
        """Test deleting an existing object."""
        # Store an object
        result = runner.invoke(main, ["--repo", str(git_repo), "store", "To be deleted"])
        object_id = result.output.strip()

        # Delete it
        result = runner.invoke(main, ["--repo", str(git_repo), "delete", object_id])
        assert result.exit_code == 0
        assert f"Deleted: {object_id}" in result.output

        # Verify it's gone
        result = runner.invoke(main, ["--repo", str(git_repo), "show", object_id])
        assert result.exit_code == 1
        assert "Object not found" in result.output

    def test_delete_nonexistent_object(self, runner, git_repo):
        """Test deleting a nonexistent object."""
        result = runner.invoke(main, ["--repo", str(git_repo), "delete", "nonexistent"])
        assert result.exit_code == 1
        assert "Object not found" in result.output

    def test_delete_from_list(self, runner, git_repo):
        """Test that deleted objects are removed from list."""
        # Store multiple objects
        ids = []
        for i in range(3):
            result = runner.invoke(main, ["--repo", str(git_repo), "store", f"Content {i}"])
            ids.append(result.output.strip())

        # Delete the middle one
        runner.invoke(main, ["--repo", str(git_repo), "delete", ids[1]])

        # Verify list only contains the other two
        result = runner.invoke(main, ["--repo", str(git_repo), "list"])
        listed_ids = result.output.strip().split("\n")

        assert ids[0] in listed_ids
        assert ids[1] not in listed_ids
        assert ids[2] in listed_ids

