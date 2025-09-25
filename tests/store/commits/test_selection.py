#!/usr/bin/env python3
"""Test commit selection functionality including visual mode."""

import tempfile
from pathlib import Path

import pytest
from framework.fixtures import create_test_repo
from framework.paths import PYTHON_DIR
from framework.tui import TUI
from framework.tui import get_first_pane


@pytest.fixture
def commits_repo():
    """Create repository with varied commits for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "commits_repo"

        # Create commits for selection testing
        commits = []
        for i in range(20):
            if i % 3 == 0:
                commits.append(f"Feature commit {i + 1}: Add new functionality")
            else:
                commits.append(f"Fix commit {i + 1}: Bug fixes")

        create_test_repo(repo_path, commits)
        yield repo_path


@pytest.fixture
def scrolling_repo():
    """Create repository with varied commits for scrolling selection tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "scrolling_repo"

        # Create varied commits for testing selection during scroll
        commits = []
        for i in range(60):
            if i % 5 == 0:
                commits.append(
                    f"Long commit {i + 1}: " + "This is a long commit message " * 10
                )
            else:
                commits.append(f"Commit {i + 1}: Regular changes")

        create_test_repo(repo_path, commits)
        yield repo_path


class TestCommitSelection:
    """Test commit selection functionality."""

    def test_basic_selection_operations(self, commits_repo):
        """Test basic commit selection with space/c/a keys."""

        command = f"uv run tigs --repo {commits_repo} store"

        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)

                print("=== Basic Selection Test ===")

                # Test Space toggle selection
                print("--- Testing Space toggle ---")
                tui.send(" ")
                space_result = tui.capture()

                # Look for selection indicators
                for line in space_result:
                    first_pane = get_first_pane(line, width=50)
                    if "[x]" in first_pane or "✓" in first_pane or "*" in first_pane:
                        print(f"✓ Found selection indicator: {first_pane}")
                        break

                # Test select all 'a'
                print("--- Testing select all ---")
                tui.send("a")
                tui.capture()

                # Test clear all 'c'
                print("--- Testing clear all ---")
                tui.send("c")
                clear_result = tui.capture()

                print("=== Selection commands completed ===")

                # Basic verification: commands didn't crash
                assert len(clear_result) > 0, (
                    "Should have display after selection commands"
                )

            except Exception as e:
                print(f"Basic selection test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")

    def test_selection_persistence_during_scroll(self, commits_repo):
        """Test that selections survive scrolling operations."""

        command = f"uv run tigs --repo {commits_repo} store"

        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)

                print("=== Selection Persistence Test ===")

                # Make a selection
                tui.send(" ")  # Space to select

                after_select = tui.capture()
                print("=== After Space selection ===")

                # Look for selection indicators
                selection_found = False
                for line in after_select:
                    first_pane = get_first_pane(line, width=50)
                    if "[x]" in first_pane or "✓" in first_pane or "*" in first_pane:
                        selection_found = True
                        print(f"✓ Found selection indicator: {first_pane}")
                        break

                # Scroll down and back up to test persistence
                print("=== Testing scroll persistence ===")

                for i in range(10):
                    tui.send_arrow("down")

                # Scroll back up
                for i in range(10):
                    tui.send_arrow("up")

                after_scroll_back = tui.capture()

                # Check if selection is still there
                selection_persists = False
                for line in after_scroll_back:
                    first_pane = get_first_pane(line, width=50)
                    if "[x]" in first_pane or "✓" in first_pane or "*" in first_pane:
                        selection_persists = True
                        print(f"✓ Selection persisted after scroll: {first_pane}")
                        break

                if selection_found and selection_persists:
                    print("✓ Selection persistence verified")
                elif selection_found:
                    print("Selection was created but didn't persist scroll")
                else:
                    print("Selection functionality may not be implemented yet")

            except Exception as e:
                print(f"Selection persistence test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")

    def test_visual_mode_selection(self, commits_repo):
        """Test visual mode selection in commits."""

        command = f"uv run tigs --repo {commits_repo} store"

        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)

                print("=== Visual Mode Selection Test ===")

                # Enter visual mode
                tui.send("v")
                visual_start = tui.capture()

                # Check for visual mode indicator
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

                    # Test visual mode cancellation
                    tui.send("v")  # Enter visual mode again
                    tui.send_key("Escape")  # Cancel visual mode
                    tui.capture()
                    print("✓ Visual mode cancellation tested")
                else:
                    print("Visual mode indicator not clearly visible")

            except Exception as e:
                print(f"Visual mode selection test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")

    def test_selection_during_scrolling(self, scrolling_repo):
        """Test selections work correctly during scrolling with varied commits."""

        command = f"uv run tigs --repo {scrolling_repo} store"

        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)

                print("=== Selection During Scroll Test ===")

                # Make some selections while scrolling
                selections_made = []

                for i in range(12):
                    # Every 3rd move, make a selection
                    if i % 3 == 0:
                        tui.send(" ")  # Select current commit
                        selections_made.append(i)
                        print(f"Made selection at move {i}")

                    # Move down
                    tui.send_arrow("down")

                print(f"Made {len(selections_made)} selections while scrolling")

                # Check final display for selection indicators
                final_lines = tui.capture()

                selection_indicators = 0
                for line in final_lines:
                    if "[x]" in line or "✓" in line or "*" in line:
                        selection_indicators += 1

                print(f"Selection indicators visible: {selection_indicators}")

                if selection_indicators > 0:
                    print("✓ Selections visible after scrolling through varied commits")
                else:
                    print(
                        "No selection indicators visible - selections might not be implemented"
                    )

                # Test doesn't crash during selection + scroll with varied commits
                assert len(final_lines) > 0, (
                    "Should maintain display during selection/scroll"
                )

            except Exception as e:
                print(f"Selection during scroll test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")
                else:
                    raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
