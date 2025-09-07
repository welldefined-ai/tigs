#!/usr/bin/env python3
"""Test tigs display handling for various commit message formats."""

import pytest

from framework.tui import TUI, find_cursor_row, get_first_pane, get_commit_at_cursor, get_all_visible_commits
from framework.paths import PYTHON_DIR


def test_multiline_commit_display(test_repo):
    """Test tigs display of long/multi-line commit messages."""
    
    command = f"uv run tigs --repo {test_repo} store"
    
    with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
        # Wait for UI to load
        tui.wait_for("Commits")
        
        # Capture initial display
        initial_lines = tui.capture()
        
        print("=== Multi-line Commit Test ===")
        for i, line in enumerate(initial_lines[:10]):
            print(f"{i:02d}: {line}")
        
        # Test basic functionality with multi-line commits
        cursor_row = find_cursor_row(initial_lines)
        commit_at_cursor = get_commit_at_cursor(initial_lines)
        all_commits = get_all_visible_commits(initial_lines)
        
        print(f"Cursor at row {cursor_row}, commit {commit_at_cursor}")
        print(f"Visible commits: {all_commits[:5]}...")  # Show first 5
        
        # Basic assertions
        assert len(all_commits) >= 3, f"Should see at least 3 commits, got: {len(all_commits)}"
        assert commit_at_cursor == "50", f"Expected cursor on Change 50, got: {commit_at_cursor}"
        
        # Test that cursor detection works with multi-line commits
        cursor_pane_content = get_first_pane(initial_lines[cursor_row])
        assert cursor_pane_content.strip(), "Should have content at cursor position"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])