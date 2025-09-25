#!/usr/bin/env python3
"""Test CLI error handling - language-agnostic scenarios."""

import subprocess
import tempfile
from pathlib import Path

import pytest
from framework.fixtures import create_test_repo


def run_tigs(repo_path, *args):
    """Run tigs command and return result."""
    cmd = ["uv", "run", "tigs", "--repo", str(repo_path)] + list(args)
    result = subprocess.run(
        cmd,
        cwd="/Users/basicthinker/Projects/tigs/python",
        capture_output=True,
        text=True,
    )
    return result


class TestCLIErrors:
    """Test CLI error handling across all commands."""

    def test_not_git_repository(self):
        """Test running commands in a non-Git directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            non_git = Path(tmpdir) / "not_git"
            non_git.mkdir()

            # Test various commands should all fail gracefully
            commands = [
                ["list-chats"],
                ["add-chat", "-m", "test content"],
                ["show-chat"],
                ["remove-chat"],
                ["push-chats", "origin"],
                ["fetch-chats", "origin"],
            ]

            for cmd in commands:
                result = run_tigs(non_git, *cmd)
                print(f"Command {cmd}: exit_code={result.returncode}")
                print(f"Stdout: {result.stdout}")
                print(f"Stderr: {result.stderr}")

                # Should fail with appropriate error
                assert result.returncode != 0
                error_output = result.stdout + result.stderr
                assert any(
                    indicator in error_output.lower()
                    for indicator in [
                        "not a git repository",
                        "not git repository",
                        "git repo",
                        "invalid repo",
                    ]
                )

    def test_invalid_repo_path(self):
        """Test with a non-existent repository path."""
        result = run_tigs("/nonexistent/path", "list-chats")
        print(
            f"Invalid path result: {result.returncode}, {result.stdout}, {result.stderr}"
        )

        # Should fail - path doesn't exist
        assert result.returncode != 0

    def test_empty_repository(self):
        """Test commands in a Git repo with no commits."""
        with tempfile.TemporaryDirectory() as tmpdir:
            empty_repo = Path(tmpdir) / "empty_repo"
            empty_repo.mkdir()

            # Initialize empty Git repo
            subprocess.run(
                ["git", "init"], cwd=empty_repo, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "config", "user.name", "Test User"], cwd=empty_repo, check=True
            )
            subprocess.run(
                ["git", "config", "user.email", "test@example.com"],
                cwd=empty_repo,
                check=True,
            )

            # Try to add chat to HEAD (which doesn't exist)
            result = run_tigs(empty_repo, "add-chat", "-m", "test")
            print(
                f"Empty repo add-chat: {result.returncode}, {result.stdout}, {result.stderr}"
            )

            # Should fail gracefully
            assert result.returncode != 0
            error_output = result.stdout + result.stderr
            assert any(
                indicator in error_output.lower()
                for indicator in ["no commit", "invalid commit", "no head", "empty"]
            )

    def test_invalid_commit_sha(self):
        """Test commands with invalid commit SHA."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test_repo"
            create_test_repo(repo_path, ["Test commit"])

            # Try to use invalid SHA
            result = run_tigs(repo_path, "add-chat", "invalid-sha-123", "-m", "test")
            print(f"Invalid SHA: {result.returncode}, {result.stdout}, {result.stderr}")

            # Should fail gracefully
            assert result.returncode != 0
            error_output = result.stdout + result.stderr
            assert any(
                indicator in error_output.lower()
                for indicator in ["invalid commit", "not found", "bad commit"]
            )

    def test_sync_without_remote(self):
        """Test push/fetch commands without configured remote."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test_repo"
            create_test_repo(repo_path, ["Test commit"])

            # Test push without remote
            result = run_tigs(repo_path, "push-chats", "nonexistent")
            print(
                f"Push without remote: {result.returncode}, {result.stdout}, {result.stderr}"
            )

            # Should fail gracefully
            assert result.returncode != 0
            error_output = result.stdout + result.stderr
            assert any(
                indicator in error_output.lower()
                for indicator in ["remote", "not found", "error", "does not exist"]
            )

            # Test fetch without remote
            result = run_tigs(repo_path, "fetch-chats", "nonexistent")
            print(
                f"Fetch without remote: {result.returncode}, {result.stdout}, {result.stderr}"
            )

            # Should fail gracefully
            assert result.returncode != 0

    def test_malformed_yaml_content(self):
        """Test adding malformed YAML content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test_repo"
            create_test_repo(repo_path, ["Test commit"])

            # Try to add malformed YAML
            malformed = "invalid: yaml: content: [unclosed"
            result = run_tigs(repo_path, "add-chat", "-m", malformed)
            print(
                f"Malformed YAML: {result.returncode}, {result.stdout}, {result.stderr}"
            )

            # Behavior depends on implementation - might succeed (store as-is) or fail
            # Just verify it doesn't crash
            assert result.returncode in [0, 1]  # Either succeeds or fails gracefully

    def test_permission_errors(self):
        """Test handling of permission-related errors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "test_repo"
            create_test_repo(repo_path, ["Test commit"])

            # Make .git directory read-only (if possible)
            git_dir = repo_path / ".git"
            try:
                import os

                os.chmod(git_dir, 0o444)  # Read-only

                result = run_tigs(repo_path, "add-chat", "-m", "test content")
                print(
                    f"Permission error: {result.returncode}, {result.stdout}, {result.stderr}"
                )

                # Should fail gracefully, not crash
                assert result.returncode != 0

                # Restore permissions
                os.chmod(git_dir, 0o755)

            except (OSError, PermissionError):
                # Skip if we can't modify permissions
                pytest.skip("Cannot modify directory permissions on this system")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
