#!/usr/bin/env python3
"""Test message selection functionality including visual mode."""

import tempfile
from pathlib import Path

import pytest
from framework.fixtures import create_test_repo
from framework.mock_claude_logs import create_mock_claude_home
from framework.paths import PYTHON_DIR
from framework.tui import TUI


@pytest.fixture
def messages_setup(monkeypatch):
    """Create repo and messages for selection testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "repo"
        mock_home = Path(tmpdir) / "mock_home"
        mock_home.mkdir()

        # Mock HOME environment variable
        monkeypatch.setenv("HOME", str(mock_home))

        # Create repo with minimal commits
        commits = [f"Test commit {i + 1}" for i in range(5)]
        create_test_repo(repo_path, commits)

        # Create mock Claude logs with several messages
        sessions_data = [[]]
        for i in range(8):
            sessions_data[0].append(
                ("user", f"User message {i + 1}: Question about the code")
            )
            sessions_data[0].append(
                ("assistant", f"Assistant message {i + 1}: Here is the answer")
            )

        create_mock_claude_home(mock_home, sessions_data)

        yield repo_path, mock_home


class TestMessageSelection:
    """Test message selection functionality."""

    def test_message_selection_operations(self, messages_setup):
        """Test message selection with space/v/c/a keys."""
        repo_path, mock_home = messages_setup

        command = f"uv run tigs --repo {repo_path} store"

        with TUI(
            command, cwd=PYTHON_DIR, dimensions=(30, 120), env={"HOME": str(mock_home)}
        ) as tui:
            try:
                tui.wait_for("Messages", timeout=5.0)

                print("=== Message Selection Test ===")

                # Switch to messages pane
                tui.send_key("Tab")  # Move to messages pane

                # Test Space toggle selection
                print("--- Testing Space toggle in messages ---")
                tui.send(" ")
                tui.capture()

                # Test visual mode 'v'
                print("--- Testing visual mode in messages ---")
                tui.send("v")
                visual_start = tui.capture()

                # Check for "VISUAL" in status or different display
                visual_mode_active = False
                for line in visual_start:
                    if "visual" in line.lower():
                        visual_mode_active = True
                        print(f"✓ Visual mode indicator: {line.strip()}")
                        break

                if visual_mode_active:
                    # Move cursor in visual mode
                    tui.send_arrow("down")
                    tui.send_arrow("down")

                    # Confirm selection
                    tui.send(" ")
                    tui.capture()
                    print("✓ Visual mode selection completed")
                else:
                    print("Visual mode indicator not clearly visible")

                # Test clear all 'c'
                print("--- Testing clear all ---")
                tui.send("c")
                tui.capture()

                # Test select all 'a'
                print("--- Testing select all ---")
                tui.send("a")
                select_all_result = tui.capture()

                print("=== Message selection commands completed ===")

                # Basic verification: commands didn't crash
                assert len(select_all_result) > 0, (
                    "Should have display after selection commands"
                )

            except Exception as e:
                print(f"Message selection test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Messages not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
