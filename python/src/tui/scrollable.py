"""Scrollable view functionality for TUI components."""

from typing import Optional, Tuple


class ScrollableMixin:
    """Mixin providing scrollable view functionality.
    
    Classes using this mixin must have:
    - self.cursor_idx: int - Current cursor position
    - self.items: list - List of items being displayed
    """
    
    def __init__(self):
        """Initialize scrollable state."""
        self.scroll_offset: int = 0
    
    def get_visible_range(self, viewport_height: int, border_size: int = 2) -> Tuple[int, int, int]:
        """Calculate visible range for scrolling.
        
        Args:
            viewport_height: Total height available for display
            border_size: Size of borders to subtract from height
            
        Returns:
            Tuple of (visible_count, start_idx, end_idx)
        """
        if not hasattr(self, 'items') or not self.items:
            return 0, 0, 0
        
        visible_count = min(viewport_height - border_size, len(self.items))
        
        # Adjust scroll offset based on cursor position
        if hasattr(self, 'cursor_idx'):
            if self.cursor_idx < self.scroll_offset:
                self.scroll_offset = self.cursor_idx
            elif self.cursor_idx >= self.scroll_offset + visible_count:
                self.scroll_offset = self.cursor_idx - visible_count + 1
        
        # Ensure scroll offset is within bounds
        max_offset = max(0, len(self.items) - visible_count)
        self.scroll_offset = max(0, min(self.scroll_offset, max_offset))
        
        start_idx = self.scroll_offset
        end_idx = min(start_idx + visible_count, len(self.items))
        
        return visible_count, start_idx, end_idx
    
    def reset_scroll(self) -> None:
        """Reset scroll position to top."""
        self.scroll_offset = 0
    
    def scroll_to_cursor(self, viewport_height: int, border_size: int = 2) -> None:
        """Ensure cursor is visible in viewport.
        
        Args:
            viewport_height: Total height available for display
            border_size: Size of borders to subtract from height
        """
        if not hasattr(self, 'cursor_idx'):
            return
        
        visible_count = min(viewport_height - border_size, len(self.items))
        
        if self.cursor_idx < self.scroll_offset:
            self.scroll_offset = self.cursor_idx
        elif self.cursor_idx >= self.scroll_offset + visible_count:
            self.scroll_offset = self.cursor_idx - visible_count + 1
    
    def scroll_to_bottom(self, viewport_height: int, border_size: int = 2) -> None:
        """Scroll to show the bottom of the list.
        
        Args:
            viewport_height: Total height available for display
            border_size: Size of borders to subtract from height
        """
        if not hasattr(self, 'items') or not self.items:
            return
        
        visible_count = min(viewport_height - border_size, len(self.items))
        self.scroll_offset = max(0, len(self.items) - visible_count)
        
        # Position cursor at bottom of visible area if applicable
        if hasattr(self, 'cursor_idx'):
            self.cursor_idx = min(
                len(self.items) - 1,
                self.scroll_offset + visible_count - 1
            )