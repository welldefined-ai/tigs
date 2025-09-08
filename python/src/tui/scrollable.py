"""Scrollable view functionality for TUI components."""

from typing import Optional, Tuple, List


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
    
    def get_visible_range_variable(
        self, 
        viewport_height: int, 
        item_heights: List[int], 
        border_size: int = 2
    ) -> Tuple[int, int, int]:
        """Calculate visible range for scrolling with variable item heights.
        
        Args:
            viewport_height: Total height available for display
            item_heights: Heights for each item
            border_size: Size of borders to subtract from height
            
        Returns:
            Tuple of (visible_count, start_idx, end_idx)
        """
        if not hasattr(self, 'items') or not self.items:
            return 0, 0, 0
        
        available_height = viewport_height - border_size
        
        # Handle extremely large single item
        if hasattr(self, 'cursor_idx') and self.cursor_idx < len(item_heights):
            cursor_height = item_heights[self.cursor_idx]
            if cursor_height >= available_height:
                # Show only the cursor item with scrolling
                return 1, self.cursor_idx, self.cursor_idx + 1
        
        # Calculate visible range based on scroll offset and heights
        current_height = 0
        start_idx = self.scroll_offset
        end_idx = start_idx
        
        for i in range(start_idx, len(self.items)):
            if i < len(item_heights):
                item_height = item_heights[i]
                if current_height + item_height <= available_height:
                    current_height += item_height
                    end_idx = i + 1
                else:
                    break
        
        # Ensure cursor is visible
        if hasattr(self, 'cursor_idx'):
            if self.cursor_idx < start_idx:
                # Scroll up to show cursor
                self.scroll_offset = self.cursor_idx
                return self.get_visible_range_variable(viewport_height, item_heights, border_size)
            elif self.cursor_idx >= end_idx:
                # Scroll down to show cursor
                # Calculate new start to fit cursor
                new_start = self.cursor_idx
                test_height = item_heights[self.cursor_idx] if self.cursor_idx < len(item_heights) else 3
                
                while new_start > 0 and test_height < available_height:
                    new_start -= 1
                    if new_start < len(item_heights):
                        test_height += item_heights[new_start]
                        if test_height > available_height:
                            new_start += 1
                            break
                
                self.scroll_offset = new_start
                return self.get_visible_range_variable(viewport_height, item_heights, border_size)
        
        return end_idx - start_idx, start_idx, end_idx