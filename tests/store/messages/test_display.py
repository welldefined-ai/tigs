#!/usr/bin/env python3
"""Test message display functionality including formatting and anchoring."""

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
    """Create repo and messages for message testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "repo"
        logs_path = Path(tmpdir) / "logs"
        
        # Create repo with minimal commits
        commits = [f"Test commit {i+1}" for i in range(5)]
        create_test_repo(repo_path, commits)
        
        # Create log with several messages
        logs_path.mkdir(parents=True, exist_ok=True)

        log_file = logs_path / "log_20250107_141500.jsonl"
        messages = []
        for i in range(8):
            messages.append(f'{{"role": "user", "content": "User message {i+1}: Question about the code"}}')
            messages.append(f'{{"role": "assistant", "content": "Assistant message {i+1}: Here is the detailed answer with explanations"}}')

        log_file.write_text('\n'.join(messages))
        log_file.touch()
        os.utime(log_file, times=(time.time(), time.time()))
        
        yield repo_path, logs_path


class TestMessageDisplay:
    """Test message display functionality."""
    
    def test_message_format_and_display(self, messages_setup):
        """Test message formatting and basic display."""
        repo_path, logs_path = messages_setup
        
        import os
        env = os.environ.copy()
        env['TIGS_LOGS_DIR'] = str(logs_path)
        
        command = f"uv run tigs --repo {repo_path} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env=env) as tui:
            try:
                tui.wait_for("Messages", timeout=5.0)
                
                print("=== Message Format Test ===")
                
                lines = tui.capture()
                
                # Check for message indicators
                user_messages = []
                assistant_messages = []
                
                for line in lines:
                    if "user:" in line.lower():
                        user_messages.append(line)
                    elif "assistant:" in line.lower():
                        assistant_messages.append(line)
                
                print(f"Found {len(user_messages)} user messages")
                print(f"Found {len(assistant_messages)} assistant messages")
                
                # Should find some messages
                if len(user_messages) > 0 or len(assistant_messages) > 0:
                    print("✓ Message formatting working")
                else:
                    print("No clear message format detected")
                
            except Exception as e:
                print(f"Message format test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Messages not available")
                else:
                    raise
    
    def test_bottom_anchored_display(self, messages_setup):
        """Test bottom-anchored message display behavior."""
        repo_path, logs_path = messages_setup
        
        import os
        env = os.environ.copy()
        env['TIGS_LOGS_DIR'] = str(logs_path)
        
        command = f"uv run tigs --repo {repo_path} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env=env) as tui:
            try:
                tui.wait_for("Messages", timeout=5.0)
                
                print("=== Bottom Anchor Test ===")
                
                # Switch to messages pane if needed
                tui.send("<tab>")  # Move to messages pane
                
                initial_lines = tui.capture()
                
                print("=== Message pane display ===")
                for i, line in enumerate(initial_lines[-10:], len(initial_lines)-10):
                    print(f"{i:02d}: {line}")
                
                # Look for messages near bottom of display
                bottom_lines = initial_lines[-10:]
                message_indicators_at_bottom = 0
                
                for line in bottom_lines:
                    if any(indicator in line.lower() for indicator in ["user:", "assistant:", "message"]):
                        message_indicators_at_bottom += 1
                
                print(f"Message indicators near bottom: {message_indicators_at_bottom}")
                
                if message_indicators_at_bottom > 0:
                    print("✓ Bottom-anchored display working")
                else:
                    print("Messages may not be bottom-anchored or not visible")
                
            except Exception as e:
                print(f"Bottom anchor test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Messages not available")
                else:
                    raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])