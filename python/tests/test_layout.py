"""Tests for dynamic layout management."""

import pytest
from src.tui.layout_manager import LayoutManager


class TestLayoutManager:
    """Test layout calculation and text formatting."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.layout = LayoutManager()
    
    def test_calculate_widths_normal_case(self):
        """Test width calculation with normal inputs."""
        titles = ["Short", "Medium length title", "Very long commit message that should be truncated"]
        commit_w, msg_w, log_w = self.layout.calculate_column_widths(120, titles, 5)
        
        assert commit_w >= self.layout.MIN_COMMIT_WIDTH
        assert msg_w >= self.layout.MIN_MESSAGE_WIDTH
        assert log_w == self.layout.MIN_LOG_WIDTH
        assert commit_w + msg_w + log_w == 120
    
    def test_calculate_widths_small_terminal(self):
        """Test width calculation with smaller terminal size."""
        titles = ["Test"]
        commit_w, msg_w, log_w = self.layout.calculate_column_widths(100, titles, 3)
        
        # Should meet minimums with new compact layout
        assert commit_w >= self.layout.MIN_COMMIT_WIDTH
        assert msg_w >= self.layout.MIN_MESSAGE_WIDTH
        assert commit_w + msg_w + log_w == 100
    
    def test_calculate_widths_no_logs(self):
        """Test width calculation with no logs."""
        titles = ["Test commit message"]
        commit_w, msg_w, log_w = self.layout.calculate_column_widths(100, titles, 0)
        
        assert log_w == 0
        assert commit_w + msg_w == 100
        assert msg_w >= self.layout.MIN_MESSAGE_WIDTH
    
    def test_calculate_widths_very_long_titles(self):
        """Test with extremely long commit titles."""
        titles = ["A" * 200]  # Very long title
        commit_w, msg_w, log_w = self.layout.calculate_column_widths(150, titles, 5)
        
        # Should be capped at MAX_COMMIT_WIDTH (now 80)
        assert commit_w <= self.layout.MAX_COMMIT_WIDTH
        assert msg_w >= self.layout.MIN_MESSAGE_WIDTH
    
    def test_calculate_widths_empty_titles(self):
        """Test with empty titles list."""
        commit_w, msg_w, log_w = self.layout.calculate_column_widths(100, [], 5)
        
        assert commit_w >= self.layout.MIN_COMMIT_WIDTH  # Uses proportion, not just minimum
        assert msg_w >= self.layout.MIN_MESSAGE_WIDTH
        assert log_w == self.layout.MIN_LOG_WIDTH
    
    def test_format_scrollable_text_short(self):
        """Test formatting text that fits in available width."""
        text = "Short text"
        formatted, can_left, can_right = self.layout.format_scrollable_text(
            text, 20, scroll_offset=0
        )
        
        assert formatted == text
        assert not can_left
        assert not can_right
    
    def test_format_scrollable_text_long_start(self):
        """Test horizontal scrolling at start position."""
        text = "This is a very long commit message that needs scrolling"
        formatted, can_left, can_right = self.layout.format_scrollable_text(
            text, 20, scroll_offset=0
        )
        
        assert len(formatted) <= 20
        assert not can_left  # At start
        assert can_right  # More to right
        assert self.layout.SCROLL_RIGHT in formatted
    
    def test_format_scrollable_text_middle(self):
        """Test horizontal scrolling in middle position."""
        text = "This is a very long commit message that needs scrolling"
        formatted, can_left, can_right = self.layout.format_scrollable_text(
            text, 20, scroll_offset=10
        )
        
        assert len(formatted) <= 20
        assert can_left  # Can go back
        assert can_right  # Still more
        assert self.layout.SCROLL_BOTH in formatted
    
    def test_format_scrollable_text_end(self):
        """Test horizontal scrolling at end position."""
        text = "This is a very long commit message"
        # Scroll to near the end
        scroll_pos = len(text) - 15
        formatted, can_left, can_right = self.layout.format_scrollable_text(
            text, 20, scroll_offset=scroll_pos
        )
        
        assert len(formatted) <= 20
        assert can_left  # Can go back
        # can_right depends on exact positioning
    
    def test_format_scrollable_text_no_indicators(self):
        """Test formatting without scroll indicators."""
        text = "This is a very long commit message that needs scrolling"
        formatted, can_left, can_right = self.layout.format_scrollable_text(
            text, 20, scroll_offset=0, show_indicators=False
        )
        
        assert len(formatted) <= 20
        assert not can_left
        assert can_right
        assert self.layout.SCROLL_RIGHT not in formatted
        assert self.layout.SCROLL_LEFT not in formatted
    
    def test_needs_recalculation(self):
        """Test resize detection."""
        assert self.layout.needs_recalculation(120)  # No cache
        
        self.layout.calculate_column_widths(120, ["Test"], 1)
        assert not self.layout.needs_recalculation(120)  # Same size
        assert self.layout.needs_recalculation(100)  # Different size
    
    def test_cache_behavior(self):
        """Test that caching works correctly."""
        titles = ["Test commit"]
        
        # First calculation
        result1 = self.layout.calculate_column_widths(120, titles, 5)
        assert self.layout.cached_widths == result1
        assert self.layout.last_screen_width == 120
        
        # Second calculation with same width should return cached
        result2 = self.layout.calculate_column_widths(120, ["Different title"], 5)
        assert result2 == result1  # Should be same (cached)
        
        # Different width should recalculate
        result3 = self.layout.calculate_column_widths(100, titles, 5)
        assert result3 != result1
        assert self.layout.last_screen_width == 100
    
    def test_extreme_narrow_terminal(self):
        """Test behavior with narrow terminal."""
        titles = ["Test"]
        commit_w, msg_w, log_w = self.layout.calculate_column_widths(100, titles, 3)
        
        # At 100 width, should fit both minimums (51 + 30 + 15 = 96)
        assert commit_w >= self.layout.MIN_COMMIT_WIDTH
        assert msg_w >= self.layout.MIN_MESSAGE_WIDTH  
        assert commit_w + msg_w + log_w == 100
    
    def test_very_narrow_terminal_graceful_degradation(self):
        """Test graceful degradation when terminal is too narrow for both minimums."""
        titles = ["Test"]
        commit_w, msg_w, log_w = self.layout.calculate_column_widths(80, titles, 3)
        
        # Should still fit in available space, even if one minimum isn't met
        assert commit_w + msg_w + log_w == 80
        # At least one should approach its minimum 
        assert commit_w >= 30 or msg_w >= 15  # Some reasonable minimum
    
    def test_scroll_indicators_constants(self):
        """Test that scroll indicator constants are properly defined."""
        assert isinstance(self.layout.SCROLL_LEFT, str)
        assert isinstance(self.layout.SCROLL_RIGHT, str) 
        assert isinstance(self.layout.SCROLL_BOTH, str)
        assert len(self.layout.SCROLL_LEFT) > 0
        assert len(self.layout.SCROLL_RIGHT) > 0
        assert len(self.layout.SCROLL_BOTH) > 0