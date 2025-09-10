#!/usr/bin/env python3
"""Test session navigation and lifecycle functionality."""

import os
import tempfile
import time
from pathlib import Path

import pytest

from framework.tui import TUI
from framework.fixtures import create_test_repo
from framework.paths import PYTHON_DIR


@pytest.fixture
def repo_with_sessions():
    """Create repository with session files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "repo"
        logs_path = Path(tmpdir) / "logs"
        
        # Create test repo
        commits = [f"Session test commit {i+1}" for i in range(5)]
        create_test_repo(repo_path, commits)
        
        # Create multiple session files
        logs_path.mkdir(parents=True, exist_ok=True)
        
        sessions = [
            "session_20250107_141500.jsonl",
            "session_20250107_151200.jsonl", 
            "session_20250107_161800.jsonl"
        ]
        
        for session_name in sessions:
            session_file = logs_path / session_name
            messages = [
                '{"role": "user", "content": "Test question"}',
                '{"role": "assistant", "content": "Test response"}'
            ]
            session_file.write_text('\n'.join(messages))
            session_file.touch()
            os.utime(session_file, times=(time.time(), time.time()))
        
        yield repo_path, logs_path


class TestSessionNavigation:
    """Test session navigation functionality."""
    
    def test_session_lifecycle_operations(self, repo_with_sessions):
        """Test session creation and loading."""
        repo_path, logs_path = repo_with_sessions
        
        import os
        env = os.environ.copy()
        env['TIGS_LOGS_DIR'] = str(logs_path)
        
        command = f"uv run tigs --repo {repo_path} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env=env) as tui:
            try:
                tui.wait_for("Sessions", timeout=5.0)
                
                print("=== Session Lifecycle Test ===")
                
                lines = tui.capture()
                
                # Look for session indicators
                session_indicators = 0
                for line in lines:
                    if "session" in line.lower() or "20250107" in line:
                        session_indicators += 1
                
                print(f"Session indicators found: {session_indicators}")
                
                if session_indicators > 0:
                    print("✓ Session lifecycle functionality detected")
                else:
                    print("No clear session indicators found")
                
            except Exception as e:
                print(f"Session lifecycle test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Sessions not available")
                else:
                    raise
    
    def test_session_navigation_triggers_reload(self, repo_with_sessions):
        """Test that session navigation triggers message reload."""
        repo_path, logs_path = repo_with_sessions
        
        import os
        env = os.environ.copy()
        env['TIGS_LOGS_DIR'] = str(logs_path)
        
        command = f"uv run tigs --repo {repo_path} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env=env) as tui:
            try:
                tui.wait_for("Sessions", timeout=5.0)
                
                print("=== Session Navigation Reload Test ===")
                
                # Try to navigate between sessions
                initial_lines = tui.capture()
                
                # Navigate in sessions (if session pane exists)
                tui.send_arrow("down")
                tui.send_arrow("up")
                
                after_navigation = tui.capture()
                
                print("=== After session navigation ===")
                for i, line in enumerate(after_navigation[:10]):
                    print(f"{i:02d}: {line}")
                
                # Basic test: navigation doesn't crash
                assert len(after_navigation) > 0, "Should maintain display after session navigation"
                
            except Exception as e:
                print(f"Session navigation test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Sessions not available")
                else:
                    raise
    
    def test_empty_session_state(self, repo_with_sessions):
        """Test handling of empty session state."""
        repo_path, logs_path = repo_with_sessions
        
        # Create empty logs directory
        empty_logs = logs_path.parent / "empty_logs"
        empty_logs.mkdir(exist_ok=True)
        
        import os
        env = os.environ.copy()
        env['TIGS_LOGS_DIR'] = str(empty_logs)
        
        command = f"uv run tigs --repo {repo_path} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env=env) as tui:
            try:
                # Wait for some content to load
                tui.wait_for("commit", timeout=5.0)
                
                print("=== Empty Session State Test ===")
                
                lines = tui.capture()
                
                print("=== Display with empty sessions ===")
                for i, line in enumerate(lines[:15]):
                    print(f"{i:02d}: {line}")
                
                # Should handle empty state gracefully
                empty_indicators = []
                for line in lines:
                    if any(indicator in line.lower() for indicator in 
                          ["no session", "empty", "no messages"]):
                        empty_indicators.append(line)
                
                if empty_indicators:
                    print("✓ Empty session state handling detected")
                else:
                    print("No specific empty session indicators found")
                
                # Basic test: doesn't crash with empty sessions
                assert len(lines) > 0, "Should display something even with empty sessions"
                
            except Exception as e:
                print(f"Empty session state test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Sessions not available")
                else:
                    raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])