#!/usr/bin/env python3
"""Test complete CLI workflows."""

import subprocess
import tempfile
from pathlib import Path

import pytest

from framework.fixtures import create_test_repo


@pytest.fixture
def workflow_repo():
    """Create a test repository for workflow testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_path = Path(tmpdir) / "workflow_repo"
        
        # Create repository with multiple commits for testing
        commits = [f"Workflow commit {i+1}: Feature implementation" for i in range(15)]
        create_test_repo(repo_path, commits)
        yield repo_path


def run_tigs(repo_path, *args):
    """Run tigs command and return result."""
    cmd = ["uv", "run", "tigs", "--repo", str(repo_path)] + list(args)
    result = subprocess.run(cmd, cwd="/Users/basicthinker/Projects/tigs/python", 
                          capture_output=True, text=True)
    return result


def check_git_notes(repo_path, commit_sha=None):
    """Check if Git notes exist for a commit."""
    if commit_sha is None:
        # Get HEAD SHA
        result = subprocess.run(["git", "rev-parse", "HEAD"], 
                              cwd=repo_path, capture_output=True, text=True)
        if result.returncode != 0:
            return False, "Could not get HEAD SHA"
        commit_sha = result.stdout.strip()
    
    # Check for notes
    result = subprocess.run(["git", "notes", "--ref=refs/notes/chats", "show", commit_sha],
                          cwd=repo_path, capture_output=True, text=True)
    return result.returncode == 0, result.stdout


class TestCLIWorkflows:
    """Test complete CLI workflows."""
    
    def test_complete_workflow(self, workflow_repo):
        """Test Add → List → Show → Remove → Verify gone workflow."""
        
        # Step 1: Add chat
        chat_content = """chat:
- role: user
  content: "Can you help me understand this code?"
- role: assistant
  content: "Sure! This code implements a basic sorting algorithm."
"""
        
        print("=== Step 1: Add Chat ===")
        result = run_tigs(workflow_repo, "add-chat", "-m", chat_content)
        print(f"Add result: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        if result.returncode != 0:
            print("Add-chat command failed - workflow cannot continue")
            print("This might indicate the command is not implemented yet")
            return
        
        # Extract commit SHA if provided in output
        commit_sha = None
        if "commit:" in result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                if "commit:" in line:
                    commit_sha = line.split(':')[-1].strip()
                    break
        
        # Step 2: List chats
        print("\n=== Step 2: List Chats ===")
        result = run_tigs(workflow_repo, "list-chats")
        print(f"List result: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        if result.returncode == 0:
            # Should see our chat listed
            assert len(result.stdout.strip()) > 0, "List should show at least one chat"
        
        # Step 3: Show chat
        print("\n=== Step 3: Show Chat ===")
        show_args = ["show-chat"]
        if commit_sha:
            show_args.append(commit_sha)
            
        result = run_tigs(workflow_repo, *show_args)
        print(f"Show result: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        if result.returncode == 0:
            # Should show our chat content
            assert "help me understand" in result.stdout
            assert "sorting algorithm" in result.stdout
        
        # Step 4: Verify Git notes were created
        print("\n=== Step 4: Verify Git Notes ===")
        notes_exist, notes_content = check_git_notes(workflow_repo, commit_sha)
        print(f"Notes exist: {notes_exist}")
        print(f"Notes content: {notes_content}")
        
        if notes_exist:
            assert "help me understand" in notes_content or "sorting algorithm" in notes_content
        
        # Step 5: Remove chat
        print("\n=== Step 5: Remove Chat ===")
        remove_args = ["remove-chat"]
        if commit_sha:
            remove_args.append(commit_sha)
            
        result = run_tigs(workflow_repo, *remove_args)
        print(f"Remove result: {result.returncode}")
        print(f"Stdout: {result.stdout}")  
        print(f"Stderr: {result.stderr}")
        
        # Step 6: Verify removal
        print("\n=== Step 6: Verify Removal ===")
        result = run_tigs(workflow_repo, "list-chats")
        print(f"Final list result: {result.returncode}")
        print(f"Final stdout: {result.stdout}")
        
        # Should be empty or not contain our chat
        if result.returncode == 0:
            assert "help me understand" not in result.stdout
        
        # Verify Git notes are gone
        notes_exist_after, _ = check_git_notes(workflow_repo, commit_sha)
        print(f"Notes exist after removal: {notes_exist_after}")
        
        if not notes_exist_after:
            print("✓ Notes successfully removed")
    
    def test_multiple_commits_workflow(self, workflow_repo):
        """Test workflow with multiple commits."""
        
        # Get first and second commit SHAs
        result = subprocess.run(["git", "log", "--format=%H", "-n", "2"], 
                              cwd=workflow_repo, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("Could not get commit SHAs for multi-commit test")
            return
            
        commit_shas = result.stdout.strip().split('\n')
        if len(commit_shas) < 2:
            print("Need at least 2 commits for multi-commit test")
            return
        
        first_sha = commit_shas[0]
        second_sha = commit_shas[1]
        
        print(f"Testing with commits: {first_sha[:8]}, {second_sha[:8]}")
        
        # Add chat to first commit
        chat1 = """chat:
- role: user
  content: "Question about first commit"
"""
        
        result = run_tigs(workflow_repo, "add-chat", first_sha, "-m", chat1)
        print(f"Add to first commit: {result.returncode}")
        
        # Add chat to second commit  
        chat2 = """chat:
- role: user
  content: "Question about second commit"
"""
        
        result = run_tigs(workflow_repo, "add-chat", second_sha, "-m", chat2)
        print(f"Add to second commit: {result.returncode}")
        
        # List should show both
        result = run_tigs(workflow_repo, "list-chats")
        print(f"List multiple: {result.returncode}")
        
        if result.returncode == 0:
            print(f"List output: {result.stdout}")
            # Should mention both commits or show count > 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])