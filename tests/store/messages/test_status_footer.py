#!/usr/bin/env python3
"""Test status footer display in messages view for store command."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from framework.tui import TUI, get_middle_pane
from framework.fixtures import create_test_repo
from framework.paths import PYTHON_DIR


class TestMessagesStatusFooter:
    """Test the status footer display in messages view."""

    def test_status_footer_display(self):
        """Test that status footer shows current position."""

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "messages_footer_test_repo"

            # Create a repo with a commit
            create_test_repo(repo_path, ["Initial commit"])

            # Get the commit SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            sha = result.stdout.strip()

            # Add chat to the commit
            chat = """schema: tigs.chat/v1
messages:
- role: user
  content: How do I implement a binary search?
- role: assistant
  content: Here's how to implement binary search:
- role: user
  content: Can you show an example?
- role: assistant
  content: Sure, here's a Python example:
- role: user
  content: Thanks!
"""
            subprocess.run(
                ["git", "notes", "--ref=refs/notes/chats", "add", "-m", chat, sha],
                cwd=repo_path,
                check=True
            )

            command = f"uv run tigs --repo {repo_path} store"

            with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
                # Wait for UI to load
                tui.wait_for("Commits")

                # Select the first commit to view messages
                tui.send(" ")

                # Wait for messages to appear
                tui.wait_for("User")

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

    def test_status_footer_updates_on_navigation(self):
        """Test that status footer updates when navigating messages."""

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "messages_nav_test_repo"

            # Create a repo with a commit
            create_test_repo(repo_path, ["Chat commit"])

            # Get the commit SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            sha = result.stdout.strip()

            # Add chat to the commit
            chat = """schema: tigs.chat/v1
messages:
- role: user
  content: Message 1
- role: assistant
  content: Response 1
- role: user
  content: Message 2
- role: assistant
  content: Response 2
- role: user
  content: Message 3
- role: assistant
  content: Response 3
"""
            subprocess.run(
                ["git", "notes", "--ref=refs/notes/chats", "add", "-m", chat, sha],
                cwd=repo_path,
                check=True
            )

            command = f"uv run tigs --repo {repo_path} store"

            with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
                # Wait for UI to load
                tui.wait_for("Commits")

                # Select the first commit
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
                assert "(1/6)" in initial_footer

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
                assert "(2/6)" in new_footer, f"Expected (2/6), got: {new_footer}"

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
                assert "(5/6)" in final_footer, f"Expected (5/6), got: {final_footer}"

    def test_status_footer_no_messages(self):
        """Test status footer behavior when no messages selected."""

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "no_messages_repo"

            # Create a repo with commits but no chats
            create_test_repo(repo_path, ["Commit without chat"])

            command = f"uv run tigs --repo {repo_path} store"

            with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
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

    def test_status_footer_single_message(self):
        """Test status footer with single message."""

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "single_message_repo"

            # Create a repo with a commit
            create_test_repo(repo_path, ["Single chat"])

            # Get the commit SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            sha = result.stdout.strip()

            # Add chat with single message
            chat = """schema: tigs.chat/v1
messages:
- role: user
  content: Single message
"""
            subprocess.run(
                ["git", "notes", "--ref=refs/notes/chats", "add", "-m", chat, sha],
                cwd=repo_path,
                check=True
            )

            command = f"uv run tigs --repo {repo_path} store"

            with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
                # Wait for UI to load
                tui.wait_for("Commits")

                # Select the first commit
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
                        # Should show (1/1) for single message
                        assert "(1/1)" in second_pane, f"Expected (1/1), got: {second_pane}"
                        break

                assert footer_found, "Status footer not found for single message"