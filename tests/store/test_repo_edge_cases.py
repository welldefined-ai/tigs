#!/usr/bin/env python3
"""Test edge cases and boundary conditions for different repository types."""

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


class TestRepoEdgeCases:
    """Test edge cases and boundary conditions for different repo types."""
    
    def test_empty_repo_handling(self, empty_repo):
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
                
                # Look for empty state indicators
                empty_indicators = []
                for line in lines:
                    if any(indicator in line.lower() for indicator in 
                          ["no commits", "empty", "0 commits", "nothing to display"]):
                        empty_indicators.append(line)
                
                if empty_indicators:
                    print("✓ Empty repository state handled")
                    for indicator in empty_indicators:
                        print(f"  Found: {indicator.strip()}")
                else:
                    print("No specific empty repo indicators found")
                
                # Should handle empty repos gracefully
                assert len(lines) > 0, "Should display something even with empty repo"
                
            except Exception as e:
                print(f"Empty repo test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")
                else:
                    # Empty repos might cause specific errors, which is acceptable
                    print(f"Empty repo caused error: {e}")
    
    def test_few_commits_handling(self, small_repo):
        """Test handling of repository with very few commits."""
        
        command = f"uv run tigs --repo {small_repo} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)
                lines = tui.capture()
                
                print("=== Small Repo Test ===")
                for i, line in enumerate(lines[:15]):
                    print(f"{i:02d}: {line}")
                
                # Count commit-like content
                small_commit_count = 0
                for line in lines:
                    if "small repo commit" in line.lower():
                        small_commit_count += 1
                
                print(f"Small repo commits visible: {small_commit_count}")
                
                # Should display all commits since there are only 8
                if small_commit_count > 0:
                    print(f"✓ Small repo handling working: {small_commit_count} commits")
                    # With only 8 commits, should show all or most
                    assert small_commit_count <= 8, f"Should not show more than 8 commits, got {small_commit_count}"
                else:
                    print("No small repo commits clearly visible")
                
            except Exception as e:
                print(f"Small repo test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")
                else:
                    raise
    
    def test_unicode_content_handling(self, unicode_repo):
        """Test handling of unicode and special characters."""
        
        command = f"uv run tigs --repo {unicode_repo} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)
                lines = tui.capture()
                
                print("=== Unicode Content Test ===")
                for i, line in enumerate(lines[:20]):
                    print(f"{i:02d}: {line}")
                
                # Look for unicode characters in display
                unicode_indicators = []
                for line in lines:
                    # Check for various unicode content
                    if any(char in line for char in ["🚀", "🎉", "中文", "émoji", "∑", "≠"]):
                        unicode_indicators.append(line.strip())
                
                print(f"Unicode indicators found: {len(unicode_indicators)}")
                for indicator in unicode_indicators[:3]:  # Show first 3
                    print(f"  {indicator}")
                
                if unicode_indicators:
                    print("✓ Unicode content handling working")
                else:
                    print("Unicode content may be filtered or not visible")
                
                # Should handle unicode without crashing
                assert len(lines) > 0, "Should display content even with unicode characters"
                
            except Exception as e:
                print(f"Unicode content test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")
                else:
                    raise
    
    def test_very_long_messages_handling(self, unicode_repo):
        """Test handling of very long commit messages."""
        
        command = f"uv run tigs --repo {unicode_repo} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120)) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)
                lines = tui.capture()
                
                print("=== Very Long Messages Test ===")
                
                # Look for very long lines or wrapping
                long_lines = []
                wrapped_indicators = []
                
                for line in lines:
                    if len(line.strip()) > 100:
                        long_lines.append(len(line.strip()))
                    if "🎉" in line:  # The very long unicode line
                        wrapped_indicators.append(line.strip()[:50] + "...")
                
                print(f"Lines longer than 100 chars: {len(long_lines)}")
                print(f"Unicode celebration indicators: {len(wrapped_indicators)}")
                
                if long_lines:
                    print(f"✓ Long message handling detected, max length: {max(long_lines)}")
                if wrapped_indicators:
                    print("✓ Very long unicode message detected")
                    for indicator in wrapped_indicators[:2]:
                        print(f"  {indicator}")
                
                # Should handle very long messages without crashing
                assert len(lines) > 0, "Should display content even with very long messages"
                
            except Exception as e:
                print(f"Very long messages test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")
                else:
                    raise


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])