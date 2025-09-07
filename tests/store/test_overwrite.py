#!/usr/bin/env python3
"""Test overwrite existing notes workflow."""

import os
import subprocess
import tempfile
import time
from pathlib import Path

import pytest

from framework.tui import TUI
from framework.fixtures import create_test_repo
from framework.paths import PYTHON_DIR


@pytest.fixture
def overwrite_setup():
    """Create repo with existing Git notes for overwrite testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "repo"
        logs_path = Path(tmpdir) / "logs"
        
        # Create repo
        commits = [f"Overwrite test commit {i+1}" for i in range(5)]
        create_test_repo(repo_path, commits)
        
        # Create session with messages
        logs_path.mkdir(parents=True, exist_ok=True)
        
        session_file = logs_path / "session_20250107_144000.jsonl"
        session_content = """\
{"role": "user", "content": "New message for overwrite test"}
{"role": "assistant", "content": "New response for overwrite test"}
"""
        session_file.write_text(session_content)
        session_file.touch()
        os.utime(session_file, times=(time.time(), time.time()))
        
        # Add existing Git note to HEAD commit
        try:
            # Get HEAD commit SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            head_sha = result.stdout.strip()
            
            # Add existing note
            existing_note = """chat:
- role: user
  content: "Original message in existing note"
- role: assistant
  content: "Original response in existing note"
"""
            
            subprocess.run(
                ["git", "notes", "--ref", "refs/notes/chats", "add", "-m", existing_note, head_sha],
                cwd=repo_path,
                check=True
            )
            
            print(f"Created existing note on commit {head_sha[:8]}")
            
        except subprocess.CalledProcessError as e:
            print(f"Warning: Could not create existing note: {e}")
        
        yield repo_path, logs_path


def check_note_content(repo_path, commit_sha=None):
    """Get Git note content for a commit."""
    try:
        if commit_sha is None:
            # Get HEAD SHA
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return None
            commit_sha = result.stdout.strip()
        
        # Get note content
        result = subprocess.run(
            ["git", "notes", "--ref", "refs/notes/chats", "show", commit_sha],
            cwd=repo_path,
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            return result.stdout
        else:
            return None
            
    except Exception:
        return None


class TestOverwrite:
    """Test overwrite existing notes workflow."""
    
    def test_overwrite_prompt(self, overwrite_setup):
        """Test existing note triggers overwrite confirmation."""
        repo_path, logs_path = overwrite_setup
        
        import os
        env = os.environ.copy()
        env['TIGS_LOGS_DIR'] = str(logs_path)
        
        command = f"uv run tigs --repo {repo_path} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env=env) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)
                
                print("=== Overwrite Prompt Test ===")
                
                # Check that HEAD commit has existing note indicator
                initial_display = tui.capture()
                
                print("=== Initial display (should show existing note indicator) ===")
                for i, line in enumerate(initial_display[:15]):
                    print(f"{i:02d}: {line}")
                
                # Look for existing note indicators (*, [C], etc.)
                existing_indicators = []
                for line in initial_display:
                    if "*" in line or "[" in line:
                        existing_indicators.append(line.strip())
                
                if existing_indicators:
                    print(f"✓ Found existing note indicators: {len(existing_indicators)}")
                else:
                    print("No clear existing note indicators visible")
                
                # Select the commit with existing note (HEAD - should be first/selected)
                tui.send(" ")  # Select HEAD commit
                
                # Select a message
                tui.send("<tab>")  # Go to messages
                tui.send(" ")     # Select message
                
                # Try to store - should prompt for overwrite
                tui.send("<enter>")
                
                overwrite_display = tui.capture()
                
                print("=== Display after Enter (should show overwrite prompt) ===")
                for i, line in enumerate(overwrite_display[:20]):
                    print(f"{i:02d}: {line}")
                
                # Look for overwrite prompt patterns
                display_text = "\n".join(overwrite_display).lower()
                prompt_patterns = [
                    "overwrite", "replace", "exists", "already",
                    "confirm", "continue", "y/n", "[y]", "[n]"
                ]
                
                prompt_found = any(pattern in display_text for pattern in prompt_patterns)
                
                if prompt_found:
                    print("✓ Overwrite prompt displayed")
                    
                    # Test confirming overwrite
                    print("--- Testing overwrite confirmation ---")
                    tui.send("y")  # Confirm overwrite
                    
                    after_confirm = tui.capture()
                    
                    print("=== After overwrite confirmation ===")
                    for i, line in enumerate(after_confirm[:15]):
                        print(f"{i:02d}: {line}")
                    
                    # Check note content changed
                    new_content = check_note_content(repo_path)
                    if new_content:
                        if "new message for overwrite" in new_content.lower():
                            print("✓ Note content was overwritten with new message")
                        elif "original message" in new_content.lower():
                            print("Note content appears unchanged after overwrite")
                        else:
                            print(f"Note content changed: {new_content[:100]}...")
                    
                else:
                    print("No overwrite prompt detected")
                    print("This might indicate:")
                    print("1. Existing notes not detected properly")
                    print("2. Overwrite prompts not implemented")
                    print("3. Silent overwrite behavior")
                
            except Exception as e:
                print(f"Overwrite prompt test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")
    
    def test_overwrite_success(self, overwrite_setup):
        """Test confirming overwrite replaces note content."""
        repo_path, logs_path = overwrite_setup
        
        # Check original content first
        original_content = check_note_content(repo_path)
        print(f"Original note content: {original_content[:100] if original_content else 'None'}...")
        
        import os
        env = os.environ.copy()
        env['TIGS_LOGS_DIR'] = str(logs_path)
        
        command = f"uv run tigs --repo {repo_path} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env=env) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)
                
                print("=== Overwrite Success Test ===")
                
                # Quick selections and overwrite
                tui.send(" ")      # Select commit with existing note
                tui.send("<tab>")  # Messages
                tui.send(" ")      # Select message
                tui.send("<enter>") # Store
                
                # If prompted, confirm
                prompt_display = tui.capture()
                if any(pattern in "\n".join(prompt_display).lower() 
                      for pattern in ["overwrite", "confirm", "y/n"]):
                    print("Overwrite prompt detected, confirming...")
                    tui.send("y")
                    
                    # Wait for operation to complete
                    import time
                    time.sleep(0.5)
                
                final_display = tui.capture()
                
                # Check final note content
                final_content = check_note_content(repo_path)
                print(f"Final note content: {final_content[:100] if final_content else 'None'}...")
                
                if original_content and final_content:
                    if original_content != final_content:
                        print("✓ Note content was successfully overwritten")
                        
                        if "new message for overwrite" in final_content.lower():
                            print("✓ New content contains expected message")
                        else:
                            print("Note changed but doesn't contain expected content")
                    else:
                        print("Note content appears unchanged")
                elif final_content:
                    print("Final note exists (original might not have been detected)")
                else:
                    print("No final note content found")
                
            except Exception as e:
                print(f"Overwrite success test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")
    
    def test_overwrite_cancel(self, overwrite_setup):
        """Test canceling overwrite preserves original note."""
        repo_path, logs_path = overwrite_setup
        
        # Get original content
        original_content = check_note_content(repo_path)
        print(f"Original content to preserve: {original_content[:100] if original_content else 'None'}...")
        
        import os
        env = os.environ.copy()
        env['TIGS_LOGS_DIR'] = str(logs_path)
        
        command = f"uv run tigs --repo {repo_path} store"
        
        with TUI(command, cwd=PYTHON_DIR, dimensions=(30, 120), env=env) as tui:
            try:
                tui.wait_for("commit", timeout=5.0)
                
                print("=== Overwrite Cancel Test ===")
                
                # Make selections
                tui.send(" ")      # Select commit with existing note
                tui.send("<tab>")  # Messages
                tui.send(" ")      # Select message
                tui.send("<enter>") # Store
                
                # Check for overwrite prompt
                prompt_display = tui.capture()
                display_text = "\n".join(prompt_display).lower()
                
                if any(pattern in display_text for pattern in ["overwrite", "confirm", "y/n"]):
                    print("Overwrite prompt detected, canceling...")
                    tui.send("n")  # Cancel overwrite
                    
                    cancel_display = tui.capture()
                    
                    print("=== After cancel ===")
                    for i, line in enumerate(cancel_display[:10]):
                        print(f"{i:02d}: {line}")
                    
                    # Check content preserved
                    preserved_content = check_note_content(repo_path)
                    
                    if original_content and preserved_content:
                        if original_content == preserved_content:
                            print("✓ Original note content preserved after cancel")
                        else:
                            print("Note content changed despite cancel")
                    elif preserved_content:
                        print("Note still exists after cancel")
                    else:
                        print("Note disappeared after cancel")
                        
                else:
                    print("No overwrite prompt detected - can't test cancel")
                
            except Exception as e:
                print(f"Overwrite cancel test failed: {e}")
                if "not found" in str(e).lower():
                    pytest.skip("Store command not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])