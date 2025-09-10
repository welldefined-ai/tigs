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
    
    def calculate_items_that_fit(self, start_idx: int, item_heights: List[int], 
                                 available_height: int) -> int:
        """Calculate how many items fit starting from start_idx.
        
        Args:
            start_idx: Starting index
            item_heights: Heights for each item
            available_height: Available vertical space
            
        Returns:
            End index (exclusive) of items that fit
        """
        current_height = 0
        end_idx = start_idx
        n = min(len(item_heights), len(self.items))
        
        for i in range(start_idx, n):
            if i < len(item_heights):
                item_height = item_heights[i]
                if current_height + item_height <= available_height:
                    current_height += item_height
                    end_idx = i + 1
                else:
                    break
        return end_idx
    
    def find_start_to_include_cursor(self, cursor_idx: int, item_heights: List[int],
                                     available_height: int) -> int:
        """Find the start index that includes the cursor and fills the viewport.
        
        Args:
            cursor_idx: Index that must be visible
            item_heights: Heights for each item
            available_height: Available vertical space
            
        Returns:
            Optimal start index
        """
        if cursor_idx >= len(item_heights):
            return cursor_idx
            
        # Start from cursor and work backwards to fit as much as possible
        new_start = cursor_idx
        current_height = item_heights[cursor_idx]
        
        while new_start > 0 and current_height < available_height:
            new_start -= 1
            if new_start < len(item_heights):
                item_h = item_heights[new_start]
                if current_height + item_h <= available_height:
                    current_height += item_h
                else:
                    new_start += 1
                    break
        
        return new_start
    
    def get_visible_range_variable(
        self, 
        viewport_height: int, 
        item_heights: List[int], 
        border_size: int = 2
    ) -> Tuple[int, int, int]:
        """Calculate visible range for scrolling with variable item heights.
        
        Uses minimal adjustment: only scrolls when cursor moves outside view.
        
        Args:
            viewport_height: Total height available for display
            item_heights: Heights for each item
            border_size: Size of borders to subtract from height
            
        Returns:
            Tuple of (visible_count, start_idx, end_idx)
        """
        if not hasattr(self, 'items') or not self.items:
            return 0, 0, 0
            
        n = min(len(item_heights), len(self.items))
        if n == 0:
            return 0, 0, 0
        
        available_height = max(0, viewport_height - border_size)
        
        # Handle extremely large single item
        if hasattr(self, 'cursor_idx') and self.cursor_idx < n:
            cursor_height = item_heights[self.cursor_idx] if self.cursor_idx < len(item_heights) else 0
            if cursor_height >= available_height and available_height > 0:
                # Show only the cursor item
                self.scroll_offset = self.cursor_idx
                return 1, self.cursor_idx, self.cursor_idx + 1
        
        # Minimal adjustment: only change scroll_offset if cursor is not visible
        if hasattr(self, 'cursor_idx'):
            # Calculate what would be visible with current scroll_offset
            end_idx = self.calculate_items_that_fit(self.scroll_offset, item_heights, available_height)
            
            # Only adjust if cursor is outside the visible range
            if self.cursor_idx < self.scroll_offset:
                # Cursor moved above viewport - make it first visible item
                self.scroll_offset = self.cursor_idx
            elif self.cursor_idx >= end_idx:
                # Cursor moved below viewport - adjust minimally to make it visible
                # Find the minimal scroll_offset that includes cursor
                self.scroll_offset = self.find_start_to_include_cursor(
                    self.cursor_idx, item_heights, available_height
                )
            # Otherwise, keep current scroll_offset (cursor is already visible)
        
        # Calculate the actual visible range with the (possibly adjusted) scroll_offset
        end_idx = self.calculate_items_that_fit(self.scroll_offset, item_heights, available_height)
        
        return end_idx - self.scroll_offset, self.scroll_offset, end_idx