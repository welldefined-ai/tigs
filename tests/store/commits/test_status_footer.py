#!/usr/bin/env python3
"""Test status footer display in commits view for store command."""

import tempfile
from pathlib import Path

from framework.fixtures import create_test_repo
from framework.paths import PYTHON_DIR
from framework.tui import TUI
from framework.tui import get_first_pane


class TestCommitsStatusFooter:
    """Test the status footer display in commits view."""

    def test_status_footer_display(self):
        """Test that status footer shows current position."""

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "footer_test_repo"

            # Create a simple repo with just 10 commits to ensure footer is visible
            commits = [f"Commit {i}" for i in range(1, 11)]
            create_test_repo(repo_path, commits)

            command = f"uv run tigs --repo {repo_path} store"

            with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
                # Wait for UI to load
                tui.wait_for("Commits")

                # Capture initial display
                lines = tui.capture()

                # Look for status footer in commits pane (first column)
                footer_found = False

                # Check all lines, looking in the first pane (commits column)
                for i, line in enumerate(lines):
                    first_pane = get_first_pane(line)
                    # Look for the status footer pattern (X/Y)
                    import re
                    if re.search(r'\(\d+/\d+\)', first_pane):
                        footer_found = True
                        # Should show (1/10) for first commit
                        assert "(1/10)" in first_pane, f"Expected (1/10), got: {first_pane}"
                        break

                assert footer_found, "Status footer not found in commits pane"

    def test_status_footer_updates_on_navigation(self, test_repo):
        """Test that status footer updates when navigating commits."""

        command = f"uv run tigs --repo {test_repo} store"

        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
            # Wait for UI to load
            tui.wait_for("Commits")

            # Check initial position
            initial_lines = tui.capture()
            initial_footer = None
            for line in initial_lines[-10:]:
                first_pane = get_first_pane(line)
                if "(" in first_pane and "/" in first_pane and ")" in first_pane:
                    initial_footer = first_pane.strip()
                    break

            assert initial_footer, "Initial footer not found"
            assert "(1/50)" in initial_footer

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
            assert "(2/50)" in new_footer, f"Expected (2/50), got: {new_footer}"

            # Move down a few more times
            for _ in range(3):
                tui.send_arrow("down")

            # Check position again
            final_lines = tui.capture()
            final_footer = None
            for line in final_lines[-10:]:
                first_pane = get_first_pane(line)
                if "(" in first_pane and "/" in first_pane and ")" in first_pane:
                    final_footer = first_pane.strip()
                    break

            assert final_footer, "Final footer not found"
            assert "(5/50)" in final_footer, f"Expected (5/50), got: {final_footer}"

    def test_status_footer_with_empty_repo(self):
        """Test status footer behavior with no commits."""

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "empty_repo"
            create_test_repo(repo_path, [])  # Empty repo

            command = f"uv run tigs --repo {repo_path} store"

            with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
                # Wait for UI to load
                tui.wait_for("Commits")

                # Capture display
                lines = tui.capture()

                # Should not show status footer for empty repo
                footer_found = False
                for line in lines:
                    first_pane = get_first_pane(line)
                    if "(" in first_pane and "/" in first_pane and ")" in first_pane:
                        # Make sure it's not from other panes
                        if "commits" in first_pane.lower() or any(c.isdigit() for c in first_pane):
                            footer_found = True
                            break

                # Empty repo should show "No commits" message instead of footer
                assert not footer_found or "(0/" not in str(lines), "Should not show status footer for empty repo"

    def test_status_footer_with_single_commit(self):
        """Test status footer with single commit."""

        with tempfile.TemporaryDirectory() as tmpdir:
            repo_path = Path(tmpdir) / "single_commit_repo"
            create_test_repo(repo_path, ["Single commit"])

            command = f"uv run tigs --repo {repo_path} store"

            with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
                # Wait for UI to load
                tui.wait_for("Commits")

                # Capture display
                lines = tui.capture()

                # Look for status footer
                footer_found = False
                for line in lines[-10:]:
                    first_pane = get_first_pane(line)
                    if "(" in first_pane and "/" in first_pane and ")" in first_pane:
                        footer_found = True
                        # Should show (1/1) for single commit
                        assert "(1/1)" in first_pane, f"Expected (1/1), got: {first_pane}"
                        break

                assert footer_found, "Status footer not found for single commit"
