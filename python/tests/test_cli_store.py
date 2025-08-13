"""Test cases for store-related CLI commands."""

from tigs.cli import main


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

    def test_store_generates_hash_id(self, runner, git_repo):
        """Test that store generates hash-based IDs."""
        content = "Test content for hashing"
        result = runner.invoke(main, ["--repo", str(git_repo), "store", content])
        assert result.exit_code == 0

        object_id = result.output.strip()
        # Should be a 40-character hex string (SHA-1)
        assert len(object_id) == 40
        assert all(c in '0123456789abcdef' for c in object_id)

    def test_store_same_content_same_id(self, runner, git_repo):
        """Test that identical content produces the same ID (deduplication)."""
        content = "Duplicate content test"

        # Store the same content twice
        result1 = runner.invoke(main, ["--repo", str(git_repo), "store", content])
        result2 = runner.invoke(main, ["--repo", str(git_repo), "store", content])

        assert result1.exit_code == 0
        assert result2.exit_code == 0

        id1 = result1.output.strip()
        id2 = result2.output.strip()

        # Should be the same ID
        assert id1 == id2

        # List should only show one object (deduplication)
        result = runner.invoke(main, ["--repo", str(git_repo), "list"])
        listed_ids = result.output.strip().split("\n") if result.output.strip() else []
        assert listed_ids.count(id1) == 1

    def test_store_predictable_hash(self, runner, git_repo):
        """Test that hash generation is predictable."""
        import hashlib

        content = "Predictable hash test"
        expected_hash = hashlib.sha1(content.encode('utf-8')).hexdigest()

        result = runner.invoke(main, ["--repo", str(git_repo), "store", content])
        assert result.exit_code == 0

        actual_id = result.output.strip()
        assert actual_id == expected_hash

