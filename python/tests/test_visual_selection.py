"""Tests for visual selection functionality."""

import pytest
import curses
from unittest.mock import Mock, MagicMock, patch

from src.tui.selection_mixin import VisualSelectionMixin
from src.tui.commits_view import CommitView
from src.tui.messages_view import MessageView


class TestVisualSelectionMixin:
    """Test the VisualSelectionMixin class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a test class that uses the mixin
        class TestView(VisualSelectionMixin):
            def __init__(self):
                super().__init__()
                self.items = ['item1', 'item2', 'item3', 'item4', 'item5']
                self.cursor_idx = 0
        
        self.view = TestView()
    
    def test_initialization(self):
        """Test that mixin initializes correctly."""
        assert self.view.visual_mode is False
        assert self.view.visual_start_idx is None
        assert len(self.view.selected_items) == 0
    
    def test_is_item_selected_explicit(self):
        """Test checking if an item is explicitly selected."""
        self.view.selected_items.add(1)
        self.view.selected_items.add(3)
        
        assert self.view.is_item_selected(0) is False
        assert self.view.is_item_selected(1) is True
        assert self.view.is_item_selected(2) is False
        assert self.view.is_item_selected(3) is True
    
    def test_is_item_selected_visual_range(self):
        """Test checking if an item is in visual selection range."""
        self.view.cursor_idx = 3
        self.view.visual_mode = True
        self.view.visual_start_idx = 1
        
        assert self.view.is_item_selected(0) is False
        assert self.view.is_item_selected(1) is True  # Start of range
        assert self.view.is_item_selected(2) is True  # In range
        assert self.view.is_item_selected(3) is True  # End of range
        assert self.view.is_item_selected(4) is False
    
    def test_toggle_item_selection(self):
        """Test toggling selection of an item."""
        # Toggle on
        assert self.view.toggle_item_selection(1) is True
        assert 1 in self.view.selected_items
        
        # Toggle off
        assert self.view.toggle_item_selection(1) is True
        assert 1 not in self.view.selected_items
        
        # Toggle at cursor position
        self.view.cursor_idx = 2
        assert self.view.toggle_item_selection() is True
        assert 2 in self.view.selected_items
    
    def test_toggle_exits_visual_mode(self):
        """Test that toggling selection exits visual mode."""
        self.view.visual_mode = True
        self.view.visual_start_idx = 0
        
        self.view.toggle_item_selection(1)
        
        assert self.view.visual_mode is False
        assert self.view.visual_start_idx is None
    
    def test_enter_visual_mode(self):
        """Test entering visual mode."""
        self.view.cursor_idx = 2
        self.view.enter_visual_mode()
        
        assert self.view.visual_mode is True
        assert self.view.visual_start_idx == 2
    
    def test_exit_visual_mode_without_confirm(self):
        """Test exiting visual mode without confirming selection."""
        self.view.cursor_idx = 3
        self.view.visual_mode = True
        self.view.visual_start_idx = 1
        
        result = self.view.exit_visual_mode(confirm_selection=False)
        
        assert result is False
        assert self.view.visual_mode is False
        assert self.view.visual_start_idx is None
        assert len(self.view.selected_items) == 0
    
    def test_exit_visual_mode_with_confirm(self):
        """Test exiting visual mode and confirming selection."""
        self.view.cursor_idx = 3
        self.view.visual_mode = True
        self.view.visual_start_idx = 1
        
        result = self.view.exit_visual_mode(confirm_selection=True)
        
        assert result is True
        assert self.view.visual_mode is False
        assert self.view.visual_start_idx is None
        assert self.view.selected_items == {1, 2, 3}
    
    def test_toggle_visual_mode(self):
        """Test toggling visual mode on and off."""
        self.view.cursor_idx = 2
        
        # First toggle - enter visual mode
        result = self.view.toggle_visual_mode()
        assert result is False
        assert self.view.visual_mode is True
        assert self.view.visual_start_idx == 2
        
        # Move cursor and toggle again - exit and confirm
        self.view.cursor_idx = 4
        result = self.view.toggle_visual_mode()
        assert result is True
        assert self.view.visual_mode is False
        assert self.view.selected_items == {2, 3, 4}
    
    def test_clear_selection(self):
        """Test clearing all selections."""
        self.view.selected_items = {0, 2, 4}
        self.view.visual_mode = True
        self.view.visual_start_idx = 1
        
        result = self.view.clear_selection()
        
        assert result is True
        assert len(self.view.selected_items) == 0
        assert self.view.visual_mode is False
        assert self.view.visual_start_idx is None
    
    def test_select_all(self):
        """Test selecting all items."""
        result = self.view.select_all()
        
        assert result is True
        assert self.view.selected_items == {0, 1, 2, 3, 4}
        assert self.view.visual_mode is False
        assert self.view.visual_start_idx is None
    
    def test_handle_selection_input_space(self):
        """Test handling space key for selection toggle."""
        self.view.cursor_idx = 2
        
        result = self.view.handle_selection_input(ord(' '))
        
        assert result is True
        assert 2 in self.view.selected_items
    
    def test_handle_selection_input_v(self):
        """Test handling 'v' key for visual mode."""
        self.view.cursor_idx = 1
        
        # Enter visual mode
        result = self.view.handle_selection_input(ord('v'))
        assert result is False
        assert self.view.visual_mode is True
        
        # Exit visual mode
        self.view.cursor_idx = 3
        result = self.view.handle_selection_input(ord('v'))
        assert result is True
        assert self.view.selected_items == {1, 2, 3}
    
    def test_handle_selection_input_c(self):
        """Test handling 'c' key for clear."""
        self.view.selected_items = {0, 1, 2}
        
        result = self.view.handle_selection_input(ord('c'))
        
        assert result is True
        assert len(self.view.selected_items) == 0
    
    def test_handle_selection_input_a(self):
        """Test handling 'a' key for select all."""
        result = self.view.handle_selection_input(ord('a'))
        
        assert result is True
        assert len(self.view.selected_items) == 5
    
    def test_handle_selection_input_escape(self):
        """Test handling escape key."""
        self.view.visual_mode = True
        self.view.visual_start_idx = 1
        
        result = self.view.handle_selection_input(27)
        
        assert result is False
        assert self.view.visual_mode is False
        assert self.view.visual_start_idx is None
    
    def test_get_visual_mode_indicator(self):
        """Test getting visual mode indicator."""
        assert self.view.get_visual_mode_indicator() == ""
        
        self.view.visual_mode = True
        assert self.view.get_visual_mode_indicator() == "-- VISUAL --"
    
    def test_get_selection_range(self):
        """Test getting visual selection range."""
        # Not in visual mode
        start, end = self.view.get_selection_range()
        assert start is None
        assert end is None
        
        # In visual mode
        self.view.visual_mode = True
        self.view.visual_start_idx = 3
        self.view.cursor_idx = 1
        
        start, end = self.view.get_selection_range()
        assert start == 1
        assert end == 3


class TestCommitViewSelection:
    """Test CommitView's use of visual selection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_store = Mock()
        self.mock_store.repo_path = '/test/repo'
        self.mock_store.list_chats.return_value = []
        
        # Mock subprocess to avoid actual git calls
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "abc123|Test commit|Author|1234567890"
            self.view = CommitView(self.mock_store)
    
    def test_commit_view_initialization(self):
        """Test CommitView initializes with mixin."""
        assert hasattr(self.view, 'visual_mode')
        assert hasattr(self.view, 'visual_start_idx')
        assert hasattr(self.view, 'selected_items')
        assert self.view.selected_items is self.view.selected_commits
    
    def test_commit_view_handle_input_navigation(self):
        """Test CommitView handles navigation and keeps aliases in sync."""
        # Add some test commits
        self.view.commits = [
            {'sha': 'abc123', 'full_sha': 'abc123def', 'subject': 'Test 1'},
            {'sha': 'def456', 'full_sha': 'def456ghi', 'subject': 'Test 2'},
            {'sha': 'ghi789', 'full_sha': 'ghi789jkl', 'subject': 'Test 3'},
        ]
        self.view.items = self.view.commits
        
        # Test down arrow
        self.view.handle_input(curses.KEY_DOWN)
        assert self.view.commit_cursor_idx == 1
        assert self.view.cursor_idx == 1
        
        # Test up arrow
        self.view.handle_input(curses.KEY_UP)
        assert self.view.commit_cursor_idx == 0
        assert self.view.cursor_idx == 0
    
    def test_commit_view_visual_selection(self):
        """Test CommitView uses mixin for visual selection."""
        self.view.commits = [
            {'sha': 'abc123', 'full_sha': 'abc123def', 'subject': 'Test 1'},
            {'sha': 'def456', 'full_sha': 'def456ghi', 'subject': 'Test 2'},
            {'sha': 'ghi789', 'full_sha': 'ghi789jkl', 'subject': 'Test 3'},
        ]
        self.view.items = self.view.commits
        
        # Enter visual mode
        result = self.view.handle_input(ord('v'))
        assert self.view.visual_mode is True
        
        # Move cursor
        self.view.handle_input(curses.KEY_DOWN)
        self.view.handle_input(curses.KEY_DOWN)
        
        # Exit visual mode
        result = self.view.handle_input(ord('v'))
        assert result is True
        assert self.view.selected_commits == {0, 1, 2}


class TestMessageViewSelection:
    """Test MessageView's use of visual selection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_parser = Mock()
        self.view = MessageView(self.mock_parser)
    
    def test_message_view_initialization(self):
        """Test MessageView initializes with mixin."""
        assert hasattr(self.view, 'visual_mode')
        assert hasattr(self.view, 'visual_start_idx')
        assert hasattr(self.view, 'selected_items')
        assert self.view.selected_items is self.view.selected_messages
    
    def test_message_view_handle_input_navigation(self):
        """Test MessageView handles navigation and keeps aliases in sync."""
        # Add some test messages
        self.view.messages = [
            ('user', 'Message 1', None),
            ('assistant', 'Response 1', None),
            ('user', 'Message 2', None),
        ]
        self.view.items = self.view.messages
        
        # Test down arrow with pane height
        self.view.handle_input(None, curses.KEY_DOWN, 20)
        assert self.view.message_cursor_idx == 1
        assert self.view.cursor_idx == 1
        
        # Test up arrow
        self.view.handle_input(None, curses.KEY_UP, 20)
        assert self.view.message_cursor_idx == 0
        assert self.view.cursor_idx == 0
    
    def test_message_view_visual_selection(self):
        """Test MessageView uses mixin for visual selection."""
        self.view.messages = [
            ('user', 'Message 1', None),
            ('assistant', 'Response 1', None),
            ('user', 'Message 2', None),
        ]
        self.view.items = self.view.messages
        
        # Enter visual mode
        self.view.handle_input(None, ord('v'), 20)
        assert self.view.visual_mode is True
        
        # Move cursor
        self.view.handle_input(None, curses.KEY_DOWN, 20)
        
        # Exit visual mode
        self.view.handle_input(None, ord('v'), 20)
        assert self.view.selected_messages == {0, 1}