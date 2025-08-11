"""Test cases for store-related CLI commands."""

from tig.cli import main


class TestStore:
    """Test the 'tig store' command."""
    
    def test_store_basic(self, runner, git_repo):
        """Test basic content storage."""
        result = runner.invoke(main, ["--repo", str(git_repo), "store", "Hello, World!"])
        assert result.exit_code == 0
        assert len(result.output.strip()) > 0  # Should return an object ID
    
    def test_store_with_custom_id(self, runner, git_repo):
        """Test storing with a custom ID."""
        result = runner.invoke(main, ["--repo", str(git_repo), "store", "Content", "--id", "my-id"])
        assert result.exit_code == 0
        assert result.output.strip() == "my-id"
    
    def test_store_empty_content(self, runner, git_repo):
        """Test storing empty content."""
        result = runner.invoke(main, ["--repo", str(git_repo), "store", ""])
        assert result.exit_code == 0
        assert len(result.output.strip()) > 0
    
    def test_store_multiline_content(self, runner, git_repo):
        """Test storing multiline content."""
        content = "Line 1\nLine 2\nLine 3"
        result = runner.invoke(main, ["--repo", str(git_repo), "store", content])
        assert result.exit_code == 0
        assert len(result.output.strip()) > 0
    
    def test_store_unicode_content(self, runner, git_repo):
        """Test storing Unicode content."""
        content = "Hello 世界! 🌍"
        result = runner.invoke(main, ["--repo", str(git_repo), "store", content])
        assert result.exit_code == 0
        assert len(result.output.strip()) > 0