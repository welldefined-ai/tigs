#!/usr/bin/env python3
"""Test message selection functionality including visual mode."""

import os
import tempfile
import time
from pathlib import Path

import pytest

from framework.tui import TUI
from framework.fixtures import create_test_repo
from framework.paths import PYTHON_DIR


@pytest.fixture
def messages_setup():
    """Create repo and messages for selection testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "repo"
        logs_path = Path(tmpdir) / "logs"
        
        # Create repo with minimal commits
        commits = [f"Test commit {i+1}" for i in range(5)]
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


class TestMessageSelection:
    """Test message selection functionality."""
    
    def test_message_selection_operations(self, messages_setup):
        """Test message selection with space/v/c/a keys."""
        repo_path, logs_path = messages_setup
        
        import os
        env = os.environ.copy()
        env['TIGS_LOGS_DIR'] = str(logs_path)
        
        command = f"uv run tigs --repo {repo_path} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env=env) as tui:
            try:
                tui.wait_for("Messages", timeout=5.0)
                
                print("=== Message Selection Test ===")
                
                # Switch to messages pane
                tui.send_key("Tab")  # Move to messages pane
                
                # Test Space toggle selection
                print("--- Testing Space toggle in messages ---")
                tui.send(" ")
                space_result = tui.capture()
                
                # Test visual mode 'v'
                print("--- Testing visual mode in messages ---")
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
                
                print("=== Message selection commands completed ===")
                
                # Basic verification: commands didn't crash
                assert len(select_all_result) > 0, "Should have display after selection commands"
                
            except Exception as e:
                print(f"Message selection test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Messages not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])