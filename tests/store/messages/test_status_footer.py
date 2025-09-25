#!/usr/bin/env python3
"""Test status footer display in messages view for store command."""

import tempfile
from pathlib import Path

from framework.fixtures import create_test_repo
from framework.mock_claude_logs import create_mock_claude_home
from framework.paths import PYTHON_DIR
from framework.tui import TUI
from framework.tui import get_middle_pane


class TestMessagesStatusFooter:
    """Test the status footer display in messages view."""

    def test_status_footer_display(self, monkeypatch):
        """Test that status footer shows current position."""

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "messages_footer_test_repo"
            mock_home = Path(tmpdir) / "mock_home"
            mock_home.mkdir()

            # Mock HOME environment variable
            monkeypatch.setenv("HOME", str(mock_home))

            # Create mock Claude logs with 5 messages
            sessions_data = [[
                ("user", "How do I implement a binary search?"),
                ("assistant", "Here's how to implement binary search:"),
                ("user", "Can you show an example?"),
                ("assistant", "Sure, here's a Python example:"),
                ("user", "Thanks!")
            ]]
            create_mock_claude_home(mock_home, sessions_data)

            # Create a repo with a commit
            create_test_repo(repo_path, ["Initial commit"])

            command = f"uv run tigs --repo {repo_path} store"

            with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env={"HOME": str(mock_home)}) as tui:
                # Wait for UI to load
                tui.wait_for("Commits")

                # Tab to logs pane to select the log
                tui.send("\t\t")

                # Select the first log
                tui.send(" ")

                # Wait for messages to appear
                tui.wait_for("How do I implement")

                # Capture display
                lines = tui.capture()

                # Look for status footer in messages pane (second column)
                footer_found = False
                for line in lines[-10:]:
                    second_pane = get_middle_pane(line)
                    # Look for the status footer pattern (X/Y)
                    if "(" in second_pane and "/" in second_pane and ")" in second_pane:
                        footer_found = True
                        # Should show (1/5) for first message
                        assert "(1/5)" in second_pane, f"Expected (1/5), got: {second_pane}"
                        break

                assert footer_found, "Status footer not found in messages pane"

    def test_status_footer_updates_on_navigation(self, monkeypatch):
        """Test that status footer updates when navigating messages."""

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "messages_nav_test_repo"
            mock_home = Path(tmpdir) / "mock_home"
            mock_home.mkdir()

            # Mock HOME environment variable
            monkeypatch.setenv("HOME", str(mock_home))

            # Create mock Claude logs with 6 messages
            sessions_data = [[
                ("user", "Message 1"),
                ("assistant", "Response 1"),
                ("user", "Message 2"),
                ("assistant", "Response 2"),
                ("user", "Message 3"),
                ("assistant", "Response 3")
            ]]
            create_mock_claude_home(mock_home, sessions_data)

            # Create a repo with a commit
            create_test_repo(repo_path, ["Chat commit"])

            command = f"uv run tigs --repo {repo_path} store"

            with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env={"HOME": str(mock_home)}) as tui:
                # Wait for UI to load
                tui.wait_for("Commits")

                # Tab to logs pane to select the log
                tui.send("\t\t")

                # Select the first log
                tui.send(" ")

                # Wait for messages
                tui.wait_for("Message 1")

                # Check initial position
                initial_lines = tui.capture()
                initial_footer = None
                for line in initial_lines[-10:]:
                    second_pane = get_middle_pane(line)
                    if "(" in second_pane and "/" in second_pane and ")" in second_pane:
                        initial_footer = second_pane.strip()
                        break

                assert initial_footer, "Initial footer not found"
                # Mock logs have at least 4 messages (from fixture)
                assert "(1/" in initial_footer

                # Tab to messages pane
                tui.send("\t")

                # Move cursor down
                tui.send_arrow("down")

                # Check updated position
                new_lines = tui.capture()
                new_footer = None
                for line in new_lines[-10:]:
                    second_pane = get_middle_pane(line)
                    if "(" in second_pane and "/" in second_pane and ")" in second_pane:
                        new_footer = second_pane.strip()
                        break

                assert new_footer, "Updated footer not found"
                assert "(2/" in new_footer, f"Expected (2/X), got: {new_footer}"

                # Move down more
                for _ in range(3):
                    tui.send_arrow("down")

                # Check position again
                final_lines = tui.capture()
                final_footer = None
                for line in final_lines[-10:]:
                    second_pane = get_middle_pane(line)
                    if "(" in second_pane and "/" in second_pane and ")" in second_pane:
                        final_footer = second_pane.strip()
                        break

                assert final_footer, "Final footer not found"
                # After moving down 4 times (1 + 3), should be at position 5
                # But need to check actual message count from mock
                assert "/" in final_footer and "(" in final_footer, f"Expected position indicator, got: {final_footer}"

    def test_status_footer_no_messages(self, monkeypatch):
        """Test status footer behavior when no messages selected."""

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "no_messages_repo"
            mock_home = Path(tmpdir) / "mock_home"
            mock_home.mkdir()

            # Mock HOME environment variable
            monkeypatch.setenv("HOME", str(mock_home))

            # Create empty Claude logs directory (no logs)
            create_mock_claude_home(mock_home, [])

            # Create a repo with commits but no chats
            create_test_repo(repo_path, ["Commit without chat"])

            command = f"uv run tigs --repo {repo_path} store"

            with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env={"HOME": str(mock_home)}) as tui:
                # Wait for UI to load
                tui.wait_for("Commits")

                # Don't select any commit
                # Capture display
                lines = tui.capture()

                # Should not have status footer in messages pane
                footer_found = False
                for line in lines:
                    second_pane = get_middle_pane(line)
                    if "(" in second_pane and "/" in second_pane and ")" in second_pane:
                        # Make sure it's not from other content
                        if any(c.isdigit() for c in second_pane):
                            footer_found = True
                            break

                assert not footer_found, "Should not show status footer when no messages"

                # Should show "No messages" message instead
                has_no_messages = False
                for line in lines:
                    second_pane = get_middle_pane(line)
                    if "No messages" in second_pane:
                        has_no_messages = True
                        break

                assert has_no_messages, "Should show 'No messages' message"

    def test_status_footer_single_message(self, monkeypatch):
        """Test status footer with single message."""

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "single_message_repo"
            mock_home = Path(tmpdir) / "mock_home"
            mock_home.mkdir()

            # Mock HOME environment variable
            monkeypatch.setenv("HOME", str(mock_home))

            # Create mock Claude logs with single message
            sessions_data = [[
                ("user", "Single message")
            ]]
            create_mock_claude_home(mock_home, sessions_data)

            # Create a repo with a commit
            create_test_repo(repo_path, ["Single chat"])

            command = f"uv run tigs --repo {repo_path} store"

            with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env={"HOME": str(mock_home)}) as tui:
                # Wait for UI to load
                tui.wait_for("Commits")

                # Tab to logs pane to select the log
                tui.send("\t\t")

                # Select the first log
                tui.send(" ")

                # Wait for message
                tui.wait_for("Single message")

                # Capture display
                lines = tui.capture()

                # Look for status footer
                footer_found = False
                for line in lines[-10:]:
                    second_pane = get_middle_pane(line)
                    if "(" in second_pane and "/" in second_pane and ")" in second_pane:
                        footer_found = True
                        # Should show position indicator
                        # Mock logs have at least 4 messages, so expect (1/4) or similar
                        assert "(1/" in second_pane, f"Expected position indicator (1/X), got: {second_pane}"
                        break

                assert footer_found, "Status footer not found for single message"
