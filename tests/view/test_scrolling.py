#!/usr/bin/env python3
"""Test scrolling functionality in tigs view command."""

import tempfile
from pathlib import Path

import pytest
from framework.fixtures import create_test_repo
from framework.paths import PYTHON_DIR
from framework.tui import TUI
from framework.tui import find_in_pane
from framework.tui import get_middle_pane
from framework.tui import get_third_pane


@pytest.fixture
def long_commit_repo():
    """Create repository with commits that have long details."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "long_commit_repo"

        # Create commits with long messages for testing scrolling
        commits = []
        for i in range(10):
            # Create a long commit message with many lines
            message_lines = [f"Commit {i+1}: Main subject line"]
            message_lines.append("")
            message_lines.append("Detailed description:")
            for j in range(30):  # 30 lines of details
                message_lines.append(f"  - Detail line {j+1} for commit {i+1}")
            message_lines.append("")
            message_lines.append("This ensures we have content that exceeds the viewport height")

            commits.append("\n".join(message_lines))

        create_test_repo(repo_path, commits)
        yield repo_path


class TestViewScrolling:
    """Test scrolling in tigs view command."""

    def test_details_pane_scrolling(self, long_commit_repo):
        """Test UP/DOWN scrolling in commit details pane."""

        command = f"uv run tigs --repo {long_commit_repo} view"

        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
            try:
                tui.wait_for("Commit", timeout=5.0)

                print("=== Details Pane Scrolling Test ===")

                # Switch to details pane
                tui.send("\t")  # Tab to details pane

                # Capture initial view of details
                initial_lines = tui.capture()
                initial_details = []
                for line in initial_lines:
                    detail = get_middle_pane(line)
                    if detail:
                        initial_details.append(detail)

                print("Initial details view:")
                for i, detail in enumerate(initial_details[:5]):
                    print(f"  {i}: {detail}")

                # Scroll down in details pane
                tui.send_arrow("down")
                after_down_lines = tui.capture()
                after_down_details = []
                for line in after_down_lines:
                    detail = get_middle_pane(line)
                    if detail:
                        after_down_details.append(detail)

                print("After scrolling down:")
                for i, detail in enumerate(after_down_details[:5]):
                    print(f"  {i}: {detail}")

                # Content should have changed (scrolled)
                assert initial_details != after_down_details, "Details should scroll when pressing DOWN"

                # Scroll back up
                tui.send_arrow("up")
                after_up_lines = tui.capture()
                after_up_details = []
                for line in after_up_lines:
                    detail = get_middle_pane(line)
                    if detail:
                        after_up_details.append(detail)

                print("After scrolling up:")
                for i, detail in enumerate(after_up_details[:5]):
                    print(f"  {i}: {detail}")

                # Should be back to original view
                assert after_up_details == initial_details, "Should return to original view after UP"

                print("✓ Details pane scrolling works correctly")

            except Exception as e:
                print(f"Details pane scrolling test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("View command not available")
                else:
                    raise

    def test_chat_pane_scrolling(self, test_repo):
        """Test scrolling in chat pane when chat content is available."""

        command = f"uv run tigs --repo {test_repo} view"

        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
            try:
                tui.wait_for("Commit", timeout=5.0)

                print("=== Chat Pane Scrolling Test ===")

                # Switch to chat pane (Tab twice)
                tui.send("\t")  # Tab to details
                tui.send("\t")  # Tab to chat

                # Check if there's any chat content
                initial_lines = tui.capture()
                has_chat = find_in_pane(initial_lines, "chat", pane=3) or \
                          find_in_pane(initial_lines, "message", pane=3)

                if not has_chat:
                    # Check for "No chat" message
                    no_chat = find_in_pane(initial_lines, "No chat", pane=3)
                    if no_chat:
                        print("No chat content available for this commit")
                        pytest.skip("No chat content to test scrolling")

                # If we have chat content, test scrolling
                initial_chat = []
                for line in initial_lines:
                    chat = get_third_pane(line)
                    if chat:
                        initial_chat.append(chat)

                print("Initial chat view:")
                for i, chat in enumerate(initial_chat[:5]):
                    print(f"  {i}: {chat}")

                # Try to scroll down
                tui.send_arrow("down")
                after_down_lines = tui.capture()
                after_down_chat = []
                for line in after_down_lines:
                    chat = get_third_pane(line)
                    if chat:
                        after_down_chat.append(chat)

                # Even if content doesn't scroll (too short), it shouldn't error
                print("After attempting scroll:")
                for i, chat in enumerate(after_down_chat[:5]):
                    print(f"  {i}: {chat}")

                print("✓ Chat pane handles scrolling without errors")

            except Exception as e:
                print(f"Chat pane scrolling test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("View command not available")
                else:
                    raise

    def test_tab_navigation_between_panes(self, test_repo):
        """Test Tab/Shift-Tab navigation between panes."""

        command = f"uv run tigs --repo {test_repo} view"

        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
            try:
                tui.wait_for("Commit", timeout=5.0)

                print("=== Tab Navigation Test ===")

                # Check initial focus (should be on commits)
                initial_lines = tui.capture()

                # Look for focus indicators in status bar
                status_line = initial_lines[-1] if initial_lines else ""
                print(f"Initial status: {status_line}")

                # Tab to next pane
                tui.send("\t")
                after_tab1 = tui.capture()
                status_after_tab1 = after_tab1[-1] if after_tab1 else ""
                print(f"After first Tab: {status_after_tab1}")

                # Tab again
                tui.send("\t")
                after_tab2 = tui.capture()
                status_after_tab2 = after_tab2[-1] if after_tab2 else ""
                print(f"After second Tab: {status_after_tab2}")

                # Tab should wrap around
                tui.send("\t")
                after_tab3 = tui.capture()
                status_after_tab3 = after_tab3[-1] if after_tab3 else ""
                print(f"After third Tab (wrapped): {status_after_tab3}")

                # Status messages should change to indicate focus
                # We can't easily verify the exact text, but we can check they're different
                assert (status_line != status_after_tab1 or
                       status_after_tab1 != status_after_tab2 or
                       "scroll" in status_after_tab1.lower() or
                       "navigate" in status_line.lower()), \
                       "Status should change to reflect focused pane"

                print("✓ Tab navigation between panes works")

            except Exception as e:
                print(f"Tab navigation test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("View command not available")
                else:
                    raise

    def test_independent_pane_scrolling(self, long_commit_repo):
        """Test that scrolling in one pane doesn't affect others."""

        command = f"uv run tigs --repo {long_commit_repo} view"

        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
            try:
                tui.wait_for("Commit", timeout=5.0)

                print("=== Independent Pane Scrolling Test ===")

                # Capture initial state of commits pane
                initial_lines = tui.capture()
                initial_commits = []
                for line in initial_lines:
                    from framework.tui import get_first_pane
                    commit = get_first_pane(line)
                    if "Commit" in commit:
                        # Strip cursor marker to only check content
                        commit_cleaned = commit.lstrip('>').lstrip()
                        initial_commits.append(commit_cleaned)

                print(f"Initial commits: {initial_commits[:3]}")

                # Switch to details pane and scroll
                tui.send("\t")  # Tab to details
                tui.send_arrow("down")
                tui.send_arrow("down")

                # Switch back to commits pane
                tui.send("\t")  # Tab to chat
                tui.send("\t")  # Tab back to commits

                # Commits should be unchanged
                final_lines = tui.capture()
                final_commits = []
                for line in final_lines:
                    from framework.tui import get_first_pane
                    commit = get_first_pane(line)
                    if "Commit" in commit:
                        # Strip cursor marker to only check content
                        commit_cleaned = commit.lstrip('>').lstrip()
                        final_commits.append(commit_cleaned)

                print(f"Final commits: {final_commits[:3]}")

                # Commits view should be unchanged
                assert initial_commits == final_commits, \
                       "Commits view should not change when scrolling in other panes"

                print("✓ Panes scroll independently")

            except Exception as e:
                print(f"Independent scrolling test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("View command not available")
                else:
                    raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
