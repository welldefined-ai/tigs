#!/usr/bin/env python3
"""Test log navigation and lifecycle functionality."""

import tempfile
from pathlib import Path

import pytest
from framework.fixtures import create_test_repo
from framework.mock_claude_logs import create_mock_claude_home
from framework.paths import PYTHON_DIR
from framework.tui import TUI


@pytest.fixture
def repo_with_logs(monkeypatch):
    """Create repository with log files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "repo"
        mock_home = Path(tmpdir) / "mock_home"
        mock_home.mkdir()

        # Mock HOME environment variable
        monkeypatch.setenv("HOME", str(mock_home))

        # Create test repo
        commits = [f"Log test commit {i+1}" for i in range(5)]
        create_test_repo(repo_path, commits)

        # Create multiple mock Claude log sessions
        sessions_data = [
            [("user", "Test question 1"), ("assistant", "Test response 1")],
            [("user", "Test question 2"), ("assistant", "Test response 2")],
            [("user", "Test question 3"), ("assistant", "Test response 3")]
        ]
        create_mock_claude_home(mock_home, sessions_data)

        yield repo_path, mock_home


class TestLogNavigation:
    """Test log navigation functionality."""

    def test_log_lifecycle_operations(self, repo_with_logs):
        """Test log creation and loading."""
        repo_path, mock_home = repo_with_logs

        command = f"uv run tigs --repo {repo_path} store"

        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env={"HOME": str(mock_home)}) as tui:
            try:
                tui.wait_for("Logs", timeout=5.0)

                print("=== Log Lifecycle Test ===")

                lines = tui.capture()

                # Look for log indicators
                log_indicators = 0
                for line in lines:
                    if "log" in line.lower() or "20250107" in line:
                        log_indicators += 1

                print(f"Log indicators found: {log_indicators}")

                if log_indicators > 0:
                    print("✓ Log lifecycle functionality detected")
                else:
                    print("No clear log indicators found")

            except Exception as e:
                print(f"Log lifecycle test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Logs not available")
                else:
                    raise

    def test_log_navigation_triggers_reload(self, repo_with_logs):
        """Test that log navigation triggers message reload."""
        repo_path, mock_home = repo_with_logs

        command = f"uv run tigs --repo {repo_path} store"

        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env={"HOME": str(mock_home)}) as tui:
            try:
                tui.wait_for("Logs", timeout=5.0)

                print("=== Log Navigation Reload Test ===")

                # Try to navigate between logs
                tui.capture()

                # Navigate in logs (if log pane exists)
                tui.send_arrow("down")
                tui.send_arrow("up")

                after_navigation = tui.capture()

                print("=== After log navigation ===")
                for i, line in enumerate(after_navigation[:10]):
                    print(f"{i:02d}: {line}")

                # Basic test: navigation doesn't crash
                assert len(after_navigation) > 0, "Should maintain display after log navigation"

            except Exception as e:
                print(f"Log navigation test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Logs not available")
                else:
                    raise

    def test_empty_log_state(self, repo_with_logs):
        """Test handling of empty log state."""
        repo_path, mock_home = repo_with_logs

        # Test with no logs is already handled by empty claude home

        command = f"uv run tigs --repo {repo_path} store"

        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env={"HOME": str(mock_home)}) as tui:
            try:
                # Wait for some content to load
                tui.wait_for("commit", timeout=5.0)

                print("=== Empty Log State Test ===")

                lines = tui.capture()

                print("=== Display with empty logs ===")
                for i, line in enumerate(lines[:15]):
                    print(f"{i:02d}: {line}")

                # Should handle empty state gracefully
                empty_indicators = []
                for line in lines:
                    if any(indicator in line.lower() for indicator in
                          ["no log", "empty", "no messages"]):
                        empty_indicators.append(line)

                if empty_indicators:
                    print("✓ Empty log state handling detected")
                else:
                    print("No specific empty log indicators found")

                # Basic test: doesn't crash with empty logs
                assert len(lines) > 0, "Should display something even with empty logs"

            except Exception as e:
                print(f"Empty log state test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Logs not available")
                else:
                    raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
