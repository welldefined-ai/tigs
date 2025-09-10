"""Tests for ViewScrollMixin functionality."""

import pytest
from src.tui.view_scroll_mixin import ViewScrollMixin


class TestViewScrollMixin:
    """Test ViewScrollMixin class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mixin = ViewScrollMixin()
        # Create test content with 20 lines
        self.mixin.total_lines = [f"Line {i}" for i in range(20)]
    
    def test_initialization(self):
        """Test mixin initializes correctly."""
        mixin = ViewScrollMixin()
        assert mixin.view_offset == 0
        assert mixin.total_lines == []
    
    def test_scroll_up_from_middle(self):
        """Test scrolling up from middle of content."""
        self.mixin.view_offset = 5
        
        # Scroll up one line
        result = self.mixin.scroll_up()
        assert result is True
        assert self.mixin.view_offset == 4
        
        # Scroll up multiple lines
        result = self.mixin.scroll_up(lines=3)
        assert result is True
        assert self.mixin.view_offset == 1
    
    def test_scroll_up_from_top(self):
        """Test scrolling up when already at top."""
        self.mixin.view_offset = 0
        
        result = self.mixin.scroll_up()
        assert result is False
        assert self.mixin.view_offset == 0
    
    def test_scroll_down_from_top(self):
        """Test scrolling down from top of content."""
        self.mixin.view_offset = 0
        
        # Scroll down one line
        result = self.mixin.scroll_down(viewport_height=10)
        assert result is True
        assert self.mixin.view_offset == 1
        
        # Scroll down multiple lines
        result = self.mixin.scroll_down(lines=3, viewport_height=10)
        assert result is True
        assert self.mixin.view_offset == 4
    
    def test_scroll_down_at_bottom(self):
        """Test scrolling down when at bottom."""
        # 20 lines total, viewport of 10, max offset is 12 (20 - 10 + 2)
        self.mixin.view_offset = 12
        
        result = self.mixin.scroll_down(viewport_height=10)
        assert result is False
        assert self.mixin.view_offset == 12
    
    def test_scroll_down_respects_max_offset(self):
        """Test that scrolling down respects maximum offset."""
        self.mixin.view_offset = 10
        
        # Try to scroll down by 5, but max offset is 12
        result = self.mixin.scroll_down(lines=5, viewport_height=10)
        assert result is True
        assert self.mixin.view_offset == 12  # Clamped to max
    
    def test_get_visible_lines(self):
        """Test getting visible lines for viewport."""
        self.mixin.view_offset = 5
        
        # Get visible lines for viewport height of 10
        visible = self.mixin.get_visible_lines(viewport_height=10)
        
        # Should return lines 5-12 (8 lines, accounting for 2 border lines)
        assert len(visible) == 8
        assert visible[0] == "Line 5"
        assert visible[-1] == "Line 12"
    
    def test_get_visible_lines_at_end(self):
        """Test getting visible lines at end of content."""
        self.mixin.view_offset = 15
        
        # Get visible lines for viewport height of 10
        visible = self.mixin.get_visible_lines(viewport_height=10)
        
        # Should return lines 15-19 (5 lines remaining)
        assert len(visible) == 5
        assert visible[0] == "Line 15"
        assert visible[-1] == "Line 19"
    
    def test_reset_view(self):
        """Test resetting view to top."""
        self.mixin.view_offset = 10
        
        self.mixin.reset_view()
        
        assert self.mixin.view_offset == 0
    
    def test_empty_content(self):
        """Test behavior with empty content."""
        self.mixin.total_lines = []
        
        # Scrolling should return False
        assert self.mixin.scroll_up() is False
        assert self.mixin.scroll_down(viewport_height=10) is False
        
        # Get visible lines should return empty
        visible = self.mixin.get_visible_lines(viewport_height=10)
        assert visible == []
    
    def test_small_content(self):
        """Test with content smaller than viewport."""
        self.mixin.total_lines = ["Line 1", "Line 2", "Line 3"]
        
        # Max offset should be 0 (all content fits)
        result = self.mixin.scroll_down(viewport_height=10)
        assert result is False
        assert self.mixin.view_offset == 0
        
        # All lines should be visible
        visible = self.mixin.get_visible_lines(viewport_height=10)
        assert len(visible) == 3
        assert visible == ["Line 1", "Line 2", "Line 3"]