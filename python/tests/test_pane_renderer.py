"""Unit tests for PaneRenderer class."""

import pytest
from unittest.mock import MagicMock, patch

from src.tui.pane_renderer import PaneRenderer


class TestPaneRenderer:
    """Test the PaneRenderer class."""
    
    @patch('src.tui.pane_renderer.curses')
    def test_draw_pane_with_focus(self, mock_curses):
        """Test that focused panes have bold borders and title but not content."""
        mock_stdscr = MagicMock()
        
        # Mock curses attributes
        mock_curses.A_BOLD = 1
        mock_curses.color_pair = lambda x: x
        mock_curses.ACS_ULCORNER = ord('+')
        mock_curses.ACS_URCORNER = ord('+')
        mock_curses.ACS_LLCORNER = ord('+')
        mock_curses.ACS_LRCORNER = ord('+')
        mock_curses.ACS_HLINE = ord('-')
        mock_curses.ACS_VLINE = ord('|')
        mock_curses.error = Exception
        
        content = ["Line 1", "Line 2", "Line 3"]
        PaneRenderer.draw_pane(
            mock_stdscr, 0, 0, 10, 20, 
            "Test", True, content, True
        )
        
        # Check that bold was turned on for borders
        mock_stdscr.attron.assert_any_call(1)  # A_BOLD
        
        # Check that bold was turned off before content
        mock_stdscr.attroff.assert_any_call(1)  # A_BOLD
        
        # Check that content lines were drawn without bold
        mock_stdscr.addstr.assert_any_call(1, 2, "Line 1")
        mock_stdscr.addstr.assert_any_call(2, 2, "Line 2")
        mock_stdscr.addstr.assert_any_call(3, 2, "Line 3")
    
    @patch('src.tui.pane_renderer.curses')
    def test_draw_pane_without_focus(self, mock_curses):
        """Test that unfocused panes don't have bold."""
        mock_stdscr = MagicMock()
        
        # Mock curses attributes
        mock_curses.A_BOLD = 1
        mock_curses.color_pair = lambda x: x
        mock_curses.ACS_ULCORNER = ord('+')
        mock_curses.ACS_URCORNER = ord('+')
        mock_curses.ACS_LLCORNER = ord('+')
        mock_curses.ACS_LRCORNER = ord('+')
        mock_curses.ACS_HLINE = ord('-')
        mock_curses.ACS_VLINE = ord('|')
        mock_curses.error = Exception
        
        content = ["Line 1"]
        PaneRenderer.draw_pane(
            mock_stdscr, 0, 0, 10, 20, 
            "Test", False, content, True
        )
        
        # Check that bold was NOT turned on
        # For unfocused, we don't use bold
        bold_calls = [call for call in mock_stdscr.attron.call_args_list 
                      if call[0][0] == 1]  # A_BOLD = 1
        assert len(bold_calls) == 0, "Bold should not be used for unfocused panes"
    
    @patch('src.tui.pane_renderer.curses')
    def test_multi_colored_content(self, mock_curses):
        """Test that multi-colored content (list of tuples) is handled correctly."""
        mock_stdscr = MagicMock()
        
        # Mock curses attributes
        mock_curses.color_pair = lambda x: x
        mock_curses.ACS_ULCORNER = ord('+')
        mock_curses.ACS_URCORNER = ord('+')
        mock_curses.ACS_LLCORNER = ord('+')
        mock_curses.ACS_LRCORNER = ord('+')
        mock_curses.ACS_HLINE = ord('-')
        mock_curses.ACS_VLINE = ord('|')
        mock_curses.error = Exception
        
        # Multi-colored line: blue filename, separator, green +
        content = [[("file.txt", 7), (" | ", 0), ("+10", 3)]]
        PaneRenderer.draw_pane(
            mock_stdscr, 0, 0, 10, 30, 
            "Test", False, content, True
        )
        
        # Check that each part was drawn with correct color
        mock_stdscr.attron.assert_any_call(7)  # Blue for filename
        mock_stdscr.attron.assert_any_call(3)  # Green for +10
        
        # Check that all parts were drawn (positions calculated dynamically)
        addstr_calls = mock_stdscr.addstr.call_args_list
        content_drawn = False
        for call in addstr_calls:
            if len(call[0]) == 3 and call[0][0] == 1:  # Row 1
                if call[0][2] == "file.txt":
                    content_drawn = True
                    break
        assert content_drawn, "Multi-colored content should be drawn"
    
    @patch('src.tui.pane_renderer.curses')
    def test_single_colored_content(self, mock_curses):
        """Test that single-colored content (tuple) is handled correctly."""
        mock_stdscr = MagicMock()
        
        # Mock curses attributes
        mock_curses.color_pair = lambda x: x
        mock_curses.ACS_ULCORNER = ord('+')
        mock_curses.ACS_URCORNER = ord('+')
        mock_curses.ACS_LLCORNER = ord('+')
        mock_curses.ACS_LRCORNER = ord('+')
        mock_curses.ACS_HLINE = ord('-')
        mock_curses.ACS_VLINE = ord('|')
        mock_curses.error = Exception
        
        # Single-colored line
        content = [("Colored text", 4)]
        PaneRenderer.draw_pane(
            mock_stdscr, 0, 0, 10, 30, 
            "Test", False, content, True
        )
        
        # Check that color was applied
        mock_stdscr.attron.assert_any_call(4)
        mock_stdscr.addstr.assert_any_call(1, 2, "Colored text")
    
    @patch('src.tui.pane_renderer.curses')
    def test_plain_string_content(self, mock_curses):
        """Test that plain string content is handled correctly."""
        mock_stdscr = MagicMock()
        
        # Mock curses attributes
        mock_curses.ACS_ULCORNER = ord('+')
        mock_curses.ACS_URCORNER = ord('+')
        mock_curses.ACS_LLCORNER = ord('+')
        mock_curses.ACS_LRCORNER = ord('+')
        mock_curses.ACS_HLINE = ord('-')
        mock_curses.ACS_VLINE = ord('|')
        mock_curses.error = Exception
        
        content = ["Plain text"]
        PaneRenderer.draw_pane(
            mock_stdscr, 0, 0, 10, 30, 
            "Test", False, content, False
        )
        
        # Check that plain text was drawn
        mock_stdscr.addstr.assert_any_call(1, 2, "Plain text")
    
    @patch('src.tui.pane_renderer.curses')
    def test_truncate_long_lines(self, mock_curses):
        """Test that long lines are truncated to fit pane width."""
        mock_stdscr = MagicMock()
        
        # Mock curses attributes
        mock_curses.ACS_ULCORNER = ord('+')
        mock_curses.ACS_URCORNER = ord('+')
        mock_curses.ACS_LLCORNER = ord('+')
        mock_curses.ACS_LRCORNER = ord('+')
        mock_curses.ACS_HLINE = ord('-')
        mock_curses.ACS_VLINE = ord('|')
        mock_curses.error = Exception
        
        # Very long line that should be truncated
        content = ["This is a very long line that should be truncated"]
        PaneRenderer.draw_pane(
            mock_stdscr, 0, 0, 5, 15,  # Small pane width
            "Test", False, content, False
        )
        
        # Check that line was truncated (max_width = 15 - 4 = 11)
        mock_stdscr.addstr.assert_any_call(1, 2, "This is a v")
    
    @patch('src.tui.pane_renderer.curses')
    def test_focus_with_colors(self, mock_curses):
        """Test that focused pane uses color for borders when colors are enabled."""
        mock_stdscr = MagicMock()
        
        # Mock curses attributes
        mock_curses.A_BOLD = 1
        mock_curses.color_pair = lambda x: x
        mock_curses.ACS_ULCORNER = ord('+')
        mock_curses.ACS_URCORNER = ord('+')
        mock_curses.ACS_LLCORNER = ord('+')
        mock_curses.ACS_LRCORNER = ord('+')
        mock_curses.ACS_HLINE = ord('-')
        mock_curses.ACS_VLINE = ord('|')
        mock_curses.error = Exception
        
        content = ["Test content"]
        PaneRenderer.draw_pane(
            mock_stdscr, 0, 0, 10, 20, 
            "Test", True, content, True  # focused and colors enabled
        )
        
        # Check that color pair 2 (cyan) was used for focused borders
        mock_stdscr.attron.assert_any_call(2)  # color_pair(2)
        mock_stdscr.attron.assert_any_call(1)  # A_BOLD
        
        # Check that both were turned off
        mock_stdscr.attroff.assert_any_call(1)  # A_BOLD
        mock_stdscr.attroff.assert_any_call(2)  # color_pair(2)