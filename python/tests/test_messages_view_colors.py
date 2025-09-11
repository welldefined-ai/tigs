"""Tests for message view coloring with role-based colors."""

import pytest
from unittest.mock import Mock
from datetime import datetime

from src.tui.messages_view import MessageView
from src.tui.color_constants import (
    COLOR_DEFAULT, COLOR_CYAN, COLOR_YELLOW, COLOR_METADATA,
    get_role_color
)


class TestMessagesViewColors:
    """Test color assignment in messages view."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_parser = Mock()
        self.view = MessageView(self.mock_parser)
        
        # Sample messages with different roles
        self.view.messages = [
            ('user', 'How do I implement this feature?', datetime(2025, 9, 10, 14, 30)),
            ('assistant', 'Here is how you can implement it:\n1. First step\n2. Second step', datetime(2025, 9, 10, 14, 31)),
            ('system', 'System notification: Build completed', datetime(2025, 9, 10, 14, 32)),
            ('user', 'Thanks!', None),  # Message without timestamp
        ]
        self.view._needs_message_view_init = False
    
    def test_colors_enabled_returns_colored_tuples(self):
        """Test that colors_enabled=True returns list of color tuples."""
        lines = self.view.get_display_lines(height=30, width=60, colors_enabled=True)
        
        # Should return list of color tuple lists
        assert len(lines) > 0
        for line in lines:
            if line:  # Skip empty string separators
                if isinstance(line, list):
                    for part in line:
                        assert isinstance(part, tuple), f"Expected tuple, got {type(part)}: {part}"
                        assert len(part) == 2, f"Expected (text, color) tuple: {part}"
                        text, color = part
                        assert isinstance(text, str)
                        assert isinstance(color, int)
                        assert 0 <= color <= 7, f"Invalid color code: {color}"
    
    def test_colors_disabled_returns_strings(self):
        """Test that colors_enabled=False returns plain strings."""
        lines = self.view.get_display_lines(height=30, width=60, colors_enabled=False)
        
        # Should return list of strings
        assert len(lines) > 0
        for line in lines:
            assert isinstance(line, str), f"Expected string, got {type(line)}: {line}"
    
    def test_user_role_default_color(self):
        """Test that User role has default color."""
        lines = self.view.get_display_lines(height=30, width=60, colors_enabled=True)
        
        # Find user message headers
        for line in lines:
            if isinstance(line, list):
                text_combined = "".join(t for t, _ in line)
                if "User" in text_combined and ":" in text_combined:
                    # Check User label color
                    for text, color in line:
                        if text == "User":
                            assert color == COLOR_DEFAULT, f"User role should be default color"
                            break
    
    def test_assistant_role_cyan_color(self):
        """Test that Assistant role has cyan color."""
        lines = self.view.get_display_lines(height=30, width=60, colors_enabled=True)
        
        # Find assistant message headers
        found = False
        for line in lines:
            if isinstance(line, list):
                text_combined = "".join(t for t, _ in line)
                if "Assistant" in text_combined and ":" in text_combined:
                    # Check Assistant label color
                    for text, color in line:
                        if text == "Assistant":
                            found = True
                            assert color == COLOR_CYAN, f"Assistant role should be cyan, got {color}"
                            break
        assert found, "Assistant message not found"
    
    def test_system_role_yellow_color(self):
        """Test that System role has yellow color."""
        lines = self.view.get_display_lines(height=30, width=60, colors_enabled=True)
        
        # Find system message headers
        found = False
        for line in lines:
            if isinstance(line, list):
                text_combined = "".join(t for t, _ in line)
                if "System" in text_combined and ":" in text_combined:
                    # Check System label color
                    for text, color in line:
                        if text == "System":
                            found = True
                            assert color == COLOR_YELLOW, f"System role should be yellow, got {color}"
                            break
        assert found, "System message not found"
    
    def test_timestamp_blue_color(self):
        """Test that timestamps are colored blue."""
        lines = self.view.get_display_lines(height=30, width=60, colors_enabled=True)
        
        # Find lines with timestamps
        timestamp_found = False
        for line in lines:
            if isinstance(line, list):
                for text, color in line:
                    # Look for timestamp pattern like " 09-10 14:30"
                    if " 09-10 " in text or " 14:3" in text:
                        assert color == COLOR_METADATA, f"Timestamp should be blue: '{text}'"
                        timestamp_found = True
        
        assert timestamp_found, "No timestamps found in output"
    
    def test_message_content_default_color(self):
        """Test that message content has default color."""
        lines = self.view.get_display_lines(height=30, width=60, colors_enabled=True)
        
        # Find content lines
        content_found = False
        for line in lines:
            if isinstance(line, list):
                text_combined = "".join(t for t, _ in line)
                # Content lines are indented
                if text_combined.startswith("    ") and text_combined.strip():
                    content_found = True
                    # Check content has default color
                    for text, color in line:
                        if text.strip() and not text.isspace():
                            assert color == COLOR_DEFAULT, f"Content should be default: '{text}'"
        
        assert content_found, "No content lines found"
    
    def test_multiline_message_coloring(self):
        """Test that multi-line messages maintain consistent colors."""
        lines = self.view.get_display_lines(height=30, width=60, colors_enabled=True)
        
        # Find the multi-line assistant message
        found_multiline = False
        for i, line in enumerate(lines):
            if isinstance(line, list):
                text = "".join(t for t, _ in line)
                if "First step" in text:
                    found_multiline = True
                    # This and next line should have consistent coloring
                    for part_text, part_color in line:
                        if part_text.strip():
                            assert part_color == COLOR_DEFAULT
                    
                    # Check next line (Second step)
                    if i + 1 < len(lines) and isinstance(lines[i+1], list):
                        next_text = "".join(t for t, _ in lines[i+1])
                        if "Second step" in next_text:
                            for part_text, part_color in lines[i+1]:
                                if part_text.strip():
                                    assert part_color == COLOR_DEFAULT
        
        assert found_multiline, "Multi-line message not found"
    
    def test_selection_indicators_default_color(self):
        """Test that selection indicators have default color."""
        lines = self.view.get_display_lines(height=30, width=60, colors_enabled=True)
        
        # Check for selection indicators in headers
        for line in lines:
            if isinstance(line, list) and line:
                first_part = line[0]
                text, color = first_part
                # Selection indicators like "[ ]" or ">  "
                if "[ ]" in text or "[x]" in text or ">" in text:
                    assert color == COLOR_DEFAULT, f"Selection indicator should be default: '{text}'"
    
    def test_empty_messages_colored(self):
        """Test that empty messages display is properly colored."""
        self.view.messages = []
        lines = self.view.get_display_lines(height=30, width=60, colors_enabled=True)
        
        assert len(lines) == 1
        assert isinstance(lines[0], list)
        assert lines[0][0] == ("(No messages to display)", COLOR_DEFAULT)
    
    def test_message_without_timestamp(self):
        """Test that messages without timestamps are handled correctly."""
        lines = self.view.get_display_lines(height=30, width=60, colors_enabled=True)
        
        # Find the "Thanks!" message which has no timestamp
        thanks_found = False
        for line in lines:
            if isinstance(line, list):
                text = "".join(t for t, _ in line)
                if "Thanks!" in text:
                    thanks_found = True
                    # Should still be properly colored
                    for part_text, part_color in line:
                        if "Thanks!" in part_text:
                            assert part_color == COLOR_DEFAULT
        
        assert thanks_found, "Message without timestamp not found"
    
    def test_visual_mode_indicator_colored(self):
        """Test that visual mode indicator has default color."""
        self.view.visual_mode = True
        lines = self.view.get_display_lines(height=30, width=60, colors_enabled=True)
        
        # Find visual mode indicator
        if len(lines) >= 2:
            # Check last lines for visual mode
            for line in lines[-2:]:
                if isinstance(line, list):
                    text = "".join(t for t, _ in line)
                    if "VISUAL" in text:
                        for part_text, part_color in line:
                            assert part_color == COLOR_DEFAULT
    
    def test_wrapped_content_maintains_color(self):
        """Test that wrapped message content maintains consistent color."""
        # Add a very long message
        self.view.messages.append((
            'assistant',
            'This is a very long message that will definitely wrap to multiple lines when displayed in a narrow width. It contains lots of text to ensure wrapping happens.',
            datetime(2025, 9, 10, 15, 0)
        ))
        
        # Use narrow width to force wrapping
        lines = self.view.get_display_lines(height=30, width=30, colors_enabled=True)
        
        # Find wrapped content lines
        wrapped_count = 0
        for line in lines:
            if isinstance(line, list):
                text = "".join(t for t, _ in line)
                # Look for any part of the long message content
                if text.startswith("    ") and ("long message" in text.lower() or "wrap" in text.lower() or "displayed" in text.lower()):
                    wrapped_count += 1
                    # All content should have default color
                    for part_text, part_color in line:
                        if part_text.strip():
                            assert part_color == COLOR_DEFAULT
        
        # Should have at least some wrapped lines
        assert wrapped_count > 0, f"No wrapped lines found. Lines: {[(''.join(t for t, _ in line) if isinstance(line, list) else line) for line in lines]}"
    
    def test_separator_lines_colored(self):
        """Test that separator lines between messages are properly handled."""
        lines = self.view.get_display_lines(height=30, width=60, colors_enabled=True)
        
        # Find empty separator lines
        empty_found = False
        for line in lines:
            if isinstance(line, list):
                if len(line) == 1 and line[0] == ("", COLOR_DEFAULT):
                    empty_found = True
                    break
        
        assert empty_found, "No separator lines found between messages"
    
    def test_role_color_helper_function(self):
        """Test the get_role_color helper function."""
        assert get_role_color('user') == COLOR_DEFAULT
        assert get_role_color('User') == COLOR_DEFAULT  # Case insensitive
        assert get_role_color('assistant') == COLOR_CYAN
        assert get_role_color('Assistant') == COLOR_CYAN
        assert get_role_color('system') == COLOR_YELLOW
        assert get_role_color('System') == COLOR_YELLOW
        assert get_role_color('unknown') == COLOR_DEFAULT  # Unknown roles default
    
    def test_color_consistency_across_width_changes(self):
        """Test that colors remain consistent when width changes."""
        # Get colors at different widths
        lines_wide = self.view.get_display_lines(height=30, width=80, colors_enabled=True)
        lines_narrow = self.view.get_display_lines(height=30, width=30, colors_enabled=True)
        
        # Both should have colored output
        for line in lines_wide:
            if line:  # Skip empty
                assert isinstance(line, list) or line == ""
        
        for line in lines_narrow:
            if line:  # Skip empty
                assert isinstance(line, list) or line == ""
        
        # Find Assistant role in both
        assistant_colors_wide = []
        assistant_colors_narrow = []
        
        for line in lines_wide:
            if isinstance(line, list):
                for text, color in line:
                    if text == "Assistant":
                        assistant_colors_wide.append(color)
        
        for line in lines_narrow:
            if isinstance(line, list):
                for text, color in line:
                    if text == "Assistant":
                        assistant_colors_narrow.append(color)
        
        # Assistant should be cyan in both
        assert all(c == COLOR_CYAN for c in assistant_colors_wide)
        assert all(c == COLOR_CYAN for c in assistant_colors_narrow)