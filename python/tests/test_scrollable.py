"""Tests for scrollable mixin functionality."""

import pytest
from src.tui.scrollable import ScrollableMixin


class TestScrollableMixin:
    """Test the ScrollableMixin class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Create a test class that uses the mixin
        class TestView(ScrollableMixin):
            def __init__(self):
                super().__init__()
                self.items = ['item1', 'item2', 'item3', 'item4', 'item5', 
                             'item6', 'item7', 'item8', 'item9', 'item10']
                self.cursor_idx = 0
        
        self.view = TestView()
    
    def test_initialization(self):
        """Test that mixin initializes correctly."""
        assert self.view.scroll_offset == 0
    
    def test_get_visible_range_small_viewport(self):
        """Test visible range calculation with small viewport."""
        # Viewport height of 5, minus 2 for borders = 3 visible items
        visible_count, start_idx, end_idx = self.view.get_visible_range(5, 2)
        
        assert visible_count == 3
        assert start_idx == 0
        assert end_idx == 3
    
    def test_get_visible_range_large_viewport(self):
        """Test visible range when viewport is larger than items."""
        # Viewport height of 20, minus 2 for borders = 18 visible items
        # But we only have 10 items
        visible_count, start_idx, end_idx = self.view.get_visible_range(20, 2)
        
        assert visible_count == 10
        assert start_idx == 0
        assert end_idx == 10
    
    def test_scroll_with_cursor_movement(self):
        """Test that scroll offset adjusts with cursor movement."""
        # Small viewport (3 visible items)
        self.view.cursor_idx = 5
        visible_count, start_idx, end_idx = self.view.get_visible_range(5, 2)
        
        # Should scroll to show cursor
        assert self.view.scroll_offset == 3  # Cursor at 5, visible 3 items
        assert start_idx == 3
        assert end_idx == 6
    
    def test_scroll_up_with_cursor(self):
        """Test scrolling up when cursor moves up."""
        # Start with cursor at bottom
        self.view.cursor_idx = 8
        self.view.get_visible_range(5, 2)  # 3 visible items
        
        # Move cursor up
        self.view.cursor_idx = 1
        visible_count, start_idx, end_idx = self.view.get_visible_range(5, 2)
        
        # Should scroll up to show cursor
        assert self.view.scroll_offset == 1
        assert start_idx == 1
        assert end_idx == 4
    
    def test_reset_scroll(self):
        """Test resetting scroll to top."""
        self.view.scroll_offset = 5
        self.view.reset_scroll()
        
        assert self.view.scroll_offset == 0
    
    def test_scroll_to_cursor(self):
        """Test scrolling to make cursor visible."""
        self.view.cursor_idx = 7
        self.view.scroll_to_cursor(5, 2)  # 3 visible items
        
        # Cursor at 7, need to scroll to show it
        assert self.view.scroll_offset == 5  # Shows items 5, 6, 7
    
    def test_scroll_to_bottom(self):
        """Test scrolling to bottom of list."""
        self.view.scroll_to_bottom(5, 2)  # 3 visible items
        
        # Should show last 3 items (7, 8, 9)
        assert self.view.scroll_offset == 7
        assert self.view.cursor_idx == 9  # Cursor at last item
    
    def test_empty_items_list(self):
        """Test behavior with empty items list."""
        self.view.items = []
        visible_count, start_idx, end_idx = self.view.get_visible_range(5, 2)
        
        assert visible_count == 0
        assert start_idx == 0
        assert end_idx == 0
    
    def test_single_item(self):
        """Test with single item in list."""
        self.view.items = ['only_item']
        self.view.cursor_idx = 0
        
        visible_count, start_idx, end_idx = self.view.get_visible_range(5, 2)
        
        assert visible_count == 1
        assert start_idx == 0
        assert end_idx == 1
        assert self.view.scroll_offset == 0
    
    def test_scroll_bounds_checking(self):
        """Test that scroll offset stays within bounds."""
        # Try to set scroll offset beyond bounds
        self.view.cursor_idx = 20  # Beyond list size
        visible_count, start_idx, end_idx = self.view.get_visible_range(5, 2)
        
        # Should cap at maximum valid offset
        max_offset = len(self.view.items) - 3  # 10 items - 3 visible = 7
        assert self.view.scroll_offset == max_offset