"""Mixin for view-based scrolling without cursor."""

from typing import List


class ViewScrollMixin:
    """Provides view scrolling functionality for read-only content panes."""
    
    def __init__(self):
        """Initialize view scrolling state."""
        self.view_offset = 0  # First line currently visible
        self.total_lines: List[str] = []  # All content lines
    
    def scroll_up(self, lines: int = 1) -> bool:
        """Scroll view up to show earlier content.
        
        Args:
            lines: Number of lines to scroll
            
        Returns:
            True if scrolled, False if already at top
        """
        if self.view_offset > 0:
            self.view_offset = max(0, self.view_offset - lines)
            return True
        return False
    
    def scroll_down(self, lines: int = 1, viewport_height: int = 10) -> bool:
        """Scroll view down to show later content.
        
        Args:
            lines: Number of lines to scroll
            viewport_height: Height of viewport
            
        Returns:
            True if scrolled, False if already at bottom
        """
        # Calculate maximum offset to keep last line visible
        max_offset = max(0, len(self.total_lines) - viewport_height + 2)
        if self.view_offset < max_offset:
            self.view_offset = min(max_offset, self.view_offset + lines)
            return True
        return False
    
    def get_visible_lines(self, viewport_height: int) -> List[str]:
        """Get lines currently visible in viewport.
        
        Args:
            viewport_height: Total height available
            
        Returns:
            List of visible lines
        """
        # Account for borders (2 lines)
        content_height = viewport_height - 2
        end_idx = min(self.view_offset + content_height, len(self.total_lines))
        return self.total_lines[self.view_offset:end_idx]
    
    def reset_view(self) -> None:
        """Reset view to top of content."""
        self.view_offset = 0