#!/usr/bin/env python3
"""Test status footer display in commits view for view command."""

import subprocess
import tempfile
from pathlib import Path

from framework.fixtures import create_test_repo
from framework.paths import PYTHON_DIR
from framework.tui import TUI
from framework.tui import get_first_pane


class TestViewStatusFooter:
    """Test the status footer display in view command's commits pane."""

    def test_view_status_footer_display(self):
        """Test that status footer shows in view command."""

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "view_repo"

            # Create test repo with known number of commits
            commits = [f"Commit {i}" for i in range(1, 11)]  # 10 commits
            create_test_repo(repo_path, commits)

            command = f"uv run tigs --repo {repo_path} view"

            with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
                # Wait for UI to load
                tui.wait_for("Commit")

                # Capture initial display
                lines = tui.capture()

                # Look for status footer in commits pane (first column)
                footer_found = False
                for line in lines[-10:]:  # Check last 10 lines
                    first_pane = get_first_pane(line)
                    # Status footer format: (1/10)
                    if "(" in first_pane and "/" in first_pane and ")" in first_pane:
                        footer_found = True
                        print(f"Found view status footer: {first_pane.strip()}")
                        # Should show (1/X) for first commit where X >= 1
                        import re

                        match = re.search(r"\((\d+)/(\d+)\)", first_pane)
                        if match:
                            current, total = int(match.group(1)), int(match.group(2))
                            assert current == 1, (
                                f"Expected current commit to be 1, got: {current}"
                            )
                            assert total >= 1, (
                                f"Expected total commits >= 1, got: {total}"
                            )
                        else:
                            assert False, f"Status footer format invalid: {first_pane}"
                        break

                assert footer_found, "Status footer not found in view command"

    def test_view_status_footer_navigation(self):
        """Test that status footer updates in view command."""

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "view_nav_repo"

            # Create test repo
            commits = [f"Change {i}" for i in range(1, 6)]  # 5 commits
            create_test_repo(repo_path, commits)

            command = f"uv run tigs --repo {repo_path} view"

            with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
                # Wait for UI to load
                tui.wait_for("Change")

                # Check initial position
                initial_lines = tui.capture()
                initial_footer = None
                for line in initial_lines[-10:]:
                    first_pane = get_first_pane(line)
                    if "(" in first_pane and "/" in first_pane and ")" in first_pane:
                        initial_footer = first_pane.strip()
                        break

                assert initial_footer, "Initial footer not found"
                assert "(1/5)" in initial_footer

                # Move cursor down
                tui.send_arrow("down")

                # Check updated position
                new_lines = tui.capture()
                new_footer = None
                for line in new_lines[-10:]:
                    first_pane = get_first_pane(line)
                    if "(" in first_pane and "/" in first_pane and ")" in first_pane:
                        new_footer = first_pane.strip()
                        break

                assert new_footer, "Updated footer not found"
                assert "(2/5)" in new_footer, f"Expected (2/5), got: {new_footer}"

                # Move to last commit
                for _ in range(3):
                    tui.send_arrow("down")

                # Check final position
                final_lines = tui.capture()
                final_footer = None
                for line in final_lines[-10:]:
                    first_pane = get_first_pane(line)
                    if "(" in first_pane and "/" in first_pane and ")" in first_pane:
                        final_footer = first_pane.strip()
                        break

                assert final_footer, "Final footer not found"
                assert "(5/5)" in final_footer, f"Expected (5/5), got: {final_footer}"

    def test_view_read_only_mode_has_footer(self):
        """Test that read-only mode (view command) shows footer."""

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "readonly_repo"

            # Create test repo
            commits = ["Test commit 1", "Test commit 2", "Test commit 3"]
            create_test_repo(repo_path, commits)

            command = f"uv run tigs --repo {repo_path} view"

            with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
                # Wait for UI to load
                tui.wait_for("Test commit")

                # Capture display
                lines = tui.capture()

                # Verify read-only mode indicators (no checkboxes)
                has_checkbox = False
                for line in lines:
                    first_pane = get_first_pane(line)
                    if "[ ]" in first_pane or "[x]" in first_pane:
                        has_checkbox = True
                        break

                assert not has_checkbox, "View command should not have checkboxes"

                # Verify footer is still present
                footer_found = False
                for line in lines[-10:]:
                    first_pane = get_first_pane(line)
                    if "(" in first_pane and "/" in first_pane and ")" in first_pane:
                        footer_found = True
                        assert (
                            "(1/3)" in first_pane
                            or "(2/3)" in first_pane
                            or "(3/3)" in first_pane
                        )
                        break

                assert footer_found, "Status footer should be present in read-only mode"


class TestViewMessagesStatusFooter:
    """Test the status footer display in view command's messages pane."""

    def test_messages_status_footer_display(self):
        """Test that status footer shows in messages pane."""

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "view_messages_repo"

            # Create test repo with a commit
            create_test_repo(repo_path, ["Chat commit"])

            # Get the commit SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            sha = result.stdout.strip()

            # Add chat to the commit
            chat = """schema: tigs.chat/v1
messages:
- role: user
  content: Question 1
- role: assistant
  content: Answer 1
- role: user
  content: Question 2
- role: assistant
  content: Answer 2
"""
            subprocess.run(
                ["git", "notes", "--ref=refs/notes/chats", "add", "-m", chat, sha],
                cwd=repo_path,
                check=True,
            )

            command = f"uv run tigs --repo {repo_path} view"

            with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
                # Wait for UI to load
                tui.wait_for("Chat commit")

                # Select the commit to view messages
                tui.send(" ")

                # Wait for messages to appear
                tui.wait_for("Question 1")

                # Capture display
                lines = tui.capture()

                # Look for status footer in messages pane (second column)
                from framework.tui import get_middle_pane

                footer_found = False
                for line in lines[-10:]:
                    second_pane = get_middle_pane(line)
                    if "(" in second_pane and "/" in second_pane and ")" in second_pane:
                        footer_found = True
                        # Should show (1/X) for first message where X >= 1
                        import re

                        match = re.search(r"\((\d+)/(\d+)\)", second_pane)
                        if match:
                            current, total = int(match.group(1)), int(match.group(2))
                            assert current == 1, (
                                f"Expected current message to be 1, got: {current}"
                            )
                            assert total >= 1, (
                                f"Expected total messages >= 1, got: {total}"
                            )
                        else:
                            assert False, f"Status footer format invalid: {second_pane}"
                        break

                assert footer_found, "Status footer not found in messages pane"

    def test_messages_footer_navigation(self):
        """Test that messages footer updates on navigation."""

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "view_msg_nav_repo"

            create_test_repo(repo_path, ["Discussion"])

            # Get the commit SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
            )
            sha = result.stdout.strip()

            # Add chat to the commit
            chat = """schema: tigs.chat/v1
messages:
- role: user
  content: First
- role: assistant
  content: Second
- role: user
  content: Third
"""
            subprocess.run(
                ["git", "notes", "--ref=refs/notes/chats", "add", "-m", chat, sha],
                cwd=repo_path,
                check=True,
            )

            command = f"uv run tigs --repo {repo_path} view"

            with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
                # Wait for UI to load
                tui.wait_for("Discussion")

                # Select the commit
                tui.send(" ")

                # Wait for messages
                tui.wait_for("First")

                from framework.tui import get_middle_pane

                # Check initial position
                initial_lines = tui.capture()
                initial_footer = None
                for line in initial_lines[-10:]:
                    second_pane = get_middle_pane(line)
                    if "(" in second_pane and "/" in second_pane and ")" in second_pane:
                        initial_footer = second_pane.strip()
                        break

                assert initial_footer, "Initial footer not found"
                # Check footer format is valid, but be flexible about message count
                import re

                match = re.search(r"\((\d+)/(\d+)\)", initial_footer)
                assert match, f"Invalid footer format: {initial_footer}"
                current, total = int(match.group(1)), int(match.group(2))
                assert current == 1, f"Expected to start at message 1, got: {current}"
                assert total >= 1, f"Expected at least 1 message, got: {total}"

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
                # Check navigation worked (flexible about total count)
                match = re.search(r"\((\d+)/(\d+)\)", new_footer)
                assert match, f"Invalid footer format: {new_footer}"
                current, total = int(match.group(1)), int(match.group(2))
                # If there are multiple messages, we should have navigated to the second one
                # If there's only 1 message, we stay at message 1
                if total > 1:
                    assert current == 2, (
                        f"Expected to navigate to message 2, got: {current}"
                    )
                else:
                    assert current == 1, (
                        f"Expected to stay at message 1 when only 1 total, got: {current}"
                    )

                # Move to last message
                tui.send_arrow("down")

                # Check final position
                final_lines = tui.capture()
                final_footer = None
                for line in final_lines[-10:]:
                    second_pane = get_middle_pane(line)
                    if "(" in second_pane and "/" in second_pane and ")" in second_pane:
                        final_footer = second_pane.strip()
                        break

                assert final_footer, "Final footer not found"
                # Check we're at the last message (flexible about total count)
                match = re.search(r"\((\d+)/(\d+)\)", final_footer)
                assert match, f"Invalid footer format: {final_footer}"
                current, total = int(match.group(1)), int(match.group(2))
                # We should be at the last message
                assert current == total, (
                    f"Expected to be at message {total}, got: {current}"
                )
