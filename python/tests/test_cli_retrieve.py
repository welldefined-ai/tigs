"""Test cases for retrieve-related CLI commands."""

from tig.cli import main


class TestShow:
    """Test the 'tig show' command."""
    
    def test_show_existing_object(self, runner, git_repo):
        """Test showing an existing object."""
        # First store something
        result = runner.invoke(main, ["--repo", str(git_repo), "store", "Test content"])
        object_id = result.output.strip()
        
        # Then show it
        result = runner.invoke(main, ["--repo", str(git_repo), "show", object_id])
        assert result.exit_code == 0
        assert result.output == "Test content"
    
    def test_show_nonexistent_object(self, runner, git_repo):
        """Test showing a nonexistent object."""
        result = runner.invoke(main, ["--repo", str(git_repo), "show", "nonexistent"])
        assert result.exit_code == 1
        assert "Object not found" in result.output
    
    def test_show_preserves_content_exactly(self, runner, git_repo):
        """Test that content is preserved exactly as stored."""
        # Test with trailing newline
        content = "Content with trailing newline\n"
        result = runner.invoke(main, ["--repo", str(git_repo), "store", content])
        object_id = result.output.strip()
        
        result = runner.invoke(main, ["--repo", str(git_repo), "show", object_id])
        assert result.exit_code == 0
        assert result.output == content


class TestList:
    """Test the 'tig list' command."""
    
    def test_list_empty(self, runner, git_repo):
        """Test listing when no objects exist."""
        result = runner.invoke(main, ["--repo", str(git_repo), "list"])
        assert result.exit_code == 0
        assert result.output.strip() == ""
    
    def test_list_multiple_objects(self, runner, git_repo):
        """Test listing multiple objects."""
        # Store several objects
        ids = []
        for i in range(3):
            result = runner.invoke(main, ["--repo", str(git_repo), "store", f"Content {i}"])
            ids.append(result.output.strip())
        
        # List them
        result = runner.invoke(main, ["--repo", str(git_repo), "list"])
        assert result.exit_code == 0
        
        listed_ids = result.output.strip().split("\n")
        assert len(listed_ids) == 3
        for obj_id in ids:
            assert obj_id in listed_ids
    
    def test_list_with_custom_ids(self, runner, git_repo):
        """Test listing objects with custom IDs."""
        # Store with custom IDs
        custom_ids = ["first", "second", "third"]
        for custom_id in custom_ids:
            runner.invoke(main, ["--repo", str(git_repo), "store", "content", "--id", custom_id])
        
        # List and verify
        result = runner.invoke(main, ["--repo", str(git_repo), "list"])
        assert result.exit_code == 0
        
        listed_ids = result.output.strip().split("\n")
        for custom_id in custom_ids:
            assert custom_id in listed_ids