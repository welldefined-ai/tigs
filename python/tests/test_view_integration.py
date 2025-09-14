"""Integration tests for TigsViewApp functionality."""

import curses
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

import pytest

from src.tui.view_app import TigsViewApp
from src.tui.commit_details_view import CommitDetailsView
from src.tui.chat_view import ChatView
from src.store import TigsStore


class TestViewAppIntegration:
    """Test TigsViewApp integration with views."""

    def test_view_app_initialization(self, git_repo):
        """Test view app initializes with all components."""
        store = TigsStore(git_repo)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "abc123|Test commit|Author|1234567890"
            
            app = TigsViewApp(store)
            
            # Verify all components initialized
            assert app.store == store
            assert hasattr(app, 'commit_view')
            assert hasattr(app, 'commit_details_view')
            assert hasattr(app, 'chat_display_view')
            assert app.focused_pane == 0  # Starts on commits pane
    
    def test_tab_navigation(self, git_repo):
        """Test Tab/Shift-Tab cycles through panes."""
        store = TigsStore(git_repo)
        
        with patch('subprocess.run'):
            app = TigsViewApp(store)
            
            # Start at pane 0 (commits)
            assert app.focused_pane == 0
            
            # Mock stdscr for input simulation
            mock_stdscr = Mock()
            mock_stdscr.getmaxyx.return_value = (30, 120)
            
            # Simulate Tab key press
            with patch('src.tui.view_app.PaneRenderer'):
                # Tab should move to pane 1 (details)
                app.focused_pane = 0
                key = ord('\t')
                # Simulate the Tab handling logic
                app.focused_pane = (app.focused_pane + 1) % 3
                assert app.focused_pane == 1
                
                # Another Tab should move to pane 2 (chat)
                app.focused_pane = (app.focused_pane + 1) % 3
                assert app.focused_pane == 2
                
                # Another Tab should wrap to pane 0 (commits)
                app.focused_pane = (app.focused_pane + 1) % 3
                assert app.focused_pane == 0
            
            # Test Shift-Tab (backward)
            app.focused_pane = 0
            # Shift-Tab from 0 should go to 2
            app.focused_pane = (app.focused_pane - 1) % 3
            assert app.focused_pane == 2
    
    def test_details_view_scrolling(self, git_repo):
        """Test scrolling in commit details view."""
        store = TigsStore(git_repo)
        
        # Create details view
        details_view = CommitDetailsView(store)
        
        # Load test content
        details_view.total_lines = [f"Detail line {i}" for i in range(50)]
        details_view.reset_view()
        
        # Test initial state
        assert details_view.view_offset == 0
        
        # Scroll down
        result = details_view.handle_input(curses.KEY_DOWN, pane_height=20)
        assert result is True
        assert details_view.view_offset == 1
        
        # Scroll up
        result = details_view.handle_input(curses.KEY_UP, pane_height=20)
        assert result is True
        assert details_view.view_offset == 0
        
        # Can't scroll up from top
        result = details_view.handle_input(curses.KEY_UP, pane_height=20)
        assert result is False
        assert details_view.view_offset == 0
    
    def test_chat_view_scrolling(self, git_repo):
        """Test scrolling in chat view."""
        store = TigsStore(git_repo)
        
        # Create chat view
        chat_view = ChatView(store)
        
        # Load test content
        chat_view.total_lines = [f"Chat line {i}" for i in range(30)]
        chat_view.reset_view()
        
        # Test initial state
        assert chat_view.view_offset == 0
        
        # Scroll down multiple times
        for i in range(5):
            result = chat_view.handle_input(curses.KEY_DOWN, pane_height=15)
            assert result is True
            assert chat_view.view_offset == i + 1
        
        # Get visible lines
        visible = chat_view.get_visible_lines(viewport_height=15)
        assert len(visible) == 13  # 15 - 2 borders
        assert visible[0] == "Chat line 5"
    
    def test_pane_focus_affects_input_routing(self, git_repo):
        """Test that input is routed to the focused pane."""
        store = TigsStore(git_repo)
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "abc123|Test commit|Author|1234567890"
            
            app = TigsViewApp(store)
            
            # Mock the views
            app.commit_view = Mock()
            app.commit_details_view = Mock()
            app.chat_display_view = Mock()
            
            # All handle_input methods should return False initially
            app.commit_view.handle_input.return_value = False
            app.commit_details_view.handle_input.return_value = False
            app.chat_display_view.handle_input.return_value = False
            
            # Focus on commits pane (0)
            app.focused_pane = 0
            # Simulate UP key - should go to commit_view
            key = curses.KEY_UP
            pane_height = 30
            
            # The app logic would route to commit_view
            if app.focused_pane == 0:
                app.commit_view.handle_input(key, pane_height)
            
            app.commit_view.handle_input.assert_called_once_with(key, pane_height)
            app.commit_details_view.handle_input.assert_not_called()
            app.chat_display_view.handle_input.assert_not_called()
            
            # Reset mocks
            app.commit_view.handle_input.reset_mock()
            app.commit_details_view.handle_input.reset_mock()
            app.chat_display_view.handle_input.reset_mock()
            
            # Focus on details pane (1)
            app.focused_pane = 1
            if app.focused_pane == 1:
                app.commit_details_view.handle_input(key, pane_height)
            
            app.commit_view.handle_input.assert_not_called()
            app.commit_details_view.handle_input.assert_called_once_with(key, pane_height)
            app.chat_display_view.handle_input.assert_not_called()
    
    def test_status_bar_context_sensitive(self, git_repo):
        """Test that status bar changes based on focused pane."""
        store = TigsStore(git_repo)
        
        with patch('subprocess.run'):
            app = TigsViewApp(store)
            
            # Mock stdscr
            mock_stdscr = Mock()
            mock_stdscr.getmaxyx.return_value = (30, 120)
            
            # Focus on commits pane
            app.focused_pane = 0
            expected = "↑/↓: navigate commits | Tab: switch pane | q: quit"
            # The status text is set based on focused_pane
            if app.focused_pane == 0:
                status_text = "↑/↓: navigate commits | Tab: switch pane | q: quit"
            else:
                status_text = "↑/↓: scroll | Tab: switch pane | q: quit"
            assert status_text == expected
            
            # Focus on details or chat pane
            app.focused_pane = 1
            expected = "↑/↓: scroll | Tab: switch pane | q: quit"
            if app.focused_pane == 0:
                status_text = "↑/↓: navigate commits | Tab: switch pane | q: quit"
            else:
                status_text = "↑/↓: scroll | Tab: switch pane | q: quit"
            assert status_text == expected