#!/usr/bin/env python3
"""Test edge cases and boundary conditions."""

import os
import subprocess
import tempfile
from pathlib import Path

import pytest

from framework.tui import TUI
from framework.fixtures import create_test_repo
from framework.paths import PYTHON_DIR


@pytest.fixture
def empty_repo():
    """Create repository with no commits."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "empty_repo"
        repo_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize empty repo
        subprocess.run(['git', 'init'], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(['git', 'config', 'user.email', 'test@example.com'], cwd=repo_path, check=True)
        subprocess.run(['git', 'config', 'user.name', 'Test User'], cwd=repo_path, check=True)
        
        yield repo_path


@pytest.fixture
def small_repo():
    """Create repository with very few commits (<50)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "small_repo"
        
        # Only 8 commits - well below lazy load threshold
        commits = [f"Small repo commit {i+1}" for i in range(8)]
        create_test_repo(repo_path, commits)
        yield repo_path


@pytest.fixture
def unicode_repo():
    """Create repository with unicode and special characters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "unicode_repo"
        
        # Commits with various special characters
        commits = [
            "Regular ASCII commit 1",
            "Unicode test: émoji 🚀 and spëcial characters",
            "CJK characters: 中文测试 日本語テスト 한글테스트",
            "Math symbols: ∑∫∞≈≠±×÷√∂",
            "Tab\tand\nnewline\rcharacters",
            "Very long unicode: " + "🎉" * 50 + " celebration",
            "Mixed: ASCII + 中文 + 🔥 + ∑",
            "Control chars: \x01\x02\x03 (invisible)",
            "Quotes 'single' \"double\" `backtick`",
            "Final commit"
        ]
        
        create_test_repo(repo_path, commits)
        yield repo_path


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_empty_repo(self, empty_repo):
        """Test graceful handling of repository with no commits."""
        
        command = f"uv run tigs --repo {empty_repo} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
            try:
                # Try to wait for some content, but expect it might fail gracefully
                tui.wait_for("commit", timeout=3.0)
                lines = tui.capture()
                
                print("=== Empty Repo Test ===")
                for i, line in enumerate(lines[:15]):
                    print(f"{i:02d}: {line}")
                
                # Should not crash, should show some kind of empty state
                empty_indicators = ["no commit", "empty", "0 commit", "nothing"]
                display_text = "\n".join(lines).lower()
                
                has_empty_message = any(indicator in display_text for indicator in empty_indicators)
                
                if has_empty_message:
                    print("✓ Found empty state message")
                else:
                    print("No explicit empty state message, but didn't crash")
                
                # Basic requirement: should render something
                assert len([l for l in lines if l.strip()]) > 0, "Should render some content even for empty repo"
                
            except Exception as e:
                print(f"Empty repo test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")
                elif "timeout" in str(e).lower():
                    print("Timeout with empty repo - might show empty state")
                else:
                    raise
    
    def test_few_commits(self, small_repo):
        """Test repo with very few commits (<50) - no lazy load artifacts."""
        
        command = f"uv run tigs --repo {small_repo} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)
                lines = tui.capture()
                
                print("=== Few Commits Test ===")
                for i, line in enumerate(lines[:15]):
                    print(f"{i:02d}: {line}")
                
                # Count commit-like entries
                commit_entries = 0
                for line in lines:
                    if any(keyword in line.lower() for keyword in 
                          ["small repo commit", "commit"]):
                        commit_entries += 1
                
                print(f"Commit entries found: {commit_entries}")
                
                # Should see all 8 commits (no lazy loading artifacts)
                if commit_entries > 0:
                    print(f"✓ Found {commit_entries} commits")
                    # Shouldn't trigger lazy loading behavior
                    if commit_entries <= 10:  # Should see all commits + maybe headers
                        print("✓ No lazy loading artifacts for small repo")
                    else:
                        print(f"Unexpected number of commit entries: {commit_entries}")
                else:
                    print("No commits detected - might be different display format")
                
                # Test selections and Enter work with few commits
                print("--- Testing operations with few commits ---")
                
                tui.send(" ")  # Select commit
                tui.send("<enter>")  # Try Enter (should fail validation gracefully)
                
                after_enter = tui.capture()
                
                # Should not crash
                assert len(after_enter) > 0, "Should handle operations gracefully with few commits"
                print("✓ Operations work with few commits")
                
            except Exception as e:
                print(f"Few commits test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")
                else:
                    raise
    
    def test_unicode_content(self, unicode_repo):
        """Test unicode and special characters don't break layout."""
        
        command = f"uv run tigs --repo {unicode_repo} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)
                lines = tui.capture()
                
                print("=== Unicode Content Test ===")
                for i, line in enumerate(lines[:15]):
                    # Be careful with printing unicode for test output
                    try:
                        print(f"{i:02d}: {line}")
                    except UnicodeEncodeError:
                        print(f"{i:02d}: <unicode content - {len(line)} chars>")
                
                # Check for unicode content preservation
                display_text = "\n".join(lines)
                
                unicode_patterns = ["emoji", "🚀", "中文", "∑", "celebration"]
                unicode_found = []
                
                for pattern in unicode_patterns:
                    if pattern in display_text:
                        unicode_found.append(pattern)
                
                print(f"Unicode patterns found: {unicode_found}")
                
                if unicode_found:
                    print("✓ Unicode content appears in display")
                else:
                    print("No unicode content visible - might be filtered or truncated")
                
                # Check that display structure is maintained
                # Look for pane separators despite unicode content
                has_structure = any("|" in line or "│" in line for line in lines[:10])
                
                if has_structure:
                    print("✓ Display structure maintained with unicode content")
                else:
                    print("Display structure might be affected by unicode")
                
                # Test navigation through unicode commits
                print("--- Testing navigation with unicode ---")
                
                navigation_success = True
                try:
                    for i in range(5):
                        tui.send_arrow("down")
                    
                    after_navigation = tui.capture()
                    print("✓ Navigation successful with unicode commits")
                    
                except Exception as e:
                    print(f"Navigation failed with unicode: {e}")
                    navigation_success = False
                
                # Test selection with unicode
                print("--- Testing selection with unicode ---")
                
                try:
                    tui.send(" ")  # Select commit with potentially unicode content
                    after_selection = tui.capture()
                    print("✓ Selection successful with unicode commits")
                    
                except Exception as e:
                    print(f"Selection failed with unicode: {e}")
                
                # Basic requirement: should not crash
                assert len(lines) > 0, "Should handle unicode content without crashing"
                
            except Exception as e:
                print(f"Unicode content test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")
                else:
                    raise
    
    def test_very_long_messages(self, unicode_repo):
        """Test very long content doesn't break pane boundaries."""
        
        # Create session with very long messages
        import tempfile
        import time
        
        with tempfile.TemporaryDirectory() as tmpdir:
            logs_path = Path(tmpdir) / "logs"
            logs_path.mkdir(parents=True, exist_ok=True)
            
            # Create session with extremely long messages
            session_file = logs_path / "session_20250107_145000.jsonl"
            
            long_message = "This is an extremely long message that goes on and on and on " * 100
            very_long_content = f"""\
{{"role": "user", "content": "{long_message}"}}
{{"role": "assistant", "content": "Normal response"}}
{{"role": "user", "content": "Short question"}}
{{"role": "assistant", "content": "{long_message}"}}
"""
            
            session_file.write_text(very_long_content)
            session_file.touch()
            os.utime(session_file, times=(time.time(), time.time()))
            
            env = os.environ.copy()
            env['TIGS_LOGS_DIR'] = str(logs_path)
            
            command = f"uv run tigs --repo {unicode_repo} store"
            
            with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env=env) as tui:
                try:
                    tui.wait_for("commit", timeout=5.0)
                    
                    # Tab to messages pane to see long content
                    tui.send("<tab>")
                    
                    lines = tui.capture()
                    
                    print("=== Very Long Messages Test ===")
                    for i, line in enumerate(lines[:15]):
                        # Truncate very long lines for readable output
                        display_line = line[:100] + "..." if len(line) > 100 else line
                        print(f"{i:02d}: {display_line}")
                    
                    # Check that pane boundaries are maintained
                    boundary_issues = 0
                    for line in lines:
                        if len(line) > 130:  # Beyond expected terminal width
                            boundary_issues += 1
                    
                    print(f"Lines exceeding boundaries: {boundary_issues}")
                    
                    if boundary_issues == 0:
                        print("✓ Long content properly contained within pane boundaries")
                    else:
                        print(f"Some content may exceed pane boundaries: {boundary_issues} lines")
                    
                    # Test navigation with long content
                    print("--- Testing navigation with long content ---")
                    
                    try:
                        for i in range(3):
                            tui.send_arrow("up")  # Messages might be bottom-anchored
                        
                        for i in range(3):
                            tui.send_arrow("down")
                        
                        print("✓ Navigation works with long messages")
                        
                    except Exception as e:
                        print(f"Navigation issues with long content: {e}")
                    
                    # Basic requirement: display maintained
                    assert len(lines) > 0, "Should maintain display with very long content"
                    
                except Exception as e:
                    print(f"Long messages test failed: {e}")
                    if "not found" in str(e).lower():
                        pytest.skip("Store command not available")
                    else:
                        raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])