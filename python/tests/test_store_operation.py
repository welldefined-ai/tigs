"""Tests for store operation functionality."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.tui.app import TigsStoreApp
from src.store import TigsStore


class TestStoreOperation:
    """Test the store operation in the TUI."""
    
    def test_store_operation_validation(self):
        """Test that store operation validates selections."""
        mock_store = Mock(spec=TigsStore)
        mock_store.repo_path = '.'
        mock_store.list_chats.return_value = []
        
        with patch('src.tui.app.ChatParser'), \
             patch('subprocess.run'):
            app = TigsStoreApp(mock_store)
            
            # Mock the views
            app.commit_view = Mock()
            app.message_view = Mock()
            
            # Test with no commits selected
            app.commit_view.get_selected_shas.return_value = []
            app.message_view.selected_messages = set([0])
            app.message_view.get_selected_messages_content = Mock(return_value='test content')
            
            app._handle_store_operation(None)
            
            assert app.status_message == "Error: No commits selected"
            assert app.status_message_time is not None
            
            # Test with no messages selected
            app.commit_view.get_selected_shas.return_value = ['sha123']
            app.message_view.selected_messages = set()
            
            app._handle_store_operation(None)
            
            assert app.status_message == "Error: No messages selected"
    
    def test_store_operation_success(self):
        """Test successful store operation."""
        mock_store = Mock(spec=TigsStore)
        mock_store.repo_path = '.'
        mock_store.add_chat = Mock()
        mock_store.list_chats.return_value = []
        
        with patch('src.tui.app.ChatParser'), \
             patch('subprocess.run'):
            app = TigsStoreApp(mock_store)
            
            # Mock the views
            app.commit_view = Mock()
            app.message_view = Mock()
            
            # Set up selected items
            app.commit_view.get_selected_shas.return_value = ['sha123', 'sha456']
            app.message_view.selected_messages = set([0, 1])
            app.message_view.get_selected_messages_content = Mock(return_value='test yaml content')
            app.commit_view.selected_commits = set([0, 1])
            app.commit_view.load_commits = Mock()
            
            # Add clear_selection method to mocks
            app.commit_view.clear_selection = Mock(side_effect=lambda: app.commit_view.selected_commits.clear())
            app.message_view.clear_selection = Mock(side_effect=lambda: app.message_view.selected_messages.clear())
            
            # Execute store operation
            app._handle_store_operation(None)
            
            # Verify store was called for each commit
            assert mock_store.add_chat.call_count == 2
            
            # Verify success message
            assert "Stored 2 messages → 2 commits" in app.status_message
            
            # Verify selections were cleared
            assert len(app.commit_view.selected_commits) == 0
            assert len(app.message_view.selected_messages) == 0
            
            # Verify commits were reloaded
            app.commit_view.load_commits.assert_called_once()
    
    def test_store_operation_with_overwrite(self):
        """Test store operation with existing notes."""
        mock_store = Mock(spec=TigsStore)
        mock_store.repo_path = '.'
        mock_store.list_chats.return_value = []
        
        # First call fails with "already has a chat", second succeeds
        mock_store.add_chat = Mock(side_effect=[
            ValueError("Commit sha123 already has a chat"),
            None  # Success after remove
        ])
        mock_store.remove_chat = Mock()
        
        with patch('src.tui.app.ChatParser'), \
             patch('subprocess.run'):
            app = TigsStoreApp(mock_store)
            
            # Mock the views
            app.commit_view = Mock()
            app.message_view = Mock()
            
            # Set up selected items
            app.commit_view.get_selected_shas.return_value = ['sha123']
            app.message_view.selected_messages = set([0])
            app.message_view.get_selected_messages_content = Mock(return_value='test yaml content')
            app.commit_view.selected_commits = set([0])
            app.commit_view.load_commits = Mock()
            
            # Add clear_selection method to mocks
            app.commit_view.clear_selection = Mock(side_effect=lambda: app.commit_view.selected_commits.clear())
            app.message_view.clear_selection = Mock(side_effect=lambda: app.message_view.selected_messages.clear())
            
            # Execute store operation
            app._handle_store_operation(None)
            
            # Verify remove was called
            mock_store.remove_chat.assert_called_once_with('sha123')
            
            # Verify add_chat was called twice (once failed, once after remove)
            assert mock_store.add_chat.call_count == 2
            
            # Verify success message with overwrite count
            assert "1 overwritten" in app.status_message
    
    def test_message_formatting(self):
        """Test that messages are formatted correctly for storage."""
        mock_store = Mock(spec=TigsStore)
        mock_store.repo_path = '.'
        mock_store.add_chat = Mock()
        mock_store.list_chats.return_value = []
        
        with patch('src.tui.app.ChatParser'), \
             patch('subprocess.run'):
            app = TigsStoreApp(mock_store)
            
            # Mock the views
            app.commit_view = Mock()
            app.message_view = Mock()
            
            # Set up selected items
            app.commit_view.get_selected_shas.return_value = ['sha123']
            app.message_view.selected_messages = set([0, 1])
            # Mock to return YAML format like cligent would
            yaml_content = "messages:\n- role: user\n  content: Question?\n- role: assistant\n  content: Answer."
            app.message_view.get_selected_messages_content = Mock(return_value=yaml_content)
            app.commit_view.selected_commits = set([0])
            app.commit_view.load_commits = Mock()
            
            # Add clear_selection method to mocks
            app.commit_view.clear_selection = Mock(side_effect=lambda: app.commit_view.selected_commits.clear())
            app.message_view.clear_selection = Mock(side_effect=lambda: app.message_view.selected_messages.clear())
            
            # Execute store operation
            app._handle_store_operation(None)
            
            # Get the formatted content that was stored
            call_args = mock_store.add_chat.call_args
            stored_content = call_args[0][1]  # Second positional argument
            
            # Verify that we're storing the cligent export format
            assert "messages:" in stored_content
            assert "role:" in stored_content