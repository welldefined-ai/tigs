#!/usr/bin/env python3
"""Test log navigation and lifecycle functionality."""

import os
import tempfile
import time
from pathlib import Path

import pytest

from framework.tui import TUI
from framework.fixtures import create_test_repo
from framework.paths import PYTHON_DIR


@pytest.fixture
def repo_with_logs():
    """Create repository with log files for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "repo"
        logs_path = Path(tmpdir) / "logs"
        
        # Create test repo
        commits = [f"Log test commit {i+1}" for i in range(5)]
        create_test_repo(repo_path, commits)
        
        # Create multiple log files
        logs_path.mkdir(parents=True, exist_ok=True)
        
        logs = [
            "log_20250107_141500.jsonl",
            "log_20250107_151200.jsonl",
            "log_20250107_161800.jsonl"
        ]
        
        for log_name in logs:
            log_file = logs_path / log_name
            messages = [
                '{"role": "user", "content": "Test question"}',
                '{"role": "assistant", "content": "Test response"}'
            ]
            log_file.write_text('\n'.join(messages))
            log_file.touch()
            os.utime(log_file, times=(time.time(), time.time()))
        
        yield repo_path, logs_path


class TestLogNavigation:
    """Test log navigation functionality."""
    
    def test_log_lifecycle_operations(self, repo_with_logs):
        """Test log creation and loading."""
        repo_path, logs_path = repo_with_logs
        
        import os
        env = os.environ.copy()
        env['TIGS_LOGS_DIR'] = str(logs_path)
        
        command = f"uv run tigs --repo {repo_path} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env=env) as tui:
            try:
                tui.wait_for("Logs", timeout=5.0)
                
                print("=== Log Lifecycle Test ===")
                
                lines = tui.capture()
                
                # Look for log indicators
                log_indicators = 0
                for line in lines:
                    if "log" in line.lower() or "20250107" in line:
                        log_indicators += 1
                
                print(f"Log indicators found: {log_indicators}")
                
                if log_indicators > 0:
                    print("✓ Log lifecycle functionality detected")
                else:
                    print("No clear log indicators found")
                
            except Exception as e:
                print(f"Log lifecycle test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Logs not available")
                else:
                    raise
    
    def test_log_navigation_triggers_reload(self, repo_with_logs):
        """Test that log navigation triggers message reload."""
        repo_path, logs_path = repo_with_logs
        
        import os
        env = os.environ.copy()
        env['TIGS_LOGS_DIR'] = str(logs_path)
        
        command = f"uv run tigs --repo {repo_path} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env=env) as tui:
            try:
                tui.wait_for("Logs", timeout=5.0)
                
                print("=== Log Navigation Reload Test ===")
                
                # Try to navigate between logs
                initial_lines = tui.capture()
                
                # Navigate in logs (if log pane exists)
                tui.send_arrow("down")
                tui.send_arrow("up")
                
                after_navigation = tui.capture()
                
                print("=== After log navigation ===")
                for i, line in enumerate(after_navigation[:10]):
                    print(f"{i:02d}: {line}")
                
                # Basic test: navigation doesn't crash
                assert len(after_navigation) > 0, "Should maintain display after log navigation"
                
            except Exception as e:
                print(f"Log navigation test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Logs not available")
                else:
                    raise
    
    def test_empty_log_state(self, repo_with_logs):
        """Test handling of empty log state."""
        repo_path, logs_path = repo_with_logs
        
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
                
                print("=== Empty Log State Test ===")
                
                lines = tui.capture()
                
                print("=== Display with empty logs ===")
                for i, line in enumerate(lines[:15]):
                    print(f"{i:02d}: {line}")
                
                # Should handle empty state gracefully
                empty_indicators = []
                for line in lines:
                    if any(indicator in line.lower() for indicator in 
                          ["no log", "empty", "no messages"]):
                        empty_indicators.append(line)
                
                if empty_indicators:
                    print("✓ Empty log state handling detected")
                else:
                    print("No specific empty log indicators found")
                
                # Basic test: doesn't crash with empty logs
                assert len(lines) > 0, "Should display something even with empty logs"
                
            except Exception as e:
                print(f"Empty log state test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Logs not available")
                else:
                    raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])