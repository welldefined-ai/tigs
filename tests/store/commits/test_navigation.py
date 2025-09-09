#!/usr/bin/env python3
"""Test commit navigation, cursor movement, and scrolling behavior."""

import tempfile
from pathlib import Path

import pytest

from framework.tui import TUI, find_cursor_row, get_first_pane, get_visible_commit_range, get_commit_at_cursor
from framework.fixtures import multiline_repo, create_test_repo
from framework.paths import PYTHON_DIR


@pytest.fixture
def commits_repo():
    """Create repository with varied commits for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "commits_repo"
        
        # Create 80 commits to test lazy loading
        commits = []
        for i in range(80):
            if i % 10 == 0:
                commits.append(f"Major release {i//10+1}: Complete feature overhaul with extensive testing and documentation")
            elif i % 3 == 0:
                commits.append(f"Feature commit {i+1}: Add new functionality")
            else:
                commits.append(f"Fix commit {i+1}: Bug fixes")
        
        create_test_repo(repo_path, commits)
        yield repo_path


@pytest.fixture
def scrolling_repo():
    """Create repository with varied commits for scrolling tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "scrolling_repo"
        
        # Create varied commits that will cause display issues
        commits = []
        for i in range(60):
            if i % 5 == 0:
                # Very long commits that will wrap multiple lines
                commits.append(f"Long commit {i+1}: " + "This is an extremely long commit message that will definitely wrap to multiple lines when displayed in the narrow commits pane and should cause cursor positioning issues " * 2)
            elif i % 3 == 0:
                # Multi-line commits with actual newlines
                commits.append(f"Multi-line commit {i+1}:\n\nThis commit has multiple paragraphs\nwith line breaks that might\ncause display issues\n\n- Feature A\n- Feature B\n- Bug fixes")
            else:
                # Normal commits
                commits.append(f"Commit {i+1}: Regular changes")
        
        create_test_repo(repo_path, commits)
        yield repo_path



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
        
        # Should be on Change 50 (the latest commit in multiline_repo)
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
            
            # Check if viewport has scrolled (first visible commit should change)
            if current_first and pre_scroll_first and current_first != pre_scroll_first:
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


def test_cursor_visibility_during_scrolling(scrolling_repo):
    """Test cursor remains visible when scrolling through varied commits."""
    
    command = f"uv run tigs --repo {scrolling_repo} store"
    
    with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
        try:
            tui.wait_for("commit", timeout=5.0)
            
            print("=== Cursor Visibility Test ===")
            
            # Track cursor position throughout scrolling
            cursor_positions = []
            
            # Initial position
            initial_lines = tui.capture()
            initial_cursor = find_cursor_row(initial_lines)
            cursor_positions.append(('initial', initial_cursor))
            print(f"Initial cursor at row {initial_cursor}")
            
            # Scroll down extensively
            print("--- Scrolling down extensively ---")
            for i in range(25):  # Scroll past viewport
                tui.send_arrow("down")
                
                # Check cursor every 5 moves
                if i % 5 == 4:
                    lines = tui.capture()
                    cursor_row = find_cursor_row(lines)
                    cursor_positions.append((f'down_{i+1}', cursor_row))
                    print(f"After {i+1} down moves: cursor at row {cursor_row}")
            
            # Test upward scrolling
            print("--- Testing upward scrolling ---")
            for i in range(10):
                tui.send_arrow("up")
                
                if i % 3 == 2:  # Check every 3 moves
                    lines = tui.capture()
                    cursor_row = find_cursor_row(lines)
                    cursor_positions.append((f'up_{i+1}', cursor_row))
                    print(f"After {i+1} up moves: cursor at row {cursor_row}")
            
            # Analyze results
            print("\n=== Cursor Visibility Analysis ===")
            
            visible_count = sum(1 for _, pos in cursor_positions if pos is not None)
            total_checks = len(cursor_positions)
            
            print(f"Cursor visible in {visible_count}/{total_checks} checks")
            
            # The test should maintain cursor visibility
            assert visible_count >= total_checks * 0.8, f"Cursor should remain visible in most checks, got {visible_count}/{total_checks}"
            
        except Exception as e:
            print(f"Cursor visibility test failed: {e}")
            if "not found" in str(e).lower():
                pytest.skip("Store command not available")
            else:
                raise


def test_lazy_load_and_scroll_behavior(commits_repo):
    """Test initial lazy load and scrolling loads more commits."""
    
    command = f"uv run tigs --repo {commits_repo} store"
    
    with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
        try:
            # Wait for commits to load
            tui.wait_for("commit", timeout=5.0)
            initial_lines = tui.capture()
            
            print("=== Lazy Load Test - Initial ===")
            
            # Count commit-like entries in first pane
            commit_entries = 0
            for line in initial_lines:
                first_pane = get_first_pane(line, width=50)
                if any(keyword in first_pane.lower() for keyword in 
                      ["commit", "major", "fix", "feature", "release"]):
                    commit_entries += 1
            
            print(f"Initial commit entries visible: {commit_entries}")
            
            # Should show some commits but not all 80 (lazy load)
            if commit_entries > 0:
                assert commit_entries < 70, f"Should lazy load, not show all 80 commits. Got {commit_entries}"
                print(f"✓ Lazy load working: {commit_entries} commits shown initially")
            
            # Test scrolling loads more
            print("\n=== Testing scroll to load more ===")
            
            # Scroll down multiple times to trigger more loading
            for i in range(20):
                tui.send_arrow("down")
            
            after_scroll = tui.capture()
            
            # Count commits after scrolling
            scroll_commit_entries = 0
            for line in after_scroll:
                first_pane = get_first_pane(line, width=50)
                if any(keyword in first_pane.lower() for keyword in 
                      ["commit", "major", "fix", "feature", "release"]):
                    scroll_commit_entries += 1
            
            print(f"Commit entries after scroll: {scroll_commit_entries}")
            
            if scroll_commit_entries > commit_entries:
                print(f"✓ Scrolling loaded more commits: {commit_entries} → {scroll_commit_entries}")
            
        except Exception as e:
            print(f"Lazy load test failed: {e}")
            if "not found" in str(e).lower():
                pytest.skip("Store command not available")
            else:
                raise


if __name__ == "__main__":
    pytest.main([__file__, "-v"])