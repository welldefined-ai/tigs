"""End-to-end tests for TUI store command functionality."""

import subprocess
import threading
import time
from unittest.mock import Mock, patch
from pathlib import Path

import pytest
import yaml

from src.tui.app import TigsStoreApp
from src.store import TigsStore


class TestTUIStoreEndToEnd:
    """Test TUI store functionality with real operations."""
    
    def test_tui_store_app_initialization_with_real_cligent(self, git_repo, claude_logs):
        """Test TUI app initialization with real cligent data."""
        store = TigsStore(git_repo)
        
        # Create app with real store
        app = TigsStoreApp(store)
        
        # Verify app initializes correctly
        assert app.store == store
        assert hasattr(app, 'commit_view')
        assert hasattr(app, 'message_view')
        assert hasattr(app, 'log_view')
        
        # Verify cligent integration works
        assert hasattr(app, 'chat_parser')
        logs = app.chat_parser.list_logs()
        assert len(logs) > 0  # Should have access to real logs
    
    
    def test_tui_commit_loading_with_real_git(self, multi_commit_repo):
        """Test commit loading with real Git repository."""
        git_repo, commits = multi_commit_repo
        store = TigsStore(git_repo)
        
        app = TigsStoreApp(store)
        
        # Load commits from real Git repo
        app.commit_view.load_commits()
        
        # Verify commits were loaded (should have at least the initial commit + 3 more)
        assert len(app.commit_view.commits) >= 4
        
        # Verify commit format (should be dicts with SHA and message)
        for commit in app.commit_view.commits:
            assert isinstance(commit, dict)
            assert 'sha' in commit or 'full_sha' in commit
            assert 'message' in commit or 'subject' in commit
            # Check SHA length
            sha = commit.get('sha') or commit.get('full_sha')
            assert len(sha) >= 7  # At least 7 chars for short SHA
            # Check message content
            message = commit.get('message') or commit.get('subject')
            assert len(message) > 0
    
    def test_store_operation_error_handling_real_git(self, git_repo, sample_yaml_content):
        """Test store operation error handling with real Git operations."""
        store = TigsStore(git_repo)
        app = TigsStoreApp(store)
        
        # Mock views
        app.commit_view = Mock()
        app.message_view = Mock()
        app.commit_view.load_commits = Mock()
        app.commit_view.clear_selection = Mock()
        app.message_view.clear_selection = Mock()
        
        # Test storing to invalid commit SHA
        app.commit_view.get_selected_shas.return_value = ['invalid-sha-that-does-not-exist']
        app.message_view.selected_messages = set([0])
        app.message_view.get_selected_messages_content = Mock(return_value=sample_yaml_content)
        
        # This should handle the error gracefully
        app._handle_store_operation(None)
        
        # Should have error message
        assert hasattr(app, 'status_message')
        assert app.status_message is not None
    
    def test_store_with_existing_notes_overwrite(self, git_repo, sample_yaml_content, git_notes_helper):
        """Test store operation with existing notes (overwrite scenario)."""
        store = TigsStore(git_repo)
        
        # First, manually add a note using tigs CLI
        from tigs.cli import main
        from click.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(main, ["--repo", str(git_repo), "add-chat", "-m", "Original content"])
        assert result.exit_code == 0
        commit_sha = result.output.split(":")[-1].strip()
        
        # Verify original note exists
        assert git_notes_helper.verify_note_exists(git_repo, commit_sha)
        
        # Now test TUI overwrite
        app = TigsStoreApp(store)
        app.commit_view = Mock()
        app.message_view = Mock()
        app.commit_view.load_commits = Mock()
        app.commit_view.clear_selection = Mock()
        app.message_view.clear_selection = Mock()
        
        # Set up for overwrite
        app.commit_view.get_selected_shas.return_value = [commit_sha]
        app.message_view.selected_messages = set([0])
        app.message_view.get_selected_messages_content = Mock(return_value=sample_yaml_content)
        app.commit_view.selected_commits = set([0])
        
        # Execute store (should overwrite)
        app._handle_store_operation(None)
        
        # Verify note was overwritten (handle whitespace normalization)
        stored_content = git_notes_helper.get_note_content(git_repo, commit_sha)
        assert git_notes_helper.validate_yaml_schema(stored_content)
        assert "How do I create a Python function?" in stored_content
        assert "Original content" not in stored_content
    
    def test_message_selection_integration(self, git_repo, claude_logs):
        """Test message selection with real Claude Code data."""
        if not claude_logs:
            pytest.skip("No Claude Code logs available")
            
        store = TigsStore(git_repo)
        app = TigsStoreApp(store)
        
        # Load real log
        log_id, _ = claude_logs[0]
        chat = app.chat_parser.parse(log_id)
        
        if len(chat.messages) == 0:
            pytest.skip("No messages in log")
        
        # Initialize message view with real data
        app.message_view.messages = chat.messages
        app.message_view.logs = {log_id: chat}
        
        # Test message selection
        message_count = min(3, len(chat.messages))
        app.message_view.selected_messages = set(range(message_count))
        
        # Verify selection
        assert len(app.message_view.selected_messages) == message_count
        
        # Test getting selected content
        app.chat_parser.clear_selection()
        app.chat_parser.select(log_id, list(app.message_view.selected_messages))
        yaml_content = app.chat_parser.compose()
        
        # Verify YAML format
        import yaml as yaml_lib
        data = yaml_lib.safe_load(yaml_content)
        assert data['schema'] == 'tigs.chat/v1'
        assert len(data['messages']) == message_count
    
    def test_full_tui_workflow_simulation(self, multi_commit_repo, claude_logs, git_notes_helper):
        """Simulate a full TUI workflow: load → select → store → verify."""
        if not claude_logs:
            pytest.skip("No Claude Code logs available")
            
        git_repo, commits = multi_commit_repo
        store = TigsStore(git_repo)
        app = TigsStoreApp(store)
        
        # Step 1: Load commits (real Git operation)
        app.commit_view.load_commits()
        assert len(app.commit_view.commits) >= 4
        
        # Step 2: Load messages (real cligent operation)
        log_id, _ = claude_logs[0]
        chat = app.chat_parser.parse(log_id)
        
        if len(chat.messages) == 0:
            pytest.skip("No messages in log")
        
        # Step 3: Simulate selections
        selected_commit_idx = 1  # Select second commit
        selected_message_indices = list(range(min(3, len(chat.messages))))
        
        # Mock the UI state
        app.commit_view.selected_commits = {selected_commit_idx}
        app.message_view.selected_messages = set(selected_message_indices)
        app.message_view.get_selected_messages_content = Mock()
        app.commit_view.clear_selection = Mock()
        app.message_view.clear_selection = Mock()
        app.commit_view.load_commits = Mock()
        
        # Get real commit SHA
        commit_dict = app.commit_view.commits[selected_commit_idx]
        commit_sha = commit_dict['full_sha']
        app.commit_view.get_selected_shas = Mock(return_value=[commit_sha])
        
        # Prepare real YAML content
        app.chat_parser.clear_selection()
        app.chat_parser.select(log_id, selected_message_indices)
        real_yaml = app.chat_parser.compose()
        app.message_view.get_selected_messages_content.return_value = real_yaml
        
        # Step 4: Execute store operation (real Git notes operation)
        app._handle_store_operation(None)
        
        # Step 5: Verify results
        assert git_notes_helper.verify_note_exists(git_repo, commit_sha)
        stored_content = git_notes_helper.get_note_content(git_repo, commit_sha)
        assert git_notes_helper.validate_yaml_schema(stored_content)
        # Verify essential content structure
        stored_data = yaml.safe_load(stored_content)
        expected_data = yaml.safe_load(real_yaml)
        assert stored_data['schema'] == expected_data['schema']
        assert len(stored_data['messages']) == len(expected_data['messages'])
        
        # Step 6: Verify via CLI that content is accessible
        from tigs.cli import main
        from click.testing import CliRunner
        runner = CliRunner()
        
        result = runner.invoke(main, ["--repo", str(git_repo), "show-chat", commit_sha])
        assert result.exit_code == 0
        assert git_notes_helper.validate_yaml_schema(result.output)
    
    def test_tui_app_with_empty_repository(self, tmp_path):
        """Test TUI behavior with repository that has no commits."""
        empty_repo = tmp_path / "empty_repo"
        empty_repo.mkdir()
        
        # Initialize empty Git repo
        subprocess.run(["git", "init"], cwd=empty_repo, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=empty_repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=empty_repo, check=True)
        
        store = TigsStore(empty_repo)
        app = TigsStoreApp(store)
        
        # Should handle empty repo gracefully
        app.commit_view.load_commits()
        assert len(app.commit_view.commits) == 0
        
        # Store operation should fail gracefully with no commits
        app.commit_view = Mock()
        app.message_view = Mock()
        app.commit_view.get_selected_shas.return_value = []
        app.message_view.selected_messages = set([0])
        
        app._handle_store_operation(None)
        assert "No commits selected" in app.status_message
    
