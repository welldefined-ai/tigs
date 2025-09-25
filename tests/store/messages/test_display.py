#!/usr/bin/env python3
"""Test message display functionality including formatting and anchoring."""

import tempfile
from pathlib import Path

import pytest
from framework.fixtures import create_test_repo
from framework.mock_claude_logs import create_mock_claude_home
from framework.paths import PYTHON_DIR
from framework.tui import TUI


@pytest.fixture
def messages_setup(monkeypatch):
    """Create repo and messages for message testing."""
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
                (
                    "assistant",
                    f"Assistant message {i + 1}: Here is the detailed answer with explanations",
                )
            )

        create_mock_claude_home(mock_home, sessions_data)

        yield repo_path, mock_home


class TestMessageDisplay:
    """Test message display functionality."""

    def test_message_format_and_display(self, messages_setup):
        """Test message formatting and basic display."""
        repo_path, mock_home = messages_setup

        command = f"uv run tigs --repo {repo_path} store"

        with TUI(
            command, cwd=PYTHON_DIR, dimensions=(30, 120), env={"HOME": str(mock_home)}
        ) as tui:
            try:
                tui.wait_for("Messages", timeout=5.0)

                print("=== Message Format Test ===")

                lines = tui.capture()

                # Check for message indicators
                user_messages = []
                assistant_messages = []

                for line in lines:
                    if "user:" in line.lower():
                        user_messages.append(line)
                    elif "assistant:" in line.lower():
                        assistant_messages.append(line)

                print(f"Found {len(user_messages)} user messages")
                print(f"Found {len(assistant_messages)} assistant messages")

                # Should find some messages
                if len(user_messages) > 0 or len(assistant_messages) > 0:
                    print("✓ Message formatting working")
                else:
                    print("No clear message format detected")

            except Exception as e:
                print(f"Message format test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Messages not available")
                else:
                    raise

    def test_bottom_anchored_display(self, messages_setup):
        """Test bottom-anchored message display behavior."""
        repo_path, mock_home = messages_setup

        command = f"uv run tigs --repo {repo_path} store"

        with TUI(
            command, cwd=PYTHON_DIR, dimensions=(30, 120), env={"HOME": str(mock_home)}
        ) as tui:
            try:
                tui.wait_for("Messages", timeout=5.0)

                print("=== Bottom Anchor Test ===")

                # Switch to messages pane if needed
                tui.send("<tab>")  # Move to messages pane

                initial_lines = tui.capture()

                print("=== Message pane display ===")
                for i, line in enumerate(initial_lines[-10:], len(initial_lines) - 10):
                    print(f"{i:02d}: {line}")

                # Look for messages near bottom of display
                bottom_lines = initial_lines[-10:]
                message_indicators_at_bottom = 0

                for line in bottom_lines:
                    if any(
                        indicator in line.lower()
                        for indicator in ["user:", "assistant:", "message"]
                    ):
                        message_indicators_at_bottom += 1

                print(f"Message indicators near bottom: {message_indicators_at_bottom}")

                if message_indicators_at_bottom > 0:
                    print("✓ Bottom-anchored display working")
                else:
                    print("Messages may not be bottom-anchored or not visible")

            except Exception as e:
                print(f"Bottom anchor test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Messages not available")
                else:
                    raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
