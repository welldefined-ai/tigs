#!/usr/bin/env python3
"""Test cursor movement and scrolling in tigs store."""

from pathlib import Path

import pytest

from tui import TUI, find_cursor_row, get_first_pane, get_visible_commit_range, save_screenshot


def test_cursor_movement_and_scrolling(test_repo):
    """Test cursor moves through commits and viewport scrolls when needed."""
    
    # Launch tigs store
    project_root = Path(__file__).parent.parent
    python_dir = project_root / "python"
    command = f"uv run tigs --repo {test_repo} store"
    
    with TUI(command, cwd=python_dir, dimensions=(30, 120)) as tui:
        # Wait for UI to load
        tui.wait_for("Commits")
        
        # === PHASE 1: Initial State ===
        initial_lines = tui.capture()
        initial_cursor_row = find_cursor_row(initial_lines)
        initial_cursor_content = get_first_pane(initial_lines[initial_cursor_row])
        initial_first_commit, initial_last_commit = get_visible_commit_range(initial_lines)
        
        print(f"Initial state: cursor at row {initial_cursor_row}, range {initial_first_commit}-{initial_last_commit}")
        
        assert "Change 50" in initial_cursor_content, f"Expected cursor on Change 50, got: {initial_cursor_content}"
        assert initial_first_commit == 50, f"Expected first visible commit to be 50, got: {initial_first_commit}"
        
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
        
        for i in range(15):  # Continue moving down to trigger scrolling
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
        
        # === PHASE 4: Move Up Until Cursor Reaches Top of Viewport ===
        print("\n=== PHASE 4: Moving cursor up until it hits top of viewport ===")
        
        cursor_reached_top = False
        moves_up = 0
        
        for i in range(25):  # Move up to hit top of viewport
            tui.send_arrow("up")
            moves_up += 1
            lines = tui.capture()
            cursor_row = find_cursor_row(lines)
            cursor_content = get_first_pane(lines[cursor_row])
            first_visible, last_visible = get_visible_commit_range(lines)
            
            print(f"Up move {moves_up}: cursor row {cursor_row}, range {first_visible}-{last_visible}")
            
            # Check if cursor has reached the top (row 1, since row 0 is header)
            if cursor_row <= 2:  # Top of viewport
                cursor_reached_top = True
                print(f"Cursor reached top at row {cursor_row}")
                break
        
        assert cursor_reached_top, "Cursor should have reached top of viewport"
        
        # === PHASE 5: Continue Moving Up - Should Scroll Viewport Back ===
        print("\n=== PHASE 5: Moving up more - should scroll viewport back while cursor stays at top ===")
        
        pre_scroll_lines = tui.capture()
        pre_scroll_first, pre_scroll_last = get_visible_commit_range(pre_scroll_lines)
        upward_scrolling_detected = False
        
        for i in range(15):  # Continue moving up to trigger upward scrolling
            tui.send_arrow("up")
            lines = tui.capture()
            cursor_row = find_cursor_row(lines)
            cursor_content = get_first_pane(lines[cursor_row])
            current_first, current_last = get_visible_commit_range(lines)
            
            print(f"Up scroll move {i+1}: cursor row {cursor_row}, range {current_first}-{current_last}")
            
            # Check if viewport has scrolled back up (first visible commit should be higher = newer)
            if current_first and pre_scroll_first and current_first > pre_scroll_first:
                upward_scrolling_detected = True
                print(f"Upward scrolling detected: {pre_scroll_first} -> {current_first}")
                break
                
            # If we reach Change 50, we've scrolled back to top
            if "Change 50" in cursor_content:
                upward_scrolling_detected = True
                print("Reached Change 50 - scrolled back to top")
                break
        
        assert upward_scrolling_detected, "Should have detected viewport scrolling during upward movement"
        
        # === FINAL VERIFICATION ===
        final_lines = tui.capture()
        final_cursor_row = find_cursor_row(final_lines)
        final_cursor_content = get_first_pane(final_lines[final_cursor_row])
        final_first, final_last = get_visible_commit_range(final_lines)
        
        print(f"\nFinal state: cursor row {final_cursor_row}, range {final_first}-{final_last}")
        
        # Should be back near the top with newer commits visible
        assert final_first and final_first >= 40, f"Should have scrolled back to see newer commits, got: {final_first}"
        assert final_cursor_row >= 0, "Cursor should be visible"
        assert "Change" in final_cursor_content, "Should be on a valid commit line"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])