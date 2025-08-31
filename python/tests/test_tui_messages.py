"""Tests for TUI message view functionality."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.tui.app import TigsStoreApp


class TestMessageView:
    """Test message display functionality in the TUI."""
    
    @patch('src.tui.app.CLIGENT_AVAILABLE', True)
    @patch('src.tui.app.ChatParser')
    def test_load_messages_basic(self, mock_parser_class):
        """Test that messages are loaded when a session is selected."""
        # Setup mock store
        mock_store = Mock()
        
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
        assert len(app.sessions) == 2
        assert app.sessions[0][0] == 'session-1'  # Newest first
        
        # Verify messages were loaded for first session
        assert len(app.messages) == 2
        assert app.messages[0] == ('user', 'Hello, can you help me?')
        assert app.messages[1] == ('assistant', 'Of course! What do you need help with?')
        
        # Verify parse was called with correct session ID
        mock_parser.parse.assert_called_once_with('session-1')
    
    @patch('src.tui.app.CLIGENT_AVAILABLE', True)
    @patch('src.tui.app.ChatParser')
    def test_message_display_lines(self, mock_parser_class):
        """Test that messages are formatted correctly for display."""
        # Setup
        mock_store = Mock()
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.list_logs.return_value = []
        
        app = TigsStoreApp(mock_store)
        
        # Manually set messages
        app.messages = [
            ('user', 'This is a test message'),
            ('assistant', 'This is a response that is very long and should be truncated when displayed in the pane')
        ]
        
        # Get display lines
        lines = app._get_message_display_lines(height=10)
        
        # Verify formatting
        assert '[1] User:' in lines[0]
        assert 'This is a test message' in lines[1]
        assert '[2] Assistant:' in lines[2]
        assert '...' in lines[3]  # Long message should be truncated
    
    @patch('src.tui.app.CLIGENT_AVAILABLE', True)
    @patch('src.tui.app.ChatParser')
    def test_session_selection_triggers_message_load(self, mock_parser_class):
        """Test that changing session selection loads new messages."""
        # Setup
        mock_store = Mock()
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
        assert app.messages[0] == ('user', 'Session 1 message')
        
        # Change selection
        app.selected_session_idx = 1
        app._load_messages()
        
        # Messages should now be from session 2
        assert app.messages[0] == ('user', 'Session 2 message')
        assert mock_parser.parse.call_count == 2
        mock_parser.parse.assert_called_with('session-2')
    
    @patch('src.tui.app.CLIGENT_AVAILABLE', True)
    @patch('src.tui.app.ChatParser')
    def test_message_selection_operations(self, mock_parser_class):
        """Test message selection operations."""
        # Setup
        mock_store = Mock()
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        mock_parser.list_logs.return_value = []
        
        app = TigsStoreApp(mock_store)
        
        # Set some messages
        app.messages = [
            ('user', 'Message 1'),
            ('assistant', 'Message 2'),
            ('user', 'Message 3')
        ]
        
        # Mock stdscr for screen dimensions
        mock_stdscr = Mock()
        mock_stdscr.getmaxyx.return_value = (24, 80)
        
        # Test space key toggles selection
        app.message_scroll_offset = 0
        app._handle_message_input(mock_stdscr, ord(' '))
        assert 0 in app.selected_messages
        
        app._handle_message_input(mock_stdscr, ord(' '))
        assert 0 not in app.selected_messages
        
        # Test clear selections
        app.selected_messages.add(0)
        app.selected_messages.add(1)
        app._handle_message_input(mock_stdscr, ord('c'))
        assert len(app.selected_messages) == 0
        
        # Test select all visible
        app._handle_message_input(mock_stdscr, ord('a'))
        assert len(app.selected_messages) > 0
    
    @patch('src.tui.app.CLIGENT_AVAILABLE', False)
    def test_no_cligent_available(self):
        """Test app handles missing cligent gracefully."""
        mock_store = Mock()
        app = TigsStoreApp(mock_store)
        
        assert app.chat_parser is None
        assert app.messages == []
        assert app.sessions == []
        
        # Should not crash when getting display lines
        lines = app._get_message_display_lines(height=10)
        assert '(No messages to display)' in lines[0]
    
    def test_role_enum_conversion(self):
        """Test conversion of Role enums to strings."""
        mock_store = Mock()
        
        with patch('src.tui.app.CLIGENT_AVAILABLE', True), \
             patch('src.tui.app.ChatParser') as mock_parser_class:
            
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            mock_parser.list_logs.return_value = [
                ('session-1', {'modified': '2024-01-01T10:00:00Z'})
            ]
            
            # Test with Role enum (like Role.USER)
            mock_conv = Mock()
            mock_msg1 = Mock()
            mock_msg1.role = Mock()
            mock_msg1.role.__str__ = Mock(return_value='Role.USER')
            mock_msg1.content = 'Test content'
            
            # Test with Role enum (like Role.ASSISTANT)
            mock_msg2 = Mock()
            mock_msg2.role = Mock()
            mock_msg2.role.__str__ = Mock(return_value='Role.ASSISTANT')
            mock_msg2.content = 'Assistant response'
            
            mock_conv.messages = [mock_msg1, mock_msg2]
            mock_parser.parse.return_value = mock_conv
            
            app = TigsStoreApp(mock_store)
            
            assert app.messages[0] == ('user', 'Test content')
            assert app.messages[1] == ('assistant', 'Assistant response')
    
    def test_real_cligent_integration(self):
        """Test with real cligent if available in current directory."""
        try:
            from cligent import ChatParser
            
            # Test if we can find real sessions in current directory
            cp = ChatParser('claude-code')
            logs = cp.list_logs()
            
            if logs:
                # We have real data - test the full integration
                mock_store = Mock()
                app = TigsStoreApp(mock_store)
                
                # Should have loaded real sessions and messages
                assert len(app.sessions) > 0, "Should find real sessions"
                assert len(app.messages) > 0, "Should load real messages"
                
                # Test display generation
                lines = app._get_message_display_lines(height=20)
                assert len(lines) > 0, "Should generate display lines"
                
                # Verify message format
                for role, content in app.messages:
                    assert role in ['user', 'assistant', 'system']
                    assert isinstance(content, str)
                    assert len(content) > 0
            else:
                pytest.skip("No Claude Code sessions found in current directory")
                
        except ImportError:
            pytest.skip("cligent not available")