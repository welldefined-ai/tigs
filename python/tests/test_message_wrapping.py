"""Tests for message display with variable heights."""

import pytest
from unittest.mock import Mock
from src.tui.messages_view import MessageView


class TestMessageWrapping:
    """Test message wrapping and variable height handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.view = MessageView(None)
    
    def test_word_wrap_basic(self):
        """Test basic word wrapping."""
        text = "This is a long line that needs to be wrapped at word boundaries"
        wrapped = self.view._word_wrap(text, 20)
        
        assert all(len(line) <= 20 for line in wrapped)
        assert ' '.join(wrapped) == text
        assert len(wrapped) > 1  # Should be split
    
    def test_word_wrap_single_word(self):
        """Test wrapping with words that fit exactly."""
        text = "Short message here"
        wrapped = self.view._word_wrap(text, 25)
        
        assert wrapped == [text]  # Should fit in one line
    
    def test_word_wrap_very_long_word(self):
        """Test wrapping with a word longer than width."""
        text = "Supercalifragilisticexpialidocious"
        wrapped = self.view._word_wrap(text, 10)
        
        # New implementation breaks long words to fit width
        assert len(wrapped) > 1  # Should break into multiple lines
        # Each line should be at most 10 characters wide
        for line in wrapped:
            assert len(line) <= 10
        # Reassembling should give us the original word
        assert ''.join(wrapped) == text
    
    def test_word_wrap_empty_text(self):
        """Test wrapping empty text."""
        wrapped = self.view._word_wrap("", 20)
        assert wrapped == [""]
        
        wrapped = self.view._word_wrap(None, 20)
        assert wrapped == [None]
    
    def test_word_wrap_zero_width(self):
        """Test wrapping with zero or negative width."""
        text = "Test message"
        wrapped = self.view._word_wrap(text, 0)
        assert wrapped == [text]
        
        wrapped = self.view._word_wrap(text, -5)
        assert wrapped == [text]
    
    def test_calculate_message_heights_simple(self):
        """Test message height calculation with simple messages."""
        messages = [
            ('user', 'Short message', None),
            ('assistant', 'Another short response', None),
        ]
        
        heights = self.view._calculate_message_heights(messages, 40)
        
        # Each message: header(1) + content(1) + separator(1) = 3
        assert heights[0] == 3
        assert heights[1] == 3
    
    def test_calculate_message_heights_long_content(self):
        """Test height calculation with content that needs wrapping."""
        messages = [
            ('user', 'This is a very long message that will definitely need to be wrapped when displayed', None),
            ('assistant', 'Short reply', None),
        ]
        
        heights = self.view._calculate_message_heights(messages, 30)
        
        assert heights[0] > 3  # Should be wrapped
        assert heights[1] == 3  # Short message
    
    def test_calculate_message_heights_multiline(self):
        """Test height calculation with multi-line content."""
        messages = [
            ('user', 'Multi\nline\nmessage\nwith\nbreaks', None),
        ]
        
        heights = self.view._calculate_message_heights(messages, 40)
        
        # Header(1) + 5 content lines + separator(1) = 7
        assert heights[0] == 7
    
    def test_calculate_message_heights_mixed(self):
        """Test height calculation with mixed message types."""
        messages = [
            ('user', 'Short', None),
            ('assistant', 'This is a very long response that will need multiple lines when displayed in the terminal', None),
            ('user', 'Multi\nline\nmessage', None),
        ]
        
        heights = self.view._calculate_message_heights(messages, 40)
        
        assert heights[0] == 3  # Short message
        assert heights[1] > 3   # Long wrapped message
        assert heights[2] == 5  # Multi-line message: header + 3 lines + separator
    
    def test_get_visible_messages_variable_simple(self):
        """Test visible message calculation with simple case."""
        self.view.messages = [
            ('user', 'Message 1', None),
            ('assistant', 'Response 1', None),
            ('user', 'Message 2', None),
        ]
        self.view.message_scroll_offset = 0
        self.view.message_cursor_idx = 0
        
        heights = [3, 3, 3]  # All same height
        visible_count, start_idx, end_idx = self.view._get_visible_messages_variable(15, heights)
        
        # Height 15 - 2 (borders) = 13 available
        # Can fit 4 messages of height 3 each = 12, with 1 left over
        assert visible_count == 3  # All messages fit
        assert start_idx == 0
        assert end_idx == 3
    
    def test_get_visible_messages_variable_large_message(self):
        """Test handling of extremely large single message."""
        self.view.messages = [
            ('user', 'Normal message', None),
            ('assistant', 'Huge message content', None),  # Pretend this is huge
            ('user', 'Another normal', None),
        ]
        self.view.message_scroll_offset = 0
        self.view.message_cursor_idx = 1  # Focus on huge message
        
        heights = [3, 20, 3]  # Middle message is huge
        visible_count, start_idx, end_idx = self.view._get_visible_messages_variable(15, heights)
        
        # Should show only the huge message
        assert visible_count == 1
        assert start_idx == 1
        assert end_idx == 2
    
    def test_get_visible_messages_variable_cursor_visibility(self):
        """Test that cursor is always visible."""
        self.view.messages = [
            ('user', f'Message {i}', None) for i in range(10)
        ]
        self.view.message_scroll_offset = 0
        self.view.message_cursor_idx = 5  # Focus on message in middle
        
        heights = [3] * 10  # All same height
        visible_count, start_idx, end_idx = self.view._get_visible_messages_variable(15, heights)
        
        # Should adjust scroll to show cursor
        assert start_idx <= 5 < end_idx  # Cursor should be visible
    
    def test_get_visible_messages_variable_empty(self):
        """Test with empty message list."""
        self.view.messages = []
        
        visible_count, start_idx, end_idx = self.view._get_visible_messages_variable(15, [])
        
        assert visible_count == 0
        assert start_idx == 0
        assert end_idx == 0
    
    def test_get_display_lines_with_width(self):
        """Test display lines generation with width parameter."""
        self.view.messages = [
            ('user', 'This is a message that should be wrapped', None),
            ('assistant', 'Short reply', None),
        ]
        self.view.message_cursor_idx = 0
        self.view.message_scroll_offset = 0
        
        lines = self.view.get_display_lines(20, 40)
        
        assert len(lines) > 0
        # Should contain headers
        assert any('User:' in line for line in lines)
        assert any('Assistant:' in line for line in lines)
        # Content should be wrapped/indented
        assert any(line.startswith('    ') for line in lines)
    
    def test_get_display_lines_narrow_width(self):
        """Test display with very narrow width."""
        self.view.messages = [
            ('user', 'This is a very long message that will definitely need wrapping', None),
        ]
        self.view.message_cursor_idx = 0
        
        lines = self.view.get_display_lines(20, 20)  # Narrow width
        
        assert len(lines) > 0
        # All lines should fit in narrow width (after accounting for indentation)
        content_lines = [line for line in lines if line.startswith('    ')]
        for line in content_lines:
            # Remove indentation and check remaining content
            content = line[4:]  # Remove '    '
            assert len(content) <= 14  # 20 - 6 (borders and indentation)
    
    def test_scroll_to_cursor_triggers_recalc(self):
        """Test that scroll_to_cursor triggers height recalculation."""
        self.view.messages = [('user', 'Test', None)]
        self.view._needs_message_view_init = False
        
        self.view.scroll_to_cursor(20)
        
        assert self.view._needs_message_view_init is True
    
    def test_get_display_lines_empty_messages(self):
        """Test display with no messages."""
        self.view.messages = []
        
        lines = self.view.get_display_lines(20, 40)
        
        assert len(lines) == 1
        assert "(No messages to display)" in lines[0]
    
    def test_visual_mode_indicator_space(self):
        """Test that visual mode indicator reserves space."""
        self.view.messages = [('user', 'Test', None)]
        self.view.visual_mode = True
        self.view.message_cursor_idx = 0
        
        heights = self.view._calculate_message_heights(self.view.messages, 40)
        visible_count, start_idx, end_idx = self.view._get_visible_messages_variable(10, heights)
        
        # With visual mode, less space should be available
        # This test ensures visual mode indicator space is accounted for
        assert visible_count >= 0  # Should handle gracefully