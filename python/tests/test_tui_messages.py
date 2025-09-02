"""Tests for TUI message view functionality - Fixed version."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import curses

from src.tui.app import TigsStoreApp


def create_mock_store():
    """Create a properly configured mock store."""
    mock_store = Mock()
    mock_store.list_chats.return_value = []
    mock_store.repo_path = '.'
    return mock_store


def setup_mock_subprocess(mock_run):
    """Configure subprocess mock for CommitView."""
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = ""
    

class TestMessageView:
    """Test message display functionality in the TUI."""
    
    @patch('subprocess.run')
    @patch('src.tui.app.ChatParser')
    def test_load_messages_basic(self, mock_parser_class, mock_run):
        """Test that messages are loaded when a session is selected."""
        # Setup
        mock_store = create_mock_store()
        setup_mock_subprocess(mock_run)
        
        # Setup mock ChatParser
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        
        # Setup mock sessions
        mock_parser.list_logs.return_value = [
            ('session-1', {'modified': '2024-01-01T10:00:00Z'}),
            ('session-2', {'modified': '2024-01-01T09:00:00Z'})
        ]
        
        # Setup mock conversation with messages
        mock_conversation = Mock()
        mock_message1 = Mock()
        mock_message1.role = 'user'
        mock_message1.content = 'Hello, can you help me?'
        
        mock_message2 = Mock()
        mock_message2.role = 'assistant' 
        mock_message2.content = 'Of course! What do you need help with?'
        
        mock_conversation.messages = [mock_message1, mock_message2]
        mock_parser.parse.return_value = mock_conversation
        
        # Create app and test
        app = TigsStoreApp(mock_store)
        
        # Verify sessions were loaded
        assert len(app.log_view.logs) == 2
        assert app.log_view.logs[0][0] == 'session-1'  # Newest first
        
        # Verify messages were loaded for first session
        assert len(app.message_view.messages) == 2
        assert app.message_view.messages[0] == ('user', 'Hello, can you help me?')
        assert app.message_view.messages[1] == ('assistant', 'Of course! What do you need help with?')
        
        # Verify parse was called with correct session ID
        mock_parser.parse.assert_called_once_with('session-1')
    
    @patch('subprocess.run')
    @patch('src.tui.app.ChatParser')
    def test_message_display_lines(self, mock_parser_class, mock_run):
        """Test that messages are formatted correctly for display."""
        # Setup
        mock_store = create_mock_store()
        setup_mock_subprocess(mock_run)
        
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.list_logs.return_value = []
        
        app = TigsStoreApp(mock_store)
        
        # Manually set messages and update items reference
        app.message_view.messages = [
            ('user', 'This is a test message'),
            ('assistant', 'This is a response that is very long and should be truncated when displayed in the pane')
        ]
        app.message_view.items = app.message_view.messages
        
        # Get display lines
        lines = app.message_view.get_display_lines(height=10)
        
        # Verify formatting (new format with cursor and selection indicators)
        # Using the new triangle cursor from indicators
        assert any('User:' in line for line in lines)
        assert any('This is a test message' in line for line in lines)
        assert any('Assistant:' in line for line in lines)
        assert any('...' in line for line in lines)  # Long message should be truncated
    
    @patch('subprocess.run')
    @patch('src.tui.app.ChatParser')
    def test_session_selection_triggers_message_load(self, mock_parser_class, mock_run):
        """Test that changing session selection loads new messages."""
        # Setup
        mock_store = create_mock_store()
        setup_mock_subprocess(mock_run)
        
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        
        # Setup sessions
        mock_parser.list_logs.return_value = [
            ('session-1', {'modified': '2024-01-01T10:00:00Z'}),
            ('session-2', {'modified': '2024-01-01T09:00:00Z'})
        ]
        
        # Setup different messages for each session
        mock_conv1 = Mock()
        mock_msg1 = Mock(role='user', content='Session 1 message')
        mock_conv1.messages = [mock_msg1]
        
        mock_conv2 = Mock()
        mock_msg2 = Mock(role='user', content='Session 2 message')
        mock_conv2.messages = [mock_msg2]
        
        mock_parser.parse.side_effect = [mock_conv1, mock_conv2]
        
        # Create app
        app = TigsStoreApp(mock_store)
        
        # Initial messages should be from session 1
        assert app.message_view.messages[0] == ('user', 'Session 1 message')
        
        # Simulate changing log selection
        app.log_view.selected_log_idx = 1
        log_id = app.log_view.get_selected_log_id()
        app.message_view.load_messages(log_id)
        
        # Messages should now be from session 2
        assert app.message_view.messages[0] == ('user', 'Session 2 message')
        assert mock_parser.parse.call_count == 2
        mock_parser.parse.assert_called_with('session-2')
    
    @patch('subprocess.run')
    @patch('src.tui.app.ChatParser')
    def test_message_selection_operations(self, mock_parser_class, mock_run):
        """Test message selection operations."""
        # Setup
        mock_store = create_mock_store()
        setup_mock_subprocess(mock_run)
        
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.list_logs.return_value = []
        
        app = TigsStoreApp(mock_store)
        
        # Set some messages
        app.message_view.messages = [
            ('user', 'Message 1'),
            ('assistant', 'Message 2'),
            ('user', 'Message 3')
        ]
        app.message_view.items = app.message_view.messages
        
        # Mock stdscr for screen dimensions
        mock_stdscr = Mock()
        mock_stdscr.getmaxyx.return_value = (24, 80)
        pane_height = 10
        
        # Test space key toggles selection
        app.message_view.message_cursor_idx = 0
        app.message_view.cursor_idx = 0
        app.message_view.handle_input(mock_stdscr, ord(' '), pane_height)
        assert 0 in app.message_view.selected_messages
        
        app.message_view.handle_input(mock_stdscr, ord(' '), pane_height)
        assert 0 not in app.message_view.selected_messages
        
        # Test cursor movement
        app.message_view.handle_input(mock_stdscr, curses.KEY_DOWN, pane_height)
        assert app.message_view.message_cursor_idx == 1
        
        # Test clear selection
        app.message_view.selected_messages.update({0, 1, 2})
        app.message_view.handle_input(mock_stdscr, ord('c'), pane_height)
        assert len(app.message_view.selected_messages) == 0
        
        # Test select all
        app.message_view.handle_input(mock_stdscr, ord('a'), pane_height)
        assert len(app.message_view.selected_messages) == 3
    
    @patch('subprocess.run')
    def test_no_cligent_available(self, mock_run):
        """Test app handles missing cligent gracefully."""
        mock_store = create_mock_store()
        setup_mock_subprocess(mock_run)
        
        # Make ChatParser fail
        with patch('src.tui.app.ChatParser', side_effect=Exception("No cligent")):
            app = TigsStoreApp(mock_store)
            
            # Should handle gracefully
            assert app.chat_parser is None
            assert app.log_view.logs == []
            assert app.message_view.messages == []
    
    @patch('subprocess.run')
    @patch('src.tui.app.ChatParser')
    def test_role_enum_conversion(self, mock_parser_class, mock_run):
        """Test that Role enum from cligent is properly converted."""
        from cligent import Role
        
        mock_store = create_mock_store()
        setup_mock_subprocess(mock_run)
        
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        
        # Create messages with Role enum
        mock_conv = Mock()
        mock_msg1 = Mock()
        mock_msg1.role = Role.USER
        mock_msg1.content = 'User message'
        
        mock_msg2 = Mock()
        mock_msg2.role = Role.ASSISTANT
        mock_msg2.content = 'Assistant message'
        
        mock_conv.messages = [mock_msg1, mock_msg2]
        mock_parser.parse.return_value = mock_conv
        mock_parser.list_logs.return_value = [('session-1', {'modified': '2024-01-01T10:00:00Z'})]
        
        app = TigsStoreApp(mock_store)
        
        # Verify Role enum was converted to strings
        assert app.message_view.messages[0] == ('user', 'User message')
        assert app.message_view.messages[1] == ('assistant', 'Assistant message')
    
    @patch('subprocess.run')
    def test_real_cligent_integration(self, mock_run):
        """Test with real cligent if available."""
        mock_store = create_mock_store()
        setup_mock_subprocess(mock_run)
        
        try:
            from cligent import ChatParser
            # Create app with real ChatParser
            app = TigsStoreApp(mock_store)
            
            # If we get here, cligent is available
            if app.chat_parser is not None:
                assert isinstance(app.chat_parser, ChatParser)
        except ImportError:
            pytest.skip("cligent not available")
    
    @patch('subprocess.run')
    @patch('src.tui.app.ChatParser')
    def test_cursor_and_selection_indicators(self, mock_parser_class, mock_run):
        """Test cursor and selection indicators in message display."""
        mock_store = create_mock_store()
        setup_mock_subprocess(mock_run)
        
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.list_logs.return_value = []
        
        app = TigsStoreApp(mock_store)
        
        # Set messages
        app.message_view.messages = [
            ('user', 'Message 1'),
            ('assistant', 'Message 2')
        ]
        app.message_view.items = app.message_view.messages
        app.message_view.message_cursor_idx = 0
        app.message_view.cursor_idx = 0
        app.message_view.selected_messages.add(1)
        app.message_view.selected_items = app.message_view.selected_messages
        
        lines = app.message_view.get_display_lines(height=10)
        
        # Check that we have the expected content
        # With the refactored code, each message takes 2 lines (header + content)
        # Line 0: Cursor + unselected + "User:"
        # Line 1: Message content
        # Line 2: No cursor + selected + "Assistant:"
        # Line 3: Message content
        line_str = '\n'.join(lines)
        assert '▶' in line_str  # Triangle cursor
        assert '[x]' in line_str  # Selected indicator
        assert 'User:' in line_str
        assert 'Assistant:' in line_str
    
    @patch('subprocess.run')
    @patch('src.tui.app.ChatParser')
    def test_visual_mode_display(self, mock_parser_class, mock_run):
        """Test visual mode indicator is displayed."""
        mock_store = create_mock_store()
        setup_mock_subprocess(mock_run)
        
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.list_logs.return_value = []
        
        app = TigsStoreApp(mock_store)
        
        # Set messages and enable visual mode
        app.message_view.messages = [('user', 'Test')]
        app.message_view.items = app.message_view.messages
        app.message_view.visual_mode = True
        
        lines = app.message_view.get_display_lines(height=10)
        
        # Should show visual mode indicator
        assert any('VISUAL' in line for line in lines)