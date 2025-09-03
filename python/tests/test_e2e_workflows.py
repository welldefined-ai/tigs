"""End-to-end workflow tests using real Git repos and operations."""

import subprocess
from pathlib import Path

import pytest

from tigs.cli import main


class TestEndToEndWorkflows:
    """Test complete workflows from start to finish."""
    
    def test_add_show_remove_workflow(self, runner, git_repo, git_notes_helper, sample_yaml_content):
        """Test complete add → show → remove workflow with Git notes verification."""
        # Step 1: Add chat with YAML content
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", sample_yaml_content])
        assert result.exit_code == 0
        assert "Added chat to commit:" in result.output
        commit_sha = result.output.split(":")[-1].strip()
        
        # Verify Git note was created
        assert git_notes_helper.verify_note_exists(git_repo, commit_sha)
        stored_content = git_notes_helper.get_note_content(git_repo, commit_sha)
        assert git_notes_helper.validate_yaml_schema(stored_content)
        
        # Step 2: Show chat content
        result = runner.invoke(main, ["--repo", str(git_repo), "show-chat"])
        assert result.exit_code == 0
        # Git notes may normalize whitespace, so verify essential content
        assert "schema: tigs.chat/v1" in result.output
        assert "How do I create a Python function?" in result.output
        assert "Here's a simple Python function:" in result.output
        assert git_notes_helper.validate_yaml_schema(result.output)
        
        # Step 3: List chats should contain our commit
        result = runner.invoke(main, ["--repo", str(git_repo), "list-chats"])
        assert result.exit_code == 0
        assert commit_sha in result.output
        
        # Step 4: Remove chat
        result = runner.invoke(main, ["--repo", str(git_repo), "remove-chat"])
        assert result.exit_code == 0
        assert "Removed chat from commit" in result.output
        
        # Verify Git note was removed
        assert not git_notes_helper.verify_note_exists(git_repo, commit_sha)
        
        # Verify list is empty
        result = runner.invoke(main, ["--repo", str(git_repo), "list-chats"])
        assert result.exit_code == 0
        assert result.output.strip() == ""
    
    def test_multi_commit_workflow(self, runner, multi_commit_repo, git_notes_helper, sample_yaml_content):
        """Test workflow with multiple commits."""
        git_repo, commits = multi_commit_repo
        
        # Add chats to multiple commits
        chat_contents = [
            "schema: tigs.chat/v1\nmessages:\n- role: user\n  content: First commit discussion",
            "schema: tigs.chat/v1\nmessages:\n- role: user\n  content: Second commit discussion", 
            "schema: tigs.chat/v1\nmessages:\n- role: user\n  content: Third commit discussion"
        ]
        
        for i, (commit_sha, content) in enumerate(zip(commits, chat_contents)):
            result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", commit_sha, "-m", content])
            assert result.exit_code == 0
            
            # Verify Git note exists and has correct content
            assert git_notes_helper.verify_note_exists(git_repo, commit_sha)
            stored_content = git_notes_helper.get_note_content(git_repo, commit_sha)
            assert git_notes_helper.validate_yaml_schema(stored_content)
            assert stored_content == content
        
        # List all chats
        result = runner.invoke(main, ["--repo", str(git_repo), "list-chats"])
        assert result.exit_code == 0
        for commit_sha in commits:
            assert commit_sha in result.output
        
        # Show specific commit chats
        for commit_sha, content in zip(commits, chat_contents):
            result = runner.invoke(main, ["--repo", str(git_repo), "show-chat", commit_sha])
            assert result.exit_code == 0
            assert result.output == content
        
        # Remove middle commit chat
        result = runner.invoke(main, ["--repo", str(git_repo), "remove-chat", commits[1]])
        assert result.exit_code == 0
        
        # Verify only middle commit note was removed
        assert git_notes_helper.verify_note_exists(git_repo, commits[0])
        assert not git_notes_helper.verify_note_exists(git_repo, commits[1])
        assert git_notes_helper.verify_note_exists(git_repo, commits[2])
    
    def test_git_notes_direct_verification(self, runner, git_repo, sample_yaml_content):
        """Test that we can verify Git notes using Git commands directly."""
        # Add chat
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", sample_yaml_content])
        assert result.exit_code == 0
        commit_sha = result.output.split(":")[-1].strip()
        
        # Verify using direct Git command
        git_result = subprocess.run(
            ["git", "notes", "--ref=refs/notes/chats", "show", commit_sha],
            cwd=git_repo,
            capture_output=True,
            text=True
        )
        assert git_result.returncode == 0
        # Verify essential content (Git may normalize whitespace)
        assert "schema: tigs.chat/v1" in git_result.stdout
        assert "How do I create a Python function?" in git_result.stdout
        assert "Here's a simple Python function:" in git_result.stdout
        
        # Verify notes list contains our commit
        git_result = subprocess.run(
            ["git", "notes", "--ref=refs/notes/chats", "list"],
            cwd=git_repo,
            capture_output=True,
            text=True
        )
        assert git_result.returncode == 0
        assert commit_sha in git_result.stdout
    
    def test_yaml_schema_validation(self, runner, git_repo, git_notes_helper):
        """Test YAML schema validation for stored content."""
        valid_yaml = """schema: tigs.chat/v1
messages:
- role: user
  content: Valid message
- role: assistant
  content: Valid response
"""
        
        # Add valid YAML content
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", valid_yaml])
        assert result.exit_code == 0
        commit_sha = result.output.split(":")[-1].strip()
        
        # Verify stored content passes schema validation
        stored_content = git_notes_helper.get_note_content(git_repo, commit_sha)
        assert git_notes_helper.validate_yaml_schema(stored_content)
        
        # Test invalid YAML should still be stored but won't pass validation
        invalid_yaml = "not valid yaml content: [unclosed"
        result = runner.invoke(main, ["--repo", str(git_repo), "remove-chat"])  # Remove first
        assert result.exit_code == 0
        
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", invalid_yaml])
        assert result.exit_code == 0
        commit_sha = result.output.split(":")[-1].strip()
        
        stored_content = git_notes_helper.get_note_content(git_repo, commit_sha)
        assert stored_content == invalid_yaml
        assert not git_notes_helper.validate_yaml_schema(stored_content)
    
    def test_unicode_content_preservation(self, runner, git_repo, git_notes_helper):
        """Test that Unicode content is preserved correctly."""
        unicode_yaml = """schema: tigs.chat/v1
messages:
- role: user
  content: |
    How do I say hello in different languages?
    
    🌍 Unicode test: 你好, مرحبا, नमस्ते
- role: assistant
  content: |
    Here are greetings in different languages:
    
    - Chinese: 你好 (nǐ hǎo)
    - Arabic: مرحبا (marhaban) 
    - Hindi: नमस्ते (namaste)
    
    Using emojis: 👋 🌟 ✨
"""
        
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", unicode_yaml])
        assert result.exit_code == 0
        commit_sha = result.output.split(":")[-1].strip()
        
        # Verify Unicode content is preserved
        stored_content = git_notes_helper.get_note_content(git_repo, commit_sha)
        assert git_notes_helper.validate_yaml_schema(stored_content)
        assert "你好" in stored_content
        assert "👋" in stored_content
        
        # Verify through show command
        result = runner.invoke(main, ["--repo", str(git_repo), "show-chat"])
        assert result.exit_code == 0
        assert git_notes_helper.validate_yaml_schema(result.output)
        assert "你好" in result.output
        assert "👋" in result.output
        assert "🌍" in result.output
    
    def test_large_content_handling(self, runner, git_repo, git_notes_helper):
        """Test handling of large chat content."""
        # Create a large YAML with many messages
        messages = []
        for i in range(50):
            messages.extend([
                {"role": "user", "content": f"Question {i}: What is the purpose of iteration {i}?"},
                {"role": "assistant", "content": f"Answer {i}: The purpose of iteration {i} is to test large content handling in the system. " * 10}
            ])
        
        import yaml
        large_yaml = yaml.dump({
            "schema": "tigs.chat/v1",
            "messages": messages
        }, default_flow_style=False, allow_unicode=True)
        
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", large_yaml])
        assert result.exit_code == 0
        commit_sha = result.output.split(":")[-1].strip()
        
        # Verify large content is stored correctly
        stored_content = git_notes_helper.get_note_content(git_repo, commit_sha)
        assert git_notes_helper.validate_yaml_schema(stored_content)
        assert "Question 49" in stored_content
        assert "Answer 49" in stored_content
        
        # Verify retrieval works
        result = runner.invoke(main, ["--repo", str(git_repo), "show-chat"])
        assert result.exit_code == 0
        assert len(result.output) > 10000  # Should be quite large
    
    def test_repository_isolation(self, runner, tmp_path, sample_yaml_content):
        """Test that different repositories are properly isolated."""
        # Create two separate repos
        repo1_path = tmp_path / "repo1"
        repo2_path = tmp_path / "repo2"
        
        for repo_path in [repo1_path, repo2_path]:
            repo_path.mkdir()
            subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
            subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo_path, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo_path, check=True)
            
            (repo_path / "README.md").write_text(f"Repository {repo_path.name}")
            subprocess.run(["git", "add", "README.md"], cwd=repo_path, check=True)
            subprocess.run(["git", "commit", "-m", f"Initial commit for {repo_path.name}"], 
                          cwd=repo_path, check=True, capture_output=True)
        
        # Add different chats to each repo
        content1 = sample_yaml_content.replace("How do I create", "Repo1: How do I create")
        content2 = sample_yaml_content.replace("How do I create", "Repo2: How do I create")
        
        result1 = runner.invoke(main, ["--repo", str(repo1_path), "add-chat", "-m", content1])
        assert result1.exit_code == 0
        sha1 = result1.output.split(":")[-1].strip()
        
        result2 = runner.invoke(main, ["--repo", str(repo2_path), "add-chat", "-m", content2])
        assert result2.exit_code == 0
        sha2 = result2.output.split(":")[-1].strip()
        
        # Verify isolation: repo1 should only see its chat
        result = runner.invoke(main, ["--repo", str(repo1_path), "list-chats"])
        assert sha1 in result.output
        assert sha2 not in result.output
        
        result = runner.invoke(main, ["--repo", str(repo1_path), "show-chat"])
        assert result.exit_code == 0
        assert "Repo1: How do I create a Python function?" in result.output
        
        # Verify isolation: repo2 should only see its chat
        result = runner.invoke(main, ["--repo", str(repo2_path), "list-chats"])
        assert sha2 in result.output
        assert sha1 not in result.output
        
        result = runner.invoke(main, ["--repo", str(repo2_path), "show-chat"])
        assert result.exit_code == 0
        assert "Repo2: How do I create a Python function?" in result.output