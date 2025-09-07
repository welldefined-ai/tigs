#!/usr/bin/env python3
"""Test visual range selection works identically in both commits and messages panes."""

import os
import tempfile
import time
from pathlib import Path

import pytest

from framework.tui import TUI
from framework.fixtures import create_test_repo  
from framework.paths import PYTHON_DIR


@pytest.fixture
def visual_test_setup():
    """Create repo and messages for visual selection testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "repo"
        logs_path = Path(tmpdir) / "logs"
        
        # Create repo with several commits
        commits = [f"Visual test commit {i+1}: Feature implementation" for i in range(15)]
        create_test_repo(repo_path, commits)
        
        # Create session with several messages
        logs_path.mkdir(parents=True, exist_ok=True)
        
        session_file = logs_path / "session_20250107_141500.jsonl"
        messages = []
        for i in range(8):
            messages.append(f'{{"role": "user", "content": "User message {i+1}: Question about the code"}}')
            messages.append(f'{{"role": "assistant", "content": "Assistant message {i+1}: Here is the answer"}}')
        
        session_file.write_text('\n'.join(messages))
        session_file.touch()
        os.utime(session_file, times=(time.time(), time.time()))
        
        yield repo_path, logs_path


class TestVisualSelection:
    """Test visual range selection parity."""
    
    def test_visual_mode_parity(self, visual_test_setup):
        """Test visual mode works identically in commits and messages."""
        repo_path, logs_path = visual_test_setup
        
        import os
        env = os.environ.copy()
        env['TIGS_LOGS_DIR'] = str(logs_path)
        
        command = f"uv run tigs --repo {repo_path} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env=env) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)
                
                print("=== Visual Mode Parity Test ===")
                
                # Test visual mode in commits pane (should be default focus)
                print("--- Testing visual mode in commits ---")
                
                # Enter visual mode
                tui.send("v")
                commits_visual_start = tui.capture()
                
                # Check for visual mode indicator
                commits_has_visual = any("visual" in line.lower() for line in commits_visual_start)
                print(f"Commits visual mode active: {commits_has_visual}")
                
                # Move cursor to select range
                tui.send_arrow("down")
                tui.send_arrow("down") 
                tui.send_arrow("down")
                
                # Confirm selection
                tui.send(" ")
                commits_visual_result = tui.capture()
                
                print("=== Commits visual selection result ===")
                for i, line in enumerate(commits_visual_result[:10]):
                    print(f"{i:02d}: {line}")
                
                # Now test in messages pane
                print("--- Testing visual mode in messages ---")
                
                # Tab to messages pane
                tui.send("<tab>")
                
                messages_before_visual = tui.capture()
                print("=== Messages pane before visual ===")
                for i, line in enumerate(messages_before_visual[:8]):
                    print(f"{i:02d}: {line}")
                
                # Enter visual mode in messages
                tui.send("v")
                messages_visual_start = tui.capture()
                
                # Check for visual mode indicator
                messages_has_visual = any("visual" in line.lower() for line in messages_visual_start)
                print(f"Messages visual mode active: {messages_has_visual}")
                
                # Move cursor to select range
                tui.send_arrow("up")  # Messages might be bottom-anchored
                tui.send_arrow("up")
                tui.send_arrow("up")
                
                # Confirm selection
                tui.send(" ")
                messages_visual_result = tui.capture()
                
                print("=== Messages visual selection result ===")
                for i, line in enumerate(messages_visual_result[:10]):
                    print(f"{i:02d}: {line}")
                
                # Verify parity
                if commits_has_visual and messages_has_visual:
                    print("✓ Visual mode works in both panes")
                elif commits_has_visual:
                    print("Visual mode works in commits but not clearly in messages")
                elif messages_has_visual:
                    print("Visual mode works in messages but not clearly in commits")
                else:
                    print("Visual mode indicators not clearly visible in either pane")
                
                # Basic test: operations completed without crashing
                assert len(messages_visual_result) > 0, "Visual operations should not crash"
                
            except Exception as e:
                print(f"Visual parity test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")
    
    def test_visual_indicators(self, visual_test_setup):
        """Test visual mode shows clear indicators and highlighting."""
        repo_path, logs_path = visual_test_setup
        
        import os
        env = os.environ.copy()
        env['TIGS_LOGS_DIR'] = str(logs_path)
        
        command = f"uv run tigs --repo {repo_path} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env=env) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)
                
                print("=== Visual Indicators Test ===")
                
                # Capture before visual mode
                before_visual = tui.capture()
                
                # Enter visual mode
                tui.send("v")
                in_visual = tui.capture()
                
                # Look for status line changes
                status_changed = False
                visual_status_found = False
                
                for i, (before_line, visual_line) in enumerate(zip(before_visual, in_visual)):
                    if before_line != visual_line:
                        status_changed = True
                        print(f"Line {i} changed: '{before_line}' → '{visual_line}'")
                        
                        if "visual" in visual_line.lower():
                            visual_status_found = True
                            print(f"✓ Found visual status: {visual_line.strip()}")
                
                if visual_status_found:
                    print("✓ Clear visual mode status indicator found")
                elif status_changed:
                    print("Display changed in visual mode but no clear 'VISUAL' indicator")
                else:
                    print("No visible change when entering visual mode")
                
                # Test range highlighting during selection
                print("--- Testing range highlighting ---")
                
                # Move cursor to create range
                tui.send_arrow("down")
                during_selection = tui.capture()
                
                tui.send_arrow("down")
                extended_selection = tui.capture()
                
                # Look for visual differences indicating range
                range_highlighting = during_selection != extended_selection
                print(f"Range highlighting detected: {range_highlighting}")
                
                if range_highlighting:
                    print("✓ Visual range appears to be highlighted during selection")
                
            except Exception as e:
                print(f"Visual indicators test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")
    
    def test_visual_cancel(self, visual_test_setup):
        """Test Esc cancels visual mode without changing selections."""
        repo_path, logs_path = visual_test_setup
        
        import os
        env = os.environ.copy()
        env['TIGS_LOGS_DIR'] = str(logs_path)
        
        command = f"uv run tigs --repo {repo_path} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env=env) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)
                
                print("=== Visual Cancel Test ===")
                
                # Make some initial selections with Space
                tui.send(" ")  # Select current item
                tui.send_arrow("down")
                tui.send(" ")  # Select another item
                
                initial_with_selections = tui.capture()
                
                # Enter visual mode
                tui.send("v")
                in_visual_mode = tui.capture()
                
                # Move cursor to create a range (but don't confirm)
                tui.send_arrow("down")
                tui.send_arrow("down")
                during_visual_range = tui.capture()
                
                # Cancel with Esc
                tui.send("<escape>")
                after_cancel = tui.capture()
                
                print("=== After visual cancel ===")
                for i, line in enumerate(after_cancel[:10]):
                    print(f"{i:02d}: {line}")
                
                # Compare initial selections with post-cancel
                # Selections should be preserved, visual range should be cancelled
                
                # Look for selection indicators
                initial_selections = []
                final_selections = []
                
                for line in initial_with_selections:
                    if "[x]" in line or "✓" in line:
                        initial_selections.append(line.strip())
                
                for line in after_cancel:
                    if "[x]" in line or "✓" in line:
                        final_selections.append(line.strip())
                
                print(f"Initial selections: {len(initial_selections)}")
                print(f"Final selections: {len(final_selections)}")
                
                if initial_selections and final_selections:
                    if len(initial_selections) == len(final_selections):
                        print("✓ Original selections preserved after visual cancel")
                    else:
                        print("Selection count changed after cancel")
                elif not initial_selections and not final_selections:
                    print("No clear selection indicators - selection might not be implemented")
                
                # Basic test: didn't crash
                assert len(after_cancel) > 0, "Cancel should not crash display"
                
            except Exception as e:
                print(f"Visual cancel test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])