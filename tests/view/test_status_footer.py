#!/usr/bin/env python3
"""Test status footer display in commits view for view command."""

import tempfile
from pathlib import Path

import pytest

from framework.tui import TUI, get_first_pane
from framework.fixtures import create_test_repo
from framework.paths import PYTHON_DIR


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
                        # Should show (1/10) for first commit
                        assert "(1/10)" in first_pane, f"Expected (1/10), got: {first_pane}"
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
                        assert "(1/3)" in first_pane or "(2/3)" in first_pane or "(3/3)" in first_pane
                        break

                assert footer_found, "Status footer should be present in read-only mode"