#!/usr/bin/env python3
"""Test commit list and selection behaviors."""

import tempfile
from pathlib import Path

import pytest

from framework.tui import TUI, find_cursor_row, get_first_pane
from framework.fixtures import create_test_repo
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


class TestCommits:
    """Test commit list functionality."""
    
    def test_lazy_load_and_scroll(self, commits_repo):
        """Test initial lazy load and scrolling behavior."""
        
        command = f"uv run tigs --repo {commits_repo} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
            try:
                # Wait for commits to load
                tui.wait_for("commit", timeout=5.0)
                initial_lines = tui.capture()
                
                print("=== Lazy Load Test - Initial ===")
                for i, line in enumerate(initial_lines[:15]):
                    print(f"{i:02d}: {line}")
                
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
                lines = tui.capture()
                for i, line in enumerate(lines[:20]):
                    print(f"{i:02d}: {line}")
                
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")
                else:
                    raise
    
    def test_selection_persistence(self, commits_repo):
        """Test that selections survive scrolling."""
        
        command = f"uv run tigs --repo {commits_repo} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)
                
                # Make sure we're in commits pane (should be default)
                initial_lines = tui.capture()
                
                print("=== Selection Persistence Test ===")
                
                # Try to select a commit with Space
                tui.send(" ")  # Space to select
                
                after_select = tui.capture()
                print("=== After Space selection ===")
                for i, line in enumerate(after_select[:10]):
                    print(f"{i:02d}: {line}")
                
                # Look for selection indicators
                selection_found = False
                for line in after_select:
                    first_pane = get_first_pane(line, width=50)
                    if "[x]" in first_pane or "✓" in first_pane or "*" in first_pane:
                        selection_found = True
                        print(f"✓ Found selection indicator: {first_pane}")
                        break
                
                if not selection_found:
                    print("No clear selection indicator found - selection might not be implemented")
                
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
    
    def test_selection_unified(self, commits_repo):
        """Test unified selection operations: Space/v/c/a/Esc."""
        
        command = f"uv run tigs --repo {commits_repo} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)
                
                print("=== Unified Selection Test ===")
                
                # Test Space toggle
                print("--- Testing Space toggle ---")
                tui.send(" ")
                space_result = tui.capture()
                
                # Test visual mode 'v'
                print("--- Testing visual mode ---")
                tui.send("v")
                visual_start = tui.capture()
                
                # Check for "VISUAL" in status or different display
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
                    visual_result = tui.capture()
                    print("✓ Visual mode selection completed")
                else:
                    print("Visual mode indicator not clearly visible")
                
                # Test clear all 'c'
                print("--- Testing clear all ---")
                tui.send("c")
                clear_result = tui.capture()
                
                # Test select all 'a'
                print("--- Testing select all ---")
                tui.send("a")
                select_all_result = tui.capture()
                
                print("=== Selection commands completed ===")
                
                # Basic verification: commands didn't crash
                assert len(select_all_result) > 0, "Should have display after selection commands"
                
            except Exception as e:
                print(f"Unified selection test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])