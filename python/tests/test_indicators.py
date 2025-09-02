"""Tests for selection indicators."""

import pytest
from src.tui.indicators import SelectionIndicators


class TestSelectionIndicators:
    """Test the SelectionIndicators class."""
    
    def test_selection_box_constants(self):
        """Test that selection box constants are defined correctly."""
        assert SelectionIndicators.SELECTED == "[x]"
        assert SelectionIndicators.UNSELECTED == "[ ]"
    
    def test_cursor_constants(self):
        """Test that cursor constants are defined correctly."""
        assert SelectionIndicators.CURSOR_ARROW == ">"
        assert SelectionIndicators.CURSOR_TRIANGLE == "▶"
        assert SelectionIndicators.CURSOR_BULLET == "•"
        assert SelectionIndicators.CURSOR_NONE == " "
    
    def test_visual_mode_constant(self):
        """Test visual mode indicator constant."""
        assert SelectionIndicators.VISUAL_MODE == "-- VISUAL --"
    
    def test_format_selection_box_selected(self):
        """Test formatting selected checkbox."""
        result = SelectionIndicators.format_selection_box(True)
        assert result == "[x]"
    
    def test_format_selection_box_unselected(self):
        """Test formatting unselected checkbox."""
        result = SelectionIndicators.format_selection_box(False)
        assert result == "[ ]"
    
    def test_format_cursor_arrow_style(self):
        """Test formatting cursor with arrow style."""
        # With cursor
        result = SelectionIndicators.format_cursor(True, style="arrow")
        assert result == ">"
        
        # Without cursor
        result = SelectionIndicators.format_cursor(False, style="arrow")
        assert result == " "
    
    def test_format_cursor_triangle_style(self):
        """Test formatting cursor with triangle style."""
        # With cursor
        result = SelectionIndicators.format_cursor(True, style="triangle")
        assert result == "▶"
        
        # Without cursor
        result = SelectionIndicators.format_cursor(False, style="triangle")
        assert result == " "
    
    def test_format_cursor_bullet_style(self):
        """Test formatting cursor with bullet style."""
        # With cursor
        result = SelectionIndicators.format_cursor(True, style="bullet")
        assert result == "•"
        
        # Without cursor
        result = SelectionIndicators.format_cursor(False, style="bullet")
        assert result == " "
    
    def test_format_cursor_no_padding(self):
        """Test formatting cursor without padding."""
        # Without cursor and no padding
        result = SelectionIndicators.format_cursor(False, style="arrow", pad=False)
        assert result == ""
        
        # With cursor (padding doesn't affect this)
        result = SelectionIndicators.format_cursor(True, style="arrow", pad=False)
        assert result == ">"
    
    def test_format_cursor_invalid_style(self):
        """Test formatting cursor with invalid style falls back to arrow."""
        result = SelectionIndicators.format_cursor(True, style="invalid")
        assert result == ">"
    
    def test_format_list_item_with_selection(self):
        """Test formatting complete list item with selection."""
        result = SelectionIndicators.format_list_item(
            index=2,
            cursor_idx=2,
            is_selected=True,
            text="Test Item",
            cursor_style="arrow",
            show_selection=True
        )
        assert result == ">[x] Test Item"
    
    def test_format_list_item_without_cursor(self):
        """Test formatting list item without cursor."""
        result = SelectionIndicators.format_list_item(
            index=1,
            cursor_idx=2,
            is_selected=False,
            text="Test Item",
            cursor_style="arrow",
            show_selection=True
        )
        assert result == " [ ] Test Item"
    
    def test_format_list_item_no_selection_box(self):
        """Test formatting list item without selection box."""
        result = SelectionIndicators.format_list_item(
            index=0,
            cursor_idx=0,
            is_selected=True,  # Ignored when show_selection=False
            text="Test Item",
            cursor_style="bullet",
            show_selection=False
        )
        assert result == "• Test Item"
    
    def test_format_list_item_different_cursor_styles(self):
        """Test formatting list item with different cursor styles."""
        # Triangle cursor
        result = SelectionIndicators.format_list_item(
            index=0,
            cursor_idx=0,
            is_selected=False,
            text="Item",
            cursor_style="triangle",
            show_selection=True
        )
        assert result == "▶[ ] Item"
        
        # Bullet cursor
        result = SelectionIndicators.format_list_item(
            index=0,
            cursor_idx=0,
            is_selected=True,
            text="Item",
            cursor_style="bullet",
            show_selection=True
        )
        assert result == "•[x] Item"