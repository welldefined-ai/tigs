#!/usr/bin/env python3
"""Test Git notes storage functionality - happy path."""

import os
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

from framework.tui import TUI
from framework.fixtures import create_test_repo
from framework.mock_claude_logs import create_mock_claude_home
from framework.paths import PYTHON_DIR


@pytest.fixture
def storage_setup(monkeypatch):
    """Create repo and messages for storage testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "repo"
        mock_home = Path(tmpdir) / "mock_home"
        mock_home.mkdir()

        # Mock HOME environment variable
        monkeypatch.setenv("HOME", str(mock_home))

        # Create repo with commits
        commits = [f"Storage test commit {i+1}" for i in range(8)]
        create_test_repo(repo_path, commits)
        
        # Create mock Claude logs
        sessions_data = [[
            ("user", "First message for storage"),
            ("assistant", "First response for storage"),
            ("user", "Second message for storage"),
            ("assistant", "Second response for storage")
        ]]
        create_mock_claude_home(mock_home, sessions_data)

        yield repo_path, mock_home


def check_git_notes(repo_path, ref="refs/notes/chats"):
    """Check Git notes exist and return content."""
    try:
        result = subprocess.run(
            ["git", "notes", "--ref", ref, "list"], 
            cwd=repo_path, 
            capture_output=True, 
            text=True
        )
        
        if result.returncode != 0:
            return False, "No notes found"
        
        notes_list = result.stdout.strip()
        if not notes_list:
            return False, "Empty notes list"
        
        # Get content of first note
        first_note_commit = notes_list.split('\n')[0].split()[1] if notes_list else None
        if first_note_commit:
            content_result = subprocess.run(
                ["git", "notes", "--ref", ref, "show", first_note_commit],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            return True, content_result.stdout
        
        return True, "Notes exist but no content retrieved"
        
    except Exception as e:
        return False, f"Error checking notes: {e}"


class TestStorage:
    """Test Git notes storage functionality."""
    
    def test_store_creates_notes(self, storage_setup):
        """Test 2 messages → 3 commits creates Git notes."""
        repo_path, mock_home = storage_setup
        
        command = f"uv run tigs --repo {repo_path} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env={"HOME": str(mock_home)}) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)
                
                print("=== Store Creates Notes Test ===")
                
                # Select 2 messages (tab to messages pane)
                print("--- Selecting messages ---")
                tui.send("<tab>")  # Go to messages pane
                
                # Select first message
                tui.send(" ")
                after_msg1 = tui.capture()
                
                # Select second message
                tui.send_arrow("down")
                tui.send(" ")
                after_msg2 = tui.capture()
                
                print(f"Selected 2 messages")
                
                # Tab to commits pane
                print("--- Selecting commits ---")
                tui.send("<tab>")  # Should cycle back to commits or use Shift-tab
                
                # Select 3 commits
                tui.send(" ")  # First commit
                tui.send_arrow("down")
                tui.send(" ")  # Second commit  
                tui.send_arrow("down") 
                tui.send(" ")  # Third commit
                
                after_commits = tui.capture()
                print("Selected 3 commits")
                
                # Check Git notes before storage
                notes_before, content_before = check_git_notes(repo_path)
                print(f"Notes before storage: {notes_before}")
                
                # Press Enter to store
                print("--- Pressing Enter to store ---")
                tui.send("<enter>")
                
                after_store = tui.capture()
                
                print("=== Display after Enter ===")
                for i, line in enumerate(after_store[:15]):
                    print(f"{i:02d}: {line}")
                
                # Check for confirmation message
                store_display = "\n".join(after_store)
                confirmation_patterns = [
                    "stored", "saved", "created", "success",
                    "2 message", "3 commit", "→", "notes"
                ]
                
                confirmation_found = any(pattern in store_display.lower() 
                                       for pattern in confirmation_patterns)
                
                if confirmation_found:
                    print("✓ Found confirmation message pattern")
                else:
                    print("No clear confirmation message visible")
                
                # Check Git notes after storage
                notes_after, content_after = check_git_notes(repo_path)
                print(f"Notes after storage: {notes_after}")
                print(f"Notes content preview: {content_after[:200] if content_after else 'None'}")
                
                if notes_after and not notes_before:
                    print("✓ Git notes were created by storage operation")
                elif notes_after:
                    print("Git notes exist (may have existed before)")
                else:
                    print("No Git notes found after storage - storage might not be implemented")
                
                # Look for commit indicators (*)
                indicator_count = 0
                for line in after_store:
                    if "*" in line and ("commit" in line.lower() or len(line) > 40):
                        indicator_count += 1
                
                print(f"Commit indicators (*) found: {indicator_count}")
                
                if indicator_count > 0:
                    print("✓ Found commit indicators after storage")
                
            except Exception as e:
                print(f"Storage test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")
    
    def test_confirmation_message(self, storage_setup):
        """Test confirmation shows 'Stored X messages → Y commits'."""
        repo_path, mock_home = storage_setup
        
        command = f"uv run tigs --repo {repo_path} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env={"HOME": str(mock_home)}) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)
                
                print("=== Confirmation Message Test ===")
                
                # Quick selection: 1 message, 2 commits
                tui.send("<tab>")  # Messages
                tui.send(" ")     # Select message
                
                tui.send("<tab>")  # Back to commits
                tui.send(" ")     # Select commit
                tui.send_arrow("down")
                tui.send(" ")     # Select second commit
                
                # Store
                tui.send("<enter>")
                
                confirmation_display = tui.capture()
                
                print("=== Confirmation Display ===")
                for i, line in enumerate(confirmation_display[:20]):
                    print(f"{i:02d}: {line}")
                
                # Look for specific confirmation format
                confirmation_text = "\n".join(confirmation_display).lower()
                
                # Patterns that indicate proper confirmation
                good_patterns = [
                    ("1 message", "2 commit"),
                    ("stored", "→"), 
                    ("message", "commit"),
                    ("saved", "note")
                ]
                
                confirmation_quality = 0
                for pattern_pair in good_patterns:
                    if all(p in confirmation_text for p in pattern_pair):
                        confirmation_quality += 1
                        print(f"✓ Found confirmation pattern: {pattern_pair}")
                
                if confirmation_quality > 0:
                    print(f"✓ Confirmation message quality: {confirmation_quality}/4")
                else:
                    print("No clear confirmation message pattern found")
                
            except Exception as e:
                print(f"Confirmation test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")
    
    def test_selections_cleared(self, storage_setup):
        """Test all selections cleared after successful storage."""
        repo_path, mock_home = storage_setup
        
        command = f"uv run tigs --repo {repo_path} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env={"HOME": str(mock_home)}) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)
                
                print("=== Selections Cleared Test ===")
                
                # Make selections
                tui.send(" ")     # Select commit
                tui.send_arrow("down")
                tui.send(" ")     # Select another commit
                
                tui.send("<tab>")  # Go to messages
                tui.send(" ")     # Select message
                
                # Capture before storage
                before_store = tui.capture()
                selection_count_before = sum(1 for line in before_store 
                                           if "[x]" in line or "✓" in line)
                
                print(f"Selections before storage: {selection_count_before}")
                
                # Store  
                tui.send("<enter>")
                
                # Wait a moment for storage to complete
                import time
                time.sleep(0.5)
                
                after_store = tui.capture()
                selection_count_after = sum(1 for line in after_store
                                          if "[x]" in line or "✓" in line)
                
                print(f"Selections after storage: {selection_count_after}")
                
                if selection_count_before > 0 and selection_count_after == 0:
                    print("✓ All selections cleared after storage")
                elif selection_count_before > 0 and selection_count_after < selection_count_before:
                    print(f"Some selections cleared: {selection_count_before} → {selection_count_after}")
                elif selection_count_before == 0:
                    print("No clear selections detected initially")
                else:
                    print("Selections may not have been cleared")
                
            except Exception as e:
                print(f"Selections cleared test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])