#!/usr/bin/env python3
"""Test cursor movement and scrolling navigation."""

import pytest

from framework.tui import TUI, find_cursor_row, get_first_pane, get_visible_commit_range, get_commit_at_cursor, save_screenshot
from framework.fixtures import multiline_repo
from framework.paths import PYTHON_DIR



def test_cursor_movement_and_scrolling(multiline_repo):
    """Test cursor moves through commits and viewport scrolls when needed."""
    
    # Launch tigs store
    command = f"uv run tigs --repo {multiline_repo} store"
    
    with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
        # Wait for UI to load
        tui.wait_for("Commits")
        
        # === PHASE 1: Initial State ===
        initial_lines = tui.capture()
        initial_cursor_row = find_cursor_row(initial_lines)
        initial_cursor_content = get_first_pane(initial_lines[initial_cursor_row])
        initial_first_commit, initial_last_commit = get_visible_commit_range(initial_lines)
        
        print(f"Initial state: cursor at row {initial_cursor_row}, range {initial_first_commit}-{initial_last_commit}")
        
        assert "Change 50" in initial_cursor_content, f"Expected cursor on Change 50, got: {initial_cursor_content}"
        
        # === PHASE 2: Move Down Until Cursor Reaches Bottom of Viewport ===
        print("\n=== PHASE 2: Moving cursor down until it hits bottom of viewport ===")
        
        cursor_reached_bottom = False
        moves_down = 0
        
        for i in range(25):  # Should be enough to hit bottom of 30-line terminal
            tui.send_arrow("down")
            moves_down += 1
            lines = tui.capture()
            cursor_row = find_cursor_row(lines)
            cursor_content = get_first_pane(lines[cursor_row])
            first_visible, last_visible = get_visible_commit_range(lines)
            
            print(f"Move {moves_down}: cursor row {cursor_row}, range {first_visible}-{last_visible}")
            
            # Check if cursor has reached the bottom of visible area (around row 28-29 for 30-line terminal)
            if cursor_row >= 25:  # Near bottom of screen
                cursor_reached_bottom = True
                print(f"Cursor reached bottom at row {cursor_row}")
                break
        
        assert cursor_reached_bottom, "Cursor should have reached bottom of viewport"
        
        # === PHASE 3: Continue Moving Down - Should Scroll Viewport ===
        print("\n=== PHASE 3: Moving down more - should scroll viewport while cursor stays at bottom ===")
        
        pre_scroll_lines = tui.capture()
        pre_scroll_first, pre_scroll_last = get_visible_commit_range(pre_scroll_lines)
        scrolling_detected = False
        
        for i in range(10):  # Continue moving down to trigger scrolling
            tui.send_arrow("down")
            lines = tui.capture()
            cursor_row = find_cursor_row(lines)
            cursor_content = get_first_pane(lines[cursor_row])
            current_first, current_last = get_visible_commit_range(lines)
            
            print(f"Scroll move {i+1}: cursor row {cursor_row}, range {current_first}-{current_last}")
            
            # Check if viewport has scrolled (first visible commit should be lower number = older)
            if current_first and pre_scroll_first and current_first < pre_scroll_first:
                scrolling_detected = True
                print(f"Scrolling detected: {pre_scroll_first} -> {current_first}")
                break
                
            # If we reach Change 1, we've definitely scrolled through everything
            if "Change 1" in cursor_content:
                scrolling_detected = True
                print("Reached Change 1 - scrolling complete")
                break
        
        assert scrolling_detected, "Should have detected viewport scrolling during downward movement"
        
        # === PHASE 4: Test Upward Movement ===
        print("\n=== PHASE 4: Testing upward movement ===")
        
        for i in range(5):
            tui.send_arrow("up")
        
        # Verify we can move back up
        final_lines = tui.capture()
        final_cursor_row = find_cursor_row(final_lines)
        final_cursor_content = get_first_pane(final_lines[final_cursor_row])
        final_first, final_last = get_visible_commit_range(final_lines)
        
        print(f"Final state: cursor row {final_cursor_row}, range {final_first}-{final_last}")
        
        # Should be on a valid commit line and cursor should be visible
        assert final_cursor_row >= 0, "Cursor should be visible after upward movement"
        assert "Change" in final_cursor_content, f"Should be on a valid commit line: {final_cursor_content}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])